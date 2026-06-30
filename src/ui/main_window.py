import customtkinter as ctk
from ui.theme import BG_ROOT, BG_PANEL, BORDER, ACCENT, TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, RADIUS
from ui.loader_panel import LoaderPanel
from ui.video_player import VideoPlayer
from ui.trim_panel import TrimPanel
from ui.clips_panel import ClipsPanel
from ui.detection_panel import DetectionPanel
from ui.export_panel import ExportPanel


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Cutter  —  Sports Analysis")
        self.geometry("920x1040")
        self.resizable(False, False)
        self.configure(fg_color=BG_ROOT)

        self._build_header()
        self._build_layout()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, height=48)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="▶  VIDEO CUTTER",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=20)

        ctk.CTkLabel(
            header,
            text="Sports Analysis Edition",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(0, 0))

    def _build_layout(self):
        body = ctk.CTkFrame(self, fg_color=BG_ROOT)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=1)

        self._loader = LoaderPanel(body, on_loaded=self._on_video_loaded)
        self._loader.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._player = VideoPlayer(
            body,
            on_set_start=self._on_player_set_start,
            on_set_end=self._on_player_set_end,
        )
        self._player.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self._trim = TrimPanel(body)
        self._trim.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self._clips = ClipsPanel(body, get_current_trim=self._trim.get_trim_values)
        self._clips.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        self._detection = DetectionPanel(body)
        self._detection.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self._export = ExportPanel(
            body,
            get_trim=self._trim.get_trim_values,
            get_clips=self._clips.get_clips,
            get_detection=self._detection.get_settings,
        )
        self._export.grid(row=5, column=0, sticky="ew")

    def _on_video_loaded(self, path: str):
        self._player.load(path)
        self._trim.set_video(path)
        self._export.set_source(path)

    def _on_player_set_start(self, seconds: float):
        self._trim.set_start(seconds)

    def _on_player_set_end(self, seconds: float):
        self._trim.set_end(seconds)
