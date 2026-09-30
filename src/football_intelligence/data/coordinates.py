"""105 x 68 reference metres, origin bottom-left, y increasing upwards.

Event coordinates are actor-relative. Tracking coordinates remain fixed-camera/pitch
relative. Period alone never determines an orientation flip.
"""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class CoordinateSystem:
    length: float
    width: float
    centered: bool = False
    y_down: bool = False

    def __post_init__(self):
        if not all(isfinite(v) and v > 0 for v in (self.length, self.width)):
            raise ValueError("Pitch dimensions must be finite and positive")


STATSBOMB = CoordinateSystem(120, 80, y_down=True)


def to_canonical(
    x: float,
    y: float,
    system: CoordinateSystem,
    *,
    attack_left: bool = False,
    allow_outside: bool = False,
) -> tuple[float, float]:
    if not (isfinite(x) and isfinite(y)):
        raise ValueError("Coordinates must be finite")
    u = x / system.length + (0.5 if system.centered else 0)
    v = y / system.width + (0.5 if system.centered else 0)
    if system.y_down:
        v = 1 - v
    if attack_left:
        u, v = 1 - u, 1 - v
    if not allow_outside and not (-1e-9 <= u <= 1 + 1e-9 and -1e-9 <= v <= 1 + 1e-9):
        raise ValueError("Coordinate outside pitch")
    return u * 105, v * 68


def from_canonical(x: float, y: float, system: CoordinateSystem, *, attack_left: bool = False):
    if not (isfinite(x) and isfinite(y)):
        raise ValueError("Coordinates must be finite")
    u, v = x / 105, y / 68
    if attack_left:
        u, v = 1 - u, 1 - v
    if system.y_down:
        v = 1 - v
    return (
        (u - (0.5 if system.centered else 0)) * system.length,
        (v - (0.5 if system.centered else 0)) * system.width,
    )


def in_pitch(x: float, y: float) -> bool:
    return 0 <= x <= 105 and 0 <= y <= 68
