from autofire.engine import AutofireScheduler, EngineConfig, TimingConfig, SwitchPolicy
from tests.conftest import FakeClock, RecordingSink


def test_direction_change_triggers_force_release_and_block():
    cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.20, release_time=0.10),
        switch=SwitchPolicy(settle_time=0.02, pause_after_release=0.08),
    )
    s = AutofireScheduler(cfg)
    clk = FakeClock(0.0)
    sink = RecordingSink()

    # Start UP and press
    sink.apply_at(clk.now(), s.set_desired(frozenset({"up"}), clk.now()))
    sink.apply_at(clk.now(), s.tick(clk.now()))
    assert sink.down == {"up"}

    # Change to RIGHT during hold
    clk.set(0.05)
    d_change = s.set_desired(frozenset({"right"}), clk.now())
    sink.apply_at(clk.now(), d_change)

    # Must force release all and release UP
    assert d_change.force_release_all is True
    assert "up" in d_change.release or "up" not in sink.down
    assert sink.down == set()  # RecordingSink clears on force_release_all

    # While still in settle_time window: should NOT press right
    clk.set(0.06)  # change + 0.01 < 0.02
    d_block = s.tick(clk.now())
    sink.apply_at(clk.now(), d_block)
    assert sink.down == set()
    assert d_block.press == frozenset()

    # At settle boundary: scheduler emits extra force_release_all once and extends pause
    clk.set(0.07)  # now >= 0.05 + 0.02
    d_force = s.tick(clk.now())
    sink.apply_at(clk.now(), d_force)
    assert d_force.force_release_all is True
    assert sink.down == set()

    # During pause window: still no press
    clk.set(0.10)  # still within pause_after_release (0.07 + 0.08 = 0.15)
    d_pause = s.tick(clk.now())
    sink.apply_at(clk.now(), d_pause)
    assert d_pause.press == frozenset()
    assert sink.down == set()

    # After pause ends: should be allowed to press RIGHT on a tick
    clk.set(0.16)
    d_resume = s.tick(clk.now())
    sink.apply_at(clk.now(), d_resume)
    assert sink.down in ({"right"}, set())
    # If it didn't press exactly at 0.16 due to timing, next tick should
    if sink.down != {"right"}:
        clk.advance(0.01)
        sink.apply_at(clk.now(), s.tick(clk.now()))
        assert sink.down == {"right"}


def test_lag_spike_after_change_never_reintroduces_old_key():
    cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.10, release_time=0.05),
        switch=SwitchPolicy(settle_time=0.02, pause_after_release=0.08),
    )
    s = AutofireScheduler(cfg)
    clk = FakeClock(0.0)
    sink = RecordingSink()

    # Start UP
    sink.apply_at(clk.now(), s.set_desired(frozenset({"up"}), clk.now()))
    sink.apply_at(clk.now(), s.tick(clk.now()))
    assert sink.down == {"up"}

    # Change to LEFT
    clk.set(0.03)
    sink.apply_at(clk.now(), s.set_desired(frozenset({"left"}), clk.now()))
    assert sink.down == set()

    # Big lag spike: next tick is much later
    clk.set(1.0)
    sink.apply_at(clk.now(), s.tick(clk.now()))

    # Old key must never come back
    assert "up" not in sink.down
    # Only allowed keys are either none (if timing not yet pressed) or {"left"}
    assert sink.down in (set(), {"left"})
