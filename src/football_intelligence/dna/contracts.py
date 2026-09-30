"""Publication allowlist: derived season profiles, never event or lineup payloads."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from football_intelligence.dna.registry import DNA_VERSION


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class DNAPlayer(PublicModel):
    player_id: str
    name: str
    teams: list[str]
    competition: str
    season: str
    primary_role: str | None
    secondary_role: str | None
    role_shares: dict[str, float]
    multi_role: bool
    minutes: float = Field(ge=0)
    appearances: int = Field(ge=0)
    unreliable_appearances: int = Field(ge=0)
    eligibility: dict[str, list[str]]


class DNAIndex(PublicModel):
    version: str
    cohort: str
    competition: str
    season: str
    thresholds: list[int]
    default_threshold: int
    matches: int
    players: list[DNAPlayer]


class DNAFeatureValue(PublicModel):
    id: str
    value: float | None
    percentile: float | None = Field(ge=0, le=100)


class DNAContribution(PublicModel):
    feature: str
    standardized_difference: float
    squared_contribution: float = Field(ge=0)
    share: float = Field(ge=0, le=1.000001)


class DNANeighbor(PublicModel):
    player_id: str
    name: str
    teams: list[str]
    role: str
    minutes: float
    rank: int
    distance: float = Field(ge=0)
    stability: float = Field(ge=0, le=1)
    similar: list[str]
    different: list[str]
    contributions: list[DNAContribution]
    family_contributions: dict[str, float]


class DNAProfile(PublicModel):
    player: DNAPlayer
    version: str = DNA_VERSION
    cohort: str
    threshold: int
    eligible: bool
    exclusions: list[str]
    comparison_size: int
    features: list[DNAFeatureValue]
    scaled_vector: list[float] | None
    neighbors: list[DNANeighbor]
    neighbor_jaccard: float | None
    bootstrap_samples: int
    bins: list[list[int]]


class DNAMapPoint(PublicModel):
    player_id: str
    name: str
    teams: list[str]
    role: str
    minutes: float
    x: float
    y: float


class DNAMap(PublicModel):
    threshold: int
    method: Literal["PCA"]
    explained_variance: list[float]
    points: list[DNAMapPoint]


class DNAEvaluationRow(PublicModel):
    method: str
    threshold: int
    eligible: int
    queries: int
    recall1: float | None
    recall5: float | None
    recall10: float | None
    mrr: float | None
    bootstrap_jaccard: float
    random_recall5: float


class DNAEvaluation(PublicModel):
    version: str
    default_method: str
    bootstrap_samples: int
    seed: int
    rows: list[DNAEvaluationRow]
