"""Feasibility counts only. No candidate scoring or outcome selection."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl

from football_intelligence.dna.cohort import local_cohort, write
from football_intelligence.dna.features import aggregate, eligibility
from football_intelligence.dna.registry import CORE
from football_intelligence.dna.similarity import select
from football_intelligence.recruitment.contracts import ClubContext, RecruitmentScenario
from football_intelligence.translation.dataset import historical_context


def audit(root: Path) -> dict:
    local = local_cohort(root)
    profiles = json.loads((local / "player_profiles.json").read_text())
    selected = select(profiles, 900)
    players = pl.read_parquet(local / "players.parquet")
    transitions = json.loads((root / "data/processed/phase3/transition_episode.json").read_text())
    environments = {
        p["environment_id"]: p
        for p in json.loads((root / "data/processed/phase3/player_environment.json").read_text())
    }
    dataset = json.loads((root / "data/processed/phase3/model_dataset.json").read_text())
    context = pl.read_parquet(root / "data/processed/phase3/team_match_context.parquet").to_dicts()
    observations = pl.read_parquet(
        root / "data/processed/phase3/player_feature_observation.parquet"
    ).to_dicts()
    universes = {}
    moves = []
    for t in transitions:
        if not t["actual_team_change"]:
            continue
        source = environments[t["source_environment_id"]]
        destination = environments[t["destination_environment_id"]]
        target_context = historical_context(context, destination["team_id"], t["source_end"])
        candidate_ids = None
        if not t["eligibility"]["900"]:
            key = (source["season_id"], t["source_end"])
            if key not in universes:
                groups = defaultdict(list)
                for row in observations:
                    if row["season_id"] == key[0] and row["observed_on"] <= key[1]:
                        groups[row["player_id"]].append(row)
                universes[key] = [aggregate(rows) for rows in groups.values()]
            candidate_ids = sorted(
                p["player_id"]
                for p in universes[key]
                if not eligibility(p, 900) and p["primary_role"] == t["destination_role"]
            )
        moves.append(
            dict(
                transition_id=t["transition_id"],
                player_id=t["player_id"],
                decision_date_proxy=t["source_end"],
                source_season=t["source_season"],
                destination_season=t["destination_season"],
                source_minutes=t["source_minutes"],
                destination_minutes=t["destination_minutes"],
                destination_role=t["destination_role"],
                source_profile_complete=all(source["values"][k] is not None for k in CORE),
                future_profile_available=destination["reliable_minutes"] > 0,
                pre_decision_context_available=target_context is not None,
                context_last_date=target_context["last_date"] if target_context else None,
                candidate_ids_900_same_role_at_proxy=candidate_ids,
                eligible_900=not t["eligibility"]["900"],
                exclusion_reasons=t["eligibility"]["900"],
                candidate_universe="Only observed WSL players; availability/contracts/alternative signings unknown",
            )
        )
    roster_counts = Counter((tid, p["primary_role"]) for p in selected for tid in p["team_ids"])
    source_paths = [
        local / "player_profiles.json",
        local / "players.parquet",
        root / "data/processed/phase3/transition_episode.json",
        root / "artifacts/phase2/model_manifest.json",
    ]
    result = dict(
        version="phase4-evidence-v1",
        base_main="6051ce04da532381766c69b83773fd1fe4b732b1",
        cohort="wsl_2023_24",
        season="2023/2024",
        roster_players=len(profiles),
        eligible_900=len(selected),
        roles=dict(sorted(Counter(p["primary_role"] for p in selected).items())),
        eligible_multiple_teams=sum(len(p["team_ids"]) > 1 for p in selected),
        birth_dates_available=players["birth_date"].len() - players["birth_date"].null_count(),
        same_team_role_groups_with_at_least_three=sum(n >= 3 for n in roster_counts.values()),
        same_team_role_groups=dict(sorted((f"{t}:{r}", n) for (t, r), n in roster_counts.items())),
        historical_moves=moves,
        historical_eligible_by_minutes={
            str(m): dict(
                Counter(
                    t["destination_season"]
                    for t in transitions
                    if t["actual_team_change"] and not t["eligibility"][str(m)]
                )
            )
            for m in (450, 600, 900, 1200)
        },
        historical_context_and_role_eligible=dict(
            Counter(p["split"] for p in dataset if p["actual_team_change"])
        ),
        decision="NO-GO for transfer-success evaluation; CONDITIONAL for descriptive retrieval/roster alignment and robustness",
        reasons=[
            "No observed success label or recruitment opportunity set",
            "Only three later-season team changes at 900/900 minutes before further restrictions",
            "2021/22 and 2022/23 absent; no adjacent 2023/24 season backtest",
            "Historical target outcomes already examined in Phase 3",
        ],
        source_sha256={
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in source_paths
        },
        exclusion_counts=dict(Counter(reason for p in profiles for reason in eligibility(p, 900))),
    )
    write(root / "artifacts/phase4/fit_evidence.json", result)
    write(
        root / "artifacts/phase4/requirements.schema.json", RecruitmentScenario.model_json_schema()
    )
    write(root / "artifacts/phase4/club-context.schema.json", ClubContext.model_json_schema())
    return result
