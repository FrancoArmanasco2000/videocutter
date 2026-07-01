import os
import sys


def setup():
    """Add bundled binaries (ffmpeg) to PATH when running as a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        bin_dir = os.path.join(sys._MEIPASS, "bin")
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
