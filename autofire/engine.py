from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Protocol, Set


KeyName = str  # "up", "down", "left", "right"


@dataclass(frozen=True)
class TimingConfig:
    hold_time: float = 0.133
    release_time: float = 0.033


@dataclass(frozen=True)
class SwitchPolicy:
    settle_time: float = 0.02
    pause_after_release: float = 0.08


@dataclass(frozen=True)
class EngineConfig:
    timing: TimingConfig = TimingConfig()
    switch: SwitchPolicy = SwitchPolicy()


@dataclass(frozen=True)
class OutputDelta:
    press: FrozenSet[KeyName]
    release: FrozenSet[KeyName]
    force_release_all: bool = False


class OutputSink(Protocol):
    def apply(self, delta: OutputDelta) -> None:
        ...


class AutofireScheduler:
    """
    Deterministic tick-based scheduler:
    - hold/release cycling
    - phantom prevention on direction change (stop -> force release -> pause -> resume)
    """

    def __init__(self, cfg: EngineConfig):
        self.cfg = cfg
        self._desired: FrozenSet[KeyName] = frozenset()

        self._held: Set[KeyName] = set()
        self._holding_phase: bool = False
        self._next_phase_at: float = 0.0

        self._blocked_until: float = 0.0
        self._need_force_release: bool = False

    @property
    def held_keys(self) -> FrozenSet[KeyName]:
        return frozenset(self._held)

    def set_desired(self, desired: FrozenSet[KeyName], now: float) -> OutputDelta:
        if desired == self._desired:
            return OutputDelta(frozenset(), frozenset())

        # Stop cycle immediately
        self._holding_phase = False
        self._next_phase_at = now

        self._desired = desired

        # Block briefly + force release-all once + pause
        self._blocked_until = now + self.cfg.switch.settle_time
        self._need_force_release = True

        # Immediately release any held keys
        to_release = frozenset(self._held)
        self._held.clear()

        return OutputDelta(
            press=frozenset(),
            release=to_release,
            force_release_all=True
        )

    def tick(self, now: float) -> OutputDelta:
        press: Set[KeyName] = set()
        release: Set[KeyName] = set()
        force_release_all = False

        # Once settle_time has passed, do the extra force release and extend pause
        if self._need_force_release and now >= self._blocked_until:
            force_release_all = True
            self._need_force_release = False
            self._blocked_until = now + self.cfg.switch.pause_after_release

        # While blocked, do nothing (ensures no overlap)
        if now < self._blocked_until:
            if self._held:
                release |= self._held
                self._held.clear()
            return OutputDelta(frozenset(press), frozenset(release), force_release_all)

        # If no desired keys, ensure released
        if not self._desired:
            if self._held:
                release |= self._held
                self._held.clear()
            self._holding_phase = False
            return OutputDelta(frozenset(), frozenset(release), force_release_all)

        # Enforce timing
        if now < self._next_phase_at:
            return OutputDelta(frozenset(), frozenset(), force_release_all)

        if not self._holding_phase:
            # PRESS
            for k in self._desired:
                if k not in self._held:
                    press.add(k)
                    self._held.add(k)
            self._holding_phase = True
            self._next_phase_at = now + self.cfg.timing.hold_time
        else:
            # RELEASE
            for k in list(self._held):
                if k in self._desired:
                    release.add(k)
                    self._held.remove(k)
            self._holding_phase = False
            self._next_phase_at = now + self.cfg.timing.release_time

        return OutputDelta(frozenset(press), frozenset(release), force_release_all)
