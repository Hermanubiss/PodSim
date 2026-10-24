# Where PodSim's files live, both as a .py and as a built PodSim.exe.
import os
import shutil
import sys
from pathlib import Path

VERSION = "0.1.0"

# True when running as PodSim.exe (PyInstaller sets sys.frozen).
FROZEN = getattr(sys, "frozen", False)


def resource_dir():
    # Read-only files that ship with the app: pictures, icon, default config.
    if FROZEN:
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent  # the project folder


def user_dir():
    # Files the user changes: config.json and profiles/.
    if FROZEN:
        return Path(os.environ["APPDATA"]) / "PodSim"
    return Path(__file__).parent  # the podsim folder, like before


def first_run():
    # Built app, first start on this PC: copy the default settings in.
    folder = user_dir()
    folder.mkdir(parents=True, exist_ok=True)
    config = folder / "config.json"
    if not config.exists():
        shutil.copy(resource_dir() / "default_config.json", config)
