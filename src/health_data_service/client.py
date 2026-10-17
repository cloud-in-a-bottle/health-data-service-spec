"""Consumer client for the OpenHost health-data service.

Usage::

    from health_data_service import HealthDataClient, TimeSeriesRequest

    async with HealthDataClient() as client:
        hr = await client.get_time_series(TimeSeriesRequest(metric="heart_rate", start=...))
        sessions = await client.get_sleep_sessions(SleepSessionsRequest(start=...))
        runs = await client.get_workouts(WorkoutsRequest(workout_type="running", limit=10))
        full = await client.get_workout(runs[0].id)  # heart-rate trace + route

By default reads ``OPENHOST_ROUTER_URL`` and ``OPENHOST_APP_TOKEN`` from the
environment (set automatically inside OpenHost containers). The service
shortname defaults to ``"health"`` — override if your manifest uses a
different ``[[services.v2.consumes]].shortname``.
"""

from __future__ import annotations

import asyncio
import logging
import os
from types import TracebackType

import cattrs
from cattrs.preconf.json import make_converter
import httpx

from .data_types import (
    MetricType,
    Sample,
    TimeSeries,
)
from .sleep_types import SleepSession
from .workout_types import WORKOUT_CLASSES, Workout
from .permissions import PermissionRequiredError, raise_for_permission_required
from .request_types import (
    SleepSessionsRequest,
    TimeSeriesRequest,
    WorkoutsRequest,
)

log = logging.getLogger(__name__)

converter = make_converter()

# Register hooks so cattrs can structure generic Sample[T] from JSON.
# TimeSeries samples are always float-valued; the generic parameter
# can't be inferred from the JSON payload alone.
def _structure_sample(val, _):
    from datetime import datetime
    ts = val["timestamp"]
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    return Sample(timestamp=ts, value=val["value"])

converter.register_structure_hook(Sample, _structure_sample)

SERVICE_URL = "github.com/imbue-openhost/health-data-service-spec"


def _to_params(req: object) -> dict[str, str]:
    """Unstructure an attrs request to query params, dropping None values."""
    raw = cattrs.unstructure(req)
    return {k: str(v) for k, v in raw.items() if v is not None}


def _check(resp: httpx.Response) -> None:
    """Raise PermissionRequiredError for a missing grant, else raise_for_status."""
    if resp.status_code == 403:
        try:
            body = resp.json()
        except ValueError:
            body = None
        raise_for_permission_required(resp.status_code, body)
    resp.raise_for_status()


def _structure_workout(w: dict) -> Workout:
    """Structure a workout into the subclass for its type, so activity-
    specific fields (distance, pace, route_gpx, ...) are retained."""
    return converter.structure(w, WORKOUT_CLASSES.get(w.get("workout_type"), Workout))


def _structure_workouts(data: list[dict]) -> list[Workout]:
    return [_structure_workout(w) for w in data]


