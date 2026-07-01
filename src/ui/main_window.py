import json
import os
from tkinter import filedialog
import customtkinter as ctk
from ui.theme import (
    BG_ROOT, BG_PANEL, BORDER, ACCENT, ACCENT_HOVER,
    NEUTRAL, NEUTRAL_HOVER, TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, RADIUS,
)
from ui.loader_panel import LoaderPanel
from ui.video_player import VideoPlayer, PREVIEW_H
from ui.trim_panel import TrimPanel
from ui.clips_panel import ClipsPanel
from ui.tags_panel import TagsPanel
from ui.detection_panel import DetectionPanel
from ui.export_panel import ExportPanel


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Cutter  —  Sports Analysis")
        self.geometry("920x1040")
        self.minsize(920, 700)
        self.resizable(True, True)
        self.configure(fg_color=BG_ROOT)

        self._is_fullscreen = False
        self._normal_geometry: str | None = None

        self._build_header()
        self._build_layout()

        # Launching from a terminal often leaves keyboard focus on the
        # terminal itself — force it onto the app window.
        self.after(100, lambda: (self.lift(), self.focus_force()))

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

        ctk.CTkButton(
            header, text="Load Project", width=110, height=30,
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=TEXT_PRIMARY, border_color=BORDER, border_width=1,
            font=ctk.CTkFont(size=12),
            command=self._load_project,
        ).pack(side="right", padx=(0, 20))

        ctk.CTkButton(
            header, text="Save Project", width=110, height=30,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._save_project,
        ).pack(side="right", padx=(0, 8))

    def _build_layout(self):
        body = ctk.CTkScrollableFrame(self, fg_color=BG_ROOT)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=1)
        self._body = body

        self._loader = LoaderPanel(body, on_loaded=self._on_video_loaded)
        self._loader.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._player = VideoPlayer(
            body,
            on_set_start=self._on_player_set_start,
            on_set_end=self._on_player_set_end,
            on_fullscreen_toggle=self._on_fullscreen_toggle,
        )
        self._player.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self._trim = TrimPanel(body)
        self._trim.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self._clips = ClipsPanel(body, get_current_trim=self._trim.get_trim_values)
        self._clips.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        self._tags = TagsPanel(
            body,
            get_current_time=self._player.get_current_time,
            on_seek=self._player.seek_to_time,
        )
        self._tags.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self._detection = DetectionPanel(body)
        self._detection.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        self._export = ExportPanel(
            body,
            get_trim=self._trim.get_trim_values,
            get_clips=self._clips.get_clips,
            get_detection=self._detection.get_settings,
            get_drawings=self._player.get_drawings,
        )
        self._export.grid(row=6, column=0, sticky="ew", pady=(0, 16))

    def _save_project(self):
        source = self._loader.get_source()
        if not source:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Video Cutter project", "*.json")],
        )
        if not path:
            return
        data = {
            "source": source,
            "trim": list(self._trim.get_trim_values()),
            "clips": self._clips.get_clips(),
            "tags": self._tags.get_tags(),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_project(self):
        path = filedialog.askopenfilename(filetypes=[("Video Cutter project", "*.json")])
        if not path:
            return
        with open(path) as f:
            data = json.load(f)

        source = data.get("source")
        if source and os.path.exists(source):
            self._loader.load_path(source)

        start, end = data.get("trim", [0.0, 0.0])
        self._trim.set_start(start)
        self._trim.set_end(end)
        self._clips.set_clips([tuple(c) for c in data.get("clips", [])])
        self._tags.set_tags(data.get("tags", []))

    def _on_video_loaded(self, path: str):
        self._player.load(path)
        self._trim.set_video(path)
        self._export.set_source(path)

    def _on_player_set_start(self, seconds: float):
        self._trim.set_start(seconds)

    def _on_player_set_end(self, seconds: float):
        self._trim.set_end(seconds)

    def _on_fullscreen_toggle(self):
        self._is_fullscreen = not self._is_fullscreen
        side_panels = (self._loader, self._trim, self._clips, self._tags, self._detection, self._export)

        if self._is_fullscreen:
            self._normal_geometry = self.geometry()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            self.geometry(f"{screen_w}x{screen_h}+0+0")
            for panel in side_panels:
                panel.grid_remove()
        else:
            for panel in side_panels:
                panel.grid()
            if self._normal_geometry:
                self.geometry(self._normal_geometry)

        # macOS applies the window resize asynchronously — wait for it
        # before measuring, or the canvas gets sized off the stale geometry.
        self.after(150, self._apply_player_canvas_size)

    def _apply_player_canvas_size(self):
        self.update_idletasks()
        if self._is_fullscreen:
            window_h = self.winfo_height()
            target_h = max(window_h - 150, 300)
            self._player.set_canvas_height(target_h)
        else:
            self._player.set_canvas_height(PREVIEW_H)
