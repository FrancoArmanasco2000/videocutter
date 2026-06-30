import customtkinter as ctk
from ui.theme import (
    BG_PANEL, BORDER, ACCENT, ACCENT_HOVER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, RADIUS,
)


class DetectionPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_PANEL, border_color=BORDER,
                         border_width=1, corner_radius=RADIUS)
        self._build()

    def _build(self):
        self.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(
            self, text="AI ANALYSIS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).grid(row=0, column=0, columnspan=7, padx=14, pady=(10, 6), sticky="w")

        # Enable switch
        self._enabled = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            self,
            text="Object Detection",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_PRIMARY,
            variable=self._enabled,
            progress_color=ACCENT,
            button_color=TEXT_MUTED,
            command=self._on_toggle,
        ).grid(row=1, column=0, padx=(14, 20), pady=(0, 12), sticky="w")

        # Checkboxes
        self._person = ctk.BooleanVar(value=True)
        self._ball = ctk.BooleanVar(value=True)
        self._tracking = ctk.BooleanVar(value=False)

        checkbox_style = dict(
            font=ctk.CTkFont(size=12),
            text_color=TEXT_PRIMARY,
            checkmark_color="#ffffff",
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            border_color=BORDER,
        )

        self._cb_person = ctk.CTkCheckBox(self, text="Player", variable=self._person, **checkbox_style)
        self._cb_person.grid(row=1, column=1, padx=(0, 16), pady=(0, 12))

        self._cb_ball = ctk.CTkCheckBox(self, text="Ball", variable=self._ball, **checkbox_style)
        self._cb_ball.grid(row=1, column=2, padx=(0, 16), pady=(0, 12))

        self._cb_tracking = ctk.CTkCheckBox(
            self, text="Track IDs", variable=self._tracking, **checkbox_style,
        )
        self._cb_tracking.grid(row=1, column=3, padx=(0, 24), pady=(0, 12))

        # Confidence
        ctk.CTkLabel(
            self, text="Confidence",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED,
        ).grid(row=1, column=4, padx=(0, 8), pady=(0, 12), sticky="e")

        self._confidence = ctk.DoubleVar(value=0.4)
        self._conf_label = ctk.CTkLabel(
            self, text="40%",
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"),
            text_color=TEXT_PRIMARY, width=40,
        )
        self._conf_label.grid(row=1, column=6, padx=(4, 14), pady=(0, 12))

        self._slider = ctk.CTkSlider(
            self, from_=0.1, to=0.9,
            variable=self._confidence,
            button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            progress_color=ACCENT, fg_color=BORDER,
            width=120,
            command=lambda v: self._conf_label.configure(text=f"{v:.0%}"),
        )
        self._slider.grid(row=1, column=5, padx=(0, 4), pady=(0, 12))

        self._note = ctk.CTkLabel(
            self,
            text="First run downloads the YOLO model (~6 MB).  "
                 "Track IDs assigns a persistent number to each detected player.",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM,
        )
        self._note.grid(row=2, column=0, columnspan=7, padx=14, pady=(0, 10), sticky="w")

        self._set_state("disabled")

    def _on_toggle(self):
        self._set_state("normal" if self._enabled.get() else "disabled")

    def _set_state(self, state: str):
        for w in (self._cb_person, self._cb_ball, self._cb_tracking, self._slider):
            w.configure(state=state)

    def get_settings(self) -> dict | None:
        if not self._enabled.get():
            return None
        classes = []
        if self._person.get():
            classes.append(0)
        if self._ball.get():
            classes.append(32)
        if not classes:
            return None
        return {
            "classes": classes,
            "confidence": self._confidence.get(),
            "tracking": self._tracking.get(),
        }
