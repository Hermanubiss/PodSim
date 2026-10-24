# PyInstaller recipe for PodSim.exe. Build with:  pyinstaller podsim.spec --noconfirm
from PyInstaller.utils.hooks import collect_dynamic_libs, get_package_paths

# The ViGEmBus driver installer that comes with vgamepad. It goes into the exe
# at the same place inside vgamepad, so binder.vigem_installer() finds it.
VIGEM_INSTALL = "win/vigem/install/x64"
vgamepad_folder = get_package_paths("vgamepad")[1]

a = Analysis(
    ["podsim/gui.py"],
    pathex=["podsim"],
    binaries=collect_dynamic_libs("vgamepad"),
    datas=[
        ("Devices/EVO.jpg", "Devices"),
        ("Devices/EVO_OMNI.jpg", "Devices"),
        ("media/icon.ico", "media"),
        ("default_config.json", "."),
        (f"{vgamepad_folder}/{VIGEM_INSTALL}/ViGEmBusSetup_x64.msi", f"vgamepad/{VIGEM_INSTALL}"),
    ],
)
splash = Splash(
    "media/splash.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(82, 498),
    text_size=10,
    text_color="#c9a9a3",
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, splash, [],
    exclude_binaries=True,
    name="PodSim",
    icon="media/icon.ico",
    console=False,
)
coll = COLLECT(exe, a.binaries, a.datas, splash.binaries, name="PodSim")
