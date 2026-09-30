import math

import pytest

from football_intelligence.data.coordinates import (
    STATSBOMB,
    CoordinateSystem,
    from_canonical,
    to_canonical,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ((0, 0), (0, 68)),
        ((120, 80), (105, 0)),
        ((60, 40), (52.5, 34)),
        ((0, 80), (0, 0)),
        ((120, 0), (105, 68)),
    ],
)
def test_statsbomb_reference(raw, expected):
    assert to_canonical(*raw, STATSBOMB) == pytest.approx(expected)


@pytest.mark.parametrize("system", [STATSBOMB, CoordinateSystem(106, 68, centered=True)])
@pytest.mark.parametrize("attack_left", [False, True])
def test_reversible_orientation(system, attack_left):
    raw = (22.1, 18.2)
    canonical = to_canonical(*raw, system, attack_left=attack_left)
    assert from_canonical(*canonical, system, attack_left=attack_left) == pytest.approx(raw)


def test_tracking_center_and_half_direction():
    system = CoordinateSystem(106, 68, centered=True)
    assert to_canonical(-53, -34, system) == (0, 0)
    assert to_canonical(0, 0, system) == (52.5, 34)
    assert to_canonical(-53, -34, system, attack_left=True) == (105, 68)


@pytest.mark.parametrize("x,y", [(math.nan, 0), (0, math.inf), (-1, 20), (121, 20)])
def test_invalid_coordinate_rejected(x, y):
    with pytest.raises(ValueError):
        to_canonical(x, y, STATSBOMB)


def test_outside_retained_only_explicitly():
    assert to_canonical(121, 40, STATSBOMB, allow_outside=True)[0] > 105
    with pytest.raises(ValueError):
        CoordinateSystem(0, 68)
