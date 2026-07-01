import customtkinter as ctk
from typing import Callable
from ui.theme import (
    BG_PANEL, BG_INSET, BG_ROW, BG_ROW_ALT, BORDER,
    ACCENT, ACCENT_HOVER, NEUTRAL_HOVER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, RADIUS,
)


class TagsPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        get_current_time: Callable[[], float],
        on_seek: Callable[[float], None],
    ):
        super().__init__(master, fg_color=BG_PANEL, border_color=BORDER,
                         border_width=1, corner_radius=RADIUS)
        self._get_current_time = get_current_time
        self._on_seek = on_seek
        self._tags: list[dict] = []  # {"time": float, "label": str}
        self._rows: list[ctk.CTkFrame] = []
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="TAGS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).grid(row=0, column=0, padx=14, pady=(10, 6), sticky="w")

        entry_row = ctk.CTkFrame(self, fg_color="transparent")
        entry_row.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        entry_row.grid_columnconfigure(0, weight=1)

        self._label_entry = ctk.CTkEntry(
            entry_row, placeholder_text="Gol, Falta, Jugada clave…",
            fg_color=BG_INSET, border_color=BORDER,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_DIM,
            height=32,
        )
        self._label_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._label_entry.bind("<Return>", lambda e: self._add_tag())

        ctk.CTkButton(
            entry_row, text="+ Tag at current time", width=170, height=32,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._add_tag,
        ).grid(row=0, column=1)

        self._list = ctk.CTkScrollableFrame(
            self, height=90,
            fg_color=BG_INSET,
            border_color=BORDER, border_width=0,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACCENT,
        )
        self._list.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        self._list.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self._list,
            text="No tags yet. Mark moments while you watch — goals, fouls, key plays.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
        )
        self._empty_label.grid(row=0, column=0, pady=16)

    # ── public ──────────────────────────────────────────────────────────────

    def get_tags(self) -> list[dict]:
        return list(self._tags)

    def set_tags(self, tags: list[dict]):
        self._tags = sorted(tags, key=lambda t: t["time"])
        self._refresh()

    # ── internal ────────────────────────────────────────────────────────────

    def _add_tag(self):
        label = self._label_entry.get().strip() or "Tag"
        time = self._get_current_time()
        self._tags.append({"time": time, "label": label})
        self._tags.sort(key=lambda t: t["time"])
        self._label_entry.delete(0, "end")
        self._refresh()

    def _remove(self, index: int):
        self._tags.pop(index)
        self._refresh()

    def _refresh(self):
        for row in self._rows:
            row.destroy()
        self._rows.clear()

        if not self._tags:
            self._empty_label.grid()
            return

        self._empty_label.grid_remove()

        for i, tag in enumerate(self._tags):
            bg = BG_ROW if i % 2 == 0 else BG_ROW_ALT
            row = self._make_row(i, tag, bg)
            row.grid(row=i, column=0, sticky="ew", pady=1)
            self._rows.append(row)

    def _make_row(self, idx: int, tag: dict, bg: str) -> ctk.CTkFrame:
        row = ctk.CTkFrame(self._list, fg_color=bg, corner_radius=4)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            row, text=self._fmt(tag["time"]), width=64, height=26,
            fg_color="transparent", hover_color=NEUTRAL_HOVER,
            text_color=ACCENT, font=ctk.CTkFont(family="Courier", size=12, weight="bold"),
            command=lambda t=tag["time"]: self._on_seek(t),
        ).grid(row=0, column=0, padx=(6, 4), pady=6)

        ctk.CTkLabel(
            row, text=tag["label"],
            font=ctk.CTkFont(size=13),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=1, padx=4, pady=6, sticky="w")

        ctk.CTkButton(
            row, text="✕", width=32, height=26,
            fg_color="transparent", hover_color="#3a1a1a",
            text_color=TEXT_DIM, font=ctk.CTkFont(size=13),
            command=lambda i=idx: self._remove(i),
        ).grid(row=0, column=2, padx=(0, 6), pady=6)

        return row

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f"{s // 60:02d}:{s % 60:02d}"
