# AGENTS.md

## Purpose
This document defines how to add new scripts under `examples/` for this CircuitPython project.
Target board setup is managed by `cuskey_settings.py`, and examples are expected to follow the same hardware assumptions and coding style as existing files.

## Project Snapshot
- Runtime: CircuitPython on RP2040 boards.
- Main config: `cuskey_settings.py`
- Existing examples:
  - `examples/meeting_controller.py`
  - `examples/pin_sender.py`
  - `examples/ptt_key.py`
  - `examples/auto_keysend.py`
  - `examples/youtube_controller.py`
- Common hardware model:
  - 1 button input (`pins["button"]`, pull-up, active-low)
  - 1 mode switch input (`pins["mode_a"]`, pull-up, active-low)
  - optional GND drive pins (`pins["button_gnd"]`, `pins["mode_gnd"]`)

## Non-Negotiable Rules For New Examples
1. Always load board config from `cuskey_settings.py`:
   - `pins = cuskey_settings.get_pins()`
   - `features = cuskey_settings.get_features()`
   - `board_name = cuskey_settings.get_board_name()`
2. Preserve active-low interpretation:
   - `mode_a.value == False` means Mode A (switch connected to GND).
   - Button press edge is `True -> False`.
3. If a GND helper pin exists, configure it as output low.
4. Put tweakable constants at top of file (timings, intervals, key mapping).
5. Use `time.monotonic()` for press duration and interval checks.
6. Keep debounce and loop sleep (`time.sleep(...)`) to avoid chattering and busy loops.
7. Respect debug flag:
   - Verbose logs should depend on `features["debug_enabled"]`.
8. Keep dependencies limited to built-in CircuitPython modules and `adafruit_hid`.

## HID Usage Guidelines
- Use `Keyboard` + `Keycode` for normal key taps/combos.
- Use `keyboard.press(...)` / `keyboard.release(...)` for hold-style actions (PTT-like behavior).
- Use `ConsumerControl` + `ConsumerControlCode` for media/system controls (play, volume, mute).
- Use `Mouse.move(wheel=...)` for wheel actions.

## Recommended File Structure
Follow this order:
1. Module docstring (what it does, short operation summary)
2. Imports
3. Configurable constants
4. Load board settings (`cuskey_settings`)
5. HID object initialization
6. Pin setup (mode, button, optional GND pins)
7. State variables
8. Helper functions (action senders)
9. Startup print summary (mode behavior and controls)
10. Main loop (edge detection + state machine)
11. Optional long trailing usage block docstring

## Minimal Implementation Template
```python
import digitalio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import cuskey_settings

# Config
LONG_PRESS_TIME = 0.3
DEBOUNCE_TIME = 0.05
LOOP_DELAY = 0.01

pins = cuskey_settings.get_pins()
features = cuskey_settings.get_features()
board_name = cuskey_settings.get_board_name()

keyboard = Keyboard(usb_hid.devices)

if pins["mode_gnd"]:
    mode_gnd = digitalio.DigitalInOut(pins["mode_gnd"])
    mode_gnd.direction = digitalio.Direction.OUTPUT
    mode_gnd.value = False

mode_a = digitalio.DigitalInOut(pins["mode_a"])
mode_a.direction = digitalio.Direction.INPUT
mode_a.pull = digitalio.Pull.UP

if pins["button_gnd"]:
    button_gnd = digitalio.DigitalInOut(pins["button_gnd"])
    button_gnd.direction = digitalio.Direction.OUTPUT
    button_gnd.value = False

button = digitalio.DigitalInOut(pins["button"])
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

last_button_state = True
press_start = None

while True:
    now = time.monotonic()
    current = button.value

    if last_button_state and not current:
        press_start = now
        time.sleep(DEBOUNCE_TIME)

    elif not last_button_state and current and press_start is not None:
        duration = now - press_start
        current_mode = mode_a.value
        if duration >= LONG_PRESS_TIME:
            if current_mode == False:
                keyboard.send(Keycode.LEFT_ARROW)
            else:
                keyboard.send(Keycode.RIGHT_ARROW)
        else:
            keyboard.send(Keycode.ENTER)
        press_start = None
        time.sleep(DEBOUNCE_TIME)

    last_button_state = current
    time.sleep(LOOP_DELAY)
```

## Behavior Design Patterns
- Short press vs long press:
  - Track press start time at falling edge.
  - Compare duration at release (or during hold for repeat action).
- Repeat while held:
  - Track `last_send_time`.
  - Send only when `now - last_send_time >= INTERVAL`.
- Multi-click:
  - Track `last_click_time`, `click_count`, and timeout resolution.
  - Resolve pending single-click after timeout.

## Quality Checklist Before Finalizing A New Example
1. Script imports and runs under CircuitPython without desktop-only modules.
2. No hardcoded board pin numbers inside example logic.
3. Mode semantics are clearly printed at startup.
4. Debounce and loop delays exist and are configurable.
5. Long-press logic does not accidentally trigger short-press behavior.
6. Hold actions release keys correctly when button is released.
7. File name reflects feature intent (for example: `examples/zoom_mic_toggle.py`).
8. If user-facing behavior differs from existing examples, include a usage docstring block at bottom.

## Manual Test Procedure (Hardware)
1. Copy `cuskey_settings.py`, the new example (renamed to `code.py` or executed manually), and required `adafruit_hid` modules to CIRCUITPY.
2. Open serial console and verify startup logs (board type, mode behavior, debug state).
3. Validate Mode A action set (short, long, and optional multi-click paths).
4. Validate Mode B action set.
5. Validate key release behavior after long press/hold actions.
6. Validate behavior with debug off (`DEBUG_MODE = False`) and on (`DEBUG_MODE = True`).

## Scope Boundaries
- Do not change `cuskey_settings.py` unless the task explicitly requires board definition changes.
- Do not add network dependencies.
- Keep each new example self-contained in one file under `examples/`.
