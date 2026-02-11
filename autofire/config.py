"""
Configuration file for DualSense Speed Glitch Helper

Adjust these values to customize the autofire behavior and controller sensitivity.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class AutofireConfig:
    """Autofire timing settings"""
    
    # How long the stick is held in the desired direction (seconds)
    # Lower = faster autofire, Higher = slower but more deliberate
    # Recommended range: 0.040 - 0.200
    hold_time: float = 0.128
    
    # How long the stick returns to center between pulses (seconds)
    # Lower = faster autofire, Higher = more distinct pulses
    # Recommended range: 0.020 - 0.100
    release_time: float = 0.032
    
    # Delay before starting autofire after direction change (seconds)
    # 0 = instant response, higher = smoother but delayed
    # Recommended: 0.0 for responsive feel
    settle_time: float = 0.0
    
    # Pause after releasing center before next pulse (seconds)
    # 0 = no pause, higher = adds delay between direction changes
    # Recommended: 0.0 for responsive feel
    pause_after_release: float = 0.0


@dataclass
class DeadzoneConfig:
    """Controller deadzone settings"""
    
    # Physical left stick deadzone (for normal movement)
    # Lower = more sensitive, Higher = less drift
    # Recommended range: 0.08 - 0.20
    left_stick: float = 0.12
    
    # Physical right stick deadzone (controls autofire direction)
    # Higher recommended to prevent accidental autofire from drift
    # Recommended range: 0.20 - 0.40
    right_stick: float = 0.25
    
    # At what point should stick reach full intensity (0-1)
    # 0.90 means 90% stick movement = 100% output
    # Lower = more sensitive, Higher = need more stick movement
    # Recommended range: 0.80 - 0.95
    amplify_threshold: float = 0.90


@dataclass
class OutputConfig:
    """Virtual controller output settings"""
    
    # Which output mode to use:
    # "full_passthrough" = All buttons/triggers/dpad pass through (RECOMMENDED)
    # "sticks_only" = Only sticks output, no buttons (prevents conflicts)
    mode: str = "full_passthrough"


# ==============================================================================
# PRESET CONFIGURATIONS
# ==============================================================================

# Ultra-fast autofire (for rapid attacks)
PRESET_ULTRAFAST = AutofireConfig(
    hold_time=0.040,
    release_time=0.020,
    settle_time=0.0,
    pause_after_release=0.0,
)

# Fast autofire (balanced speed and control)
PRESET_FAST = AutofireConfig(
    hold_time=0.060,
    release_time=0.025,
    settle_time=0.0,
    pause_after_release=0.0,
)

# Moderate autofire (good for most games)
PRESET_MODERATE = AutofireConfig(
    hold_time=0.100,
    release_time=0.033,
    settle_time=0.0,
    pause_after_release=0.0,
)

# Slow autofire (deliberate, precise)
PRESET_SLOW = AutofireConfig(
    hold_time=0.150,
    release_time=0.050,
    settle_time=0.0,
    pause_after_release=0.0,
)

# Custom configuration (edit values above)
PRESET_CUSTOM = AutofireConfig(
    hold_time=0.128,
    release_time=0.032,
    settle_time=0.0,
    pause_after_release=0.0,
)


# ==============================================================================
# ACTIVE CONFIGURATION
# ==============================================================================

# Choose your preset here (or use PRESET_CUSTOM and edit values above)
ACTIVE_AUTOFIRE = PRESET_CUSTOM

# Deadzone configuration
ACTIVE_DEADZONE = DeadzoneConfig(
    left_stick=0.12,
    right_stick=0.25,
    amplify_threshold=0.90,
)

# Output configuration
ACTIVE_OUTPUT = OutputConfig(
    mode="full_passthrough",  # or "sticks_only"
)


# ==============================================================================
# DEVICE PREFERENCES
# ==============================================================================

# Preferred device names (searched in order)
# The tool will use the first matching device found
DEVICE_TOKENS_PREFER = [
    "dualsense",
    "wireless controller",
    "dualshock",
    "ps5",
    "ps4",
]


# ==============================================================================
# ADVANCED SETTINGS
# ==============================================================================

# Polling rate (seconds between input reads)
# Lower = more responsive but higher CPU usage
# Recommended: 0.001 (1000 Hz)
POLLING_INTERVAL: float = 0.001

# Debug mode (print detailed information)
DEBUG_MODE: bool = False
