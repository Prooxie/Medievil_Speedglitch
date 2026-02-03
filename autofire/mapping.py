from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Set

from .input import ControllerState


@dataclass(frozen=True)
class MovementConfig:
    deadzone: float = 0.4
    diagonal_threshold: float = 0.0
    """
    If > 0, diagonals require BOTH |x| and |y| to exceed this additional threshold.
    Set to 0.0 to behave like your current script (deadzone-only).
    """


def movement_4way(state: ControllerState, cfg: MovementConfig) -> FrozenSet[str]:
    """
    Returns one of: {}, {"up"}, {"down"}, {"left"}, {"right"}.
    Chooses dominant axis if both exceed deadzone.
    """
    x = state.axis_x
    y = state.axis_y
    dz = cfg.deadzone

    if abs(x) < dz and abs(y) < dz:
        return frozenset()

    # Choose dominant axis
    if abs(x) >= abs(y):
        if x > dz:
            return frozenset({"right"})
        if x < -dz:
            return frozenset({"left"})
        return frozenset()
    else:
        if y > dz:
            return frozenset({"down"})
        if y < -dz:
            return frozenset({"up"})
        return frozenset()


def movement_8way(state: ControllerState, cfg: MovementConfig) -> FrozenSet[str]:
    """
    Returns: {}, {"up"}, {"down"}, {"left"}, {"right"}, or diagonals like {"up","right"}.
    Matches your original behavior: diagonal is simply both axes past deadzone.
    If cfg.diagonal_threshold > 0, both axes must exceed max(deadzone, diagonal_threshold).
    """
    x = state.axis_x
    y = state.axis_y
    dz = cfg.deadzone
    diag_gate = max(dz, cfg.diagonal_threshold)

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

    # Optional: if user enables extra diagonal gating, drop diagonals unless both axes pass gate.
    if cfg.diagonal_threshold > 0 and len(keys) == 2:
        if abs(x) < diag_gate or abs(y) < diag_gate:
            # keep only the dominant axis to avoid accidental diagonals
            if abs(x) >= abs(y):
                keys.discard("up")
                keys.discard("down")
            else:
                keys.discard("left")
                keys.discard("right")

    return frozenset(keys)
