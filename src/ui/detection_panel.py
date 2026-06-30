import customtkinter as ctk


class DetectionPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self._build()

    def _build(self):
        self.grid_columnconfigure((1, 2, 3), weight=1)

        # Enable toggle
        self._enabled = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            self, text="Object Detection (AI)",
            variable=self._enabled,
            command=self._on_toggle,
        ).grid(row=0, column=0, padx=10, pady=(10, 4), sticky="w")

        # Class checkboxes
        self._person = ctk.BooleanVar(value=True)
        self._ball = ctk.BooleanVar(value=True)

        self._cb_person = ctk.CTkCheckBox(self, text="Person / Player", variable=self._person)
        self._cb_person.grid(row=0, column=1, padx=6, pady=(10, 4))

        self._cb_ball = ctk.CTkCheckBox(self, text="Ball", variable=self._ball)
        self._cb_ball.grid(row=0, column=2, padx=6, pady=(10, 4))

        # Confidence slider
        self._confidence = ctk.DoubleVar(value=0.4)
        ctk.CTkLabel(self, text="Confidence:").grid(row=0, column=3, padx=(10, 2), pady=(10, 4))
        self._slider = ctk.CTkSlider(
            self, from_=0.1, to=0.9, variable=self._confidence,
            command=lambda v: self._conf_label.configure(text=f"{v:.0%}"),
        )
        self._slider.grid(row=0, column=4, padx=(0, 4), pady=(10, 4), sticky="ew")
        self._conf_label = ctk.CTkLabel(self, text="40%", width=36)
        self._conf_label.grid(row=0, column=5, padx=(0, 10), pady=(10, 4))

        self._note = ctk.CTkLabel(
            self,
            text="First run downloads the YOLO model (~6 MB).",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        )
        self._note.grid(row=1, column=0, columnspan=6, padx=10, pady=(0, 8), sticky="w")

        self._set_controls_state("disabled")

    def _on_toggle(self):
        state = "normal" if self._enabled.get() else "disabled"
        self._set_controls_state(state)

    def _set_controls_state(self, state: str):
        for widget in (self._cb_person, self._cb_ball, self._slider):
            widget.configure(state=state)

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
        }
