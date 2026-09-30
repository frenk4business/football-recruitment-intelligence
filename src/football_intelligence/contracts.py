"""Public JSON contracts shared by static export and FastAPI."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class MetricDefinition(Contract):
    id: str
    label_en: str
    label_nl: str
    unit: str
    kind: Literal["derived", "provider_estimate", "observed"]
    providers: list[str]
    description_en: str
    description_nl: str
    formula: str | None = None


class Source(Contract):
    id: str
    name: str
    url: str
    license: str
    license_url: str
    attribution: str
    limitation_en: str
    limitation_nl: str
    revision: str


class CoverageRow(Contract):
    provider: str
    competitions: int
    seasons: int
    matches: int
    teams: int
    players: int
    events: int | None
    tracking_frames: int | None
    tracking_objects: int | None
    date_start: str
    date_end: str
    missing_player_events: int | None
    undetected_objects: int | None
    available_metrics: list[str]


class Coverage(Contract):
    schema_version: str
    generated_at: str
    providers: list[CoverageRow]
    validation_status: str
    warnings: list[str]


class CompetitionSummary(Contract):
    id: str
    provider: str
    name: str
    season: str


class MatchSummary(Contract):
    id: str
    provider: str
    competition: str
    season: str
    date: str
    home: str
    away: str
    score: str
    coverage: str


class PlayerSummary(Contract):
    id: str
    match_id: str
    provider: str
    name: str
    team: str
    position: str | None
    minutes: float | None
    minutes_method: str
    shots: int | None
    passes: int | None
    xg: float | None
    shots_per90: float | None
    pass_completion: float | None


class SpatialBin(Contract):
    x: float
    y: float
    count: int


class EventCount(Contract):
    event_type: str
    count: int


class TrackingPoint(Contract):
    x: float
    y: float
    name: str
    team: str | None
    object_type: str
    is_detected: bool | None


class TrackingSnapshot(Contract):
    frame: int
    timestamp_seconds: float
    period: int
    points: list[TrackingPoint]


class Explorer(Contract):
    schema_version: str
    match: MatchSummary
    players: list[PlayerSummary]
    event_counts: list[EventCount]
    spatial_bins: list[SpatialBin]
    spatial_sample_size: int
    tracking_snapshots: list[TrackingSnapshot]


METRICS = [
    MetricDefinition(
        id="minutes",
        label_en="Minutes",
        label_nl="Minuten",
        unit="minutes",
        kind="derived",
        providers=["statsbomb", "skillcorner"],
        description_en="StatsBomb interval duration, or SkillCorner full-match metadata. Methods differ.",
        description_nl="StatsBomb-intervallen of wedstrijdmetadata van SkillCorner. De methoden verschillen.",
    ),
    MetricDefinition(
        id="shots",
        label_en="Shots",
        label_nl="Schoten",
        unit="count",
        kind="derived",
        providers=["statsbomb"],
        description_en="Shot events excluding penalty shootouts.",
        description_nl="Schoten, exclusief strafschoppenseries.",
    ),
    MetricDefinition(
        id="passes",
        label_en="Passes",
        label_nl="Passes",
        unit="count",
        kind="derived",
        providers=["statsbomb"],
        description_en="Pass events excluding penalty shootouts.",
        description_nl="Pass-events, exclusief strafschoppenseries.",
    ),
    MetricDefinition(
        id="xg",
        label_en="Provider xG",
        label_nl="xG van databron",
        unit="expected goals",
        kind="provider_estimate",
        providers=["statsbomb"],
        description_en="Sum of StatsBomb model estimates supplied with shots, excluding shootouts; not a model built here.",
        description_nl="Som van meegeleverde StatsBomb-modelschattingen, exclusief series; geen eigen model.",
    ),
    MetricDefinition(
        id="shots_per90",
        label_en="Shots / 90",
        label_nl="Schoten / 90",
        unit="per90",
        kind="derived",
        providers=["statsbomb"],
        formula="shots / minutes * 90, if minutes >= 30",
        description_en="Descriptive only. Null below 30 minutes; small samples remain unreliable.",
        description_nl="Alleen beschrijvend. Ontbreekt onder 30 minuten; kleine steekproeven blijven onzeker.",
    ),
    MetricDefinition(
        id="tracking_frames",
        label_en="Tracking frames",
        label_nl="Trackingframes",
        unit="count",
        kind="observed",
        providers=["skillcorner"],
        description_en="Retained frames at 1 Hz within a 60-second window.",
        description_nl="Bewaarde frames op 1 Hz binnen een venster van 60 seconden.",
    ),
]
