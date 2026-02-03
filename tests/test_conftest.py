from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from autofire.engine import OutputDelta, OutputSink


class FakeClock:
    def __init__(self, start: float = 0.0):
        self.t = float(start)

    def now(self) -> float:
        return float(self.t)

    def advance(self, dt: float) -> float:
        self.t += float(dt)
        return float(self.t)

    def set(self, t: float) -> float:
        self.t = float(t)
        return float(self.t)


@dataclass
class RecordedDelta:
    t: float
    delta: OutputDelta


class RecordingSink(OutputSink):
    """
    Records all deltas applied, and simulates what keys are effectively down.
    This lets tests assert "no overlap / no phantom holds" deterministically.
    """
    def __init__(self):
        self.events: List[RecordedDelta] = []
        self.down = set()

    def apply(self, delta: OutputDelta) -> None:
        # record with t=0 placeholder; tests set time externally if needed
        self.events.append(RecordedDelta(t=0.0, delta=delta))

        # emulate "force_release_all" semantics as "everything is released"
        if delta.force_release_all:
            self.down.clear()

        for k in delta.release:
            self.down.discard(k)

        for k in delta.press:
            self.down.add(k)

    def apply_at(self, t: float, delta: OutputDelta) -> None:
        self.events.append(RecordedDelta(t=float(t), delta=delta))

        if delta.force_release_all:
            self.down.clear()

        for k in delta.release:
            self.down.discard(k)

        for k in delta.press:
            self.down.add(k)
