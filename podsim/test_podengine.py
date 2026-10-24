import pytest

from podengine import held_xbox_buttons, pitch_clash, pod_controls, pod_pitch, split_throttle, steering, throttle


def test_throttle_hands_off():
    assert throttle(0.0,0.0) == 0.0

def test_throttle_full_forward():
    assert throttle(1.0,1.0) == 1.0

def test_throttle_both_forward_uses_stronger():
    assert throttle(0.8,0.5) == 0.8

def test_throttle_both_brakes():
    assert throttle(-1.0,-1.0) == -1.0

def test_throttle_only_left():
    assert throttle(1.0,0.0) == 0.5

def test_throttle_one_forward_one_back():
    assert throttle(0.6,-0.2) == pytest.approx(0.2)

def test_throttle_right_stronger():
    assert throttle(0.5,0.9) == 0.9


def test_steering_straigth():
    assert steering(0.5,0.5) == 0.0

def test_steering_left_stronger_turns_right():
    assert steering(1.0,0.2) == 0.8

def test_steering_right_stronger_turns_left():
    assert steering(0.2,1.0) == -0.8

def test_steering_is_clamped():
    assert steering(1.0,-1.0) == 1.0


def test_split_throttle_forward():
    assert split_throttle(0.8) == (0.8,0.0)
def test_split_throttle_idle():
    assert split_throttle(0.0) == (0.0,0.0)
def test_split_throttle_brake():
    assert split_throttle(-0.5) == (0.0,0.5)
def test_split_throttle_full_brake():
    assert split_throttle(-1.0) == (0.0,1.0)

def test_pod_controls_right_stick_mode_passes_through():
    assert pod_controls("right_stick", 0.7, -0.3, 0.4) == (0.7, 0.4)

def test_pod_controls_podracer_both_forward():
    assert pod_controls("podracer", 1.0, 1.0, 0.9) == (1.0, 0.0)

def test_pod_controls_podracer_ease_off_right_turns_right():
    assert pod_controls("podracer", 1.0, 0.5, 0.0) == (1.0, 0.5)

def test_pod_controls_podracer_ignores_right_stick_x():
    assert pod_controls("podracer", 0.0, 0.0, -1.0) == (0.0, 0.0)


BINDINGS = {"left": {"5": "X"}, "right": {"3": "A", "5": "X"}}

def test_held_nothing_pressed():
    assert held_xbox_buttons(BINDINGS, set(), set()) == set()

def test_held_one_button():
    assert held_xbox_buttons(BINDINGS, set(), {3}) == {"A"}

def test_held_either_stick_holds_shared_button():
    assert held_xbox_buttons(BINDINGS, {5}, set()) == {"X"}
    assert held_xbox_buttons(BINDINGS, set(), {5}) == {"X"}

def test_held_unbound_button_does_nothing():
    assert held_xbox_buttons(BINDINGS, {3}, {29}) == set()


def test_pod_pitch_passes_through():
    assert pod_pitch(0.6, False) == 0.6

def test_pod_pitch_inverted():
    assert pod_pitch(0.6, True) == -0.6


def test_pitch_clash_free_axis():
    assert pitch_clash("right_stick", "right", 1, 1, 0) == ""

def test_pitch_clash_right_stick_steering():
    assert pitch_clash("right_stick", "right", 0, 1, 0) == "steering"

def test_pitch_clash_right_stick_gas_and_brake():
    assert pitch_clash("right_stick", "left", 1, 1, 0) == "gas and brake"

def test_pitch_clash_podracer_thrust_on_either_stick():
    assert pitch_clash("podracer", "right", 1, 1, 0) == "thrust"
    assert pitch_clash("podracer", "left", 1, 1, 0) == "thrust"

def test_pitch_clash_podracer_right_x_is_free():
    assert pitch_clash("podracer", "right", 0, 1, 0) == ""

def test_pitch_clash_off_never_clashes():
    assert pitch_clash("podracer", "off", 1, 1, 0) == ""
