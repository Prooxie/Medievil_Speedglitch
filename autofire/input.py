from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass(frozen=True)
class ControllerState:
    lx: float
    ly: float
    rx: float
    ry: float
    lt: float
    rt: float
    buttons: Tuple[bool, ...]
    hat: Tuple[int, int]
    device_name: str


def _list_devices(pygame) -> List[tuple[int, str, int, int, int]]:
    out: List[tuple[int, str, int, int, int]] = []
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        j.init()
        out.append((i, j.get_name(), j.get_numaxes(), j.get_numbuttons(), j.get_numhats()))
    return out


def _find_index_by_tokens(pygame, tokens: List[str]) -> Optional[int]:
    tokens_l = [t.lower() for t in tokens]
    for i, name, *_ in _list_devices(pygame):
        n = (name or "").lower()
        if any(t in n for t in tokens_l):
            return i
    return None


class PygameSingleDeviceInput:
    """
    Single-device reader:
    - Reads axes 0/1 as left stick
    - Reads axes 2/3 as right stick
    - Reads axes 4/5 as triggers (common layout; if your device differs, we'll adjust later)
    """

    def __init__(self, device_tokens_prefer: List[str]):
        import pygame  # type: ignore

        self.pygame = pygame
        pygame.init()
        pygame.joystick.init()

        count = pygame.joystick.get_count()
        if count == 0:
            raise RuntimeError("No controller detected.")

        idx = _find_index_by_tokens(pygame, device_tokens_prefer)
        if idx is None:
            # fall back to first device so you never get blocked by renumbering/hiding
            idx = 0

        self.joy = pygame.joystick.Joystick(idx)
        self.joy.init()

        self.num_axes = self.joy.get_numaxes()
        self.num_buttons = self.joy.get_numbuttons()
        self.num_hats = self.joy.get_numhats()

        print("\nDetected devices:")
        for i, name, axes, btns, hats in _list_devices(pygame):
            print(f"  idx={i} name={name!r} axes={axes} buttons={btns} hats={hats}")
        print(f"\nUsing idx={idx} ({self.joy.get_name()!r})")

    def _axis(self, idx: int) -> float:
        if 0 <= idx < self.num_axes:
            return float(self.joy.get_axis(idx))
        return 0.0

    def read(self) -> ControllerState:
        self.pygame.event.pump()

        lx = self._axis(0)
        ly = self._axis(1)
        rx = self._axis(2)
        ry = self._axis(3)
        lt = self._axis(4)
        rt = self._axis(5)

        buttons = tuple(bool(self.joy.get_button(i)) for i in range(self.num_buttons))

        hat = (0, 0)
        if self.num_hats > 0:
            hat = tuple(self.joy.get_hat(0))

        return ControllerState(
            lx=lx, ly=ly, rx=rx, ry=ry,
            lt=lt, rt=rt,
            buttons=buttons,
            hat=hat,
            device_name=self.joy.get_name(),
        )

    def close(self) -> None:
        try:
            self.pygame.quit()
        except Exception:
            pass
