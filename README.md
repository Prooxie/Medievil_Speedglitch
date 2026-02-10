# Autofire

A Python-based autofire / speedglitch helper that uses a controller’s **right analog stick** with **true 8-way movement**, while keeping the controller fully usable.

Designed primarily for *MediEvil* running in **ePSXe 2.0.0**, where precise overlapping directional pulses are required for speedglitch execution.

This project was designed for and tested with a **PS5 DualSense controller**.

After extensive experimentation with AutoHotkey and JoyToKey (which proved unreliable for overlapping analog pulses in ePSXe), this Python implementation was created.  
Using `pygame` and a virtual Xbox controller output, Autofire provides **stable timing**, **phantom-movement prevention**, and **strong failsafes**.

---

## Project Status

- **Version:** 1.1.4
- **Status:** Stable core, actively tuned
- **Platform:** Windows 11
- **Input:** DualSense (DirectInput via pygame)
- **Output:** Virtual Xbox 360 controller (ViGEmBus)
- **Emulator Compatibility:** ePSXe
- **Architecture:** Modular

> ⚠️ Note  
> Ongoing development happens on the **`development` branch**.  
> The `main` branch always reflects the last stable release.

---

## Features

- True **analog movement**
- Deterministic autofire system with alternating hold / release cycles
- Tuned specifically for **autofire behavior**
- Works reliably in **ePSXe**

---

## How It Works

Autofire:

1. Reads controller state using `pygame`
2. Takes the **right analog stick** as the autofire source
3. Pulses that direction using a deterministic scheduler:
   - Holds movement for `HOLD_TIME`
   - Releases for `RELEASE_TIME`
4. Outputs the result to a **virtual Xbox 360 controller** (ViGEmBus)

### Movement Behavior (Current)

- **Left stick** remains usable normally
- **Right stick** produces autofire movement pulses
- Both inputs can overlap (useful for speedglitch execution)

---

## Architecture Overview

Autofire is structured around strict data separation, making it easier to extend, test, and debug.

### Core layers

1. **Input**
   - Reads controller state (pygame)
2. **Mapping**
   - Deadzones, amplification, and vector logic
3. **Engine / Scheduler**
   - Controls autofire timing
   - Handles direction changes safely
4. **Output**
   - Emits movement through a virtual controller (ViGEmBus)

This design prevents race conditions and makes future features (GUI, remapping, profiles) feasible without rewriting the core.

---

## Installation and Usage

### Requirements

- Python **3.9+**
- Windows 11
- **ViGEmBus** installed (required for virtual Xbox controller output)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Prooxie/Autofire.git
cd Autofire
```

2. Install dependencies:

```bash
pip install pygame vgamepad
```

3. Install ViGEmBus  
(Required for virtual Xbox controller output)

4. Run:

```bash
python -m autofire.app
```

Exit safely with **Ctrl+C**.

---

## ePSXe Setup

ePSXe will see an **Xbox 360 Controller** created by Autofire.

In ePSXe input configuration:

1. Select the virtual Xbox 360 controller
2. Bind movement to the correct analog stick inputs
3. Test diagonals (important for speedglitch execution)

> Autofire works by translating the right-stick input into movement pulses that the game recognizes.

---

## Controls

| Action               | Behavior |
|----------------------|----------|
| Move right stick     | Autofire pulses in that direction |
| Ctrl+C               | Exit safely |

---

## Configuration

Timing and sensitivity values are configurable in code:

```python
HOLD_TIME = 0.128        # How long movement is held (seconds)
RELEASE_TIME = 0.032     # Release duration (requested + tuned)
LEFT_DEADZONE = 0.12
RIGHT_DEADZONE = 0.25
FULL_AT = 0.90           # 90% stick = 100% output (run threshold fix)
```

> ⚠️ Warning  
> Small timing adjustments can significantly affect speedglitch behavior.  
> Change values carefully and test thoroughly.

---

## Testing

Testing removed. 

---

## Planned Features

- GUI + tray mode
- Controller monitor & diagnostics
- Custom profiles and per-game configs
- Per-direction timing tuning
- Multi-language support

---

## Credits

Script by **ProxyDarkness**

https://www.youtube.com/@ProxyWasTaken  
https://www.twitch.tv/ProxyDarkness

Special thanks to **NoobKillerRoof** for sharing crucial speedglitch knowledge and testing insights.

https://www.youtube.com/@NoobKillerRoof  
https://www.twitch.tv/NoobKillerRoof

---

## License

This project is provided as-is for educational and experimental purposes. See the LICENSE file for details.
