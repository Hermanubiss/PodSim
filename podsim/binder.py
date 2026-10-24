# The binder: two VKB sticks in, one virtual Xbox 360 pad out.
# Used by BOTH podsim.py (command line) and gui.py (window), so the pod
# flies exactly the same way whichever one you start.
#
# How it is used:
#     binder = Binder(settings)   # settings = the config.json dictionary
#     binder.start()              # plug in the virtual Xbox pad
#     binder.find_sticks()        # True once both VKBs are found
#     binder.step()               # ONE lap: read sticks, send to pad
#     binder.stop()               # unplug the virtual pad

import ctypes
import os
import subprocess

# Must be set BEFORE pygame is imported, or SDL ignores it.
# Lets the sticks update even when this window isn't focused.
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
# Hides pygame's "Hello from the pygame community" line.
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame  # noqa: E402  (this late import is on purpose)

# vgamepad is NOT imported up here: it connects to the ViGEmBus driver the
# moment it is imported, and crashes when the driver is missing. Binder.start()
# imports it instead, so PodSim still opens and can offer to install the driver.

from config import pitch_keys  # noqa: E402
from paths import resource_dir  # noqa: E402
from podengine import (  # noqa: E402
    apply_deadzone,
    clamp,
    held_xbox_buttons,
    pitch_clash,
    pod_controls,
    pod_pitch,
    split_throttle,
)


# --- Xbox buttons ------------------------------------------------------------

# The names used in config.json -> the name of vgamepad's Xbox button.
# Binder.start() turns these into the real buttons (vg.XUSB_BUTTON.<name>).
XBOX_BUTTONS = {
    "A": "XUSB_GAMEPAD_A",
    "B": "XUSB_GAMEPAD_B",
    "X": "XUSB_GAMEPAD_X",
    "Y": "XUSB_GAMEPAD_Y",
    "LB": "XUSB_GAMEPAD_LEFT_SHOULDER",
    "RB": "XUSB_GAMEPAD_RIGHT_SHOULDER",
    "BACK": "XUSB_GAMEPAD_BACK",
    "START": "XUSB_GAMEPAD_START",
    "LS": "XUSB_GAMEPAD_LEFT_THUMB",
    "RS": "XUSB_GAMEPAD_RIGHT_THUMB",
    "DPAD_UP": "XUSB_GAMEPAD_DPAD_UP",
    "DPAD_RIGHT": "XUSB_GAMEPAD_DPAD_RIGHT",
    "DPAD_DOWN": "XUSB_GAMEPAD_DPAD_DOWN",
    "DPAD_LEFT": "XUSB_GAMEPAD_DPAD_LEFT",
}

# The ViGEmBus installer that ships with PodSim (drivers/ in the project).
VIGEM_INSTALLER = "ViGEmBus_1.22.0_x64_x86_arm64.exe"


# --- Small helpers -----------------------------------------------------------

def find_stick(ending):
    # Return the stick whose name ends with `ending` ("L" or "R"),
    # or None if it isn't plugged in.
    count = pygame.joystick.get_count()
    for index in range(count):
        stick = pygame.joystick.Joystick(index)
        if stick.get_name().endswith(ending):
            return stick
    return None


def read_axis(stick, axis, flip, deadzone):
    # One axis as -1.0..1.0, with the deadzone applied.
    # flip=True turns it around: flight sticks read FORWARD as negative.
    raw = stick.get_axis(axis)
    if flip:
        raw = raw * -1.0
    clamped = clamp(raw, -1.0, 1.0)
    return apply_deadzone(clamped, deadzone)


def pressed_buttons(stick):
    # The set of buttons held right now, as BINDING-SHEET numbers.
    # pygame counts from 0, the sheet counts from 1: this is the ONLY
    # place in the project that adds the 1.
    pressed = set()
    for index in range(stick.get_numbuttons()):
        if stick.get_button(index):
            pressed.add(index + 1)
    return pressed


def all_devices():
    # Every controller Windows reports right now (VKBs, Xbox pads, ...).
    sticks = []
    for index in range(pygame.joystick.get_count()):
        sticks.append(pygame.joystick.Joystick(index))
    return sticks


def vid_pid_from_guid(guid):
    # SDL's device GUID hides the USB vendor and product IDs inside it:
    #   bytes 4-5 = vendor, bytes 8-9 = product, both written backwards
    #   (little-endian), with "0000" after each.
    # "030000001d2300000002000000000000" -> ("231D", "0200") = a VKB stick.
    # Gives (None, None) when the GUID isn't in that format.
    if len(guid) != 32 or guid[12:16] != "0000" or guid[20:24] != "0000":
        return (None, None)
    vendor = guid[10:12] + guid[8:10]
    product = guid[18:20] + guid[16:18]
    return (vendor.upper(), product.upper())


