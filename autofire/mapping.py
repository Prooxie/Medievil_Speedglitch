from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AxisConfig:
    deadzone: float = 0.15


def apply_deadzone(v: tuple[float, float], deadzone: float) -> tuple[float, float]:
    x, y = v
    if abs(x) < deadzone:
        x = 0.0
    if abs(y) < deadzone:
        y = 0.0
    return (x, y)


def clamp1(x: float) -> float:
    return 1.0 if x > 1.0 else (-1.0 if x < -1.0 else x)


def clamp2(v: tuple[float, float]) -> tuple[float, float]:
    return (clamp1(v[0]), clamp1(v[1]))

def amplify_to_full(v: tuple[float, float], full_at: float = 0.90) -> tuple[float, float]:
    """
    Remap so that reaching `full_at` (e.g. 0.90) outputs 1.0.
    Example: full_at=0.90 => 0.90 -> 1.00, 0.45 -> 0.50.
    """
    def f(x: float) -> float:
        ax = abs(x)
        if ax < 1e-6:
            return 0.0
        y = ax / full_at
        if y > 1.0:
            y = 1.0
        return y if x >= 0 else -y

    return (f(v[0]), f(v[1]))
