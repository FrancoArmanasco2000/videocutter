import threading
from tkinter import filedialog
from typing import Callable
import customtkinter as ctk
from services.downloader import Downloader
from utils.notify import notify
from ui.theme import (
    BG_PANEL, BG_INSET, BORDER, ACCENT, ACCENT_HOVER,
    NEUTRAL, NEUTRAL_HOVER, TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, RADIUS,
)


class LoaderPanel(ctk.CTkFrame):
    def __init__(self, master, on_loaded: Callable[[str], None]):
        super().__init__(master, fg_color=BG_PANEL, border_color=BORDER,
                         border_width=1, corner_radius=RADIUS)
        self._on_loaded = on_loaded
        self._downloader = Downloader()
        self._current_source: str | None = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="SOURCE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).grid(row=0, column=0, columnspan=4, padx=14, pady=(10, 4), sticky="w")

        ctk.CTkLabel(
            self, text="URL / File",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, padx=(14, 10), pady=(0, 12))

        self._url_entry = ctk.CTkEntry(
            self,
            placeholder_text="Paste a video URL or browse for an MP4 file…",
            fg_color=BG_INSET,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_DIM,
            height=34,
        )
        self._url_entry.grid(row=1, column=1, padx=0, pady=(0, 12), sticky="ew")

        ctk.CTkButton(
            self, text="Browse", width=86, height=34,
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=TEXT_PRIMARY,
            border_color=BORDER, border_width=1,
            command=self._browse,
        ).grid(row=1, column=2, padx=(8, 6), pady=(0, 12))

        ctk.CTkButton(
            self, text="Load", width=86, height=34,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#ffffff", font=ctk.CTkFont(weight="bold"),
            command=self._load,
        ).grid(row=1, column=3, padx=(0, 14), pady=(0, 12))

        self._status = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        )
        self._status.grid(row=2, column=0, columnspan=4, padx=14, pady=(0, 8), sticky="w")

    def _browse(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.mov *.mkv *.avi *.webm"), ("All files", "*.*")]
        )
        if path:
            self._url_entry.delete(0, "end")
            self._url_entry.insert(0, path)

    def _load(self):
        source = self._url_entry.get().strip()
        if not source:
            self._set_status("Enter a URL or select a file.", error=True)
            return
        if source.startswith(("http://", "https://")):
            self._set_status("Downloading…")
            threading.Thread(target=self._download, args=(source,), daemon=True).start()
        else:
            self._current_source = source
            self._on_loaded(source)
            self._set_status("File loaded.")

    def _download(self, url: str):
        try:
            path = self._downloader.download(url, on_progress=self._on_progress)
            self._current_source = path
            self.after(0, lambda: self._on_loaded(path))
            self.after(0, lambda: self._set_status("Download complete."))
            notify("Video Cutter", "Download complete.")
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._set_status(f"Error: {msg}", error=True))

    def get_source(self) -> str | None:
        return self._current_source

    def load_path(self, path: str):
        """Loads a source directly (used by Load Project) — skips URL/download logic."""
        self._url_entry.delete(0, "end")
        self._url_entry.insert(0, path)
        self._current_source = path
        self._on_loaded(path)
        self._set_status("File loaded.")

    def _on_progress(self, percent: float):
        self.after(0, lambda: self._set_status(f"Downloading…  {percent:.0f}%"))

    def _set_status(self, msg: str, error: bool = False):
        self._status.configure(text=msg, text_color="#ef4444" if error else TEXT_MUTED)
