from autofire.input import ControllerState
from autofire.mapping import MovementConfig, movement_8way


def test_8way_center_deadzone():
    cfg = MovementConfig(deadzone=0.4)
    assert movement_8way(ControllerState(0.0, 0.0), cfg) == frozenset()
    assert movement_8way(ControllerState(0.39, 0.0), cfg) == frozenset()
    assert movement_8way(ControllerState(0.0, -0.39), cfg) == frozenset()


def test_8way_cardinals():
    cfg = MovementConfig(deadzone=0.4)
    assert movement_8way(ControllerState(0.5, 0.0), cfg) == frozenset({"right"})
    assert movement_8way(ControllerState(-0.5, 0.0), cfg) == frozenset({"left"})
    assert movement_8way(ControllerState(0.0, -0.5), cfg) == frozenset({"up"})
    assert movement_8way(ControllerState(0.0, 0.5), cfg) == frozenset({"down"})


def test_8way_diagonals():
    cfg = MovementConfig(deadzone=0.4)
    assert movement_8way(ControllerState(0.6, -0.6), cfg) == frozenset({"up", "right"})
    assert movement_8way(ControllerState(-0.6, -0.6), cfg) == frozenset({"up", "left"})
    assert movement_8way(ControllerState(0.6, 0.6), cfg) == frozenset({"down", "right"})
    assert movement_8way(ControllerState(-0.6, 0.6), cfg) == frozenset({"down", "left"})


def test_8way_optional_diagonal_threshold_gate():
    # With diagonal_threshold enabled, small second-axis drift shouldn't create diagonal
    cfg = MovementConfig(deadzone=0.4, diagonal_threshold=0.7)
    # x passes deadzone but y doesn't pass diagonal gate; should become dominant axis only
    assert movement_8way(ControllerState(0.8, -0.5), cfg) == frozenset({"right"})
