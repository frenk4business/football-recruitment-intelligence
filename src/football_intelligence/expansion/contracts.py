"""Additive v1.2 publication contracts. Existing research contracts remain frozen."""

from typing import Literal

from pydantic import Field, FiniteFloat

from football_intelligence.profiles.contracts import (
    CommonMetrics,
    Number,
    ProfileCounts,
    ProfileIndexEntry,
    ProfileNeighbour,
    ProfileScope,
    RoleFamily,
    StatsBombMetrics,
    StrictModel,
)


class CapabilitySet(StrictModel):
    searchable: bool = True
    provider_profile: bool = True
    similarity: bool = False
    recruitment: bool = False
    common_profile: bool = False
    translation: bool = False
    physical: bool = False
    metadata_only: bool = False


class ExpandedEntry(ProfileIndexEntry):
    capabilities_v12: CapabilitySet
    detail_path: str = Field(pattern=r"^/data/v(11|12)/profiles/[a-zA-Z0-9_./-]+\.json$")


class ExpandedScope(ProfileScope):
    country: str
    scope_label: str
    recruitment: bool
    clubs: list[str]


class ExpandedCounts(ProfileCounts):
    club_seasons: int
    countries: int
    recruitment_profiles: int
    recruitment_clubs: int
    metadata_clubs: int
    metadata_player_records: int
    metadata_competition_seasons: int
    specialist_profiles: int
    verified_persons: Literal[0] = 0


class ExpandedIndex(StrictModel):
    version: Literal["player-database-v12"]
    common_version: Literal["common-profile-v1"]
    common_threshold: int
    search_threshold: Literal[450]
    counts: ExpandedCounts
    scopes: list[ExpandedScope]
    teams: dict[str, str]
    profiles: list[ExpandedEntry]


class ExpandedProvenance(StrictModel):
    source_revision: str
    source_files: list[str]
    source_manifest_sha256: str
    feature_manifest_sha256: str
    build_manifest: Literal["/data/v12/build-manifest.json"]
    code_commit: str
    pipeline_sha256: str


class ExpandedDetail(StrictModel):
    version: Literal["statsbomb-expanded-profile-v1"]
    identity: ProfileIndexEntry
    provider_player_id: int
    provider_role: str
    appearances: int
    first_date: str
    last_date: str
    minute_methods: list[str]
    native: StatsBombMetrics
    common: CommonMetrics | None
    common_unavailable_reasons: list[str]
    similarity_version: Literal["not_evaluated"]
    similarity_scope: Literal["not_evaluated"]
    similarity_scaling: Literal["not_evaluated"]
    neighbours: list[ProfileNeighbour] = Field(max_length=0)
    dna_player_id: None = None
    provenance: ExpandedProvenance


class NativeFeature(StrictModel):
    id: str
    en: str
    nl: str
    family: str
    formula: str
    event_mapping: str
    tags_required: list[int]
    unit: str
    null_semantics: str
    role_suitability: list[str]
    research_note: str


class NativePlayer(StrictModel):
    id: str
    name: str
    scope: str
    role: RoleFamily
    minutes: Number
    teams: list[str]
    features: dict[str, Number]
    percentiles: dict[str, Number]


class RoleContext(StrictModel):
    role: RoleFamily
    players: list[str]
    minutes: Number
    median: dict[str, Number]
    q25: dict[str, Number]
    q75: dict[str, Number]
    percentiles: dict[str, Number]


class NativeClub(StrictModel):
    id: str
    name: str
    roles: list[RoleContext]
    roster_median: dict[str, Number]
    capabilities: dict[str, bool]


class NativeLeague(StrictModel):
    version: Literal["recruitment-fit-wyscout-v1"]
    context_version: Literal["wyscout-club-context-v1"]
    feature_registry_version: Literal["wyscout-recruitment-features-v1"]
    scope: str
    competition: str
    competition_id: str
    country: str
    season: str
    season_id: str
    minutes_threshold: int
    roles: list[str]
    clubs: list[NativeClub]
    players: list[NativePlayer]
    scales: dict[str, dict[str, Number]]
    weights: dict[str, dict[str, Number]]


class NativeLeagueSummary(StrictModel):
    scope: str
    competition: str
    country: str
    season: str
    minutes_threshold: int
    clubs: int
    profiles: int
    path: str


class NativeRegistry(StrictModel):
    version: Literal["recruitment-fit-wyscout-v1"]
    features: list[NativeFeature]
    leagues: list[NativeLeagueSummary]
    source: str
    license: str
    evaluation_path: str


class MetadataClub(StrictModel):
    id: str
    name: str
    country: str
    aliases: list[str]
    stadium: str | None
    source: str
    source_line: int | None
    metadata_updated: str
    seasons: list[str]
    resolution: str | None = None
    performance_scopes: list[str]
    capabilities: dict[str, bool]


class MetadataCompetition(StrictModel):
    id: str
    name: str
    country: str
    season: str
    competition_code: str
    clubs: list[str]
    fixtures: int
    results: int
    source: str
    provider: str
    metadata_updated: str
    capabilities: dict[str, bool]


class MetadataClubSummary(StrictModel):
    id: str
    name: str
    country: str
    aliases: list[str]
    seasons: list[str]
    performance_scopes: list[str]


class MetadataDirectory(StrictModel):
    version: Literal["club-metadata-v1"]
    clubs: list[MetadataClubSummary]
    competitions: list[MetadataCompetition]
    player_countries: dict[str, int]
    player_paths: dict[str, str]
    specialist_path: str
    license: str


class MetadataPerson(StrictModel):
    id: str
    name: str
    country: str
    dob: str | None
    height_m: FiniteFloat | None
    position: str
    source: str
    source_line: int
    capabilities: CapabilitySet
    conflicting_source_rows: bool = False


class MetadataPeople(StrictModel):
    version: Literal["player-metadata-v1"]
    country: str
    metadata_updated: str
    players: list[MetadataPerson]


class MetadataFixtures(StrictModel):
    version: Literal["fixture-metadata-v1"]
    scope: str
    source: str
    # Tuple columns: home club id, away club id, source date text, round, score, status.
    columns: list[str]
    rows: list[list[str | list[int] | None]]


class PhysicalRecord(StrictModel):
    kind: Literal["physical", "obr", "passing"]
    source_file: str
    values: dict[str, str]


class PhysicalPerson(StrictModel):
    id: str
    provider: Literal["skillcorner"]
    provider_player_id: str
    name: str
    season: str
    competition: str
    country: str
    teams: dict[str, str]
    records: list[PhysicalRecord]
    capabilities: CapabilitySet
    scope_note: str
    source: str


class PhysicalSummary(StrictModel):
    id: str
    name: str
    season: str
    competition: str
    teams: list[str]


class PhysicalIndex(StrictModel):
    version: Literal["physical-research-v1"]
    profiles: list[PhysicalSummary]
    source: str
    license: str


class ExpansionManifest(StrictModel):
    version: Literal["v12-build-v1"]
    code_commit: str
    pipeline_sha256: str
    source_manifest_sha256: str
    evaluation_sha256: str
    counts: ExpandedCounts
    public_files: int
    public_bytes: int
    index_gzip_bytes: int
    source_bytes: int
    source_files: int
    partial: Literal[False]
