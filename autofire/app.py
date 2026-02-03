from __future__ import annotations

import time

from .engine import AutofireScheduler, EngineConfig, MonotonicClock
from .input import PygameRightStickInput
from .mapping import MovementConfig, movement_8way
from .output import PynputKeyboardSink


def main() -> int:
    print("AUTOFIRE - With 8-way diagonals (refactored core)")
    print("=" * 60)

    cfg = EngineConfig()
    move_cfg = MovementConfig(deadzone=0.4, diagonal_threshold=0.0)

    inp = PygameRightStickInput(axis_x_index=2, axis_y_index=3, joystick_index=0)
    out = PynputKeyboardSink()

    clock = MonotonicClock(time.monotonic)
    scheduler = AutofireScheduler(cfg)

    last_desired = frozenset()

    print("Ready! Move RIGHT stick")
    print("8-way movement: UP, UP-RIGHT, RIGHT, DOWN-RIGHT, DOWN, DOWN-LEFT, LEFT, UP-LEFT")
    print("Center stick to STOP")
    print("CTRL+C to exit")

    try:
        while True:
            now = clock.now()
            state = inp.read()
            desired = movement_8way(state, move_cfg)

            # On direction change, apply switch policy immediately
            if desired != last_desired:
                old_dir = "+".join(sorted(last_desired)) if last_desired else "NONE"
                new_dir = "+".join(sorted(desired)) if desired else "NONE"
                print(f"Change: {old_dir} → {new_dir}")

                delta = scheduler.set_desired(desired, now)
                out.apply(delta)

                if desired:
                    print(f"→ START: {'+'.join(k.upper() for k in sorted(desired))}")
                else:
                    print("→ STOPPED (stick centered)")

                last_desired = desired

            # Tick scheduler
            delta = scheduler.tick(now)
            out.apply(delta)

            time.sleep(0.01)

    except KeyboardInterrupt:
        # force stop cleanly
        now = clock.now()
        delta = scheduler.set_desired(frozenset(), now)
        out.apply(delta)
        out.apply(scheduler.tick(now))
        inp.close()
        print("\nExiting...")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
