from config import add_missing, pitch_keys, clean_profile_name, list_profiles, load_settings, save_settings


def test_load_settings_reads_deadzone(tmp_path):
    file = tmp_path / "config.json"
    file.write_text('{"deadzone": 0.2}')
    assert load_settings(file)["deadzone"] == 0.2


def test_load_settings_reads_stick_name(tmp_path):
    file = tmp_path / "config.json"
    file.write_text('{"left_stick": "L"}')
    assert load_settings(file)["left_stick"] == "L"

def test_save_then_load_gives_the_same_settings(tmp_path):
    file = tmp_path / "config.json"
    settings = {"deadzone": 0.1, "buttons": {"left": {"5": "X"}, "right": {}}}
    save_settings(file, settings)
    assert load_settings(file) == settings


def test_clean_profile_name_removes_bad_characters():
    assert clean_profile_name("  My/Race: Setup? ") == "MyRace Setup"


def test_list_profiles_sorted_names(tmp_path):
    (tmp_path / "Zebra.json").write_text("{}")
    (tmp_path / "Arcade.json").write_text("{}")
    (tmp_path / "notes.txt").write_text("not a profile")
    assert list_profiles(tmp_path) == ["Arcade", "Zebra"]


def test_list_profiles_missing_folder(tmp_path):
    assert list_profiles(tmp_path / "nope") == []


def test_add_missing_fills_new_keys():
    settings = add_missing({"deadzone": 0.02})
    assert settings["pitch_stick"] == "right"
    assert settings["deadzone"] == 0.02

def test_add_missing_keeps_existing_values():
    settings = add_missing({"pitch_stick": "off"})
    assert settings["pitch_stick"] == "off"


def test_pitch_keys_per_mode():
    assert pitch_keys("right_stick") == ("pitch_stick", "pitch_axis")
    assert pitch_keys("podracer") == ("podracer_pitch_stick", "podracer_pitch_axis")
