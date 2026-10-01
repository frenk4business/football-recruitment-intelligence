"""Season aggregation with explicit provider identities and whole-scope exclusion."""

import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from football_intelligence.dna.features import role_summary
from football_intelligence.profiles.cache import write_json
from football_intelligence.profiles.features import (
    COMMON_IDS,
    COUNT_KEYS,
    NATIVE_COUNTS,
    family,
    native_values,
    values,
)


def load_observations(destination: Path) -> list[dict]:
    with duckdb.connect() as con:
        relation = con.read_parquet(
            str(destination / "provider=*/competition=*/season=*/observations.parquet"),
            hive_partitioning=False,
        )
        names = relation.columns
        return [dict(zip(names, row, strict=True)) for row in relation.fetchall()]


def aggregate_rows(rows: list[dict]) -> dict:
    """All relevant match rows are required; an unreliable appearance poisons eligibility."""
    if not rows:
        raise ValueError("Cannot aggregate an empty player scope")
    identities = {(r["scope"], r["provider"], r["player_id"]) for r in rows}
    if len(identities) != 1 or len({r["match_id"] for r in rows}) != len(rows):
        raise ValueError("Mixed identities or duplicate appearances")
    minutes = sum(r["minutes"] or 0 for r in rows if r["reliable"])
    reasons = sorted({reason for r in rows for reason in r["reasons"]})
    if any(not r["reliable"] for r in rows):
        reasons.append("unresolved_participation_conflict")
    totals = {k: sum(r["c_" + k] for r in rows) for k in COUNT_KEYS}
    native = {
        k: sum(r["n_" + k] for r in rows) if all(r["n_" + k] is not None for r in rows) else None
        for k in NATIVE_COUNTS
    }
    provider = rows[0]["provider"]
    roles: Counter[str] = Counter()
    if provider == "statsbomb":
        for row in rows:
            roles.update(json.loads(row["role_minutes_json"]))
        role = role_summary(dict(roles), sum(r["elapsed_minutes"] or 0 for r in rows))[
            "primary_role"
        ]
        broad: Counter[str] = Counter()
        for key, value in roles.items():
            broad[family(key) or "unknown"] += value
        broad_role = role_summary(dict(broad), sum(r["elapsed_minutes"] or 0 for r in rows))[
            "primary_role"
        ]
    else:
        known = {r["role_family"] for r in rows if r["role_family"]}
        broad_role = next(iter(known)) if len(known) == 1 else None
        role = "GK" if broad_role == "GK" else None
    if not broad_role:
        reasons.append("unknown_or_ambiguous_role")
    if minutes <= 0:
        reasons.append("no_reliable_minutes")
    candidate_values = values(totals, minutes)
    common = {k: candidate_values[k] for k in COMMON_IDS}
    unavailable = [k for k in COMMON_IDS if common[k] is None]
    # Values from unresolved participation may remain local for diagnostics only.
    common_ready = not reasons and broad_role != "GK" and not unavailable
    teams = sorted({r["team_id"] for r in rows})
    return dict(
        id=f"{rows[0]['scope']}-{rows[0]['player_id']}",
        provider=provider,
        scope=rows[0]["scope"],
        player_id=rows[0]["player_id"],
        name=rows[0]["name"],
        teams=teams,
        role=role,
        role_family=broad_role,
        minutes=round(minutes, 3),
        appearances=len(rows),
        first_date=min(r["date"] for r in rows),
        last_date=max(r["date"] for r in rows),
        reliable=not reasons,
        exclusion_reasons=sorted(set(reasons)),
        common_ready=common_ready,
        common_unavailable=unavailable,
        counts=totals,
        native_counts=native,
        common=common,
        native=native_values(provider, native, minutes),
        source_files=sorted({f for r in rows for f in r["source_files"]}),
        minute_methods=sorted({r["minute_method"] for r in rows}),
    )


def aggregate(destination: Path):
    rows = load_observations(destination)
    groups: dict[tuple, list] = defaultdict(list)
    for row in rows:
        groups[(row["scope"], row["player_id"])].append(row)
    profiles = [aggregate_rows(group) for _, group in sorted(groups.items())]
    write_json(destination / "aggregates.json", profiles)
    for scope in sorted({p["scope"] for p in profiles}):
        provider, competition, season = scope.split("-")
        folder = destination / f"provider={provider}/competition={competition}/season={season}"
        pq.write_table(
            pa.Table.from_pylist([p for p in profiles if p["scope"] == scope]),
            folder / "profiles.parquet",
            compression="zstd",
        )
    with duckdb.connect(str(destination / "profiles.duckdb")) as con:
        con.read_parquet(
            str(destination / "provider=*/competition=*/season=*/profiles.parquet"),
            hive_partitioning=False,
            union_by_name=True,
        ).create_view("provider_player_season", replace=True)
        con.execute(
            "CREATE OR REPLACE VIEW provider_player_features AS SELECT id, provider, native FROM provider_player_season"
        )
        con.execute(
            "CREATE OR REPLACE VIEW common_player_features AS SELECT id, common, common_ready FROM provider_player_season"
        )
        con.execute(
            "CREATE OR REPLACE VIEW profile_eligibility AS SELECT id, reliable, exclusion_reasons, minutes, common_ready FROM provider_player_season"
        )
    return profiles


def split_profiles(destination: Path, rows: list[dict] | None = None):
    """Median chronological MATCH split, including players missing from either half."""
    rows = rows if rows is not None else load_observations(destination)
    by_scope: dict[str, list] = defaultdict(list)
    for row in rows:
        by_scope[row["scope"]].append(row)
    splits = []
    cutoffs = {}
    for scope, observations in sorted(by_scope.items()):
        matches = sorted({(r["date"], r["match_id"]) for r in observations})
        early = {mid for _, mid in matches[: len(matches) // 2]}
        cutoffs[scope] = dict(
            first_matches=len(early),
            second_matches=len(matches) - len(early),
            last_first_match=matches[len(early) - 1],
        )
        groups: dict[tuple, list] = defaultdict(list)
        for row in observations:
            groups[(int(row["match_id"] not in early), row["player_id"])].append(row)
        for (half, _), group in sorted(groups.items()):
            splits.append(aggregate_rows(group) | {"half": half})
    return splits, cutoffs
