from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimingConfig:
    hold_time: float = 0.060
    release_time: float = 0.033


@dataclass(frozen=True)
class SwitchPolicy:
    settle_time: float = 0.0
    pause_after_release: float = 0.0


@dataclass(frozen=True)
class EngineConfig:
    timing: TimingConfig = TimingConfig()
    switch: SwitchPolicy = SwitchPolicy()


@dataclass(frozen=True)
class AxisDelta:
    stick: tuple[float, float]
    force_center: bool = False


class AxisAutofireScheduler:
    """
    Pulses a 2D stick vector:
      - ON: output desired vector for hold_time
      - OFF: output (0,0) for release_time

    settle_time/pause_after_release are kept, but default to 0 for responsive feel.
    """

    def __init__(self, cfg: EngineConfig):
        self.cfg = cfg
        self._desired: tuple[float, float] = (0.0, 0.0)

        self._holding_phase: bool = False
        self._next_phase_at: float = 0.0

        self._blocked_until: float = 0.0
        self._need_force_center: bool = False

    def set_desired(self, desired: tuple[float, float], now: float) -> None:
        if desired == self._desired:
            return

        # if blocked, just store desired
        if now < self._blocked_until or self._need_force_center:
            self._desired = desired
            return

        # restart phase
        self._holding_phase = False
        self._next_phase_at = now
        self._desired = desired

        if self.cfg.switch.settle_time > 0:
            self._blocked_until = now + self.cfg.switch.settle_time
            self._need_force_center = True

    def tick(self, now: float) -> AxisDelta:
        # optional force-center step after direction switch
        if self._need_force_center and now >= self._blocked_until:
            self._need_force_center = False
            if self.cfg.switch.pause_after_release > 0:
                self._blocked_until = now + self.cfg.switch.pause_after_release
            self._holding_phase = False
            self._next_phase_at = now
            return AxisDelta(stick=(0.0, 0.0), force_center=True)

        if now < self._blocked_until:
            return AxisDelta(stick=(0.0, 0.0), force_center=False)

        # no desired => no output
        if abs(self._desired[0]) < 1e-6 and abs(self._desired[1]) < 1e-6:
            self._holding_phase = False
            return AxisDelta(stick=(0.0, 0.0), force_center=False)

        # time to switch phase?
        if now < self._next_phase_at:
            return AxisDelta(stick=self._desired if self._holding_phase else (0.0, 0.0))

        if not self._holding_phase:
            self._holding_phase = True
            self._next_phase_at = now + self.cfg.timing.hold_time
            return AxisDelta(stick=self._desired)
        else:
            self._holding_phase = False
            self._next_phase_at = now + self.cfg.timing.release_time
            return AxisDelta(stick=(0.0, 0.0))
