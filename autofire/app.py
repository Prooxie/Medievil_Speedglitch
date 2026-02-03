from __future__ import annotations

import time

from .engine import AutofireScheduler, EngineConfig, SwitchPolicy, TimingConfig
from .input import PygameRightStickInput
from .mapping import MovementConfig, movement_8way
from .output import PynputKeyboardSink


def main() -> int:
    print("AUTOFIRE - With 8-way diagonals (refactored core)")
    print("=" * 60)

    engine_cfg = EngineConfig(
        timing=TimingConfig(hold_time=0.133, release_time=0.033),
        switch=SwitchPolicy(settle_time=0.02, pause_after_release=0.08),
    )
    move_cfg = MovementConfig(deadzone=0.4, diagonal_threshold=0.0)

    inp = PygameRightStickInput(joystick_index=0, axis_x_index=2, axis_y_index=3)
    out = PynputKeyboardSink()
    scheduler = AutofireScheduler(engine_cfg)

    last_non_empty = frozenset()
    last_non_empty_time = time.monotonic()

    CENTER_GRACE = 0.12     # was 0.07
    CHANGE_DEBOUNCE = 0.06   # was 0.03
    pending_desired = frozenset()
    pending_since = 0.0


    last_desired = frozenset()

    print("Ready! Move RIGHT stick")
    print("Center stick to STOP. Ctrl+C to exit safely.")

    try:
        while True:
            now = time.monotonic()
            state = inp.read()
            raw_desired = movement_8way(state, move_cfg)

            # 1) Center grace: ignore brief center pass-through
            if raw_desired:
                candidate = raw_desired
                last_non_empty = raw_desired
                last_non_empty_time = now
            else:
                if (now - last_non_empty_time) < CENTER_GRACE:
                    candidate = last_non_empty
                else:
                    candidate = frozenset()

            # 2) Debounce any change (including UP -> UP+RIGHT)
            if candidate != last_desired:
                if candidate != pending_desired:
                    pending_desired = candidate
                    pending_since = now

                if (now - pending_since) >= CHANGE_DEBOUNCE:
                    desired = pending_desired
                else:
                    desired = last_desired
            else:
                pending_desired = candidate
                pending_since = now
                desired = candidate

            # 3) Apply desired direction to scheduler only when it truly changes
            if desired != last_desired:
                old_dir = "+".join(sorted(last_desired)) if last_desired else "NONE"
                new_dir = "+".join(sorted(desired)) if desired else "NONE"
                print(f"Change: {old_dir} → {new_dir}")

                out.apply(scheduler.set_desired(desired, now))
                last_desired = desired

            # 4) Tick scheduler every frame
            out.apply(scheduler.tick(now))

            time.sleep(0.01)



    except KeyboardInterrupt:
        now = time.monotonic()
        out.apply(scheduler.set_desired(frozenset(), now))
        out.apply(scheduler.tick(now))
        inp.close()
        print("\nExiting...")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
