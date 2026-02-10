from __future__ import annotations

from typing import Tuple

from .input import ControllerState
from .mapping import clamp1


def _to_i16(v: float) -> int:
    v = clamp1(v)
    if v >= 0:
        return int(v * 32767)
    return int(v * 32768)


def _norm_trigger(t: float) -> float:
    # pygame trigger axis: often -1..1 (rest=-1), sometimes 0..1
    if 0.0 <= t <= 1.0:
        return t
    return (t + 1.0) * 0.5


class VGamepadFullPassthroughMergedLeftSink:
    """
    Full virtual X360 controller output.

    - Virtual LEFT stick = merged_left (already clamped)
    - Virtual RIGHT stick = physical RIGHT stick passthrough (so it still exists)
      (This means right stick contributes both to merged_left via autofire and to virtual right;
       you said double inputs are okay.)
    - Buttons passthrough (supports common XInput button order automatically)
    - Triggers passthrough
    - D-pad passthrough via hat if available
    """

    def __init__(self):
        import vgamepad as vg  # type: ignore

        self.vg = vg
        self.gamepad = vg.VX360Gamepad()

    def close(self) -> None:
        try:
            self.gamepad.reset()
            self.gamepad.update()
        except Exception:
            pass

    def _set_btn(self, pressed: bool, btn) -> None:
        if pressed:
            self.gamepad.press_button(button=btn)
        else:
            self.gamepad.release_button(button=btn)

    def _apply_buttons_xinput_order(self, buttons: Tuple[bool, ...]) -> None:
        """
        Standard XInput-ish order (common for 'Xbox 360 Controller' in pygame):
          0 A, 1 B, 2 X, 3 Y, 4 LB, 5 RB, 6 Back, 7 Start, 8 LS, 9 RS
        """
        vg = self.vg
        b = list(buttons) + [False] * 16

        self._set_btn(b[0], vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self._set_btn(b[1], vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        self._set_btn(b[2], vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        self._set_btn(b[3], vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
        self._set_btn(b[4], vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        self._set_btn(b[5], vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        self._set_btn(b[6], vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        self._set_btn(b[7], vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
        self._set_btn(b[8], vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
        self._set_btn(b[9], vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)

    def _apply_hat_dpad(self, hat: Tuple[int, int]) -> None:
        x, y = hat
        vg = self.vg

        # release all
        for btn in (
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        ):
            self.gamepad.release_button(button=btn)

        if y == 1:
            self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        elif y == -1:
            self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)

        if x == -1:
            self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        elif x == 1:
            self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)

    def apply(self, phys: ControllerState, merged_left: Tuple[float, float]) -> None:
        # Virtual LEFT = merged
        lx, ly = merged_left

        # Virtual RIGHT = passthrough physical RIGHT
        rx, ry = phys.rx, phys.ry

        # pygame: up=-1, down=+1 ; XInput: up=+, down=-
        self.gamepad.left_joystick(x_value=_to_i16(lx), y_value=_to_i16(-ly))
        self.gamepad.right_joystick(x_value=_to_i16(rx), y_value=_to_i16(-ry))

        # triggers
        lt = int(max(0.0, min(1.0, _norm_trigger(phys.lt))) * 255)
        rt = int(max(0.0, min(1.0, _norm_trigger(phys.rt))) * 255)
        self.gamepad.left_trigger(value=lt)
        self.gamepad.right_trigger(value=rt)

        # buttons (XInput-style order)
        self._apply_buttons_xinput_order(phys.buttons)

        # dpad
        self._apply_hat_dpad(phys.hat)

        self.gamepad.update()
