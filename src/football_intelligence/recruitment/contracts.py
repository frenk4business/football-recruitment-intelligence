"""Versioned allowlists keep observations, assumptions and evidence separate."""

from typing import Literal

from pydantic import Field, model_validator

from football_intelligence.dna.contracts import PublicModel
from football_intelligence.dna.registry import CORE, FeatureDefinition

Role = Literal["CB", "FB/WB", "DM", "CM", "AM", "W", "ST"]
Family = Literal["shooting", "creation", "passing", "carrying", "defending"]
RequirementSource = Literal[
    "user_defined", "observed_club_context", "replacement_player", "derived_roster_gap"
]


class RecruitmentRequirement(PublicModel):
    requirement_id: str = Field(min_length=1, max_length=100)
    type: Literal["style_preference", "target_profile", "club_context"] = "style_preference"
    source: RequirementSource = "user_defined"
    feature_id: str
    preference: Literal["exact", "minimum", "maximum", "neutral"]
    value: float = Field(ge=0, le=100)
    weight: Literal[1, 2, 3] = 1
    hard_constraint: bool = False

    @model_validator(mode="after")
    def known_feature(self):
        if self.feature_id not in CORE:
            raise ValueError("Requirement feature must be an existing core Player DNA feature")
        if self.hard_constraint and self.preference not in ("minimum", "maximum"):
            raise ValueError("A hard feature constraint must be a minimum or maximum")
        return self


class RecruitmentConstraints(PublicModel):
    source: Literal["user_defined"] = "user_defined"
    minimum_minutes: int = Field(default=900, ge=900, le=10000)
    minimum_neighbor_stability: float = Field(default=0, ge=0, le=1)
    exclude_same_club: bool = True
    candidate_team_id: str | None = None
    provider: Literal["statsbomb"] = "statsbomb"
    comparison_cohort: Literal["wsl_2023_24"] = "wsl_2023_24"


class RecruitmentScenario(PublicModel):
    version: Literal["requirements-v1"] = "requirements-v1"
    fit_method_version: Literal["recruitment-fit-v1"] = "recruitment-fit-v1"
    club_id: str
    season: Literal["2023/2024"] = "2023/2024"
    target_role: Role
    mode: Literal["find", "replace"] = "find"
    replacement_player_id: str | None = None
    requirements: list[RecruitmentRequirement] = Field(default_factory=list, max_length=18)
    hard_constraints: RecruitmentConstraints = Field(default_factory=RecruitmentConstraints)
    family_weights: dict[Family, Literal[1, 2, 3]] = Field(default_factory=dict)
    translation_mode: Literal["observed_only"] = "observed_only"
    created_from: Literal["custom", "replacement", "adjusted_replacement", "shared"] = "custom"

    @model_validator(mode="after")
    def coherent(self):
        ids = [r.feature_id for r in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("A feature may occur only once in a scenario")
        if self.mode == "replace" and not self.replacement_player_id:
            raise ValueError("Replacement mode requires a reference player")
        return self


class RecruitmentFeature(FeatureDefinition):
    recruitment_relevance: list[Role]
    default_visibility: list[Role]


class ClubFeature(PublicModel):
    feature_id: str
    value: float | None
    percentile: float | None = Field(ge=0, le=100)
    available_matches: int = Field(ge=0)


class RosterPlayer(PublicModel):
    player_id: str
    name: str
    minutes: float = Field(ge=0)
    role: str | None
    profile_eligible: bool
    percentiles: dict[str, float]
    exclusions: list[str]


class ClubRoleContext(PublicModel):
    role: str
    players: list[RosterPlayer]
    reliable_minutes: float = Field(ge=0)
    roster_depth: int = Field(ge=0)
    profile_depth: int = Field(ge=0)
    top_player_minutes_share: float | None = Field(ge=0, le=1)
    minutes_hhi: float | None = Field(ge=0, le=1)
    median: dict[str, float]
    p25: dict[str, float]
    p75: dict[str, float]
    minimum: dict[str, float]
    maximum: dict[str, float]


class ClubContext(PublicModel):
    version: Literal["club-context-v1"] = "club-context-v1"
    provider: Literal["statsbomb"] = "statsbomb"
    club_id: str
    name: str
    competition: str
    season: str
    observation_start: str
    observation_end: str
    matches: int = Field(ge=0)
    team_minutes: float = Field(ge=0)
    source_revision: str
    feature_version: Literal["features-v1"] = "features-v1"
    features: list[ClubFeature]
    roles: list[ClubRoleContext]
