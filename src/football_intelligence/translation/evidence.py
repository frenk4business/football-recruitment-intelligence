"""Provider-isolated identity and adjacent observed-environment audits."""

import json
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from football_intelligence.data.schema import canonical_id
from football_intelligence.dna.cohort import write

DOMESTIC = {2, 7, 9, 11, 12, 37, 44, 49, 81, 116, 131, 135, 182, 1238}


def normalized_name(value: str) -> str:
    return " ".join(
        "".join(
            c
            for c in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(c)
        ).split()
    )


def identity_status(records: list[dict]) -> tuple[str, list[str]]:
    """Compare metadata only within an exact provider ID; never merge names."""
    reasons = []
    if len({(r["provider"], str(r["provider_player_id"])) for r in records}) != 1:
        reasons.append("provider_identity_mismatch")
    if len({normalized_name(r["name"]) for r in records}) != 1:
        reasons.append("conflicting_names")
    for key in ("nationality", "gender", "birth_date"):
        if len({r[key] for r in records if r.get(key)}) > 1:
            reasons.append("conflicting_" + key)
    return ("quarantined" if reasons else "provider_id_consistent_metadata", reasons)


def role_change(source: str | None, destination: str | None) -> str:
    if not source or not destination:
        return "unknown"
    if source == destination:
        return "same"
    adjacent = [
        set(v)
        for v in [
            ("CB", "FB/WB"),
            ("CB", "DM"),
            ("DM", "CM"),
            ("CM", "AM"),
            ("AM", "W"),
            ("W", "ST"),
            ("W", "FB/WB"),
        ]
    ]
    return "adjacent" if {source, destination} in adjacent else "major"


def adjacent_transitions(environments: list[dict], max_gap_days: int = 450) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    seen = set()
    for e in environments:
        if e["environment_id"] in seen:
            raise ValueError("Duplicate environment")
        seen.add(e["environment_id"])
        groups[e["provider"], e["player_id"], e.get("environment_class", "domestic")].append(e)
    result = []
    for _, group in sorted(groups.items()):
        ordered = sorted(group, key=lambda e: (e["start_date"], e["end_date"], e["environment_id"]))
        for a, b in zip(ordered, ordered[1:], strict=False):
            gap = (date.fromisoformat(b["start_date"]) - date.fromisoformat(a["end_date"])).days
            different_team = a["team_id"] != b["team_id"]
            different_competition = a["competition_id"] != b["competition_id"]
            reasons = []
            if gap <= 0:
                reasons.append("overlapping_observations")
            if gap > max_gap_days:
                reasons.append("observation_gap_over_450_days")
            if b["season_start_year"] - a["season_start_year"] > 1:
                reasons.append("unobserved_intervening_season")
            if (
                a.get("identity_confidence") == "quarantined"
                or b.get("identity_confidence") == "quarantined"
            ):
                reasons.append("rejected_identity")
            if (
                not different_team
                and not different_competition
                and a["season_id"] == b["season_id"]
            ):
                reasons.append("same_environment")
            kind = (
                "cross_league_change"
                if different_competition and different_team
                else "competition_context_change"
                if different_competition
                else "same_league_team_change"
                if different_team and a["season_id"] == b["season_id"]
                else "team_and_season_change"
                if different_team
                else "season_change_same_team"
            )
            result.append(
                dict(
                    transition_id=canonical_id(
                        "translation",
                        "transitions",
                        a["environment_id"] + ":" + b["environment_id"],
                    ),
                    provider=a["provider"],
                    player_id=a["player_id"],
                    source_environment_id=a["environment_id"],
                    destination_environment_id=b["environment_id"],
                    source_end=a["end_date"],
                    destination_start=b["start_date"],
                    gap_days=gap,
                    transition_type=kind,
                    actual_team_change=different_team,
                    cross_country_change=a["country"] != b["country"],
                    source_competition=a["competition"],
                    destination_competition=b["competition"],
                    source_season=a["season"],
                    destination_season=b["season"],
                    gender=a.get("gender"),
                    identity_confidence=a.get("identity_confidence"),
                    role_change=role_change(a.get("role"), b.get("role")),
                    structurally_eligible=not reasons,
                    exclusion_reasons=reasons,
                )
            )
    return result