def vigem_driver_installed():
    # Ask Windows whether the ViGEmBus driver (the virtual Xbox pad) exists.
    try:
        result = subprocess.run(
            ["sc", "query", "ViGEmBus"],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        return False
    return "RUNNING" in result.stdout


def vigem_installer():
    # The official ViGEmBus 1.22.0 installer (from github.com/nefarius/ViGEmBus).
    # podsim.spec copies it into PodSim.exe.
    return resource_dir() / "drivers" / VIGEM_INSTALLER


def install_vigem_driver():
    # Start the ViGEmBus installer. Windows asks "allow changes?" first
    # (installing a driver needs admin), then the installer's own Next/Install
    # window appears. Returns straight away: the installer keeps running on
    # its own. False if it couldn't start (or "No" was clicked).
    installer = vigem_installer()
    if not installer.exists():
        return False
    # ShellExecuteW with "runas" = "Run as administrator". It returns a number
    # above 32 when the installer started.
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", str(installer), None, None, 1
    )
    return result > 32


def set_button(pad, button, held):
    # Press the Xbox button while `held` is True, release it otherwise.
    if held:
        pad.press_button(button=button)
    else:
        pad.release_button(button=button)


# --- The binder ----------------------------------------------------------------

class Binder:
    def __init__(self, settings):
        # `settings` is shared with whoever made it (the GUI): change a value
        # there and the next step() already uses it. No restart needed.
        self.settings = settings
        self.pad = None
        self.buttons = {}  # config name -> vgamepad button, filled by start()
        self.left = None
        self.right = None
        pygame.init()

    def start(self):
        # "Plug in" the virtual Xbox 360 controller.
        # Fails (raises an error) if the ViGEmBus driver isn't installed or
        # isn't running yet, e.g. "VIGEM_ERROR_BUS_NOT_FOUND".
        import vgamepad as vg  # connects to the driver (see the top of the file)

        self.buttons = {
            name: getattr(vg.XUSB_BUTTON, button) for name, button in XBOX_BUTTONS.items()
        }
        self.pad = vg.VX360Gamepad()

    def find_sticks(self):
        # Look for both VKBs. True when both are plugged in.
        pygame.event.pump()
        self.left = find_stick(self.settings["left_stick"])
        self.right = find_stick(self.settings["right_stick"])
        return self.left is not None and self.right is not None

    def step(self):
        # ONE lap: read both sticks, work out the pod, send it to the pad.
        # Hands back a dictionary of what happened (the GUI draws it), or
        # None if a stick was unplugged (call find_sticks() again).
        pygame.event.pump()  # let pygame read the latest stick positions
        s = self.settings
        deadzone = s["deadzone"]

        try:
            left_thrust = read_axis(self.left, s["thrust_axis"], True, deadzone)
            right_thrust = read_axis(self.right, s["thrust_axis"], True, deadzone)
            right_steer = read_axis(self.right, s["steer_axis"], False, deadzone)
            pitch_in = self.read_pitch()
            left_pressed = pressed_buttons(self.left)
            right_pressed = pressed_buttons(self.right)
        except pygame.error:
            # A stick was unplugged mid-race: let go of everything.
            self.left = None
            self.right = None
            self.release_all()
            return None

        # --- Axes ---
        pod_throttle, pod_steering = pod_controls(
            s["steering_mode"], left_thrust, right_thrust, right_steer
        )
        rt, lt = split_throttle(pod_throttle)
        self.pad.right_trigger_float(value_float=rt)
        self.pad.left_trigger_float(value_float=lt)
        pitch = pod_pitch(pitch_in, s["pitch_invert"])
        self.pad.left_joystick_float(x_value_float=pod_steering, y_value_float=pitch)

        # --- Buttons ---
        held = held_xbox_buttons(s["buttons"], left_pressed, right_pressed)
        for name, button in self.buttons.items():
            set_button(self.pad, button, name in held)

        self.pad.update()  # send everything above to Windows, once per lap

        return {
            "left_thrust": left_thrust,
            "right_thrust": right_thrust,
            "right_steer": right_steer,
            "throttle": pod_throttle,
            "steering": pod_steering,
            "pitch_in": pitch_in,
            "pitch": pitch,
            "rt": rt,
            "lt": lt,
            "left_pressed": left_pressed,
            "right_pressed": right_pressed,
            "held": held,
        }

    def read_pitch(self):
        # Nose up/down from this mode's pitch stick and axis. 0.0 when pitch
        # is "off" or its axis already does another job (thrust, steering).
        # Flipped like thrust, so pushing the stick forward reads positive.
        s = self.settings
        mode = s["steering_mode"]
        stick_key, axis_key = pitch_keys(mode)
        which, axis = s[stick_key], s[axis_key]
        if which == "off" or pitch_clash(mode, which, axis, s["thrust_axis"], s["steer_axis"]):
            return 0.0
        stick = self.left if which == "left" else self.right
        return read_axis(stick, axis, True, s["deadzone"])

    def release_all(self):
        # Centre the sticks, let go of every button and trigger.
        if self.pad is not None:
            self.pad.reset()
            self.pad.update()

    def stop(self):
        # Let go of everything, then "unplug" the virtual pad.
        self.release_all()
        self.pad = None
