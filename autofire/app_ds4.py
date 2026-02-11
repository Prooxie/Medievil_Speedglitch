from __future__ import annotations

import time


from .engine import AxisAutofireScheduler, EngineConfig, SwitchPolicy, TimingConfig
from .input import PygameSingleDeviceInput
from .mapping import AxisConfig, apply_deadzone, clamp2, amplify_to_full
from .output_ds4 import ViGEmDS4MergedLeftSink, ViGEmDS4SticksOnlyMergedLeftSink

# Import configuration
try:
    from .config import (
        ACTIVE_AUTOFIRE,
        ACTIVE_DEADZONE,
        ACTIVE_OUTPUT,
        DEVICE_TOKENS_PREFER,
        POLLING_INTERVAL,
        DEBUG_MODE,
    )
except ImportError:
    # Fallback defaults if config.py doesn't exist
    from dataclasses import dataclass
    
    @dataclass
    class ACTIVE_AUTOFIRE:
        hold_time = 0.128
        release_time = 0.032
        settle_time = 0.0
        pause_after_release = 0.0
    
    @dataclass
    class ACTIVE_DEADZONE:
        left_stick = 0.12
        right_stick = 0.25
        amplify_threshold = 0.90
    
    @dataclass
    class ACTIVE_OUTPUT:
        mode = "full_passthrough"
    
    DEVICE_TOKENS_PREFER = ["dualsense", "wireless controller"]
    POLLING_INTERVAL = 0.001
    DEBUG_MODE = False


def main() -> int:
    print("=" * 70)
    print("DualSense Speed Glitch Helper - DS4 EDITION")
    print("=" * 70)
    print("Mode: RIGHT stick -> Autofire -> Merged into VIRTUAL LEFT stick")
    print("Physical DualSense: All buttons/triggers work normally")
    print("Virtual DualShock 4: Left stick = autofire for speed glitch")
    print()
    print("ADVANTAGE: Consistent button mappings!")
    print("  Cross = Cross (not A)")
    print("  Circle = Circle (not B)")
    print("  Square = Square (not X)")
    print("  Triangle = Triangle (not Y)")
    print()
    print("Setup in ePSXe:")
    print("  1. Physical DualSense: Map normally (same as before!)")
    print("  2. Virtual DS4: Map left stick to attack button for speed glitch")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Autofire: hold={ACTIVE_AUTOFIRE.hold_time*1000:.1f}ms, release={ACTIVE_AUTOFIRE.release_time*1000:.1f}ms")
    print(f"  Deadzone: left={ACTIVE_DEADZONE.left_stick:.2f}, right={ACTIVE_DEADZONE.right_stick:.2f}")
    print(f"  Output mode: {ACTIVE_OUTPUT.mode}")
    print(f"  Polling: {int(1/POLLING_INTERVAL)} Hz")
    print("=" * 70)
    print()

    # Build configuration from config file
    engine_cfg = EngineConfig(
        timing=TimingConfig(
            hold_time=ACTIVE_AUTOFIRE.hold_time,
            release_time=ACTIVE_AUTOFIRE.release_time
        ), 
        switch=SwitchPolicy(
            settle_time=ACTIVE_AUTOFIRE.settle_time,
            pause_after_release=ACTIVE_AUTOFIRE.pause_after_release
        ),
    )

    left_cfg = AxisConfig(deadzone=ACTIVE_DEADZONE.left_stick)
    right_cfg = AxisConfig(deadzone=ACTIVE_DEADZONE.right_stick)

    inp = PygameSingleDeviceInput(
        device_tokens_prefer=DEVICE_TOKENS_PREFER,
    )

    # Choose output mode based on config
    if ACTIVE_OUTPUT.mode == "sticks_only":
        out = ViGEmDS4SticksOnlyMergedLeftSink()
        print("Note: Using sticks-only mode. Buttons/triggers only work on physical controller.")
    else:
        out = ViGEmDS4MergedLeftSink()
        print("Note: Using full passthrough. All inputs mirrored to virtual DS4.")
    
    print()
    scheduler = AxisAutofireScheduler(engine_cfg)

    try:
        print("Running... Press Ctrl+C to exit.\n")
        
        while True:
            now = time.monotonic()

            phys = inp.read()

            # Process physical left stick (for normal movement)
            phys_left = apply_deadzone((phys.lx, phys.ly), left_cfg.deadzone)
            phys_left = amplify_to_full(phys_left, full_at=ACTIVE_DEADZONE.amplify_threshold)
            
            # Process right stick (for autofire source)
            src = apply_deadzone((phys.rx, phys.ry), right_cfg.deadzone)
            src = amplify_to_full(src, full_at=ACTIVE_DEADZONE.amplify_threshold)

            # Update autofire scheduler with right stick input
            scheduler.set_desired(src, now)
            delta = scheduler.tick(now)

            # Debug output
            if DEBUG_MODE and (abs(delta.stick[0]) > 0.01 or abs(delta.stick[1]) > 0.01):
                print(f"Autofire: ({delta.stick[0]:+.3f}, {delta.stick[1]:+.3f}) | "
                      f"Physical left: ({phys_left[0]:+.3f}, {phys_left[1]:+.3f})")

            # Merge: virtual LEFT = clamp(physical_left + autofire_from_right)
            merged_left = clamp2((phys_left[0] + delta.stick[0], phys_left[1] + delta.stick[1]))

            # Apply to virtual controller
            out.apply(phys, merged_left)

            time.sleep(POLLING_INTERVAL)

    except KeyboardInterrupt:
        inp.close()
        out.close()
        print("\nExiting...")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
