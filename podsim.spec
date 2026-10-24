# PyInstaller recipe for PodSim.exe. Build with:  pyinstaller podsim.spec --noconfirm
from PyInstaller.utils.hooks import collect_dynamic_libs

a = Analysis(
    ["podsim/gui.py"],
    pathex=["podsim"],
    binaries=collect_dynamic_libs("vgamepad"),
    datas=[
        ("Devices/EVO.jpg", "Devices"),
        ("Devices/EVO_OMNI.jpg", "Devices"),
        ("media/icon.ico", "media"),
        ("default_config.json", "."),
        # The ViGEmBus driver installer (binder.vigem_installer() finds it).
        ("drivers/ViGEmBus_1.22.0_x64_x86_arm64.exe", "drivers"),
    ],
    hiddenimports=["vgamepad"],  # binder imports it inside start(), not at the top
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
