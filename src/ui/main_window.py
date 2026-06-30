import customtkinter as ctk
from ui.loader_panel import LoaderPanel
from ui.trim_panel import TrimPanel
from ui.detection_panel import DetectionPanel
from ui.export_panel import ExportPanel


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Cutter")
        self.geometry("900x720")
        self.resizable(False, False)

        self._video_path: str | None = None

        self._build_layout()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._loader = LoaderPanel(self, on_loaded=self._on_video_loaded)
        self._loader.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="ew")

        self._trim = TrimPanel(self)
        self._trim.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="nsew")

        self._detection = DetectionPanel(self)
        self._detection.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="ew")

        self._export = ExportPanel(
            self,
            get_trim=self._trim.get_trim_values,
            get_detection=self._detection.get_settings,
        )
        self._export.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")

    def _on_video_loaded(self, path: str):
        self._video_path = path
        self._trim.set_video(path)
        self._export.set_source(path)
