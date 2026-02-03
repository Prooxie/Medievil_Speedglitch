from autofire.engine import AutofireScheduler, EngineConfig, TimingConfig, SwitchPolicy


def test_scheduler_hold_release_timing_basic():
    cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.1, release_time=0.05),
        switch=SwitchPolicy(settle_time=0.0, pause_after_release=0.0),
    )
    s = AutofireScheduler(cfg)

    t0 = 0.0
    # start desired
    _ = s.set_desired(frozenset({"up"}), t0)

    # first tick: should press and schedule next at t0 + hold
    d1 = s.tick(t0)
    assert d1.press == frozenset({"up"})
    assert d1.release == frozenset()

    # before hold ends: no changes
    d2 = s.tick(0.09)
    assert d2.press == frozenset()
    assert d2.release == frozenset()

    # at/after hold ends: should release
    d3 = s.tick(0.10)
    assert d3.release == frozenset({"up"})

    # before release ends: no changes
    d4 = s.tick(0.14)
    assert d4.press == frozenset()
    assert d4.release == frozenset()

    # after release ends: should press again
    d5 = s.tick(0.15)
    assert d5.press == frozenset({"up"})


def test_scheduler_disabling_releases():
    cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.1, release_time=0.05),
        switch=SwitchPolicy(settle_time=0.0, pause_after_release=0.0),
    )
    s = AutofireScheduler(cfg)

    t0 = 0.0
    s.set_desired(frozenset({"left"}), t0)
    s.tick(t0)  # press left

    d_stop = s.set_desired(frozenset(), 0.2)
    # stop should release anything held
    assert "left" in d_stop.release
