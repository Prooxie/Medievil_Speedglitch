# Autofire

A Python-based autofire / speedglitch helper that uses a controller’s **right analog stick** with **true 8-way movement**.

Designed primarily for *Medievil* running in **ePSXe 2.0.0**, where precise overlapping directional pulses are required for speedglitch execution.

This project was designed for and tested with a **PS5 controller**.

After extensive experimentation with AutoHotkey and JoyToKey (which proved unreliable for overlapping pulses in ePSXe), this Python implementation was created.  
Using `pygame` and `pynput`, Autofire provides **stable timing**, **phantom-movement prevention**, and **strong failsafes**.

---

## Project Status

* **Version:** 1.1.1 (development refactor)
* **Status:** Stable core, active refactor
* **Platform:** Windows 11
* **Input Method:** Controller to Keyboard
* **Emulator Compatibility:** ePSXe
* **Architecture:** Modular, testable, event-driven core

> ⚠️ Note  
> Ongoing development happens on the **`development` branch**.  
> The `main` branch always reflects the last stable release.

---

## Features

* True **8-way analog movement**
  * Up, Down, Left, Right
  * All diagonals (Up-Right, Down-Left, etc.)
* Deterministic autofire system with alternating press / release cycles
* Tuned specifically for **speedglitch behavior**
* Immediate stop when input ceases
* Centering the analog stick releases all keys
* **Anti-phantom movement safeguards**
* Forced key releases on direction changes
* Lag-resistant scheduling (no thread races)
* Reliable behavior in **ePSXe**

---

## Architecture Overview (Refactor)

Autofire is now structured around **strict data separation**, making it easier to extend, test, and debug.

### Core layers

1. **Input**
   * Reads controller state (pygame)
   * Produces pure data snapshots
2. **Mapping**
   * Converts analog input into logical directions (4-way / 8-way)
   * No side effects, fully testable
3. **Engine / Scheduler**
   * Controls autofire timing
   * Handles direction changes safely
   * Prevents phantom or overlapping inputs
4. **Output**
   * Emits keyboard events (pynput)
   * Includes force-release failsafes

This design removes race conditions and makes future features (GUI, remapping, virtual controllers) feasible without rewriting the core.

---

## Installation and Usage

### Requirements

* Python **3.9+**
* Windows (Linux/macOS support planned... Maybe)

### Installation

1. Clone the repository:
   
```bash
git clone https://github.com/Prooxie/Autofire.git
cd Autofire
```

2. Install dependencies:

```bash
pip install pygame pynput
```

3. Ensure your emulator controller D-PAD is mapped to keyboard arrow keys.
4. Run the script:

```bash
python -m autofire.app
```

Exit safely with **Ctrl+C**.

---

## Controls

| Action           | Behavior                                      |
| ---------------- | --------------------------------------------- |
| Move right stick | Starts autofire in that direction             |
| Diagonal stick   | Fires two keys simultaneously (true diagonal) |
| Center stick     | Stops autofire immediately                    |
| Ctrl+C           | Exit the script safely                        |

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


## Configuration

Timing and sensitivity values are configurable in code (GUI planned):

```python
HOLD_TIME = 0.133        # How long keys are held (seconds)
RELEASE_TIME = 0.033     # Release duration
DEADZONE = 0.4           # Analog stick deadzone
DIAGONAL_THRESHOLD = 0.3 # Diagonal sensitivity threshold
```

> ⚠️ Warning
> Small timing adjustments can significantly affect speedglitch behavior. Change values carefully and test thoroughly.

---


### Testing

Autofire includes unit tests covering:

4-way and 8-way movement interpretation

Autofire timing accuracy

Direction replacement policies

Phantom-movement prevention

Lag-spike resilience

Run tests with:

```python
pytest
```

Tests do **not** require a controller, pygame, or pynput.

---

## Planned Features

GUI + tray mode

Controller monitor & diagnostics

Custom mappings and profiles

Virtual controller output

Multi-OS support

Multi-Language support

---

## Credits

Script by **ProxyDarkness**

https://www.youtube.com/@ProxyWasTaken / https://www.twitch.tv/ProxyDarkness


Special thanks to **NoobKillerRoof** for sharing crucial speedglitch knowledge and testing insights.

https://www.youtube.com/@NoobKillerRoof / https://www.twitch.tv/NoobKillerRoof

---

## License

This project is provided as-is for educational and experimental purposes. See the LICENSE file for details.
