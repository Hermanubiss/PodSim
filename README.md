# PodSim

Two flight sticks in, one virtual Xbox 360 pad out, for Star Wars Galactic Racer.

## Use it
1. Run `PodSim.exe` (from a release, or `dist\PodSim` after building).
2. Home tab: if the ViGEmBus driver is missing, click **Install driver**.
3. Plug in your sticks, set the bindings on the stick tabs, click **Start**.

Settings live in `%APPDATA%\PodSim`.

## Run from source
    pip install pyside6 pygame-ce vgamepad
    python podsim\gui.py

## Build the exe
    pip install pyinstaller pillow
    python make_assets.py
    pyinstaller podsim.spec --noconfirm
