from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ControllerState:
    axis_x: float
    axis_y: float


class InputProvider(Protocol):
    def read(self) -> ControllerState:
        ...


class PygameRightStickInput(InputProvider):
    """
    Reads right stick from pygame joystick.
    Defaults axis 2 (x) and axis 3 (y) to match your current script.
    """

    def __init__(self, joystick_index: int = 0, axis_x_index: int = 2, axis_y_index: int = 3):
        self.joystick_index = joystick_index
        self.axis_x_index = axis_x_index
        self.axis_y_index = axis_y_index

        import pygame  # type: ignore
        self.pygame = pygame

        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No controller detected!")

        self.joystick = pygame.joystick.Joystick(joystick_index)
        self.joystick.init()

    def read(self) -> ControllerState:
        self.pygame.event.pump()
        x = float(self.joystick.get_axis(self.axis_x_index))
        y = float(self.joystick.get_axis(self.axis_y_index))
        return ControllerState(axis_x=x, axis_y=y)

    def close(self) -> None:
        try:
            self.pygame.quit()
        except Exception:
            pass
