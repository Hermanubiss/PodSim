# PodSim (command line): two VKB sticks -> one virtual Xbox 360 pad.
# All the real work is in binder.py; the window version is gui.py.
# Settings and button bindings come from config.json.
#
# Run it from the project folder:  python podsim\podsim.py

import time
from pathlib import Path

from binder import Binder
from config import add_missing, load_settings


# --- Settings (from config.json) --------------------------------------------

settings = add_missing(load_settings(Path(__file__).parent / "config.json"))


# --- Functions ---------------------------------------------------------------

def wait_for_sticks(binder):
    # Keep looking until both sticks are plugged in.
    while not binder.find_sticks():
        print("Waiting for both sticks to be connected...")
        time.sleep(settings["wait_seconds"])
    print(f"Left:  {binder.left.get_name()}")
    print(f"Right: {binder.right.get_name()}")


# --- Main program ------------------------------------------------------------

binder = Binder(settings)
binder.start()  # "plug in" the virtual Xbox 360 controller
wait_for_sticks(binder)
print(f"Flying ({settings['steering_mode']} mode). Press Ctrl+C to stop.")

try:
    while True:
        reading = binder.step()
        if reading is None:  # a stick was unplugged
            print()
            wait_for_sticks(binder)
            continue

        print(
            f"throttle: {reading['throttle']:+.2f} | steering: {reading['steering']:+.2f}",
            end="\r",
        )
        time.sleep(0.01)  # ~100 updates a second
except KeyboardInterrupt:
    binder.stop()
    print("\nStopped.")
