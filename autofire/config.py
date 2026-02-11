from __future__ import annotations

from dataclasses import dataclass

from .engine import EngineConfig, SwitchPolicy, TimingConfig


@dataclass(frozen=True)
class AutofireConfig:
    hold_time: float = 0.133
    release_time: float = 0.033

    settle_time: float = 0.02
    pause_after_release: float = 0.08

    deadzone: float = 0.40
    diagonal_threshold: float = 0.00

    joystick_index: int = 0
    axis_x_index: int = 2
    axis_y_index: int = 3

    def to_engine_config(self) -> EngineConfig:
        return EngineConfig(
            timing=TimingConfig(hold_time=self.hold_time, release_time=self.release_time),
            switch=SwitchPolicy(settle_time=self.settle_time, pause_after_release=self.pause_after_release),
        )
