"""Reconcile elapsed playing time from explicit participation events, never event counts."""

from collections import defaultdict

from football_intelligence.data.positions import position_group

OFFSETS = {1: 0, 2: 2700, 3: 5400, 4: 6300}


def clock_seconds(value: str) -> float:
    return sum(float(v) * 60**i for i, v in enumerate(reversed(value.split(":"))))


def reconcile(raw: dict) -> dict[int, dict]:
    events = sorted(raw["events"], key=lambda e: (e["period"], e["timestamp"], e["index"]))
    ends: dict[int, float] = {}
    for e in events:
        if e["period"] < 5 and e["type"]["name"] == "Half End":
            ends[e["period"]] = max(ends.get(e["period"], 0), clock_seconds(e["timestamp"]))
    if set(ends) not in ({1, 2}, {1, 2, 3, 4}):
        return {}  # incomplete fixture/source: no new assertion of reliable time
    if not any(e["type"]["name"] == "Starting XI" for e in events):
        return {}
    duration = sum(ends.values())
    roster = {p["player_id"]: p for t in raw["lineups"] for p in t["lineup"]}
    teams = {p["player_id"]: t["team_id"] for t in raw["lineups"] for p in t["lineup"]}
    active: dict[int, tuple[float, str | None]] = {}
    registered: set[int] = set()
    roles: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    segments: dict[int, list[tuple[float, float]]] = defaultdict(list)
    problems: dict[int, set[str]] = defaultdict(set)
    started: set[int] = set()
    xi_teams: set[int] = set()

    def close(pid: int, at: float):
        if pid in active:
            start, role = active.pop(pid)
            if at < start:
                problems[pid].add("backward_participation")
            else:
                segments[pid].append((start, at))
                roles[pid][role or "unknown"] += (at - start) / 60

    for e in events:
        period = e["period"]
        if period > 4:
            continue
        at = sum(v for p, v in ends.items() if p < period) + clock_seconds(e["timestamp"])
        kind = e["type"]["name"]
        pid = e.get("player", {}).get("id")
        if at > duration + 0.05:
            if pid:
                problems[pid].add("event_outside_match")
            continue
        if kind == "Starting XI":
            tid = e["team"]["id"]
            xi = e.get("tactics", {}).get("lineup", [])
            if len(xi) != 11 or tid in xi_teams:
                for p in roster:
                    if teams[p] == tid:
                        problems[p].add("invalid_starting_xi")
            xi_teams.add(tid)
            for q in xi:
                p = q["player"]["id"]
                active[p] = (0.0, position_group(q["position"]["name"]))
                registered.add(p)
                started.add(p)
        elif kind == "Substitution":
            incoming = e["substitution"]["replacement"]["id"]
            previous_role = active.get(pid, (at, None))[1]
            if pid not in registered or incoming in registered or incoming not in roster:
                problems[pid].add("conflicting_substitution")
                problems[incoming].add("conflicting_substitution")
            close(pid, at)
            registered.discard(pid)
            registered.add(incoming)
            positions = roster.get(incoming, {}).get("positions", [])
            matching = [
                p
                for p in positions
                if p["from_period"] == period
                and abs(clock_seconds(p["from"]) - OFFSETS[period] - clock_seconds(e["timestamp"]))
                < 2
            ]
            role = position_group(matching[0]["position"]) if matching else previous_role
            active[incoming] = (at, role)
        elif kind == "Tactical Shift":
            for q in e.get("tactics", {}).get("lineup", []):
                p = q["player"]["id"]
                if p not in registered:
                    problems[p].add("tactical_player_not_registered")
                if p in active:
                    close(p, at)
                    active[p] = (at, position_group(q["position"]["name"]))
        elif kind == "Player Off":
            if pid not in active:
                problems[pid].add("off_without_on")
            close(pid, at)
            if e.get("player_off", {}).get("permanent"):
                registered.discard(pid)
        elif kind == "Player On":
            if pid in active or pid not in registered:
                problems[pid].add("on_without_off")
            positions = roster.get(pid, {}).get("positions", [])
            matching = [
                p
                for p in positions
                if p["from_period"] == period
                and abs(clock_seconds(p["from"]) - OFFSETS[period] - clock_seconds(e["timestamp"]))
                < 2
            ]
            role = position_group(matching[0]["position"]) if matching else None
            active[pid] = (at, role)
        card = (
            e.get("foul_committed", {})
            .get("card", e.get("bad_behaviour", {}).get("card", {}))
            .get("name")
        )
        if card in ("Red Card", "Second Yellow") and pid:
            close(pid, at)
            registered.discard(pid)
    for pid in list(active):
        close(pid, duration)
    result = {}
    for pid, player in roster.items():
        minutes = sum(b - a for a, b in segments[pid]) / 60
        if teams[pid] not in xi_teams:
            problems[pid].add("missing_starting_xi")
        # Check actor evidence against the explicit participation timeline. Never infer minutes from it.
        for e in events:
            if (
                e.get("player", {}).get("id") != pid
                or e["period"] > 4
                or e["type"]["name"]
                in {"Player On", "Player Off", "Bad Behaviour", "Substitution", "Injury Stoppage"}
            ):
                continue
            at = sum(v for p, v in ends.items() if p < e["period"]) + clock_seconds(e["timestamp"])
            if not any(a - 2 <= at <= b + 2 for a, b in segments[pid]):
                problems[pid].add("action_outside_participation")
        interval_total = 0.0
        last_end = -1.0
        valid = True
        for p in player.get("positions", []):
            start = (
                sum(v for k, v in ends.items() if k < p["from_period"])
                + clock_seconds(p["from"])
                - OFFSETS[p["from_period"]]
            )
            end = (
                duration
                if p.get("to") is None
                else sum(v for k, v in ends.items() if k < p["to_period"])
                + clock_seconds(p["to"])
                - OFFSETS[p["to_period"]]
            )
            valid &= 0 <= start <= end <= duration + 0.02 and start >= last_end - 0.02
            last_end = end
            interval_total += (end - start) / 60
        agrees = (
            valid
            and abs(interval_total - minutes) <= max(2, len(player.get("positions", [])) * 2) / 60
        )
        reliable = not problems[pid]
        result[pid] = dict(
            minutes=round(minutes, 6) if reliable else None,
            minutes_reliable=reliable,
            minutes_method="explicit_participation_timeline",
            minutes_quality="reliable"
            if reliable and agrees
            else "reconciled"
            if reliable
            else "conflicting",
            minutes_quality_reason="lineup_and_events_agree"
            if reliable and agrees
            else "reconstructed_from_xi_substitutions_off_on_cards_and_period_ends"
            if reliable
            else ";".join(sorted(problems[pid])),
            role_minutes_json=__import__("json").dumps(
                {k: round(v, 6) for k, v in sorted(roles[pid].items())}, sort_keys=True
            )
            if reliable
            else "{}",
            participation_json=__import__("json").dumps(segments[pid]) if reliable else "[]",
            starter=pid in started,
        )
    return result
