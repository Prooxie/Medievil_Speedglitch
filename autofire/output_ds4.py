from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .input import ControllerState
from .mapping import clamp1


def _norm_trigger(t: float) -> float:
    """Normalize trigger axis into 0..1 float.

    pygame trigger axis is commonly:
      - -1..1 with rest=-1
      - OR 0..1 with rest=0
    """
    if 0.0 <= t <= 1.0:
        return t
    return (t + 1.0) * 0.5


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


@dataclass(frozen=True)
class _DpadState:
    direction: int  # DS4_DPAD_DIRECTIONS value


def _hat_to_ds4_direction(vg, hat: Tuple[int, int]) -> int:
    """Map pygame hat (x,y) to DS4_DPAD_DIRECTIONS enum value."""
    x, y = hat
    # pygame hat: x=-1/0/1, y=-1/0/1 (up=+1)
    # DS4: 8-way enum + NONE
    if y == 1 and x == 0:
        return int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH)
    if y == 1 and x == 1:
        return int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST)
    if y == 0 and x == 1:
        return int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST)
    if y == -1 and x == 1:
        return int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST)
    if y == -1 and x == 0:
        return int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH)
    if y == -1 and x == -1:
        return int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST)
    if y == 0 and x == -1:
        return int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST)
    if y == 1 and x == -1:
        return int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST)
    return int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)


class ViGEmDS4MergedLeftSink:
    """
    Virtual DualShock 4 controller output via **pyvjoystick** (ViGEm backend).

    Driver requirement (one-time):
      - Install ViGEmBus: https://github.com/ViGEm/ViGEmBus/releases

    Python dependency:
      - pip install pyvjoystick

    Passthrough behavior (full):
      - Virtual LEFT stick  = merged_left (physical left + autofire-from-right)
      - Virtual RIGHT stick = physical right (passthrough)
      - Triggers            = passthrough
      - Face/shoulder/etc   = passthrough
      - D-pad               = passthrough
      - PS / Touchpad click = passthrough
    """

    def __init__(self):
        try:
            from pyvjoystick import vigem as vg  # type: ignore
        except ImportError as e:
            raise ImportError(
                "pyvjoystick not installed. Install with:\n"
                "  pip install pyvjoystick\n"
                "Also requires the ViGEmBus driver installed (one-time):\n"
                "  https://github.com/ViGEm/ViGEmBus/releases"
            ) from e

        self.vg = vg
        self.gamepad = vg.VDS4Gamepad()

        # Cache last-known digital states to avoid redundant press/release calls.
        self._btn_cache: Dict[int, bool] = {}
        self._special_cache: Dict[int, bool] = {}
        self._dpad_cache = _DpadState(
            direction=int(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)
        )

        print("Virtual DualShock 4 controller created via pyvjoystick!")
        print("Note: This will show as 'Wireless Controller' in Windows")

    def close(self) -> None:
        try:
            self.gamepad.reset()
            self.gamepad.update()
        except Exception:
            pass

    def _set_button(self, pressed: bool, btn_enum: int) -> None:
        prev = self._btn_cache.get(btn_enum)
        if prev is pressed:
            return
        self._btn_cache[btn_enum] = pressed
        if pressed:
            self.gamepad.press_button(button=btn_enum)
        else:
            self.gamepad.release_button(button=btn_enum)

    def _set_special(self, pressed: bool, special_enum: int) -> None:
        prev = self._special_cache.get(special_enum)
        if prev is pressed:
            return
        self._special_cache[special_enum] = pressed
        if pressed:
            self.gamepad.press_special_button(special_button=special_enum)
        else:
            self.gamepad.release_special_button(special_button=special_enum)

    def _apply_buttons_ds4(self, buttons: Tuple[bool, ...]) -> None:
        """
        Map DualSense buttons to DS4 virtual controller.

        Expected pygame order (common for DualSense/DS4 via pygame):
          0 = Cross (X)
          1 = Circle (O)
          2 = Square (□)
          3 = Triangle (△)
          4 = L1
          5 = R1
          6 = Share
          7 = Options
          8 = L3
          9 = R3
          10 = PS button
          11 = Touchpad click
        """
        vg = self.vg
        b = list(buttons) + [False] * 20  # pad for safety

        # Face buttons
        self._set_button(b[0], int(vg.DS4_BUTTONS.DS4_BUTTON_CROSS))
        self._set_button(b[1], int(vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE))
        self._set_button(b[2], int(vg.DS4_BUTTONS.DS4_BUTTON_SQUARE))
        self._set_button(b[3], int(vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE))

        # Shoulders
        self._set_button(b[4], int(vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT))
        self._set_button(b[5], int(vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT))

        # Share / Options
        self._set_button(b[6], int(vg.DS4_BUTTONS.DS4_BUTTON_SHARE))
        self._set_button(b[7], int(vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS))

        # Stick clicks
        self._set_button(b[8], int(vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT))
        self._set_button(b[9], int(vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT))

        # PS / Touchpad click are "special" in ViGEm
        self._set_special(b[10], int(vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS))
        self._set_special(
            b[11], int(vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD)
        )

    def _apply_dpad_ds4(self, hat: Tuple[int, int]) -> None:
        direction = int(_hat_to_ds4_direction(self.vg, hat))
        if direction == self._dpad_cache.direction:
            return
        self._dpad_cache = _DpadState(direction=direction)
        self.gamepad.directional_pad(direction=direction)

    def apply(self, phys: ControllerState, merged_left: Tuple[float, float]) -> None:
        # Sticks: use float API (-1..1).
        # pyvjoystick notes DS4 Y is inverted for consistency with the X360 API,
        # so we treat it like X360: "up" should be positive.
        lx, ly = merged_left
        rx, ry = phys.rx, phys.ry

        lx = clamp1(lx)
        ly = clamp1(ly)
        rx = clamp1(rx)
        ry = clamp1(ry)

        # pygame: up=-1, down=+1 -> convert to "up positive" for ViGEm-style APIs
        self.gamepad.left_joystick_float(x_value_float=lx, y_value_float=ly)
        self.gamepad.right_joystick_float(x_value_float=rx, y_value_float=ry)

        # Triggers: float API (0..1)
        self.gamepad.left_trigger_float(value_float=_clamp01(_norm_trigger(phys.lt)))
        self.gamepad.right_trigger_float(value_float=_clamp01(_norm_trigger(phys.rt)))

        # Buttons + dpad
        self._apply_buttons_ds4(phys.buttons)
        self._apply_dpad_ds4(phys.hat)

        # Send update
        self.gamepad.update()


