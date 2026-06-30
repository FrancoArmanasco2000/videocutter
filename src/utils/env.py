import os
import sys


def setup():
    """Add bundled binaries (ffmpeg) to PATH when running as a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        bundle_dir = sys._MEIPASS
        os.environ["PATH"] = bundle_dir + os.pathsep + os.environ.get("PATH", "")
