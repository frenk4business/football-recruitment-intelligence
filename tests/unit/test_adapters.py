from copy import deepcopy

import polars as pl
import pytest
from pydantic import ValidationError

from football_intelligence.data.adapters.skillcorner import SkillCornerAdapter
from football_intelligence.data.adapters.statsbomb import StatsBombAdapter
from football_intelligence.data.positions import position_group
from football_intelligence.data.schema import EntityMap, Event, canonical_id, frame_from_records


def test_stable_namespaced_ids():
    assert canonical_id("statsbomb", "players", 1) == canonical_id("statsbomb", "players", "1")
    assert canonical_id("statsbomb", "players", 1) != canonical_id("skillcorner", "players", 1)
    assert canonical_id("statsbomb", "players", 1) != canonical_id("statsbomb", "teams", 1)


def test_statsbomb_preserves_originals_and_minutes(fixtures):
    result = StatsBombAdapter().normalise(fixtures["statsbomb"], "test")
    assert result["lineups"][0]["minutes"] == 90
    assert result["events"][0]["outcome"] == "Complete"
    assert result["events"][0]["x"] == 52.5
    assert "end_location" in result["events"][0]["attributes_json"]
    assert all(
        r["match_method"] == "exact_provider_id"
        for r in frame_from_records(
            EntityMap,
            result["provider_entity_map"],
        ).to_dicts()
    )


def test_overlapping_lineups_are_not_summed(fixtures):
    raw = deepcopy(fixtures["statsbomb"])
    raw["lineups"][0]["lineup"][0]["positions"] *= 2
    result = StatsBombAdapter().normalise(raw, "test")
    assert result["lineups"][0]["minutes"] is None
    assert result["lineups"][0]["minutes_method"] == "unavailable_inconsistent_lineup_intervals"


def test_duplicate_event_rejected(fixtures):
    raw = deepcopy(fixtures["statsbomb"])
    raw["events"].append(raw["events"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        StatsBombAdapter().normalise(raw, "test")


def test_tracking_preserves_detection_and_original_dimensions(fixtures):
    result = SkillCornerAdapter().normalise(fixtures["skillcorner"], "test")
    assert result["matches"][0]["pitch_length"] == 106
    assert result["tracking_objects"][0]["x"] == 0
    assert result["tracking_objects"][1]["is_detected"] is False
    assert result["tracking_frames"][0]["home_attacking_direction"] == "left_to_right"
    assert result["events"] == []


def test_missing_skillcorner_metadata(fixtures):
    raw = deepcopy(fixtures["skillcorner"])
    raw["match"]["players"][0]["playing_time"]["total"] = None
    result = SkillCornerAdapter().normalise(raw, "test")
    assert result["lineups"][0]["minutes"] is None


def test_duplicate_tracking_rejected(fixtures):
    raw = deepcopy(fixtures["skillcorner"])
    raw["tracking"] *= 2
    with pytest.raises(ValueError, match="Duplicate"):
        SkillCornerAdapter().normalise(raw, "test")


def test_empty_schema_is_typed():
    frame = frame_from_records(Event, [])
    assert frame.schema["x"] == pl.Float64
    assert frame.schema["observed_on"] == pl.Date
    assert frame.schema["period"] == pl.Int64


def test_schema_rejects_unknown_field(fixtures):
    row = StatsBombAdapter().normalise(fixtures["statsbomb"], "test")["events"][0]
    with pytest.raises(ValidationError):
        Event.model_validate({**row, "made_up_score": 42})


@pytest.mark.parametrize(
    "name,group",
    [
        ("Goalkeeper", "GK"),
        ("Left Center Back", "CB"),
        ("Right Wing Back", "FB/WB"),
        ("Center Defensive Midfield", "DM"),
        ("Left Center Midfield", "CM"),
        ("Attacking Midfield", "AM"),
        ("Left Winger", "W"),
        ("Center Forward", "ST"),
        ("Unknown", None),
    ],
)
def test_positions(name, group):
    assert position_group(name) == group


def test_second_half_preserves_fixed_coordinates_and_normalizes_clock(fixtures):
    raw = deepcopy(fixtures["skillcorner"])
    raw["tracking"][0]["period"] = 2
    raw["tracking"][0]["timestamp"] = "00:45:10.00"
    result = SkillCornerAdapter().normalise(raw, "test")
    assert result["tracking_objects"][0]["x"] == 0
    frame = result["tracking_frames"][0]
    assert frame["timestamp_seconds"] == 10
    assert frame["provider_timestamp"] == "00:45:10.00"
    assert frame["home_attacking_direction"] == "right_to_left"
