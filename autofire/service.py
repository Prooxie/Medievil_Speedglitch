from __future__ import annotations

import importlib
import inspect
import time
from dataclasses import asdict
from typing import Any, FrozenSet, Optional, Set, Tuple, Type

from PySide6.QtCore import QObject, QThread, Signal, Slot, QTimer

from .config import AutofireConfig

# Scheduler: AutofireScheduler (older) vs AxisAutofireScheduler (newer)
try:
    from .engine import AutofireScheduler as Scheduler  # type: ignore
except Exception:  # pragma: no cover
    from .engine import AxisAutofireScheduler as Scheduler  # type: ignore

# Input: prefer repo-provided PygameRightStickInput; else fallback.
try:
    from .input import PygameRightStickInput, ControllerState  # type: ignore
except Exception:  # pragma: no cover
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class ControllerState:
        axis_x: float
        axis_y: float

    class PygameRightStickInput:  # type: ignore
        def __init__(self, joystick_index: int = 0, axis_x_index: int = 2, axis_y_index: int = 3):
            import pygame  # type: ignore
            self.pygame = pygame
            self.ax_x = axis_x_index
            self.ax_y = axis_y_index
            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() == 0:
                raise RuntimeError("No controller detected!")
            self.j = pygame.joystick.Joystick(joystick_index)
            self.j.init()

        def read(self) -> ControllerState:
            self.pygame.event.pump()
            return ControllerState(float(self.j.get_axis(self.ax_x)), float(self.j.get_axis(self.ax_y)))

        def close(self) -> None:
            try:
                self.pygame.quit()
            except Exception:
                pass


