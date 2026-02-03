from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class ControllerState:
    """
    A pure snapshot of controller state.
    You can extend this later (buttons, hats, triggers, etc.)
    """
    axis_x: float
    axis_y: float


class InputProvider(Protocol):
    def read(self) -> ControllerState:
        """Return a controller snapshot (pure data)."""
        ...


class PygameRightStickInput:
    """
    Reads right stick from pygame joystick.
    Defaults to axis 2 (x) and axis 3 (y) to match your current script.
    """

    def __init__(self, axis_x_index: int = 2, axis_y_index: int = 3, joystick_index: int = 0):
        self.axis_x_index = axis_x_index
        self.axis_y_index = axis_y_index
        self.joystick_index = joystick_index

        # Imported here so tests don't require pygame installed.
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
