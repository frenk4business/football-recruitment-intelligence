"""Versioned canonical contracts; provider namespaces never imply resolved identities."""

from datetime import date
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.1.0"


def canonical_id(provider: str, entity: str, provider_id: str | int) -> str:
    return str(uuid5(NAMESPACE_URL, f"fri:{provider}:{entity}:{provider_id}"))


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str
    provider: Literal["statsbomb", "skillcorner"]
    provider_id: str
    provenance_id: str
    observed_on: date


class Competition(Record):
    name: str
    country: str | None = None
    gender: str | None = None
    tier: int | None = None


class Season(Record):
    competition_id: str
    name: str
    start_year: int
    end_year: int


class Team(Record):
    name: str
    country: str | None = None


class Player(Record):
    name: str
    birth_date: date | None = None
    nationality: str | None = None


class Match(Record):
    competition_id: str
    season_id: str
    home_team_id: str
    away_team_id: str
    home_score: int | None = Field(default=None, ge=0)
    away_score: int | None = Field(default=None, ge=0)
    pitch_length: float | None = Field(default=None, gt=0)
    pitch_width: float | None = Field(default=None, gt=0)
    coverage: str


class Lineup(Record):
    match_id: str
    team_id: str
    player_id: str
    starter: bool
    position: str | None = None
    provider_positions_json: str
    minutes: float | None = Field(default=None, ge=0, le=160)
    minutes_method: str
    minutes_reliable: bool = False
    minutes_quality: str = "unavailable"
    minutes_quality_reason: str = "not_reconciled"
    role_minutes_json: str = "{}"
    participation_json: str = "[]"
    substitution_in: str | None = None
    substitution_out: str | None = None


class Event(Record):
    match_id: str
    index: int = Field(ge=0)
    period: int = Field(ge=1, le=5)
    timestamp_seconds: float = Field(ge=0, le=5000)
    team_id: str
    player_id: str | None = None
    event_type: str
    subtype: str | None = None
    outcome: str | None = None
    x: float | None = None
    y: float | None = None
    end_x: float | None = None
    end_y: float | None = None
    raw_x: float | None = None
    raw_y: float | None = None
    possession: int | None = None
    body_part: str | None = None
    xg: float | None = Field(default=None, ge=0, le=1)
    attributes_json: str
    coordinate_orientation: str = "attacking_left_to_right"


class TrackingFrame(Record):
    match_id: str
    frame: int = Field(ge=0)
    period: int = Field(ge=1, le=4)
    timestamp_seconds: float = Field(ge=0)
    provider_timestamp: str
    ball_state: str | None = None
    possession_team_id: str | None = None
    home_attacking_direction: str | None = None


class TrackingObject(Record):
    frame_id: str
    match_id: str
    player_id: str | None = None
    team_id: str | None = None
    object_type: Literal["player", "ball"]
    x: float
    y: float
    z: float | None = None
    raw_x: float
    raw_y: float
    is_detected: bool | None = None
    confidence: float | None = None
    in_pitch: bool
    coordinate_orientation: str = "fixed_pitch"


class EntityMap(BaseModel):
    canonical_id: str
    provider: str
    provider_entity_type: str
    provider_entity_id: str
    provider_name: str | None = None
    match_confidence: float = 1.0
    match_method: str = "exact_provider_id"
    verified: bool = True


TABLES: dict[str, type[BaseModel]] = {
    "competitions": Competition,
    "seasons": Season,
    "teams": Team,
    "players": Player,
    "matches": Match,
    "lineups": Lineup,
    "events": Event,
    "tracking_frames": TrackingFrame,
    "tracking_objects": TrackingObject,
    "provider_entity_map": EntityMap,
}


def frame_from_records(model: type[BaseModel], records: list[dict]) -> pl.DataFrame:
    """Enforce the same types even for empty and all-null columns."""
    dtype = {"string": pl.String, "integer": pl.Int64, "number": pl.Float64, "boolean": pl.Boolean}
    schema = {}
    for name, field in model.model_json_schema()["properties"].items():
        concrete = next((v for v in field.get("anyOf", []) if v.get("type") != "null"), field)
        schema[name] = pl.Date if concrete.get("format") == "date" else dtype[concrete["type"]]
    return pl.DataFrame([model.model_validate(r).model_dump() for r in records], schema=schema)
