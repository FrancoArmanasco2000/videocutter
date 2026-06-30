import threading
from tkinter import filedialog
from typing import Callable
import customtkinter as ctk
from services.downloader import Downloader


class LoaderPanel(ctk.CTkFrame):
    def __init__(self, master, on_loaded: Callable[[str], None]):
        super().__init__(master)
        self._on_loaded = on_loaded
        self._downloader = Downloader()
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Video source:").grid(row=0, column=0, padx=(10, 6), pady=12)

        self._url_entry = ctk.CTkEntry(self, placeholder_text="Paste URL or leave empty to pick a file…")
        self._url_entry.grid(row=0, column=1, padx=0, pady=12, sticky="ew")

        ctk.CTkButton(self, text="Browse", width=80, command=self._browse).grid(
            row=0, column=2, padx=(6, 6), pady=12
        )
        ctk.CTkButton(self, text="Load", width=80, command=self._load).grid(
            row=0, column=3, padx=(0, 10), pady=12
        )

        self._status = ctk.CTkLabel(self, text="", text_color="gray")
        self._status.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 8))

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

        if source.startswith("http://") or source.startswith("https://"):
            self._set_status("Downloading…")
            threading.Thread(target=self._download, args=(source,), daemon=True).start()
        else:
            self._on_loaded(source)
            self._set_status("File loaded.")

    def _download(self, url: str):
        try:
            path = self._downloader.download(url, on_progress=self._on_progress)
            self.after(0, lambda: self._on_loaded(path))
            self.after(0, lambda: self._set_status("Download complete."))
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Error: {e}", error=True))

    def _on_progress(self, percent: float):
        self.after(0, lambda: self._set_status(f"Downloading… {percent:.0f}%"))

    def _set_status(self, msg: str, error: bool = False):
        self._status.configure(text=msg, text_color="red" if error else "gray")
