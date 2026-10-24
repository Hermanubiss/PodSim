import json


def load_settings(path):
    # Read a JSON file and hand back its contents as a dictionary.
    text = path.read_text()
    return json.loads(text)


def save_settings(path, settings):
    # Write the dictionary back to the JSON file, 4-space indented so it
    # stays easy to read and edit by hand.
    text = json.dumps(settings, indent=4)
    path.write_text(text + "\n")


# --- Profiles ------------------------------------------------------------------
# A profile is a full copy of the settings, saved as profiles/<name>.json.

BAD_NAME_CHARACTERS = r'\/:*?"<>|'  # Windows doesn't allow these in file names


def clean_profile_name(name):
    # "  My/Profile? " -> "MyProfile": safe to use as a file name.
    cleaned = ""
    for character in name:
        if character not in BAD_NAME_CHARACTERS:
            cleaned += character
    return cleaned.strip()


def list_profiles(folder):
    # The names of all saved profiles, A to Z (file names without ".json").
    if not folder.exists():
        return []
    return sorted(path.stem for path in folder.glob("*.json"))


# --- Settings added after v0.1.0 -------------------------------------------------
# Older config.json and profile files don't have these keys yet, so
# add_missing() fills them in right after a file is loaded.

DEFAULTS = {
    "pitch_stick": "right",  # which stick tilts the nose: "right", "left" or "off"
    "pitch_axis": 1,  # its forward/back axis
    # Podracer mode uses both forward/back axes as engines, so it has its own
    # pitch axis. 0 = right stick left/right: free in that mode.
    "podracer_pitch_stick": "right",
    "podracer_pitch_axis": 0,
    "pitch_invert": False,  # True = swap nose up and nose down
}


def pitch_keys(mode):
    # The settings keys holding the pitch stick and axis for a steering mode.
    if mode == "podracer":
        return ("podracer_pitch_stick", "podracer_pitch_axis")
    return ("pitch_stick", "pitch_axis")


def add_missing(settings):
    # Give `settings` every key from DEFAULTS it doesn't have yet.
    # Keys it already has are left alone.
    for key, value in DEFAULTS.items():
        if key not in settings:
            settings[key] = value
    return settings
