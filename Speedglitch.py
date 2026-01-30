# Autofire script v1.1, right analogs, 8-way movement
# If script does not work: pip install pygame pynput
import pygame
import time
import threading
from pynput.keyboard import Key, Controller

# Setup of the controller
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No controller detected!")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
keyboard = Controller()

print("AUTOFIRE - With 8-way diagonals")
print("="*50)

# Config, feel free to adjust this, but be wary!
HOLD_TIME = 0.133
RELEASE_TIME = 0.033
DEADZONE = 0.4
DIAGONAL_THRESHOLD = 0.3  # How much both axes need to trigger diagonal

current_keys = []  # Now a list since diagonals need 2 keys
running = True
is_holding = False
autofire_active = False

KEY_MAP = {
    'up': Key.up,
    'down': Key.down,
    'left': Key.left,
    'right': Key.right
}

ALL_ARROW_KEYS = [Key.up, Key.down, Key.left, Key.right]

def force_release_all():
    """Release all keys multiple times"""
    for _ in range(5):
        for key in ALL_ARROW_KEYS:
            try:
                keyboard.release(key)
            except:
                pass
        time.sleep(0.01)

def get_direction():
    """8-way directions including diagonals"""
    pygame.event.pump()
    x = joystick.get_axis(2)
    y = joystick.get_axis(3)
    
    # Check if stick is centered
    if abs(x) < DEADZONE and abs(y) < DEADZONE:
        return []  # No input
    
    keys = []
    
    # Vertical
    if y < -DEADZONE:
        keys.append('up')
    elif y > DEADZONE:
        keys.append('down')
    
    # Horizontal
    if x > DEADZONE:
        keys.append('right')
    elif x < -DEADZONE:
        keys.append('left')
    
    return keys

def keys_equal(keys1, keys2):
    """Compare two key lists"""
    if len(keys1) != len(keys2):
        return False
    return set(keys1) == set(keys2)

def autofire_thread():
    """HOLD / RELEASE cycle for all current keys"""
    global current_keys, running, is_holding, autofire_active
    
    while running:
        if autofire_active and len(current_keys) > 0:
            if not is_holding:
                # PRESS all current keys
                for key_name in current_keys:
                    keyboard.press(KEY_MAP[key_name])
                is_holding = True
                time.sleep(HOLD_TIME)
            else:
                # RELEASE all current keys
                for key_name in current_keys:
                    keyboard.release(KEY_MAP[key_name])
                is_holding = False
                time.sleep(RELEASE_TIME)
        else:
            # Not active - ensure everything released
            if is_holding:
                force_release_all()
                is_holding = False
            time.sleep(0.01)

def main():
    global current_keys, running, is_holding, autofire_active
    
    fire_thread = threading.Thread(target=autofire_thread, daemon=True)
    fire_thread.start()
    
    print("Ready! Move RIGHT stick")
    print("8-way movement: UP, UP-RIGHT, RIGHT, DOWN-RIGHT, DOWN, DOWN-LEFT, LEFT, UP-LEFT")
    print("Center stick to STOP")
    
    try:
        while running:
            new_keys = get_direction()
            
            if not keys_equal(new_keys, current_keys):
                # Direction changed
                old_dir = "+".join(current_keys) if current_keys else "NONE"
                new_dir = "+".join(new_keys) if new_keys else "NONE"
                print(f"Change: {old_dir} → {new_dir}")
                
                # FUNK PHANTOM MOVES
                autofire_active = False
                is_holding = False
                time.sleep(0.02)  # Let current cycle finish
                
                # Force release ALL keys
                force_release_all()
                time.sleep(0.08)  # 80ms pause
                
                # Update direction
                current_keys = new_keys
                
                if len(current_keys) > 0:
                    # Start autofire with new direction(s)
                    autofire_active = True
                    dir_str = "+".join([k.upper() for k in current_keys])
                    print(f"→ START: {dir_str}")
                else:
                    # Stick centered - stay stopped
                    autofire_active = False
                    print("→ STOPPED (stick centered)")
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        running = False
        autofire_active = False
        force_release_all()
        print("\nExiting...")
        pygame.quit()

# Is it done, Yuri?
# No, comrade Premiere. It has only begun.

# If the script is working for you, feel free to check my youtube https://www.youtube.com/@ProxyWasTaken or twitch https://www.twitch.tv/ProxyDarkness
# Credits to NoobKillerRoof for giving me enough informations to work with, show him some love https://www.youtube.com/@NoobKillerRoof / https://www.twitch.tv/noobkillerroof

# Thank you and have a nice day!
if __name__ == "__main__":
    main()