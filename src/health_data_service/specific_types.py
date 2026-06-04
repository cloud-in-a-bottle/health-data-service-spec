"""Concrete metric types shared across health domains.

These subclass the generic types in data_types.py and are used by more than
one domain (sleep and workouts). Domain-specific types live in
workout_types.py and sleep_types.py.
"""

from __future__ import annotations

import attr
import attrs

from .data_types import Sample, ScalarMetric, TimeSeries


# ---------------------------------------------------------------------------
# Scalar metric types
# ---------------------------------------------------------------------------

@attr.s(auto_attribs=True, frozen=True)
class Duration(ScalarMetric[float]):
    metric_id: str = "duration"
    display_name: str = "Duration"
    unit: str = "min"


@attr.s(auto_attribs=True, frozen=True)
class HeartRateAvg(ScalarMetric[float]):
    metric_id: str = "average_heart_rate"
    display_name: str = "Avg Heart Rate"
    unit: str = "bpm"


@attr.s(auto_attribs=True, frozen=True)
class HeartRateMin(ScalarMetric[float]):
    metric_id: str = "lowest_heart_rate"
    display_name: str = "Lowest Heart Rate"
    unit: str = "bpm"


# ---------------------------------------------------------------------------
# Time series metric types
# ---------------------------------------------------------------------------

@attr.s(auto_attribs=True, frozen=True)
class HeartRate(TimeSeries):
    metric_id: str = "heart_rate"
    display_name: str = "Heart Rate"
    unit: str = "bpm"
    samples: list[Sample[float]] = attrs.Factory(list)
