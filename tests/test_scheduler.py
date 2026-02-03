from autofire.engine import AutofireScheduler, EngineConfig, TimingConfig, SwitchPolicy
from tests.conftest import FakeClock, RecordingSink


def test_hold_release_cycle_timing():
    cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.10, release_time=0.05),
        switch=SwitchPolicy(settle_time=0.0, pause_after_release=0.0),
    )
    s = AutofireScheduler(cfg)
    clk = FakeClock(0.0)
    sink = RecordingSink()

    # Set desired and tick -> should press immediately
    sink.apply_at(clk.now(), s.set_desired(frozenset({"up"}), clk.now()))
    sink.apply_at(clk.now(), s.tick(clk.now()))
    assert "up" in sink.down

    # Before hold ends -> no delta
    clk.advance(0.09)
    d = s.tick(clk.now())
    assert d.press == frozenset()
    assert d.release == frozenset()
    sink.apply_at(clk.now(), d)
    assert "up" in sink.down

    # At hold boundary -> release
    clk.advance(0.01)
    d = s.tick(clk.now())
    sink.apply_at(clk.now(), d)
    assert "up" not in sink.down
    assert d.release == frozenset({"up"})

    # After release_time -> press again
    clk.advance(0.05)
    d = s.tick(clk.now())
    sink.apply_at(clk.now(), d)
    assert "up" in sink.down
    assert d.press == frozenset({"up"})


def test_stop_releases_any_held_keys():
    cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.10, release_time=0.05),
        switch=SwitchPolicy(settle_time=0.0, pause_after_release=0.0),
    )
    s = AutofireScheduler(cfg)
    clk = FakeClock(0.0)
    sink = RecordingSink()

    sink.apply_at(clk.now(), s.set_desired(frozenset({"left"}), clk.now()))
    sink.apply_at(clk.now(), s.tick(clk.now()))
    assert "left" in sink.down

    # Stop
    clk.advance(0.2)
    d = s.set_desired(frozenset(), clk.now())
    sink.apply_at(clk.now(), d)
    assert "left" not in sink.down
    assert "left" in d.release or d.force_release_all
