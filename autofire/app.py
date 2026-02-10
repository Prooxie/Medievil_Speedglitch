from __future__ import annotations

import time

from .engine import AxisAutofireScheduler, EngineConfig, SwitchPolicy, TimingConfig
from .input import PygameSingleDeviceInput
from .mapping import AxisConfig, apply_deadzone, clamp2, amplify_to_full
from .output import VGamepadFullPassthroughMergedLeftSink


def main() -> int:
    print("Mode: Physical RIGHT stick -> Autofire -> Added onto VIRTUAL LEFT stick")
    print(" - Physical LEFT stick remains usable (merged)")
    print(" - Virtual LEFT = clamp(physical LEFT + autofire(physical RIGHT))")
    print(" - Release time fixed at 33ms (requested)")
    print("=" * 78)

    # Key tweak: keep release at 33ms, reduce hold to make it feel tighter.
    # Also remove settle/pause to avoid 'laggy' direction changes.
    engine_cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.128, release_time=0.032), 
        switch=SwitchPolicy(settle_time=0.0, pause_after_release=0.0),
    )

    # Separate deadzones: normal left stick can be smaller; autofire source should be higher.
    left_cfg = AxisConfig(deadzone=0.12)
    right_cfg = AxisConfig(deadzone=0.25)

    inp = PygameSingleDeviceInput(
        # Python is not able to work the same as DSX.
        device_tokens_prefer=["dualsense", "wireless controller", "xbox 360 controller", "xbox"],
    )

    out = VGamepadFullPassthroughMergedLeftSink()
    scheduler = AxisAutofireScheduler(engine_cfg)

    # Anti-jitter so the pulsing doesn't stutter when crossing center.
    # Last update: Get rid of this useless shit. Seriously. 
    CENTER_GRACE = 0.0
    CHANGE_DEBOUNCE = 0.0

    last_non_center = (0.0, 0.0)
    last_non_center_time = time.monotonic()

    last_desired = (0.0, 0.0)
    pending_desired = (0.0, 0.0)
    pending_since = 0.0

    def is_center(v: tuple[float, float]) -> bool:
        return abs(v[0]) < 1e-6 and abs(v[1]) < 1e-6

    try:
        while True:
            now = time.monotonic()

            phys = inp.read()

            # Normal left stick (for passthrough/merge)
            phys_left = apply_deadzone((phys.lx, phys.ly), left_cfg.deadzone)
            phys_left = amplify_to_full(phys_left, full_at=0.90)
            src = apply_deadzone((phys.rx, phys.ry), right_cfg.deadzone)
            src = amplify_to_full(src, full_at=0.90)
            # Center grace for source
            if not is_center(src):
                candidate = src
                last_non_center = src
                last_non_center_time = now
            else:
                candidate = last_non_center if (now - last_non_center_time) < CENTER_GRACE else (0.0, 0.0)

            # Debounce direction changes a bit
            if candidate != last_desired:
                if candidate != pending_desired:
                    pending_desired = candidate
                    pending_since = now
                desired = pending_desired if (now - pending_since) >= CHANGE_DEBOUNCE else last_desired
            else:
                pending_desired = candidate
                pending_since = now
                desired = candidate

            if desired != last_desired:
                scheduler.set_desired(desired, now)
                last_desired = desired

            delta = scheduler.tick(now)

            # Merge: virtual LEFT = clamp(phys_left + delta)
            merged_left = clamp2((phys_left[0] + delta.stick[0], phys_left[1] + delta.stick[1]))

            out.apply(phys, merged_left)

            time.sleep(0.001)

    except KeyboardInterrupt:
        inp.close()
        out.close()
        print("\nExiting...")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