class LocalPynputKeyboardSink:
    """Always-available fallback sink (doesn't depend on your output.py exports)."""

    def __init__(self):
        from pynput.keyboard import Key, Controller  # type: ignore

        self._kb = Controller()
        self._map = {"up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right}
        self._all = [Key.up, Key.down, Key.left, Key.right]

    def apply(self, delta: Any) -> None:
        # Delta is expected to have: press, release, force_release_all
        force = bool(getattr(delta, "force_release_all", False))
        if force:
            for _ in range(3):
                for k in self._all:
                    try:
                        self._kb.release(k)
                    except Exception:
                        pass
                time.sleep(0.01)

        for k in getattr(delta, "release", []):
            try:
                self._kb.release(self._map[k])
            except Exception:
                pass

        for k in getattr(delta, "press", []):
            try:
                self._kb.press(self._map[k])
            except Exception:
                pass


def _pick_sink() -> Type[Any]:
    """Pick an instantiable sink with apply(), otherwise fall back to LocalPynputKeyboardSink."""
    try:
        mod = importlib.import_module(f"{__package__}.output")
    except Exception:
        return LocalPynputKeyboardSink

    classes = []
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if obj.__module__ != mod.__name__:
            continue
        if not hasattr(obj, "apply"):
            continue
        classes.append((name, obj))

    if not classes:
        return LocalPynputKeyboardSink

    def score(n: str) -> int:
        nn = n.lower()
        s = 0
        if "vgamepad" in nn or "vigem" in nn or "x360" in nn or "ds4" in nn:
            s += 100
        if "keyboard" in nn or "pynput" in nn:
            s += 50
        if "sink" in nn:
            s += 10
        return s

    classes.sort(key=lambda it: score(it[0]), reverse=True)

    for name, cls in classes:
        try:
            cls()  # test instantiate
            return cls
        except Exception:
            continue

    # Nothing instantiable without args -> fallback
    return LocalPynputKeyboardSink


Sink = _pick_sink()


def movement_8way(state: ControllerState, deadzone: float, diagonal_threshold: float) -> FrozenSet[str]:
    x, y = state.axis_x, state.axis_y
    dz = deadzone
    if abs(x) < dz and abs(y) < dz:
        return frozenset()

    keys: Set[str] = set()
    if y < -dz:
        keys.add("up")
    elif y > dz:
        keys.add("down")
    if x > dz:
        keys.add("right")
    elif x < -dz:
        keys.add("left")

    if diagonal_threshold > 0 and len(keys) == 2:
        if abs(x) < diagonal_threshold or abs(y) < diagonal_threshold:
            if abs(x) >= abs(y):
                keys.discard("up"); keys.discard("down")
            else:
                keys.discard("left"); keys.discard("right")

    return frozenset(keys)


def keys_to_axes(keys: FrozenSet[str]) -> Tuple[float, float]:
    x = (-1.0 if "left" in keys else 0.0) + (1.0 if "right" in keys else 0.0)
    y = (-1.0 if "up" in keys else 0.0) + (1.0 if "down" in keys else 0.0)
    return x, y


class AutofireWorker(QObject):
    telemetry = Signal(dict)
    log = Signal(str)
    running_changed = Signal(bool)

    def __init__(self, cfg: AutofireConfig):
        super().__init__()
        self._cfg = cfg
        self._should_run = False
        self._inp: Optional[PygameRightStickInput] = None
        self._out: Optional[Any] = None
        self._sched: Optional[Any] = None
        self._last_desired: FrozenSet[str] = frozenset()

    @Slot(dict)
    def set_config(self, cfg_dict: dict) -> None:
        merged = {**asdict(self._cfg), **cfg_dict}
        new_cfg = AutofireConfig(**merged)

        needs_reopen = (
            new_cfg.joystick_index != self._cfg.joystick_index
            or new_cfg.axis_x_index != self._cfg.axis_x_index
            or new_cfg.axis_y_index != self._cfg.axis_y_index
        )
        self._cfg = new_cfg

        if self._sched is not None:
            self._sched = Scheduler(self._cfg.to_engine_config())
            self._last_desired = frozenset()

        if needs_reopen and self._should_run:
            self.log.emit("Input changed — reopening joystick.")
            self._reopen_input()

    @Slot()
    def start(self) -> None:
        if self._should_run:
            return
        self._should_run = True
        self._last_desired = frozenset()

        try:
            try:
                self._open()
            except Exception as e:
                # Don't crash the GUI if no controller / no sink is available.
                self.log.emit(f"Cannot start: {e}")
                self._should_run = False
                return

            self.running_changed.emit(True)
            self.log.emit(f"Started. Sink: {type(self._out).__name__}")

            while self._should_run:
                now = time.monotonic()
                assert self._inp and self._out and self._sched

                state = self._inp.read()
                desired = movement_8way(state, self._cfg.deadzone, self._cfg.diagonal_threshold)

                if desired != self._last_desired:
                    self._apply(self._sched_set_desired(desired, now))
                    self._last_desired = desired

                self._apply(self._sched_tick(now))

                self.telemetry.emit({
                    "axis_x": state.axis_x,
                    "axis_y": state.axis_y,
                    "desired": sorted(list(desired)),
                    "phase": "ON" if bool(getattr(self._sched, "_holding_phase", False)) else "OFF",
                })

                time.sleep(0.008)

        finally:
            self._close()
            self.running_changed.emit(False)
            self.log.emit("Stopped.")

    @Slot()
    def stop(self) -> None:
        self._should_run = False

    def _open(self) -> None:
        self._inp = PygameRightStickInput(self._cfg.joystick_index, self._cfg.axis_x_index, self._cfg.axis_y_index)
        self._out = Sink()
        self._sched = Scheduler(self._cfg.to_engine_config())

    def _close(self) -> None:
        try:
            if self._out and self._sched:
                now = time.monotonic()
                self._apply(self._sched_set_desired(frozenset(), now))
                self._apply(self._sched_tick(now))
        except Exception:
            pass
        try:
            if self._inp:
                self._inp.close()
        except Exception:
            pass
        self._inp = None
        self._out = None
        self._sched = None

    def _reopen_input(self) -> None:
        try:
            if self._inp:
                self._inp.close()
        except Exception:
            pass
        self._inp = PygameRightStickInput(self._cfg.joystick_index, self._cfg.axis_x_index, self._cfg.axis_y_index)

    # ---- compatibility for scheduler/sink APIs ----
    def _sched_set_desired(self, desired: FrozenSet[str], now: float) -> Any:
        try:
            return self._sched.set_desired(desired, now)  # type: ignore[attr-defined]
        except Exception:
            pass
        x, y = keys_to_axes(desired)
        if hasattr(self._sched, "set_desired_axes"):
            return self._sched.set_desired_axes(x, y, now)  # type: ignore[attr-defined]
        return self._sched.set_desired((x, y), now)  # type: ignore[misc]

    def _sched_tick(self, now: float) -> Any:
        if hasattr(self._sched, "tick"):
            return self._sched.tick(now)  # type: ignore[attr-defined]
        return self._sched.update(now)  # type: ignore[attr-defined]

    def _apply(self, delta: Any) -> None:
        self._out.apply(delta)  # type: ignore[attr-defined]


class AutofireService(QObject):
    telemetry = Signal(dict)
    log = Signal(str)
    running_changed = Signal(bool)

    def __init__(self, cfg: AutofireConfig):
        super().__init__()
        self._thread = QThread()
        self.worker = AutofireWorker(cfg)
        self.worker.moveToThread(self._thread)

        self.worker.telemetry.connect(self.telemetry)
        self.worker.log.connect(self.log)
        self.worker.running_changed.connect(self.running_changed)

        self._thread.start()

    def shutdown(self) -> None:
        try:
            self.stop()
        except Exception:
            pass
        self._thread.quit()
        self._thread.wait(1500)

    def start(self) -> None:
        QTimer.singleShot(0, self.worker.start)

    def stop(self) -> None:
        self.worker.stop()

    def set_config(self, **kwargs) -> None:
        self.worker.set_config(kwargs)
