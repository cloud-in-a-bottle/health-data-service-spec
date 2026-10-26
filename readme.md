# health-data-service

Types and client library for the Cloud in a Bottle health-data service.

## Permissions

The service defines one grant, `read`, which covers every endpoint (metrics, time series, sleep sessions, workouts). It is a global-scoped grant, so one approval applies to every provider. Consumers declare it in their manifest:

```toml
[[services.v2.consumes]]
service = "github.com/imbue-openhost/health-data-service-spec"
shortname = "health"
version = ">=0.1.0"
grants = ["read"]
```

Providers must refuse any service call whose `X-OpenHost-Permissions` header does not include the `read` grant, with:

```json
HTTP 403
{"error": "permission_required", "required_grant": {"grant": "read", "scope": "global"}}
```

The router adds a `grant_url` for the owner to approve it. Requests from the owner's own browser to a provider's UI (marked by the router with `X-OpenHost-Is-Owner: true`) are not service calls and don't need the grant.

`HealthDataClient` raises `PermissionRequiredError` (with `grant_url`) when a provider refuses a call, including from the `*_merged` fan-out methods, instead of returning empty results.

## Design notes

questions:
- should this be quite generic, ie specifying types for the data shapes that we need, but not actually trying to enumerate all the potential metrics?
  - eg "time series", "container", "scalar", etc.
  - and then the metric names just become suggestions/conventions? could have a list of common ones.
  - advantage is that this doesn't limit things to the canonical set of metrics, and you avoid hard questions of what should be included or not.
  - disadvantage is the typing is quite weak, and the client/server we provide here is rather weak.
  - how would apps actually interoperate on novel types?
    - i guess typically a producer would add something first - it's the source of the data
    - and then people would request in the consumer app that they add support for this new data field.
    - dashboarding software could also just display all discovered metrics, regardless of if they're known or not.
- alternatively you fully specify everything
  - means we could fully specify a client+server.
  - more immediately understandable.
  - most readily interoperable.
  - this is the model of apple/android health
    - isn't ideal tho, people end up trying stuff things in metadata fields or whatnot
- some hybrid? standard taxonomy, but apps can also push custom metric names?
  - typing is weirdish here.
  - is there any way to do this cleanly tho? this seems most natural. it's basically #1 but with the "canonical set" baked in somehow.
  - i mean in the client library, we could just have like "get_heart_rate(start, end)` and that calls `get_global_time_series(metric_name="heart rate", start, end)`.
  - or we could have a HeartRateTimeSeries(TimeSeries) where metric_name is pre-filled.



tbh i'm leaning towards just doing #1. it seems simple enough, along with a registry of the actual common structure.
