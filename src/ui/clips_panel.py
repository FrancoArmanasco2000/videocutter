import customtkinter as ctk
from typing import Callable
from ui.theme import (
    BG_PANEL, BG_INSET, BG_ROW, BG_ROW_ALT, BORDER,
    ACCENT, ACCENT_HOVER, NEUTRAL, NEUTRAL_HOVER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, RADIUS,
)


class ClipsPanel(ctk.CTkFrame):
    def __init__(self, master, get_current_trim: Callable[[], tuple[float, float]]):
        super().__init__(master, fg_color=BG_PANEL, border_color=BORDER,
                         border_width=1, corner_radius=RADIUS)
        self._get_current_trim = get_current_trim
        self._clips: list[tuple[float, float]] = []
        self._rows: list[ctk.CTkFrame] = []
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 6))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="CLIPS QUEUE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header, text="+ Add to queue", width=130, height=30,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._add_clip,
        ).grid(row=0, column=1)

        # Column headers
        cols = ctk.CTkFrame(self, fg_color=BG_INSET, corner_radius=0)
        cols.grid(row=1, column=0, sticky="ew", padx=14)
        cols.grid_columnconfigure(1, weight=1)

        for col, text, w in [
            (0, "#",        32),
            (1, "SEGMENT",   0),
            (2, "DURATION", 80),
            (3, "",         36),
        ]:
            ctk.CTkLabel(
                cols, text=text, width=w,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=TEXT_DIM,
            ).grid(row=0, column=col, padx=(10 if col == 0 else 4, 4), pady=4,
                   sticky="w" if col == 1 else "")

        # Scrollable list
        self._list = ctk.CTkScrollableFrame(
            self, height=110,
            fg_color=BG_INSET,
            border_color=BORDER, border_width=0,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACCENT,
        )
        self._list.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        self._list.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self._list,
            text="No clips yet.  Set start / end then click  + Add to queue",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
        )
        self._empty_label.grid(row=0, column=0, pady=20)

    # ── public ──────────────────────────────────────────────────────────────

    def get_clips(self) -> list[tuple[float, float]]:
        return list(self._clips)

    def set_clips(self, clips: list[tuple[float, float]]):
        self._clips = list(clips)
        self._refresh()

    # ── internal ────────────────────────────────────────────────────────────

    def _add_clip(self):
        start, end = self._get_current_trim()
        if end <= start:
            return
        self._clips.append((start, end))
        self._refresh()

    def _remove(self, index: int):
        self._clips.pop(index)
        self._refresh()

    def _refresh(self):
        for row in self._rows:
            row.destroy()
        self._rows.clear()

        if not self._clips:
            self._empty_label.grid()
            return

        self._empty_label.grid_remove()

        for i, (start, end) in enumerate(self._clips):
            bg = BG_ROW if i % 2 == 0 else BG_ROW_ALT
            row = self._make_row(i, start, end, bg)
            row.grid(row=i, column=0, sticky="ew", pady=1)
            self._rows.append(row)

    def _make_row(self, idx: int, start: float, end: float, bg: str) -> ctk.CTkFrame:
        duration = end - start
        row = ctk.CTkFrame(self._list, fg_color=bg, corner_radius=4)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row, text=f"{idx + 1:02d}", width=32,
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"),
            text_color=ACCENT,
        ).grid(row=0, column=0, padx=(10, 4), pady=8)

        ctk.CTkLabel(
            row,
            text=f"{self._fmt(start)}  →  {self._fmt(end)}",
            font=ctk.CTkFont(family="Courier", size=13),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=1, padx=4, pady=8, sticky="w")

        ctk.CTkLabel(
            row,
            text=self._fmt(duration),
            font=ctk.CTkFont(family="Courier", size=12),
            text_color=TEXT_MUTED, width=80,
        ).grid(row=0, column=2, padx=4, pady=8)

        ctk.CTkButton(
            row, text="✕", width=32, height=26,
            fg_color="transparent", hover_color="#3a1a1a",
            text_color=TEXT_DIM, font=ctk.CTkFont(size=13),
            command=lambda i=idx: self._remove(i),
        ).grid(row=0, column=3, padx=(0, 6), pady=8)

        return row

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f"{s // 60:02d}:{s % 60:02d}"
