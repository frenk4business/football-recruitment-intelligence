"""Strict aggregate-only contracts: observations, assumptions, estimates and ranges."""

from typing import Literal

from pydantic import Field, model_validator

from football_intelligence.dna.contracts import PublicModel


class TranslationPlayer(PublicModel):
    player_id: str
    name: str
    teams: list[str]
    supported_sources: int = Field(ge=0)


class TranslationTarget(PublicModel):
    environment_id: str
    team_id: str
    team: str
    competition: str
    season: str


class TranslationMetric(PublicModel):
    id: str
    label_en: str
    label_nl: str
    unit: str = "per90"
    selected_method: str


class TranslationIndex(PublicModel):
    version: str
    translated_profile_version: str
    feature_version: str
    observed_dna_version: str
    scope: str
    source_season: str
    target_season: str
    minimum_minutes: int
    prediction_minutes: int
    development_episodes: int
    test_episodes: int
    test_team_changes: int
    players: list[TranslationPlayer]
    targets: list[TranslationTarget]
    roles: list[str]
    metrics: list[TranslationMetric]


class TranslationEnvironment(PublicModel):
    environment_id: str
    team_id: str
    team: str
    competition: str
    season: str
    start_date: str
    end_date: str
    role: str | None
    role_shares: dict[str, float]
    reliable_minutes: float = Field(ge=0)
    appearances: int = Field(ge=0)
    used_as_development_outcome: bool
    supported: bool
    exclusions: list[str]


class TranslationEstimate(PublicModel):
    metric: str
    method: str
    observed_source: float = Field(ge=0)
    expected_target: float = Field(ge=0)
    p10: float = Field(ge=0)
    p90: float = Field(ge=0)
    p025: float = Field(ge=0)
    p975: float = Field(ge=0)
    interval_kind: Literal["posterior_predictive", "empirical_predictive"]
    expected_rate_p10: float | None = Field(default=None, ge=0)
    expected_rate_p90: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def ordered(self):
        if not self.p025 <= self.p10 <= self.p90 <= self.p975:
            raise ValueError("Prediction interval is not ordered")
        if (
            self.expected_rate_p10 is not None
            and self.expected_rate_p90 is not None
            and self.expected_rate_p10 > self.expected_rate_p90
        ):
            raise ValueError("Expected-rate interval is not ordered")
        return self


class TranslationEvidence(PublicModel):
    direct_episodes: int = Field(ge=0)
    direct_players: int = Field(ge=0)
    target_team_role_episodes: int = Field(ge=0)
    role_episodes: int = Field(ge=0)
    development_episodes: int = Field(ge=0)
    development_seasons: list[str]
    relies_on_pooling: bool
    unseen_target_team: bool
    source_context_matches: int = Field(ge=0)
    target_context_matches: int = Field(ge=0)
    context_latest_date: str | None


class TranslationPrediction(PublicModel):
    model_version: str
    source_environment_id: str
    target_environment_id: str
    target_role: str
    status: Literal["supported", "insufficient_evidence", "out_of_scope"]
    exclusions: list[str]
    prediction_minutes: int
    estimates: list[TranslationEstimate]
    research_estimates: list[TranslationEstimate]
    evidence: TranslationEvidence

    @model_validator(mode="after")
    def no_unsupported_numbers(self):
        if self.status != "supported" and (self.estimates or self.research_estimates):
            raise ValueError("Unsupported translation cannot publish estimates")
        if self.status == "supported" and not self.estimates:
            raise ValueError("Supported translation requires estimates")
        return self


class TranslationPlayerDetail(PublicModel):
    player: TranslationPlayer
    model_version: str
    environments: list[TranslationEnvironment]
    predictions: list[TranslationPrediction]


class TranslationEvaluationRow(PublicModel):
    metric: str
    method: str
    n: int
    mae: float
    rmse: float
    coverage50: float = Field(ge=0, le=1)
    coverage80: float = Field(ge=0, le=1)
    coverage95: float = Field(ge=0, le=1)
    width80: float = Field(ge=0)
    selected: bool


class TranslationEvaluation(PublicModel):
    model_version: str
    train: int
    validation: int
    test: int
    test_period: list[str]
    test_team_changes: int
    max_rhat: float
    divergences: int
    rows: list[TranslationEvaluationRow]


class TranslationModels(PublicModel):
    version: str
    scope: str
    provider: str
    source_revision: str
    feature_version: str
    observed_dna_version: str
    supported_competitions: list[str]
    development_period: list[str]
    heldout_period: list[str]
    likelihood: str
    primary_priors_version: str
    selected_methods: dict[str, str]
    model_code_commit: str
