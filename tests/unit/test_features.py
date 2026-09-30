import pytest

from football_intelligence.dna.features import eligibility, per90, progressive, role_summary
from football_intelligence.dna.registry import CORE, REGISTRY


@pytest.mark.parametrize(
    "value,minutes,expected",
    [(2, 60, 3), (0, 90, 0), (None, 90, None), (1, None, None), (1, 0, None)],
)
def test_per90_nulls(value, minutes, expected):
    assert per90(value, minutes) == expected


def test_progression_and_orientation():
    assert progressive(20, 34, 50, 34)
    assert not progressive(50, 34, 55, 34)
    assert not progressive(60, 34, 20, 34)
    assert progressive(85, 34, 55, 34, attack_left=True)
    assert not progressive(20, 0, 20, 68)


def test_roles_are_minute_weighted_and_split_roles_visible():
    r = role_summary({"CM": 620, "DM": 310, "AM": 70}, 1000)
    assert r["primary_role"] == "CM" and r["secondary_role"] == "DM"
    assert r["role_shares"]["DM"] == 0.31 and r["multi_role"]
    assert role_summary({"CM": 20, "unknown": 80}, 100)["primary_role"] is None


def test_eligibility_rejects_missing_core_and_keepers():
    p = dict(minutes=899, primary_role="GK", values=dict.fromkeys(CORE, 0))
    assert eligibility(p, 900) == ["below_minutes", "goalkeeper_excluded"]
    p.update(minutes=1000, primary_role="CM")
    p["values"][CORE[0]] = None
    assert eligibility(p, 900) == ["missing_core_features"]


def test_registry_is_complete_and_style_only():
    assert len(CORE) == 18
    assert len({f.id for f in REGISTRY}) == len(REGISTRY)
    assert all(f.label_en and f.label_nl and f.formula and f.null_semantics for f in REGISTRY)
    assert not any(f.core for f in REGISTRY if f.family in ("output", "context"))


def test_event_features_filter_penalties_link_xa_and_validate_possessions(fixtures):
    from copy import deepcopy

    from football_intelligence.data.adapters.statsbomb import StatsBombAdapter
    from football_intelligence.data.schema import Lineup, frame_from_records
    from football_intelligence.dna.features import aggregate, match_observations

    raw = deepcopy(fixtures["statsbomb"])
    for e in raw["events"]:
        e["possession"] = 1 if e["index"] < 2 else 2
        e["possession_team"] = {"id": 1 if e["index"] < 2 else 2}
    raw["events"][0]["pass"]["assisted_shot_id"] = "1"
    raw["events"][1]["shot"]["key_pass_id"] = "0"
    rows = StatsBombAdapter().normalise(raw, "test")
    lu = frame_from_records(Lineup, rows["lineups"]).to_dicts()
    for r in lu:
        r.update(
            minutes_reliable=True, participation_json="[[0,5400]]", role_minutes_json='{"ST":90}'
        )
    obs = match_observations(rows["events"], lu, rows["matches"][0])
    p = aggregate([obs[0]])
    assert p["values"]["shots_per90"] == 1  # period 5 excluded
    assert p["values"]["xa_per90"] == pytest.approx(0.3)
    assert p["values"]["shot_assists_per90"] == 1
    assert (
        obs[0]["own_possessions"] == 1 and obs[0]["opponent_possessions"] == 2
    )  # period-scoped ID
    raw["events"][1]["shot"]["type"] = {"name": "Penalty"}
    rows = StatsBombAdapter().normalise(raw, "test")
    p = aggregate([match_observations(rows["events"], lu, rows["matches"][0])[0]])
    assert p["values"]["shots_per90"] == 0 and p["values"]["xa_per90"] == 0
    assert p["values"]["xg_per_shot"] is None
    del raw["events"][1]["shot"]["type"]
    del raw["events"][1]["shot"]["key_pass_id"]
    rows = StatsBombAdapter().normalise(raw, "test")
    p = aggregate([match_observations(rows["events"], lu, rows["matches"][0])[0]])
    assert p["values"]["xa_per90"] is None and p["values"]["shot_assists_per90"] is None
