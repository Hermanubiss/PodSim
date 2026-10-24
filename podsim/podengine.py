# The pod's maths. Pure functions only: numbers in, numbers out.


def clamp(value, low, high):
    # Keep value inside low..high. A value exactly on the edge is inside.
    if value < low:
        return low
    elif value > high:
        return high
    else:
        return value


def apply_deadzone(value, deadzone):
    # Tiny wobbles near the middle become exactly 0.0.
    if abs(value) < deadzone:
        return 0.0
    else:
        return value


def split_throttle(value):
    # One throttle (-1.0..1.0) becomes two triggers (each 0.0..1.0):
    # forward = gas on RT, back = brake on LT.
    if value >= 0:
        return (value, 0.0)
    else:
        return (0.0, abs(value))


# --- Podracer mode -----------------------------------------------------------
# Both sticks forward/back = two engines. Picked with "steering_mode":
# "podracer" in config.json (see pod_controls below).

def throttle(left, right):
    # Both forward: the stronger stick. Otherwise: the average.
    if left > 0 and right > 0:
        return max(left, right)
    else:
        return (left + right) / 2


def steering(left, right):
    # Left engine stronger = turn right (positive).
    return clamp(left - right, -1.0, 1.0)


# --- Steering modes and button bindings -------------------------------------

def pod_controls(mode, left_thrust, right_thrust, right_steer):
    # Turn the stick readings into (throttle, steering) for the chosen mode.
    # "podracer": both sticks are engines (uses throttle() and steering()).
    # Anything else ("right_stick"): left stick = throttle, right stick steers.
    if mode == "podracer":
        return (throttle(left_thrust, right_thrust), steering(left_thrust, right_thrust))
    else:
        return (left_thrust, right_steer)


def held_xbox_buttons(bindings, left_pressed, right_pressed):
    # Which Xbox buttons should be held down right now?
    # bindings looks like {"left": {"5": "X"}, "right": {"3": "A", "5": "X"}}:
    # binding-sheet number (as text, JSON keys are always text) -> Xbox name.
    # left_pressed / right_pressed are sets of sheet numbers held right now.
    # Two VKB buttons on the same Xbox button = either one holds it (an `or`).
    held = set()
    for side, pressed in (("left", left_pressed), ("right", right_pressed)):
        for number, xbox_name in bindings[side].items():
            if int(number) in pressed:
                held.add(xbox_name)
    return held


def pitch_clash(mode, pitch_stick, pitch_axis, thrust_axis, steer_axis):
    # The job the pitch axis ALREADY does, or "" if it's free.
    # A clashing axis is never used for pitch (see Binder.read_pitch).
    if pitch_stick == "off":
        return ""
    if mode == "podracer":
        if pitch_axis == thrust_axis:
            return "thrust"  # both sticks' forward/back are engines
    elif pitch_stick == "left" and pitch_axis == thrust_axis:
        return "gas and brake"
    elif pitch_stick == "right" and pitch_axis == steer_axis:
        return "steering"
    return ""


def pod_pitch(value, invert):
    # Nose up/down for the Xbox left stick's up/down.
    # Games disagree on which way is "up", so invert=True swaps it.
    if invert:
        return -value
    return value
