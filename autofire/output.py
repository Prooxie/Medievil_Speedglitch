from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, Set

from .engine import KeyName, OutputDelta, OutputSink


@dataclass(frozen=True)
class KeyboardConfig:
    """
    Maps your abstract KeyNames to pynput Key objects.
    """
    pass


class PynputKeyboardSink(OutputSink):
    def __init__(self):
        # Import inside so tests don't require pynput
        from pynput.keyboard import Key, Controller  # type: ignore

        self._Key = Key
        self._keyboard = Controller()

        self._keymap = {
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
        }
        self._all_keys = [Key.up, Key.down, Key.left, Key.right]

    def _force_release_all(self) -> None:
        # Same safety tactic as your script: multiple releases
        for _ in range(5):
            for key in self._all_keys:
                try:
                    self._keyboard.release(key)
                except Exception:
                    pass
            time.sleep(0.01)

    def apply(self, delta: OutputDelta) -> None:
        if delta.force_release_all:
            self._force_release_all()

        for k in delta.release:
            try:
                self._keyboard.release(self._keymap[k])
            except Exception:
                pass

        for k in delta.press:
            try:
                self._keyboard.press(self._keymap[k])
            except Exception:
                pass
