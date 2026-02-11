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
    Full virtual X360 controller output with complete passthrough.
    
    Physical DualSense -> Virtual Xbox 360:
    - Virtual LEFT stick = merged_left (physical left + autofire from right)
    - Virtual RIGHT stick = physical RIGHT stick (passthrough)
    - Buttons = full passthrough (A/B/X/Y/LB/RB/Back/Start/LS/RS)
    - Triggers = full passthrough (LT/RT)
    - D-pad = full passthrough
    
    This allows:
    - Physical DualSense to work normally in ePSXe for all buttons/triggers
    - Virtual Xbox 360 to provide autofire on left stick
    - You bind virtual left stick to attack in ePSXe for speed glitch
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
        
        DualSense button mapping (when detected as Xbox controller by pygame):
          0 Cross(X)→A, 1 Circle→B, 2 Square→X, 3 Triangle→Y
          4 L1→LB, 5 R1→RB, 6 Share→Back, 7 Options→Start
          8 L3→LS, 9 R3→RS
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
        # Virtual LEFT = merged (physical left + autofire)
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


class VGamepadSticksOnlyMergedLeftSink:
    """
    Virtual X360 output, but ONLY sticks:
    - Virtual LEFT stick = merged_left (already clamped)
    - Virtual RIGHT stick = physical RIGHT passthrough (optional but kept)
    - NO buttons, NO triggers, NO dpad (prevents mismapped buttons)
    
    Use this if you want physical controller buttons to work without interference.
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

    def apply(self, phys: ControllerState, merged_left: Tuple[float, float]) -> None:
        lx, ly = merged_left
        rx, ry = phys.rx, phys.ry

        # pygame: up=-1, down=+1 ; XInput: up=+, down=-
        self.gamepad.left_joystick(x_value=_to_i16(lx), y_value=_to_i16(-ly))
        self.gamepad.right_joystick(x_value=_to_i16(rx), y_value=_to_i16(-ry))

        # important: do not touch triggers/buttons/dpad at all
        self.gamepad.update()
