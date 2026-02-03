from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, FrozenSet, List, Optional, Protocol, Sequence, Set, Tuple


KeyName = str  # "up", "down", "left", "right"


@dataclass(frozen=True)
class TimingConfig:
    hold_time: float = 0.133
    release_time: float = 0.033


@dataclass(frozen=True)
class SwitchPolicy:
    """
    Phantom-move prevention policy (your current 'funk phantom moves'):
    - on direction change: stop autofire, release all, wait, then restart.
    """
    settle_time: float = 0.02   # let current cycle finish
    pause_after_release: float = 0.08  # 80ms pause after force release


@dataclass(frozen=True)
class EngineConfig:
    timing: TimingConfig = TimingConfig()
    switch: SwitchPolicy = SwitchPolicy()


@dataclass(frozen=True)
class OutputDelta:
    press: FrozenSet[KeyName]
    release: FrozenSet[KeyName]
    force_release_all: bool = False  # when True, sink should release everything multiple times (safety)


class OutputSink(Protocol):
    def apply(self, delta: OutputDelta) -> None:
        ...


class Clock(Protocol):
    def now(self) -> float:
        ...


class MonotonicClock:
    def __init__(self, monotonic_func: Callable[[], float]):
        self._mono = monotonic_func

    def now(self) -> float:
        return float(self._mono())


class AutofireScheduler:
    """
    A deterministic state machine (no threads) that emits press/release deltas.
    It implements your hold/release cycle AND your phantom-prevention switch behavior.
    """

    def __init__(self, cfg: EngineConfig):
        self.cfg = cfg

        self._desired: FrozenSet[KeyName] = frozenset()
        self._active: bool = False

        self._held: Set[KeyName] = set()
        self._phase_holding: bool = False
        self._next_switch_at: float = 0.0

        # Switching / pause gates
        self._blocked_until: float = 0.0
        self._need_force_release: bool = False

    @property
    def held_keys(self) -> FrozenSet[KeyName]:
        return frozenset(self._held)

    def set_desired(self, desired: FrozenSet[KeyName], now: float) -> OutputDelta:
        """
        Called when mapping changes. Applies switch policy immediately.
        Returns immediate deltas if we need to force-release.
        """
        if desired == self._desired:
            return OutputDelta(press=frozenset(), release=frozenset())

        # Direction changed => phantom prevention sequence:
        # 1) stop, 2) force release all, 3) pause, 4) accept new desired, 5) resume
        self._active = False
        self._phase_holding = False

        self._desired = desired
        self._blocked_until = now + self.cfg.switch.settle_time

        # Force release-all and then pause_after_release
        self._need_force_release = True

        # We also release any currently held keys immediately
        to_release = frozenset(self._held)
        self._held.clear()

        return OutputDelta(
            press=frozenset(),
            release=to_release,
            force_release_all=True
        )

    def tick(self, now: float) -> OutputDelta:
        """
        Called at high frequency (e.g., 100 Hz). Emits deltas to apply this tick.
        """
        press: Set[KeyName] = set()
        release: Set[KeyName] = set()
        force_release_all = False

        # If we have pending forced release (extra safety), do it once and extend pause
        if self._need_force_release and now >= self._blocked_until:
            force_release_all = True
            self._need_force_release = False
            self._blocked_until = now + self.cfg.switch.pause_after_release

        # During blocked time, do nothing (ensures no phantom key overlap)
        if now < self._blocked_until:
            # ensure everything remains released
            if self._held:
                release |= self._held
                self._held.clear()
            return OutputDelta(
                press=frozenset(press),
                release=frozenset(release),
                force_release_all=force_release_all
            )

        # Determine active
        self._active = len(self._desired) > 0

        if not self._active:
            # ensure released
            if self._held:
                release |= self._held
                self._held.clear()
            self._phase_holding = False
            return OutputDelta(
                press=frozenset(press),
                release=frozenset(release),
                force_release_all=force_release_all
            )

        # Active autofire
        if now < self._next_switch_at:
            return OutputDelta(
                press=frozenset(),
                release=frozenset(),
                force_release_all=force_release_all
            )

        # switch phase
        if not self._phase_holding:
            # press desired
            for k in self._desired:
                if k not in self._held:
                    press.add(k)
                    self._held.add(k)
            self._phase_holding = True
            self._next_switch_at = now + self.cfg.timing.hold_time
        else:
            # release desired
            for k in list(self._held):
                if k in self._desired:
                    release.add(k)
                    self._held.remove(k)
            self._phase_holding = False
            self._next_switch_at = now + self.cfg.timing.release_time

        return OutputDelta(
            press=frozenset(press),
            release=frozenset(release),
            force_release_all=force_release_all
        )