def audit_catalogue_identities(root: Path) -> dict:
    catalogue = json.loads((root / "artifacts/phase3/source_catalogue.json").read_text())
    if not catalogue["lineup_audit_complete"]:
        raise ValueError("Complete the catalogue lineup audit first")
    raw = root / "data/raw/phase3/statsbomb" / catalogue["revision"]
    records: dict[int, list[dict]] = defaultdict(list)
    all_environments: dict[tuple, list[dict]] = defaultdict(list)
    for c in catalogue["competition_seasons"]:
        matches = json.loads(
            (raw / f"data/matches/{c['competition_id']}/{c['season_id']}.json").read_text()
        )
        for m in matches:
            for team in json.loads((raw / f"data/lineups/{m['match_id']}.json").read_text()):
                for p in team["lineup"]:
                    row = dict(
                        provider="statsbomb",
                        provider_player_id=p["player_id"],
                        player_id=canonical_id("statsbomb", "players", p["player_id"]),
                        name=p["player_name"],
                        nationality=p.get("country", {}).get("name"),
                        gender=c["competition_gender"],
                        competition_id=c["competition_id"],
                        competition=c["competition_name"],
                        season_id=c["season_id"],
                        season=c["season_name"],
                        season_start_year=int(c["season_name"].split("/")[0]),
                        country=c["country_name"],
                        team_id=team["team_id"],
                        team=team["team_name"],
                        date=m["match_date"],
                        match_id=m["match_id"],
                        played=bool(p.get("positions")),
                        environment_class="domestic"
                        if c["competition_id"] in DOMESTIC
                        else "international"
                        if c["competition_international"]
                        else "club_cup",
                    )
                    records[p["player_id"]].append(row)
                    all_environments[p["player_id"], c["competition_id"], c["season_id"]].append(
                        row
                    )
    identities = []
    states = {}
    for pid, rows in sorted(records.items()):
        status, reasons = identity_status(rows)
        states[pid] = status
        identities.append(
            dict(
                provider="statsbomb",
                provider_player_id=pid,
                player_id=rows[0]["player_id"],
                names=sorted({r["name"] for r in rows}),
                status=status,
                reasons=reasons,
                competitions=len({r["competition_id"] for r in rows}),
                seasons=len({r["season_id"] for r in rows}),
                teams=len({r["team_id"] for r in rows}),
                roster_appearances=len(rows),
                appearances=sum(r["played"] for r in rows),
                first_date=min(r["date"] for r in rows),
                last_date=max(r["date"] for r in rows),
            )
        )
    stint_groups = {}
    for key, rows in sorted(all_environments.items()):
        stints: list[list[dict]] = []
        for row in sorted(rows, key=lambda r: (r["date"], r["match_id"], r["team_id"])):
            if not stints or stints[-1][-1]["team_id"] != row["team_id"]:
                stints.append([])
            stints[-1].append(row)
        for stint in stints:
            stint_groups[(*key, stint[0]["team_id"], stint[0]["date"])] = stint
    environments = []
    for key, rows in sorted(stint_groups.items()):
        first = rows[0]
        dates = sorted({r["date"] for r in rows})
        e = {
            k: first[k]
            for k in (
                "provider",
                "provider_player_id",
                "player_id",
                "name",
                "gender",
                "competition_id",
                "competition",
                "season_id",
                "season",
                "season_start_year",
                "country",
                "team_id",
                "team",
                "environment_class",
            )
        }
        e.update(
            environment_id=canonical_id(
                "translation", "screening_environments", ":".join(map(str, key))
            ),
            identity_confidence=states[key[0]],
            start_date=dates[0],
            end_date=dates[-1],
            roster_appearances=len(rows),
            appearances=sum(r["played"] for r in rows),
            reliable_minutes=None,
            minutes_status="not_reconciled_catalogue_screen",
            match_dates=dates,
        )
        environments.append(e)
    domestic = [e for e in environments if e["environment_class"] == "domestic"]
    transitions = adjacent_transitions(domestic)
    lookup = {e["environment_id"]: e for e in domestic}
    matrix: dict[tuple, list[dict]] = defaultdict(list)
    for t in transitions:
        if t["structurally_eligible"] and t["transition_type"] == "cross_league_change":
            matrix[t["gender"], t["source_competition"], t["destination_competition"]].append(t)
    # This is an explicit conservative screening ceiling, not reliable-minute eligibility.
    pairs = [
        dict(
            gender=k[0],
            source=k[1],
            destination=k[2],
            episodes=len(v),
            players=len({t["player_id"] for t in v}),
            at_least_five_appearances_both=sum(
                min(
                    lookup[t["source_environment_id"]]["appearances"],
                    lookup[t["destination_environment_id"]]["appearances"],
                )
                >= 5
                for t in v
            ),
        )
        for k, v in sorted(matrix.items())
    ]
    report = dict(
        revision=catalogue["revision"],
        unique_players=len(identities),
        repeated_ids=sum(p["roster_appearances"] > 1 for p in identities),
        cross_team_ids=sum(p["teams"] > 1 for p in identities),
        cross_season_ids=sum(p["seasons"] > 1 for p in identities),
        cross_competition_ids=sum(p["competitions"] > 1 for p in identities),
        identity_status=dict(Counter(p["status"] for p in identities)),
        anomalies=[p for p in identities if p["reasons"]],
        environments=len(environments),
        domestic_environments=len(domestic),
        domestic_candidates=len(transitions),
        structural_rejections=dict(Counter(r for t in transitions for r in t["exclusion_reasons"])),
        cross_league_matrix=pairs,
        limitation="Catalogue screening only: reliable minutes and feature availability require event reconciliation; overlapping or sparse observations do not establish a contractual transfer.",
    )
    write(root / "data/processed/phase3/catalogue_identities.json", identities)
    write(root / "data/processed/phase3/catalogue_environments.json", environments)
    write(root / "data/processed/phase3/catalogue_transitions.json", transitions)
    write(root / "artifacts/phase3/identity_audit.json", report)
    return report
