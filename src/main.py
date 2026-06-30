import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.env import setup
setup()

import customtkinter as ctk
from ui.main_window import MainWindow


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