class HealthDataClient:
    """Async client for the health-data service."""

    def __init__(
        self,
        *,
        router_url: str | None = None,
        app_token: str | None = None,
        shortname: str = "health",
    ) -> None:
        self._router_url = (
            router_url or os.environ["OPENHOST_ROUTER_URL"]
        ).rstrip("/")
        self._app_token = app_token or os.environ["OPENHOST_APP_TOKEN"]
        self._shortname = shortname
        self._base_url = f"{self._router_url}/api/services/v2/call/{self._shortname}"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> HealthDataClient:
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._app_token}"},
            timeout=30,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Use 'async with HealthDataClient() as client:'")
        return self._client

    # ------------------------------------------------------------------
    # Single-provider methods
    # ------------------------------------------------------------------

    async def list_metrics(self) -> list[MetricType]:
        resp = await self._http.get("/v1/metrics")
        _check(resp)
        return converter.structure(resp.json()["metrics"], list[MetricType])

    async def get_time_series(self, req: TimeSeriesRequest) -> TimeSeries:
        resp = await self._http.get("/v1/time-series", params=_to_params(req))
        _check(resp)
        return converter.structure(resp.json(), TimeSeries)

    async def get_sleep_sessions(self, req: SleepSessionsRequest) -> list[SleepSession]:
        resp = await self._http.get("/v1/sleep-sessions", params=_to_params(req))
        _check(resp)
        return converter.structure(resp.json()["data"], list[SleepSession])

    async def get_workouts(self, req: WorkoutsRequest) -> list[Workout]:
        """List workouts as summaries: scalar metrics only, no per-sample
        time series or route. Use ``get_workout`` for a single workout's full
        detail (heart-rate trace, GPS route)."""
        resp = await self._http.get("/v1/workouts", params=_to_params(req))
        _check(resp)
        return _structure_workouts(resp.json()["data"])

    async def get_workout(self, workout_id: str) -> Workout | None:
        """Fetch one workout with full detail (heart-rate samples, route GPX).
        Returns None if the provider doesn't have it."""
        resp = await self._http.get(f"/v1/workouts/{workout_id}")
        if resp.status_code == 404:
            return None
        _check(resp)
        return _structure_workout(resp.json())

    # ------------------------------------------------------------------
    # Provider discovery + fan-out
    # ------------------------------------------------------------------

    async def discover_providers(self) -> list[dict]:
        """Discover all providers of this service."""
        try:
            resp = await self._http.get(
                f"{self._router_url}/api/services/v2/providers",
                params={"service": SERVICE_URL},
            )
            if resp.status_code == 200:
                data = resp.json()
                # The router returns a bare list; older routers wrapped it as {"providers": [...]}.
                return data if isinstance(data, list) else data.get("providers", [])
        except Exception:
            log.exception("Provider discovery failed")
        return []

    async def _call_provider(
        self, provider: dict, path: str, params: dict | None = None,
    ) -> dict | None:
        """Call a specific provider, return parsed JSON or None on failure.

        A missing grant raises PermissionRequiredError rather than being dropped like other
        failures: grants are global, so every provider would refuse, and silently returning
        no data would hide why."""
        headers = {"X-OpenHost-Provider": provider["app_id"]}
        try:
            resp = await self._http.get(path, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 403:
                _check(resp)
        except PermissionRequiredError:
            raise
        except Exception:
            log.warning("Service call to %s failed", provider.get("app_name"))
        return None

    async def _fan_out(self, path: str, params: dict | None = None) -> list[dict]:
        """Call all running providers in parallel, return list of JSON responses."""
        providers = await self.discover_providers()
        running = [p for p in providers if p.get("status") == "running"]

        if not running:
            resp = await self._http.get(path, params=params)
            if resp.status_code == 403:
                _check(resp)
            return [resp.json()] if resp.status_code == 200 else []

        results = await asyncio.gather(
            *[self._call_provider(p, path, params) for p in running]
        )
        return [r for r in results if r is not None]

    async def list_metrics_merged(self) -> list[MetricType]:
        results = await self._fan_out("/v1/metrics")
        seen: set[str] = set()
        merged: list[MetricType] = []
        for r in results:
            for m in converter.structure(r.get("metrics", []), list[MetricType]):
                if m.metric_id not in seen:
                    seen.add(m.metric_id)
                    merged.append(m)
        return merged

    async def get_time_series_merged(self, req: TimeSeriesRequest) -> TimeSeries:
        results = await self._fan_out("/v1/time-series", _to_params(req))
        if not results:
            return TimeSeries(
                metric_id=req.metric, display_name=req.metric,
                unit=None, samples=[], source="",
            )
        all_ts = [converter.structure(r, TimeSeries) for r in results]
        first = all_ts[0]
        all_samples = []
        for ts in all_ts:
            all_samples.extend(ts.samples)
        all_samples.sort(key=lambda s: s.timestamp)
        return TimeSeries(
            metric_id=first.metric_id,
            display_name=first.display_name,
            unit=first.unit,
            samples=all_samples,
            source=first.source,
        )

    async def get_sleep_sessions_merged(self, req: SleepSessionsRequest) -> list[SleepSession]:
        results = await self._fan_out("/v1/sleep-sessions", _to_params(req))
        all_sessions: list[SleepSession] = []
        for r in results:
            all_sessions.extend(
                converter.structure(r.get("data", []), list[SleepSession])
            )
        all_sessions.sort(key=lambda s: s.start, reverse=True)
        if req.limit is not None:
            all_sessions = all_sessions[:req.limit]
        return all_sessions

    async def get_workouts_merged(self, req: WorkoutsRequest) -> list[Workout]:
        results = await self._fan_out("/v1/workouts", _to_params(req))
        all_workouts: list[Workout] = []
        for r in results:
            all_workouts.extend(_structure_workouts(r.get("data", [])))
        all_workouts.sort(key=lambda s: s.start, reverse=True)
        if req.limit is not None:
            all_workouts = all_workouts[:req.limit]
        return all_workouts

    async def get_workout_merged(self, workout_id: str) -> Workout | None:
        """Fetch one workout's full detail, querying every provider and
        returning the first that has it (ids are provider-unique)."""
        results = await self._fan_out(f"/v1/workouts/{workout_id}")
        for r in results:
            if r:
                return _structure_workout(r)
        return None
