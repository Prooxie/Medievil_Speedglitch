from autofire.engine import AutofireScheduler, EngineConfig, TimingConfig, SwitchPolicy


def test_phantom_prevention_hard_switch_force_release_and_pause():
    cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.2, release_time=0.1),
        switch=SwitchPolicy(settle_time=0.02, pause_after_release=0.08),
    )
    s = AutofireScheduler(cfg)

    # Start holding "up"
    t0 = 0.0
    s.set_desired(frozenset({"up"}), t0)
    d_press = s.tick(t0)
    assert d_press.press == frozenset({"up"})

    # Change direction while in hold: should immediately release and force release-all
    t_change = 0.05
    d_change = s.set_desired(frozenset({"right"}), t_change)
    assert d_change.force_release_all is True
    assert "up" in d_change.release

    # During settle_time, scheduler should emit nothing and keep released
    d_blocked = s.tick(t_change + 0.01)
    assert d_blocked.press == frozenset()
    assert d_blocked.release == frozenset()

    # After settle_time, it should emit a force_release_all ONCE and then pause
    d_force = s.tick(t_change + 0.02)
    assert d_force.force_release_all is True

    # During pause_after_release, still should not press
    d_pause = s.tick(t_change + 0.05)
    assert d_pause.press == frozenset()

    # After pause is over, it can start pressing "right"
    d_resume = s.tick(t_change + 0.11)
    # might press depending on exact tick; ensure it does not press before pause ends
    assert d_resume.press in (frozenset({"right"}), frozenset())


def test_lag_spike_does_not_create_overlap():
    cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.1, release_time=0.05),
        switch=SwitchPolicy(settle_time=0.02, pause_after_release=0.08),
    )
    s = AutofireScheduler(cfg)

    # Press up
    s.set_desired(frozenset({"up"}), 0.0)
    s.tick(0.0)

    # Direction change
    s.set_desired(frozenset({"left"}), 0.03)

    # Simulate big lag spike: next tick comes late
    d_late = s.tick(0.50)

    # In any case, we must not have "up" held again (no overlap)
    assert "up" not in s.held_keys
