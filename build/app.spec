import os
import sys
import shutil
import platform
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

# ── ffmpeg binary ────────────────────────────────────────────────────────────
ffmpeg_bin = shutil.which("ffmpeg")
if not ffmpeg_bin:
    raise RuntimeError(
        "ffmpeg not found in PATH.\n"
        "  Mac:     brew install ffmpeg\n"
        "  Windows: winget install ffmpeg"
    )

# ── data files ───────────────────────────────────────────────────────────────
datas = []
datas += collect_data_files("customtkinter")
datas += collect_data_files("ultralytics")

# ── hidden imports ───────────────────────────────────────────────────────────
hiddenimports = [
    "cv2",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "yt_dlp",
    "ffmpeg",
    "tkinter",
    "tkinter.filedialog",
    "lap",
]
hiddenimports += collect_submodules("ultralytics")
hiddenimports += collect_submodules("lap")
hiddenimports += collect_submodules("yt_dlp")

block_cipher = None

a = Analysis(
    ["../src/main.py"],
    pathex=["../src"],
    binaries=[(ffmpeg_bin, "bin")],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "notebook", "ipython"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VideoCutter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="VideoCutter",
)

if IS_MAC:
    app = BUNDLE(
        coll,
        name="VideoCutter.app",
        icon=None,
        bundle_identifier="com.videocutter.sports",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.1.0",
            "CFBundleName": "Video Cutter",
            "CFBundleDisplayName": "Video Cutter",
            "NSRequiresAquaSystemAppearance": False,
        },
    )
