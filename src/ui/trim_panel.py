import customtkinter as ctk


class TrimPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self._duration: float = 0.0
        self._build()

    def _build(self):
        self.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(self, text="Start (s):").grid(row=0, column=0, padx=(10, 4), pady=16)
        self._start_entry = ctk.CTkEntry(self, placeholder_text="0")
        self._start_entry.grid(row=0, column=1, padx=(0, 16), pady=16, sticky="ew")

        ctk.CTkLabel(self, text="End (s):").grid(row=0, column=2, padx=(0, 4), pady=16)
        self._end_entry = ctk.CTkEntry(self, placeholder_text="0")
        self._end_entry.grid(row=0, column=3, padx=(0, 10), pady=16, sticky="ew")

        self._info = ctk.CTkLabel(self, text="Load a video to set trim points.", text_color="gray")
        self._info.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 10))

    def set_video(self, path: str):
        try:
            import ffmpeg
            probe = ffmpeg.probe(path)
            duration = float(probe["format"]["duration"])
            self._duration = duration
            self._end_entry.delete(0, "end")
            self._end_entry.insert(0, f"{duration:.2f}")
            self._info.configure(text=f"Duration: {duration:.2f}s  |  Set start and end in seconds.")
        except Exception as e:
            self._info.configure(text=f"Could not read duration: {e}", text_color="red")

    def get_trim_values(self) -> tuple[float, float]:
        start = float(self._start_entry.get() or 0)
        end = float(self._end_entry.get() or self._duration)
        return start, end
