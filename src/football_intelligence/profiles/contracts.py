"""Additive v1.1 public contracts; frozen v1.0 schemas remain byte-identical."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

Number = Annotated[FiniteFloat, Field(ge=0)]
Provider = Literal["statsbomb", "wyscout"]
RoleFamily = Literal["GK", "DEF", "MID", "FWD"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProfileCapabilities(StrictModel):
    common: bool
    similarity: bool
    translation: bool
    validated_dna: bool


class ProfileIndexEntry(StrictModel):
    id: str = Field(pattern=r"^(statsbomb|wyscout)-[0-9]+-[0-9]+-[0-9]+$")
    name: str
    provider: Provider
    scope: str
    teams: list[str]
    role: str | None
    role_family: RoleFamily
    minutes: Number
    capabilities: ProfileCapabilities


class ProfileScope(StrictModel):
    id: str
    provider: Provider
    competition: str
    competition_key: str
    season: str
    gender: Literal["male", "female"]
    matches: int = Field(ge=1)
    profiles: int = Field(ge=0)
    common_profiles: int = Field(ge=0)
    similarity_profiles: int = Field(ge=0)
    coverage: str
    first_date: str
    last_date: str


class ProfileCounts(StrictModel):
    providers: int
    competitions: int
    provider_competitions: int
    competition_seasons: int
    seasons: int
    matches: int
    events: int
    profiles: int
    provider_identities: int
    native_profiles: int
    common_profiles: int
    similarity_profiles: int
    translation_profiles: int
    validated_dna_profiles: int


class ProfileIndex(StrictModel):
    version: Literal["player-database-v1"]
    common_version: Literal["common-profile-v1"]
    common_threshold: int
    search_threshold: Literal[450]
    counts: ProfileCounts
    scopes: list[ProfileScope]
    teams: dict[str, str]
    profiles: list[ProfileIndexEntry]


class CommonMetrics(StrictModel):
    non_penalty_shots_per90: Number
    passes_all_per90: Number
    long_passes_all_per90: Number


class StatsBombMetrics(StrictModel):
    open_play_passes_per90: Number | None
    open_play_completion: Number | None
    crosses_per90: Number | None
    pressures_per90: Number | None
    carries_per90: Number | None
    dribbles_per90: Number | None
    tackles_per90: Number | None
    interceptions_per90: Number | None
    recoveries_per90: Number | None
    non_penalty_xg_per90: Number | None


class WyscoutMetrics(StrictModel):
    pass_events_per90: Number | None
    pass_event_completion: Number | None
    crosses_per90: Number | None
    key_passes_per90: Number | None
    duels_per90: Number | None
    attacking_duels_per90: Number | None
    sliding_tackles_per90: Number | None
    interceptions_per90: Number | None
    accelerations_per90: Number | None
    clearances_per90: Number | None


class ProfileProvenance(StrictModel):
    source_revision: str
    source_files: list[str]
    source_manifest_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    feature_manifest_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    build_manifest: Literal["/data/v11/build-manifest.json"]
    code_commit: str = Field(pattern="^[0-9a-f]{40}$")
    pipeline_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class ProfileNeighbour(StrictModel):
    id: str
    distance: Number


class ProfileDetail(StrictModel):
    version: Literal["statsbomb-profile-v2", "wyscout-profile-v1"]
    identity: ProfileIndexEntry
    provider_player_id: int
    provider_role: str
    appearances: int = Field(ge=1)
    first_date: str
    last_date: str
    minute_methods: list[str]
    native: StatsBombMetrics | WyscoutMetrics
    common: CommonMetrics | None
    common_unavailable_reasons: list[str]
    similarity_version: Literal["common-similarity-v1"]
    similarity_scope: Literal["same_provider_competition_season_role"]
    similarity_scaling: Literal["shared_first_half_development_zscore"]
    neighbours: list[ProfileNeighbour] = Field(max_length=10)
    dna_player_id: str | None
    provenance: ProfileProvenance

    @model_validator(mode="after")
    def check_provider(self):
        sb = self.identity.provider == "statsbomb"
        if sb != isinstance(self.native, StatsBombMetrics) or sb != (
            self.version == "statsbomb-profile-v2"
        ):
            raise ValueError("Provider-native profile mismatch")
        if self.identity.capabilities.common != (self.common is not None):
            raise ValueError("Common availability mismatch")
        if not self.identity.capabilities.similarity and self.neighbours:
            raise ValueError("Unsupported similarity")
        return self


class ProfileMetricDefinition(StrictModel):
    id: str
    en: str
    nl: str
    unit: Literal["per90", "fraction"]
    definition_en: str
    definition_nl: str
    statsbomb_mapping: str
    wyscout_mapping: str


class ProfileRegistry(StrictModel):
    version: Literal["common-profile-v1"]
    features: list[ProfileMetricDefinition]
    statsbomb: list[ProfileMetricDefinition]
    wyscout: list[ProfileMetricDefinition]
    coordinate_convention: str
    denominator: str
    excluded_concepts: list[str]
    scaler_policy: str
    evidence_threshold: int
    validation_date: str
    source_versions: dict[str, str]
    definitions_sha256: str


class ProfileBuildManifest(StrictModel):
    version: Literal["player-database-v1"]
    code_commit: str
    pipeline_sha256: str
    source_manifest_sha256: str
    feature_manifest_sha256: str
    evaluation_sha256: str
    public_files: int
    public_bytes: int
    index_bytes: int
    index_gzip_bytes: int
    largest_profile_bytes: int
    counts: ProfileCounts
    partial: Literal[False]


class ProfileBiasSummary(StrictModel):
    auc: Number
    balanced_accuracy: Number
    heldout_profiles: int


class ProfileCoverage(StrictModel):
    version: Literal["player-database-v1"]
    counts: ProfileCounts
    scopes: list[ProfileScope]
    common_threshold: int
    common_features: list[str]
    provider_bias: ProfileBiasSummary
    cross_provider_ranking_enabled: bool
    temporal_mrr: dict[str, Number]
    excluded_profiles: dict[str, int]
    threshold_counts: dict[str, int]
