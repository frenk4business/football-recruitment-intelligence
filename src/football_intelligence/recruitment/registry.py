"""Recruitment metadata extends existing feature definitions without changing v1."""

from football_intelligence.dna.registry import REGISTRY
from football_intelligence.recruitment.contracts import RecruitmentFeature, Role

ROLES: list[Role] = ["CB", "FB/WB", "DM", "CM", "AM", "W", "ST"]
VISIBLE: dict[str, list[Role]] = {
    "shots_per90": ["AM", "W", "ST"],
    "shot_assists_per90": ["CM", "AM", "W", "ST"],
    "progressive_passes_per90": ROLES,
    "progressive_carries_per90": ROLES,
    "pressures_per90": ROLES,
    "long_passes_per90": ["CB", "DM"],
    "crosses_per90": ["FB/WB", "W"],
}
RECRUITMENT_FEATURES = [
    RecruitmentFeature(
        **f.model_dump(),
        recruitment_relevance=ROLES,
        default_visibility=VISIBLE.get(f.id, []),
    )
    for f in REGISTRY
    if f.core
]
# These are team event counts / actual team-match minutes, not averages of player rates.
CONTEXT_FEATURES = [
    "passes_per90",
    "progressive_passes_per90",
    "long_passes_per90",
    "progressive_carries_per90",
    "final_third_passes_per90",
    "box_passes_per90",
    "box_carries_per90",
    "shot_assists_per90",
    "crosses_per90",
    "pressures_per90",
    "counterpressures_per90",
    "interceptions_per90",
    "shots_per90",
    "npxg_per90",
]