class ViGEmDS4SticksOnlyMergedLeftSink:
    """
    Virtual DS4 output, sticks + triggers only (no buttons/dpad/specials).

    - Virtual LEFT stick  = merged_left
    - Virtual RIGHT stick = physical right passthrough
    - Triggers            = passthrough

    Use this if you want to avoid any button conflicts in your emulator.
    """

    def __init__(self):
        try:
            from pyvjoystick import vigem as vg  # type: ignore
        except ImportError as e:
            raise ImportError(
                "pyvjoystick not installed. Install with:\n"
                "  pip install pyvjoystick\n"
                "Also requires the ViGEmBus driver installed (one-time):\n"
                "  https://github.com/ViGEm/ViGEmBus/releases"
            ) from e

        self.vg = vg
        self.gamepad = vg.VDS4Gamepad()

        print("Virtual DualShock 4 controller created via pyvjoystick (sticks-only mode)!")

    def close(self) -> None:
        try:
            self.gamepad.reset()
            self.gamepad.update()
        except Exception:
            pass

    def apply(self, phys: ControllerState, merged_left: Tuple[float, float]) -> None:
        lx, ly = merged_left
        rx, ry = phys.rx, phys.ry

        lx = clamp1(lx)
        ly = clamp1(ly)
        rx = clamp1(rx)
        ry = clamp1(ry)

        self.gamepad.left_joystick_float(x_value_float=lx, y_value_float=-ly)
        self.gamepad.right_joystick_float(x_value_float=rx, y_value_float=-ry)

        self.gamepad.left_trigger_float(value_float=_clamp01(_norm_trigger(phys.lt)))
        self.gamepad.right_trigger_float(value_float=_clamp01(_norm_trigger(phys.rt)))

        self.gamepad.update()
