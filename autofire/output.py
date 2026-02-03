from __future__ import annotations

import time

from .engine import OutputDelta, OutputSink


class PynputKeyboardSink(OutputSink):
    def __init__(self):
        from pynput.keyboard import Key, Controller  # type: ignore

        self._keyboard = Controller()
        self._map = {
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
        }
        self._all = [Key.up, Key.down, Key.left, Key.right]

    def _force_release_all(self) -> None:
        for _ in range(5):
            for k in self._all:
                try:
                    self._keyboard.release(k)
                except Exception:
                    pass
            time.sleep(0.01)

    def apply(self, delta: OutputDelta) -> None:
        if delta.force_release_all:
            self._force_release_all()

        for k in delta.release:
            try:
                self._keyboard.release(self._map[k])
            except Exception:
                pass

        for k in delta.press:
            try:
                self._keyboard.press(self._map[k])
            except Exception:
                pass
