from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Set

from .input import ControllerState


@dataclass(frozen=True)
class MovementConfig:
    deadzone: float = 0.4
    diagonal_threshold: float = 0.0
    """
    If > 0, diagonals require BOTH |x| and |y| to exceed this threshold.
    Set to 0.0 to match original deadzone-only diagonal behavior.
    """


def movement_4way(state: ControllerState, cfg: MovementConfig) -> FrozenSet[str]:
    x = state.axis_x
    y = state.axis_y
    dz = cfg.deadzone

    if abs(x) < dz and abs(y) < dz:
        return frozenset()

    # Dominant axis wins
    if abs(x) >= abs(y):
        if x > dz:
            return frozenset({"right"})
        if x < -dz:
            return frozenset({"left"})
        return frozenset()
    else:
        if y < -dz:
            return frozenset({"up"})
        if y > dz:
            return frozenset({"down"})
        return frozenset()


def movement_8way(state: ControllerState, cfg: MovementConfig) -> FrozenSet[str]:
    x = state.axis_x
    y = state.axis_y
    dz = cfg.deadzone

    if abs(x) < dz and abs(y) < dz:
        return frozenset()

    keys: Set[str] = set()

    # Vertical
    if y < -dz:
        keys.add("up")
    elif y > dz:
        keys.add("down")

    # Horizontal
    if x > dz:
        keys.add("right")
    elif x < -dz:
        keys.add("left")

    # Optional diagonal gating
    if cfg.diagonal_threshold > 0 and len(keys) == 2:
        if abs(x) < cfg.diagonal_threshold or abs(y) < cfg.diagonal_threshold:
            # Drop weaker axis
            if abs(x) >= abs(y):
                keys.discard("up")
                keys.discard("down")
            else:
                keys.discard("left")
                keys.discard("right")

    return frozenset(keys)
