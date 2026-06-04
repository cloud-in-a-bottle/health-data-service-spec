"""Sleep and daily-readiness container types and their metrics.

Covers the SleepSession container plus the sleep/readiness scalar and
time-series metrics (Oura-style daily wellness signals). Types shared with
other domains (Duration, HeartRate, ...) live in specific_types.py.
"""

from __future__ import annotations

from enum import Enum

import attr
import attrs

from .data_types import Container, IntervalSample, Sample, ScalarMetric, TimeSeries
from .specific_types import Duration, HeartRate, HeartRateAvg, HeartRateMin


# ---------------------------------------------------------------------------
# Sample value types
# ---------------------------------------------------------------------------

class SleepStage(str, Enum):
    DEEP = "deep"
    LIGHT = "light"
    REM = "rem"
    AWAKE = "awake"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Sleep / readiness scalar metrics
# ---------------------------------------------------------------------------

@attr.s(auto_attribs=True, frozen=True)
class HRVAvg(ScalarMetric[float]):
    metric_id: str = "average_hrv"
    display_name: str = "Avg HRV"
    unit: str = "ms"


@attr.s(auto_attribs=True, frozen=True)
class BreathRateAvg(ScalarMetric[float]):
    metric_id: str = "average_breath"
    display_name: str = "Avg Breath Rate"
    unit: str = "breaths/min"


@attr.s(auto_attribs=True, frozen=True)
class Efficiency(ScalarMetric[float]):
    metric_id: str = "efficiency"
    display_name: str = "Efficiency"
    unit: str = "%"


@attr.s(auto_attribs=True, frozen=True)
class Score(ScalarMetric[float]):
    """A 0-100 score (readiness, sleep quality, etc)."""
    metric_id: str = "score"
    display_name: str = "Score"
    unit: str | None = None


@attr.s(auto_attribs=True, frozen=True)
class Count(ScalarMetric[int]):
    metric_id: str = "count"
    display_name: str = "Count"
    unit: str | None = None


@attr.s(auto_attribs=True, frozen=True)
class TemperatureDeviation(ScalarMetric[float]):
    metric_id: str = "temperature_deviation"
    display_name: str = "Temp Deviation"
    unit: str = "°C"


# ---------------------------------------------------------------------------
# Time series metric types
# ---------------------------------------------------------------------------

@attr.s(auto_attribs=True, frozen=True)
class HRV_RMSSD(TimeSeries):
    metric_id: str = "hrv_rmssd"
    display_name: str = "Heart Rate Variability (RMSSD)"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class SleepStages(TimeSeries):
    metric_id: str = "sleep_stages"
    display_name: str = "Sleep Stages"
    unit: str | None = None
    samples: list[IntervalSample[SleepStage]] = attrs.Factory(list)


# ---------------------------------------------------------------------------
# Containers: Sleep
# ---------------------------------------------------------------------------

@attr.s(auto_attribs=True, frozen=True)
class SleepSession(Container):
    """A complete sleep event (one night or nap)."""

    # Stage timeline
    stages: SleepStages | None = None

    # Time series during sleep
    heart_rate: HeartRate | None = None
    hrv: HRV_RMSSD | None = None

    # Duration metrics
    total_duration: Duration | None = None
    deep_sleep_duration: Duration | None = None
    light_sleep_duration: Duration | None = None
    rem_sleep_duration: Duration | None = None
    awake_time: Duration | None = None
    time_in_bed: Duration | None = None
    latency: Duration | None = None

    # Heart metrics (session-level summaries)
    average_heart_rate: HeartRateAvg | None = None
    lowest_heart_rate: HeartRateMin | None = None
    average_hrv: HRVAvg | None = None

    # Other metrics
    average_breath: BreathRateAvg | None = None
    efficiency: Efficiency | None = None
    restless_periods: Count | None = None
    sleep_score: Score | None = None

    # id, start, end come from Container.
    source: str | None = None


# ---------------------------------------------------------------------------
# Daily time series (one sample per day)
# ---------------------------------------------------------------------------

# Readiness

@attr.s(auto_attribs=True, frozen=True)
class ReadinessScore(TimeSeries):
    metric_id: str = "readiness_score"
    display_name: str = "Readiness Score"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class ReadinessActivityBalance(TimeSeries):
    metric_id: str = "readiness_activity_balance"
    display_name: str = "Activity Balance"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class ReadinessBodyTemperature(TimeSeries):
    metric_id: str = "readiness_body_temperature"
    display_name: str = "Body Temperature"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class ReadinessHRVBalance(TimeSeries):
    metric_id: str = "readiness_hrv_balance"
    display_name: str = "HRV Balance"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class ReadinessPreviousDayActivity(TimeSeries):
    metric_id: str = "readiness_previous_day_activity"
    display_name: str = "Previous Day Activity"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class ReadinessPreviousNight(TimeSeries):
    metric_id: str = "readiness_previous_night"
    display_name: str = "Previous Night"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class ReadinessRecoveryIndex(TimeSeries):
    metric_id: str = "readiness_recovery_index"
    display_name: str = "Recovery Index"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class ReadinessRestingHeartRate(TimeSeries):
    metric_id: str = "readiness_resting_heart_rate"
    display_name: str = "Resting Heart Rate"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class ReadinessSleepBalance(TimeSeries):
    metric_id: str = "readiness_sleep_balance"
    display_name: str = "Sleep Balance"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class ReadinessSleepRegularity(TimeSeries):
    metric_id: str = "readiness_sleep_regularity"
    display_name: str = "Sleep Regularity"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


# Body signals

@attr.s(auto_attribs=True, frozen=True)
class BodyTemperatureDeviation(TimeSeries):
    metric_id: str = "temperature_deviation"
    display_name: str = "Temperature Deviation"
    unit: str = "°C"
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class BodyTemperatureTrendDeviation(TimeSeries):
    metric_id: str = "temperature_trend_deviation"
    display_name: str = "Temperature Trend Deviation"
    unit: str = "°C"
    samples: list[Sample[float]] = attrs.Factory(list)


# Sleep score

@attr.s(auto_attribs=True, frozen=True)
class SleepScore(TimeSeries):
    metric_id: str = "sleep_score"
    display_name: str = "Sleep Score"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class SleepScoreDeepSleep(TimeSeries):
    metric_id: str = "sleep_score_deep_sleep"
    display_name: str = "Deep Sleep Score"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class SleepScoreEfficiency(TimeSeries):
    metric_id: str = "sleep_score_efficiency"
    display_name: str = "Efficiency Score"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class SleepScoreLatency(TimeSeries):
    metric_id: str = "sleep_score_latency"
    display_name: str = "Latency Score"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class SleepScoreREMSleep(TimeSeries):
    metric_id: str = "sleep_score_rem_sleep"
    display_name: str = "REM Sleep Score"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class SleepScoreRestfulness(TimeSeries):
    metric_id: str = "sleep_score_restfulness"
    display_name: str = "Restfulness Score"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class SleepScoreTiming(TimeSeries):
    metric_id: str = "sleep_score_timing"
    display_name: str = "Timing Score"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)


@attr.s(auto_attribs=True, frozen=True)
class SleepScoreTotalSleep(TimeSeries):
    metric_id: str = "sleep_score_total_sleep"
    display_name: str = "Total Sleep Score"
    unit: str | None = None
    samples: list[Sample[float]] = attrs.Factory(list)
