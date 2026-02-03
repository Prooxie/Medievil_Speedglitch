from autofire.input import ControllerState
from autofire.mapping import MovementConfig, movement_4way


def test_4way_center_deadzone():
    cfg = MovementConfig(deadzone=0.4)
    assert movement_4way(ControllerState(0.0, 0.0), cfg) == frozenset()
    assert movement_4way(ControllerState(0.39, 0.0), cfg) == frozenset()
    assert movement_4way(ControllerState(0.0, -0.39), cfg) == frozenset()


def test_4way_cardinals():
    cfg = MovementConfig(deadzone=0.4)
    assert movement_4way(ControllerState(0.5, 0.0), cfg) == frozenset({"right"})
    assert movement_4way(ControllerState(-0.5, 0.0), cfg) == frozenset({"left"})
    assert movement_4way(ControllerState(0.0, -0.5), cfg) == frozenset({"up"})
    assert movement_4way(ControllerState(0.0, 0.5), cfg) == frozenset({"down"})


def test_4way_dominant_axis_when_both_active():
    cfg = MovementConfig(deadzone=0.4)
    # x dominates
    assert movement_4way(ControllerState(0.9, -0.6), cfg) == frozenset({"right"})
    # y dominates
    assert movement_4way(ControllerState(0.6, -0.9), cfg) == frozenset({"up"})
