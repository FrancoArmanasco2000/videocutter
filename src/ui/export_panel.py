import os
import threading
from tkinter import filedialog
from typing import Callable
import customtkinter as ctk
from services.annotator import burn_clip
from services.cutter import Cutter
from services.detector import Detector
from utils.notify import notify
from ui.theme import (
    BG_PANEL, BORDER, ACCENT, ACCENT_HOVER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, RADIUS,
)


class ExportPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        get_trim: Callable[[], tuple[float, float]],
        get_clips: Callable[[], list[tuple[float, float]]],
        get_detection: Callable[[], dict | None],
        get_drawings: Callable[[], list[dict]],
    ):
        super().__init__(master, fg_color=BG_PANEL, border_color=BORDER,
                         border_width=1, corner_radius=RADIUS)
        self._get_trim = get_trim
        self._get_clips = get_clips
        self._get_detection = get_detection
        self._get_drawings = get_drawings
        self._source: str | None = None
        self._cutter = Cutter()
        self._detector = Detector()
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="EXPORT",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).grid(row=0, column=0, columnspan=2, padx=14, pady=(10, 6), sticky="w")

        self._progress = ctk.CTkProgressBar(
            self,
            progress_color=ACCENT, fg_color=BORDER,
            height=6, corner_radius=3,
        )
        self._progress.set(0)
        self._progress.grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 8), sticky="ew")
        self._progress.grid_remove()

        self._status = ctk.CTkLabel(
            self, text="Ready to export.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
        )
        self._status.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")

        ctk.CTkButton(
            self, text="EXPORT  ▶", width=130, height=38,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._export,
        ).grid(row=2, column=1, padx=(0, 14), pady=(0, 12))

    def set_source(self, path: str):
        self._source = path
        self._set_status("Video loaded. Configure trim and export.")

    # ── export entry point ─────────────────────────────────────────────────

    def _export(self):
        if not self._source:
            self._set_status("No video loaded.", error=True)
            return

        clips = self._get_clips()
        detection = self._get_detection()
        drawings = self._get_drawings()

        if clips:
            self._start_multi(clips, detection, drawings)
        else:
            self._start_single(detection, drawings)

    # ── single ─────────────────────────────────────────────────────────────

    def _start_single(self, detection: dict | None, drawings: list[dict]):
        out = filedialog.asksaveasfilename(
            defaultextension=".mp4", filetypes=[("MP4 video", "*.mp4")]
        )
        if not out:
            return
        start, end = self._get_trim()
        self._reset_progress()
        target = self._pick_worker(detection, drawings)
        threading.Thread(
            target=target, args=([(start, end)], [out], detection, drawings), daemon=True
        ).start()

    # ── multi ──────────────────────────────────────────────────────────────

    def _start_multi(self, clips: list[tuple[float, float]], detection: dict | None, drawings: list[dict]):
        base = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4")],
            title=f"Base filename for {len(clips)} clips",
        )
        if not base:
            return
        root, ext = os.path.splitext(base)
        paths = [f"{root}_{i + 1:02d}{ext}" for i in range(len(clips))]
        self._reset_progress()
        target = self._pick_worker(detection, drawings)
        threading.Thread(
            target=target, args=(clips, paths, detection, drawings), daemon=True
        ).start()

    def _pick_worker(self, detection: dict | None, drawings: list[dict]):
        if detection:
            return self._run_detection
        if drawings:
            return self._run_drawings_only
        return self._run_plain

    # ── workers ────────────────────────────────────────────────────────────

    def _run_plain(self, clips, paths, _detection, _drawings):
        total = len(clips)
        try:
            for i, ((start, end), path) in enumerate(zip(clips, paths)):
                self.after(0, lambda i=i: self._set_status(f"Exporting clip {i + 1} / {total}…"))
                self._cutter.cut(self._source, path, start, end)
                self.after(0, lambda i=i: self._progress.set((i + 1) / total))
            notify("Video Cutter", f"Export complete — {total} clip{'s' if total != 1 else ''} saved.")
            self.after(0, self._done)
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._set_status(f"Error: {msg}", error=True))
            self.after(0, self._stop_progress)

    def _run_drawings_only(self, clips, paths, _detection, drawings):
        total = len(clips)
        try:
            for i, ((start, end), path) in enumerate(zip(clips, paths)):
                label = f"Clip {i + 1}/{total}"

                def on_progress(pct: float, lbl=label, idx=i):
                    overall = (idx + pct / 100) / total
                    self.after(0, lambda: self._progress.set(overall))
                    self.after(0, lambda: self._set_status(f"{lbl}  ·  {pct:.0f}%"))

                burn_clip(self._source, path, start, end, drawings, on_progress=on_progress)
            notify("Video Cutter", f"Export complete — {total} clip{'s' if total != 1 else ''} saved.")
            self.after(0, self._done)
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._set_status(f"Error: {msg}", error=True))
            self.after(0, self._stop_progress)

    def _run_detection(self, clips, paths, detection, drawings):
        total = len(clips)
        possession_a = possession_b = 0
        fps = 0.0
        try:
            for i, ((start, end), path) in enumerate(zip(clips, paths)):
                label = f"Clip {i + 1}/{total}"

                def on_progress(pct: float, lbl=label, idx=i):
                    overall = (idx + pct / 100) / total
                    self.after(0, lambda: self._progress.set(overall))
                    self.after(0, lambda: self._set_status(f"{lbl}  ·  {pct:.0f}%"))

                result = self._detector.process_video(
                    source=self._source, dest=path,
                    start=start, end=end,
                    classes=detection["classes"],
                    confidence=detection["confidence"],
                    tracking=detection.get("tracking", False),
                    teams=detection.get("teams", False),
                    drawings=drawings,
                    on_progress=on_progress,
                )
                if result:
                    possession_a += result["a"]
                    possession_b += result["b"]
                    fps = result["fps"] or fps

            summary = f"Export complete — {total} clip{'s' if total != 1 else ''} saved."
            if fps and (possession_a + possession_b) > 0:
                pct_a = possession_a / (possession_a + possession_b) * 100
                summary += f"  Posesión — Team A {pct_a:.0f}% · Team B {100 - pct_a:.0f}%."
            notify("Video Cutter", summary)
            self.after(0, lambda: self._done(summary))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._set_status(f"Error: {msg}", error=True))
            self.after(0, self._stop_progress)

    # ── helpers ────────────────────────────────────────────────────────────

    def _reset_progress(self):
        self._progress.set(0)
        self._progress.grid()

    def _done(self, message: str = "Export complete."):
        self._progress.set(1)
        self._stop_progress()
        self._set_status(message)

    def _stop_progress(self):
        self._progress.grid_remove()

    def _set_status(self, msg: str, error: bool = False):
        self._status.configure(text=msg, text_color="#ef4444" if error else TEXT_MUTED)
