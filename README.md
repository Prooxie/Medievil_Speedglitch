# Autofire Speedglitch Script (Python)

A Python-based autofire / speedglitch helper that uses a controller’s right analog stick with true 8-way movement.
Designed for games such as *Medievil* running in **ePSXe**, where precise overlapping directional pulses are required.

This project was designed for and tested with a **PS5 controller**.

After extensive experimentation with AutoHotkey, which proved unreliable for overlapping pulses in some emulators, this Python implementation was created. Using `pygame` and `pynput`, it provides stable timing, eliminates phantom movement, and includes strong failsafes.

---

## Project Status

* Status: Stable
* Platform: Windows 11
* Input Method: Controller → Keyboard
* Emulator Compatibility: ePSXe (tested)

---

## Features

* True 8-way analog movement

  * Up, Down, Left, Right
  * All diagonal directions (Up-Right, Down-Left, etc.)
* Autofire system with alternating press and release cycles
* Tuned specifically for speedglitch behavior
* Immediate stop when input ceases
* Centering the analog stick releases all keys
* Anti-phantom movement safeguards
* Force-releases keys on direction changes
* Reliable behavior in ePSXe

---

## Requirements

* Python 3.9 or newer (recommended)
* A controller with a right analog stick
* ePSXe with D-Pad directions mapped to keyboard arrow keys
* Required Python packages:

```bash
pip install pygame pynput
```

---

## Installation

1. Install Python 3.9 or newer.
2. Clone or download this repository.
3. Install dependencies:

```bash
pip install pygame pynput
```

4. Ensure your emulator controller D-PAD is mapped to keyboard arrow keys.
5. Run the script:

```bash
python autofire.py
```

---

## How It Works

* Reads right analog stick axes using `pygame`
* Converts stick direction into keyboard arrow key inputs
* Runs a background thread that:

  * Holds keys for `HOLD_TIME`
  * Releases keys for `RELEASE_TIME`

### Direction Changes

When the analog stick direction changes:

1. Autofire is stopped
2. All keys are force-released
3. A short delay is applied
4. The new direction starts cleanly

This prevents common emulator-related issues such as:

* Stuck directions
* Phantom movement
* Conflicting or oscillating inputs

---

## Controls

| Action           | Behavior                                      |
| ---------------- | --------------------------------------------- |
| Move right stick | Starts autofire in that direction             |
| Diagonal stick   | Fires two keys simultaneously (true diagonal) |
| Center stick     | Stops autofire immediately                    |
| Ctrl+C           | Exit the script safely                        |

---

## Configuration

The following values can be adjusted at the top of the script:

```python
HOLD_TIME = 0.133        # How long keys are held (seconds)
RELEASE_TIME = 0.033     # Release duration
DEADZONE = 0.4           # Analog stick deadzone
DIAGONAL_THRESHOLD = 0.3 # Diagonal sensitivity threshold
```

### Warning

Small timing adjustments can significantly affect speedglitch behavior. Change values carefully and test thoroughly.

---

## Anti-Phantom Safeguards

This script intentionally:

* Releases all arrow keys multiple times
* Inserts short delays between direction changes
* Prevents overlapping old and new directions
* Resets autofire state cleanly on every transition

These safeguards are the primary reason this script behaves reliably in ePSXe.

---

## Tested With

* ePSXe
* Medievil 1 NTSC version
* DualShock-style controllers (including PS5 controller)
* Windows 11

---

## Credits

Script by **ProxyDarkness**

https://www.youtube.com/@ProxyWasTaken / https://www.twitch.tv/ProxyDarkness


Special thanks to **NoobKillerRoof** for sharing crucial speedglitch knowledge and testing insights.

https://www.youtube.com/@NoobKillerRoof / https://www.twitch.tv/NoobKillerRoof

---

## License

This project is provided as-is for educational and experimental purposes. See the LICENSE file for details.
