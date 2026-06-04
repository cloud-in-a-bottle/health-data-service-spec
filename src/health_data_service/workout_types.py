"""Workout container types and the metrics specific to workouts.

The Workout hierarchy keeps the base minimal (only what every workout has)
and pushes activity-specific metrics onto subclasses. Types shared with other
domains (Duration, HeartRate, ...) live in specific_types.py.
"""

from __future__ import annotations

from enum import Enum

import attr

from .data_types import Container, ScalarMetric
from .specific_types import Duration, HeartRate, HeartRateAvg, HeartRateMin


class WorkoutType(str, Enum):
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    WALKING = "walking"
    HIKING = "hiking"
    STRENGTH = "strength"
    YOGA = "yoga"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Workout-specific scalar metrics
# ---------------------------------------------------------------------------

@attr.s(auto_attribs=True, frozen=True)
class Calories(ScalarMetric[float]):
    metric_id: str = "calories"
    display_name: str = "Calories"
    unit: str = "kcal"


@attr.s(auto_attribs=True, frozen=True)
class Distance(ScalarMetric[float]):
    metric_id: str = "distance"
    display_name: str = "Distance"
    unit: str = "m"


@attr.s(auto_attribs=True, frozen=True)
class Pace(ScalarMetric[float]):
    """Pace in seconds per kilometer."""
    metric_id: str = "pace"
    display_name: str = "Pace"
    unit: str = "s/km"


@attr.s(auto_attribs=True, frozen=True)
class HeartRateMax(ScalarMetric[float]):
    metric_id: str = "max_heart_rate"
    display_name: str = "Max Heart Rate"
    unit: str = "bpm"


@attr.s(auto_attribs=True, frozen=True)
class Speed(ScalarMetric[float]):
    metric_id: str = "speed"
    display_name: str = "Speed"
    unit: str = "m/s"


@attr.s(auto_attribs=True, frozen=True)
class Intensity(ScalarMetric[float]):
    """Workout intensity (active energy per hour per kg of body weight)."""
    metric_id: str = "intensity"
    display_name: str = "Intensity"
    unit: str = "kcal/hr·kg"


@attr.s(auto_attribs=True, frozen=True)
class Temperature(ScalarMetric[float]):
    metric_id: str = "temperature"
    display_name: str = "Temperature"
    unit: str = "°C"


@attr.s(auto_attribs=True, frozen=True)
class Humidity(ScalarMetric[float]):
    metric_id: str = "humidity"
    display_name: str = "Humidity"
    unit: str = "%"


@attr.s(auto_attribs=True, frozen=True)
class Cadence(ScalarMetric[float]):
    metric_id: str = "cadence"
    display_name: str = "Cadence"
    unit: str = "count/min"


@attr.s(auto_attribs=True, frozen=True)
class StrokeCount(ScalarMetric[float]):
    metric_id: str = "stroke_count"
    display_name: str = "Stroke Count"
    unit: str = "count"


# ---------------------------------------------------------------------------
# Containers: Workouts
# ---------------------------------------------------------------------------

# kw_only lets required and optional fields mix freely across the hierarchy.
@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class Workout(Container):
    """An exercise session. The base holds only what every workout has,
    regardless of activity: effort (HR, intensity), energy and conditions.
    Activity-specific metrics live on subclasses (see DistanceWorkout,
    SwimmingWorkout, etc.). Only fields that may genuinely be absent are
    optional.
    """

    workout_type: str = WorkoutType.OTHER

    # Every workout has these (id, start, end come from Container).
    duration: Duration
    calories: Calories
    source: str

    # May be absent when the sensor/metric wasn't recorded.
    intensity: Intensity | None = None
    average_heart_rate: HeartRateAvg | None = None
    max_heart_rate: HeartRateMax | None = None
    lowest_heart_rate: HeartRateMin | None = None
    heart_rate: HeartRate | None = None
    heart_rate_recovery: HeartRate | None = None
    temperature: Temperature | None = None
    humidity: Humidity | None = None
    is_indoor: bool | None = None


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class DistanceWorkout(Workout):
    """A workout that covers ground (run, cycle, walk, snow sports, ...).
    Distance/speed may be absent (e.g. stationary cycling)."""

    distance: Distance | None = None
    average_speed: Speed | None = None
    max_speed: Speed | None = None
    elevation_gain: Distance | None = None
    elevation_loss: Distance | None = None
    # GPS track as a GPX 1.1 document, when recorded.
    route_gpx: str | None = None


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class RunningWorkout(DistanceWorkout):
    workout_type: str = WorkoutType.RUNNING
    average_pace: Pace | None = None


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class WalkingWorkout(DistanceWorkout):
    workout_type: str = WorkoutType.WALKING
    average_pace: Pace | None = None


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class HikingWorkout(DistanceWorkout):
    workout_type: str = WorkoutType.HIKING
    average_pace: Pace | None = None


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class CyclingWorkout(DistanceWorkout):
    """Cycling reports speed rather than pace; otherwise a typed DistanceWorkout."""

    workout_type: str = WorkoutType.CYCLING


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class SwimmingWorkout(Workout):
    """A swim: distance/speed plus stroke metrics, but no elevation."""

    workout_type: str = WorkoutType.SWIMMING

    distance: Distance | None = None
    average_speed: Speed | None = None
    max_speed: Speed | None = None
    stroke_count: StrokeCount | None = None
    average_cadence: Cadence | None = None
    lap_length: Distance | None = None
    # GPS track as a GPX 1.1 document, when recorded (e.g. open-water swims).
    route_gpx: str | None = None


# Maps a workout_type string to the most specific class for deserialization.
# Unknown types fall back to the base Workout (extra fields are ignored).
WORKOUT_CLASSES: dict[str, type[Workout]] = {
    WorkoutType.RUNNING: RunningWorkout,
    WorkoutType.WALKING: WalkingWorkout,
    WorkoutType.HIKING: HikingWorkout,
    WorkoutType.CYCLING: CyclingWorkout,
    WorkoutType.SWIMMING: SwimmingWorkout,
    "snowboarding": DistanceWorkout,
    "downhill_skiing": DistanceWorkout,
}
