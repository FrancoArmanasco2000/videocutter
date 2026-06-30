import customtkinter as ctk
from ui.theme import (
    BG_PANEL, BG_INSET, BORDER, ACCENT, TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, RADIUS,
)


class TrimPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_PANEL, border_color=BORDER,
                         border_width=1, corner_radius=RADIUS)
        self._duration: float = 0.0
        self._build()

    def _build(self):
        self.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(
            self, text="TRIM",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).grid(row=0, column=0, columnspan=5, padx=14, pady=(10, 4), sticky="w")

        ctk.CTkLabel(
            self, text="Start (s)",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
        ).grid(row=1, column=0, padx=(14, 8), pady=(0, 12))

        self._start_entry = ctk.CTkEntry(
            self, placeholder_text="0.00",
            fg_color=BG_INSET, border_color=BORDER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Courier", size=13),
            height=34,
        )
        self._start_entry.grid(row=1, column=1, padx=(0, 20), pady=(0, 12), sticky="ew")

        ctk.CTkLabel(
            self, text="End (s)",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
        ).grid(row=1, column=2, padx=(0, 8), pady=(0, 12))

        self._end_entry = ctk.CTkEntry(
            self, placeholder_text="0.00",
            fg_color=BG_INSET, border_color=BORDER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Courier", size=13),
            height=34,
        )
        self._end_entry.grid(row=1, column=3, padx=(0, 0), pady=(0, 12), sticky="ew")

        self._info = ctk.CTkLabel(
            self, text="Load a video to set trim points.",
            font=ctk.CTkFont(size=11), text_color=TEXT_DIM,
        )
        self._info.grid(row=1, column=4, padx=(16, 14), pady=(0, 12), sticky="w")

    # ── public ──────────────────────────────────────────────────────────────

    def set_video(self, path: str):
        try:
            import ffmpeg
            probe = ffmpeg.probe(path)
            duration = float(probe["format"]["duration"])
            self._duration = duration
            self._end_entry.delete(0, "end")
            self._end_entry.insert(0, f"{duration:.2f}")
            self._info.configure(
                text=f"Duration  {self._fmt(duration)}",
                text_color=TEXT_MUTED,
            )
        except Exception as e:
            self._info.configure(text=f"Could not read duration: {e}", text_color="#ef4444")

    def set_start(self, seconds: float):
        self._start_entry.delete(0, "end")
        self._start_entry.insert(0, f"{seconds:.2f}")

    def set_end(self, seconds: float):
        self._end_entry.delete(0, "end")
        self._end_entry.insert(0, f"{seconds:.2f}")

    def get_trim_values(self) -> tuple[float, float]:
        start = float(self._start_entry.get() or 0)
        end = float(self._end_entry.get() or self._duration)
        return start, end

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f"{s // 60:02d}:{s % 60:02d}"
