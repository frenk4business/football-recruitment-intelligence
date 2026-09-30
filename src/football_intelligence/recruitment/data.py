"""Compose unchanged DNA artifacts into a compact recruitment index."""

import json
from pathlib import Path

from football_intelligence.dna.cohort import local_cohort
from football_intelligence.dna.publish import write
from football_intelligence.dna.registry import CORE
from football_intelligence.recruitment.contracts import RecruitmentIndex, RecruitmentRequirement
from football_intelligence.recruitment.registry import RECRUITMENT_FEATURES


def build_index(root: Path, method: str = "weighted_rms") -> dict:
    public = root / "artifacts/phase2/public"
    dna = json.loads((public / "index.json").read_text())
    profiles = {
        p["player_id"]: p
        for p in json.loads((local_cohort(root) / "player_profiles.json").read_text())
    }
    clubs = json.loads((root / "artifacts/phase4/club_context.json").read_text())
    candidates = []
    for p in dna["players"]:
        detail = json.loads((public / "900" / (p["player_id"] + ".json")).read_text())
        candidates.append(
            dict(
                player_id=p["player_id"],
                name=p["name"],
                team_ids=profiles[p["player_id"]]["team_ids"],
                teams=p["teams"],
                role=p["primary_role"],
                minutes=p["minutes"],
                appearances=p["appearances"],
                eligible=detail["eligible"],
                exclusions=detail["exclusions"],
                neighbor_stability=detail["neighbor_jaccard"],
                percentiles={
                    f["id"]: f["percentile"]
                    for f in detail["features"]
                    if f["id"] in CORE and f["percentile"] is not None
                },
                multi_club=len(p["teams"]) > 1,
            )
        )
    result = RecruitmentIndex.model_validate(
        dict(
            competition=dna["competition"],
            observation_start=min(c["observation_start"] for c in clubs),
            observation_end=max(c["observation_end"] for c in clubs),
            method=method,
            roles=sorted({p["role"] for p in candidates if p["eligible"]}),
            players=sorted(candidates, key=lambda p: p["player_id"]),
            clubs=[
                {k: c[k] for k in ["club_id", "name", "season", "matches"]}
                for c in sorted(clubs, key=lambda c: c["name"])
            ],
            features=[f.model_dump() for f in RECRUITMENT_FEATURES],
        )
    ).model_dump()
    write(root / "artifacts/phase4/candidate_index.json", result)
    return result


def replacement_requirements(player: dict) -> list[RecruitmentRequirement]:
    if not player["eligible"]:
        raise ValueError("Replacement profile is unsupported")
    return [
        RecruitmentRequirement(
            requirement_id=f,
            feature_id=f,
            preference="exact",
            value=player["percentiles"][f],
            source="replacement_player",
            type="target_profile",
        )
        for f in sorted(CORE)
    ]


def research_requirements() -> list[RecruitmentRequirement]:
    return [
        RecruitmentRequirement(requirement_id=f, feature_id=f, preference="minimum", value=v)
        for f, v in [
            ("progressive_passes_per90", 75),
            ("progressive_carries_per90", 70),
            ("pressures_per90", 75),
        ]
    ]
