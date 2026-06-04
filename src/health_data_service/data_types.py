"""Health data service interface types.

These attrs classes define the wire format for the OpenHost health-data
service (github.com/imbue-openhost/openhost/services/health-data).
Providers serialize these to JSON; consumers deserialize them.

All timestamps are datetime.datetime objects (should be timezone-aware UTC).
On the wire they are serialized as ISO 8601 strings.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

import attr
import attrs

## Metric catalog

class MetricKind(str, Enum):
    TIME_SERIES = "time_series"
    SCALAR = "scalar"


@attr.s(auto_attribs=True, frozen=True)
class MetricType:
    """Describes an available metric a provider can serve."""
    metric_id: str
    display_name: str
    kind: MetricKind = MetricKind.TIME_SERIES
    unit: str | None = None


## Samples

@attr.s(auto_attribs=True, frozen=True)
class Sample[T]:
    timestamp: datetime
    value: T


@attr.s(auto_attribs=True, frozen=True)
class IntervalSample[T](Sample[T]):
    # this sample covers the interval [timestamp, end_timestamp)
    end_timestamp: datetime


## Metrics

@attr.s(auto_attribs=True, frozen=True)
class ScalarMetric[T]:
    """A single metric with no timestamp, usually associated with a container."""
    # Metric identifier, e.g. "heart_rate"
    metric_id: str
    display_name: str

    # Unit of measurement, e.g. "bpm"
    unit: str | None

    value: T

    # Data source identifier, e.g. "oura", "apple_watch", etc
    source: str


@attr.s(auto_attribs=True, frozen=True)
class TimeSeries:
    """A sequence of samples for one metric."""
    # Metric identifier, e.g. "heart_rate"
    metric_id: str
    display_name: str

    # Unit of measurement, e.g. "bpm"
    unit: str | None

    samples: list[Sample]

    # Data source identifier, e.g. "oura", "apple_watch", etc
    source: str


@attr.s(auto_attribs=True, frozen=True)
class Container:
    """Groups metrics together that are derived from a single event, eg a sleep session or workout."""
    start: datetime
    end: datetime
    # Stable identifier for the event from its source.
    id: str
