import threading
from tkinter import filedialog
from typing import Callable
import customtkinter as ctk
from services.cutter import Cutter
from services.detector import Detector


class ExportPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        get_trim: Callable[[], tuple[float, float]],
        get_detection: Callable[[], dict | None],
    ):
        super().__init__(master)
        self._get_trim = get_trim
        self._get_detection = get_detection
        self._source: str | None = None
        self._cutter = Cutter()
        self._detector = Detector()
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        self._progress = ctk.CTkProgressBar(self, mode="determinate")
        self._progress.set(0)
        self._progress.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 6), sticky="ew")
        self._progress.grid_remove()

        self._status = ctk.CTkLabel(self, text="", text_color="gray")
        self._status.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="w")

        ctk.CTkButton(self, text="Export clip", command=self._export).grid(
            row=1, column=1, padx=(0, 10), pady=(0, 6)
        )

    def set_source(self, path: str):
        self._source = path

    def _export(self):
        if not self._source:
            self._set_status("No video loaded.", error=True)
            return

        out_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4")],
        )
        if not out_path:
            return

        start, end = self._get_trim()
        detection = self._get_detection()

        self._progress.set(0)
        self._progress.grid()
        self._set_status("Exporting…")

        if detection:
            threading.Thread(
                target=self._run_detection_export,
                args=(self._source, out_path, start, end, detection),
                daemon=True,
            ).start()
        else:
            threading.Thread(
                target=self._run_plain_export,
                args=(self._source, out_path, start, end),
                daemon=True,
            ).start()

    def _run_plain_export(self, source: str, dest: str, start: float, end: float):
        try:
            self._cutter.cut(source, dest, start, end)
            self.after(0, lambda: self._progress.set(1))
            self.after(0, self._export_done)
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Error: {e}", error=True))
            self.after(0, self._stop_progress)

    def _run_detection_export(
        self, source: str, dest: str, start: float, end: float, detection: dict
    ):
        try:
            self._detector.process_video(
                source=source,
                dest=dest,
                start=start,
                end=end,
                classes=detection["classes"],
                confidence=detection["confidence"],
                on_progress=self._on_detection_progress,
            )
            self.after(0, self._export_done)
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Error: {e}", error=True))
            self.after(0, self._stop_progress)

    def _on_detection_progress(self, percent: float):
        self.after(0, lambda: self._progress.set(percent / 100))
        self.after(0, lambda: self._set_status(f"Detecting… {percent:.0f}%"))

    def _export_done(self):
        self._stop_progress()
        self._set_status("Export complete.")

    def _stop_progress(self):
        self._progress.grid_remove()

    def _set_status(self, msg: str, error: bool = False):
        self._status.configure(text=msg, text_color="red" if error else "gray")
