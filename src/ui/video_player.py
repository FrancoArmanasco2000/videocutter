import tkinter as tk
from typing import Callable

import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
from ui.theme import (
    BG_PANEL, BG_INSET, BORDER, ACCENT, ACCENT_HOVER,
    SUCCESS, SUCCESS_HOVER, DANGER, DANGER_HOVER,
    NEUTRAL, NEUTRAL_HOVER, TEXT_PRIMARY, TEXT_MUTED, TEXT_DIM, RADIUS,
)

PREVIEW_W = 880
PREVIEW_H = 495  # 16:9

# Drawing tools
TOOLS = [
    ("pen",    "✏  Pen"),
    ("arrow",  "→  Arrow"),
    ("circle", "○  Circle"),
    ("rect",   "□  Rect"),
]

# Color palette for annotations
DRAW_COLORS = [
    ("#ffffff", "White"),
    ("#ef4444", "Red"),
    ("#3b82f6", "Blue"),
    ("#fbbf24", "Yellow"),
    ("#22c55e", "Green"),
]


class VideoPlayer(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_set_start: Callable[[float], None],
        on_set_end: Callable[[float], None],
    ):
        super().__init__(master, fg_color=BG_PANEL, border_color=BORDER,
                         border_width=1, corner_radius=RADIUS)
        self._on_set_start = on_set_start
        self._on_set_end = on_set_end

        # Playback state
        self._cap: cv2.VideoCapture | None = None
        self._fps: float = 25.0
        self._total_frames: int = 1
        self._current_frame: int = 0
        self._playing: bool = False
        self._speed: float = 1.0
        self._after_id = None
        self._photo = None
        self._video_item_id = None  # single canvas item — updated via itemconfig

        # Drawing state
        self._draw_mode: str = "arrow"
        self._draw_color: str = "#ef4444"
        self._draw_start: tuple[int, int] | None = None
        self._temp_item = None
        self._pen_points: list[tuple[int, int]] = []

        # UI references
        self._speed_btns: dict[float, ctk.CTkButton] = {}
        self._tool_btns: dict[str, ctk.CTkButton] = {}
        self._color_btns: dict[str, ctk.CTkButton] = {}

        self._build()

    # ── build ───────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="PREVIEW",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).grid(row=0, column=0, padx=14, pady=(10, 4), sticky="w")

        # ── Video canvas ────────────────────────────────────────────────────
        self._canvas = tk.Canvas(
            self,
            width=PREVIEW_W, height=PREVIEW_H,
            bg="#010409", highlightthickness=0,
            cursor="crosshair",
        )
        self._canvas.grid(row=1, column=0, padx=14)
        self._canvas.create_text(
            PREVIEW_W // 2, PREVIEW_H // 2,
            text="Load a video to start",
            fill=TEXT_DIM, font=("Helvetica", 14),
            tags="placeholder",
        )
        self._canvas.bind("<Button-1>",        self._on_draw_start)
        self._canvas.bind("<B1-Motion>",       self._on_draw_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_draw_end)

        # ── Scrubber ────────────────────────────────────────────────────────
        scrub = ctk.CTkFrame(self, fg_color="transparent")
        scrub.grid(row=2, column=0, padx=14, pady=(8, 2), sticky="ew")
        scrub.grid_columnconfigure(1, weight=1)

        self._time_label = ctk.CTkLabel(
            scrub, text="00:00",
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"),
            text_color=TEXT_PRIMARY, width=52,
        )
        self._time_label.grid(row=0, column=0, padx=(0, 8))

        self._scrubber = ctk.CTkSlider(
            scrub, from_=0, to=1,
            button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            progress_color=ACCENT, fg_color=BORDER,
            command=self._on_scrub,
        )
        self._scrubber.set(0)
        self._scrubber.grid(row=0, column=1, sticky="ew")

        self._duration_label = ctk.CTkLabel(
            scrub, text="00:00",
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"),
            text_color=TEXT_MUTED, width=52,
        )
        self._duration_label.grid(row=0, column=2, padx=(8, 0))

        # ── Playback controls ───────────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=3, column=0, padx=14, pady=(4, 6))

        _sec = dict(height=34, fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
                    text_color=TEXT_PRIMARY, border_color=BORDER, border_width=1)

        ctk.CTkButton(ctrl, text="⏮", width=44, command=self._go_to_start, **_sec).pack(side="left", padx=(0, 2))
        ctk.CTkButton(ctrl, text="‹", width=36, command=self._step_backward,
                      **_sec).pack(side="left", padx=(0, 4))

        self._play_btn = ctk.CTkButton(
            ctrl, text="▶  Play", width=96, height=34,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#ffffff", font=ctk.CTkFont(weight="bold"),
            command=self._toggle_play,
        )
        self._play_btn.pack(side="left", padx=(0, 4))

        ctk.CTkButton(ctrl, text="›", width=36, command=self._step_forward,
                      **_sec).pack(side="left", padx=(0, 2))
        ctk.CTkButton(ctrl, text="⏭", width=44, command=self._go_to_end, **_sec).pack(side="left", padx=(0, 24))

        ctk.CTkButton(
            ctrl, text="◀  Set Start", width=110, height=34,
            fg_color=SUCCESS, hover_color=SUCCESS_HOVER,
            text_color="#ffffff", font=ctk.CTkFont(weight="bold"),
            command=self._set_start,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            ctrl, text="Set End  ▶", width=110, height=34,
            fg_color=DANGER, hover_color=DANGER_HOVER,
            text_color="#ffffff", font=ctk.CTkFont(weight="bold"),
            command=self._set_end,
        ).pack(side="left")

        # ── Speed controls ──────────────────────────────────────────────────
        speed_row = ctk.CTkFrame(self, fg_color="transparent")
        speed_row.grid(row=4, column=0, padx=14, pady=(0, 6))

        ctk.CTkLabel(
            speed_row, text="SPEED",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(0, 10))

        for speed, label in [(0.25, "0.25×"), (0.5, "0.5×"), (1.0, "1×"), (2.0, "2×")]:
            btn = ctk.CTkButton(
                speed_row, text=label, width=58, height=28,
                fg_color=ACCENT if speed == 1.0 else NEUTRAL,
                hover_color=ACCENT_HOVER if speed == 1.0 else NEUTRAL_HOVER,
                text_color="#ffffff" if speed == 1.0 else TEXT_MUTED,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda s=speed: self._set_speed(s),
            )
            btn.pack(side="left", padx=2)
            self._speed_btns[speed] = btn

        # ── Drawing toolbar ─────────────────────────────────────────────────
        draw_row = ctk.CTkFrame(self, fg_color=BG_INSET, corner_radius=RADIUS)
        draw_row.grid(row=5, column=0, padx=14, pady=(0, 14), sticky="ew")

        ctk.CTkLabel(
            draw_row, text="DRAW  (pause to annotate)",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(12, 14))

        # Tool buttons
        for mode, label in TOOLS:
            btn = ctk.CTkButton(
                draw_row, text=label, width=88, height=28,
                fg_color=ACCENT if mode == self._draw_mode else NEUTRAL,
                hover_color=ACCENT_HOVER if mode == self._draw_mode else NEUTRAL_HOVER,
                text_color="#ffffff" if mode == self._draw_mode else TEXT_MUTED,
                font=ctk.CTkFont(size=12),
                command=lambda m=mode: self._set_tool(m),
            )
            btn.pack(side="left", padx=2, pady=6)
            self._tool_btns[mode] = btn

        # Divider
        ctk.CTkFrame(draw_row, width=1, height=20, fg_color=BORDER).pack(side="left", padx=10)

        # Color buttons
        for color, _ in DRAW_COLORS:
            btn = ctk.CTkButton(
                draw_row, text="", width=26, height=26,
                fg_color=color, hover_color=color,
                border_color="#ffffff" if color == self._draw_color else "transparent",
                border_width=2,
                corner_radius=13,
                command=lambda c=color: self._set_draw_color(c),
            )
            btn.pack(side="left", padx=3, pady=6)
            self._color_btns[color] = btn

        # Divider
        ctk.CTkFrame(draw_row, width=1, height=20, fg_color=BORDER).pack(side="left", padx=10)

        ctk.CTkButton(
            draw_row, text="Clear", width=60, height=28,
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER,
            text_color=TEXT_MUTED, font=ctk.CTkFont(size=12),
            command=self._clear_drawings,
        ).pack(side="left", padx=(0, 8), pady=6)

        # Keyboard shortcuts — bound after widget is attached to the window
        self.after(200, self._bind_keys)

    # ── public API ──────────────────────────────────────────────────────────

    def load(self, path: str):
        self._stop()
        if self._cap:
            self._cap.release()
        self._clear_drawings()
        self._cap = cv2.VideoCapture(path)
        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 25.0
        self._total_frames = max(int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT)), 1)
        self._duration_label.configure(text=self._fmt(self._total_frames / self._fps))
        self._scrubber.set(0)
        self._canvas.delete("placeholder")
        self._seek_to_frame(0)

    # ── playback ────────────────────────────────────────────────────────────

    def _toggle_play(self):
        if self._playing:
            self._stop()
        else:
            self._play()

    def _play(self):
        if not self._cap:
            return
        self._clear_drawings()
        self._playing = True
        self._play_btn.configure(
            text="⏸  Pause", fg_color=NEUTRAL,
            hover_color=NEUTRAL_HOVER, text_color=TEXT_PRIMARY,
        )
        self._schedule_next()

    def _stop(self):
        self._playing = False
        self._play_btn.configure(
            text="▶  Play", fg_color=ACCENT,
            hover_color=ACCENT_HOVER, text_color="#ffffff",
        )
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _schedule_next(self):
        delay = max(1, int(1000 / (self._fps * self._speed)))
        self._after_id = self.after(delay, self._next_frame)

    def _next_frame(self):
        if not self._playing or not self._cap:
            return
        ret, frame = self._cap.read()
        if not ret:
            self._stop()
            return
        self._current_frame = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
        self._render(frame)
        self._sync_scrubber()
        self._schedule_next()

    def _set_speed(self, speed: float):
        self._speed = speed
        for s, btn in self._speed_btns.items():
            active = s == speed
            btn.configure(
                fg_color=ACCENT if active else NEUTRAL,
                hover_color=ACCENT_HOVER if active else NEUTRAL_HOVER,
                text_color="#ffffff" if active else TEXT_MUTED,
            )

    # ── seeking ─────────────────────────────────────────────────────────────

    def _seek_to_frame(self, frame_no: int):
        if not self._cap:
            return
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = self._cap.read()
        if ret:
            self._current_frame = frame_no
            self._render(frame)
            self._sync_scrubber()

    def _on_scrub(self, value: float):
        if not self._cap:
            return
        was_playing = self._playing
        self._stop()
        self._seek_to_frame(int(float(value) * self._total_frames))
        if was_playing:
            self._play()

    def _step_backward(self):
        self._stop()
        self._seek_to_frame(max(0, self._current_frame - 1))

    def _step_forward(self):
        self._stop()
        self._seek_to_frame(min(self._total_frames - 1, self._current_frame + 1))

    def _go_to_start(self):
        self._stop()
        self._seek_to_frame(0)

    def _go_to_end(self):
        self._stop()
        self._seek_to_frame(max(0, self._total_frames - 1))

    def _bind_keys(self):
        root = self.winfo_toplevel()
        root.bind("<Left>",  self._on_key_left)
        root.bind("<Right>", self._on_key_right)
        root.bind("<space>", self._on_key_space)

    def _on_key_left(self, event: tk.Event):
        if isinstance(event.widget, tk.Entry):
            return
        self._step_backward()

    def _on_key_right(self, event: tk.Event):
        if isinstance(event.widget, tk.Entry):
            return
        self._step_forward()

    def _on_key_space(self, event: tk.Event):
        if isinstance(event.widget, tk.Entry):
            return
        self._toggle_play()

    def _set_start(self):
        self._on_set_start(self._current_frame / self._fps)

    def _set_end(self):
        self._on_set_end(self._current_frame / self._fps)

    # ── drawing ─────────────────────────────────────────────────────────────

    def _set_tool(self, mode: str):
        self._draw_mode = mode
        for m, btn in self._tool_btns.items():
            active = m == mode
            btn.configure(
                fg_color=ACCENT if active else NEUTRAL,
                hover_color=ACCENT_HOVER if active else NEUTRAL_HOVER,
                text_color="#ffffff" if active else TEXT_MUTED,
            )

    def _set_draw_color(self, color: str):
        self._draw_color = color
        for c, btn in self._color_btns.items():
            btn.configure(border_color="#ffffff" if c == color else "transparent")

    def _clear_drawings(self):
        self._canvas.delete("drawing")
        self._temp_item = None
        self._draw_start = None
        self._pen_points = []

    def _on_draw_start(self, event: tk.Event):
        if self._playing:
            return
        self._draw_start = (event.x, event.y)
        self._pen_points = [(event.x, event.y)]

    def _on_draw_drag(self, event: tk.Event):
        if self._playing or not self._draw_start:
            return

        x0, y0 = self._draw_start
        x1, y1 = event.x, event.y

        if self._draw_mode == "pen":
            self._pen_points.append((x1, y1))
            if len(self._pen_points) >= 2:
                p1 = self._pen_points[-2]
                p2 = self._pen_points[-1]
                self._canvas.create_line(
                    p1[0], p1[1], p2[0], p2[1],
                    fill=self._draw_color, width=3,
                    capstyle=tk.ROUND, joinstyle=tk.ROUND,
                    tags="drawing",
                )
        else:
            if self._temp_item:
                self._canvas.delete(self._temp_item)
            self._temp_item = self._draw_shape(x0, y0, x1, y1, tags="preview")

    def _on_draw_end(self, event: tk.Event):
        if self._playing or not self._draw_start:
            return

        if self._draw_mode != "pen" and self._temp_item:
            self._canvas.delete(self._temp_item)
            self._temp_item = None
            x0, y0 = self._draw_start
            self._draw_shape(x0, y0, event.x, event.y, tags="drawing")

        self._draw_start = None
        self._pen_points = []

    def _draw_shape(self, x0: int, y0: int, x1: int, y1: int, tags: str):
        kw = dict(fill=self._draw_color, tags=tags)

        if self._draw_mode == "arrow":
            return self._canvas.create_line(
                x0, y0, x1, y1,
                width=3, arrow=tk.LAST,
                arrowshape=(14, 18, 6),
                **kw,
            )
        if self._draw_mode == "circle":
            return self._canvas.create_oval(
                x0, y0, x1, y1,
                outline=self._draw_color, width=3,
                fill="", tags=tags,
            )
        if self._draw_mode == "rect":
            return self._canvas.create_rectangle(
                x0, y0, x1, y1,
                outline=self._draw_color, width=3,
                fill="", tags=tags,
            )
        return None

    # ── rendering ───────────────────────────────────────────────────────────

    def _render(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        img.thumbnail((PREVIEW_W, PREVIEW_H), Image.LANCZOS)
        bg = Image.new("RGB", (PREVIEW_W, PREVIEW_H), (1, 4, 9))
        bg.paste(img, ((PREVIEW_W - img.width) // 2, (PREVIEW_H - img.height) // 2))
        self._photo = ImageTk.PhotoImage(bg)

        if self._video_item_id is None:
            self._video_item_id = self._canvas.create_image(0, 0, anchor="nw", image=self._photo)
        else:
            self._canvas.itemconfig(self._video_item_id, image=self._photo)
            # Keep video frame below all drawing items
            self._canvas.tag_lower(self._video_item_id)

    def _sync_scrubber(self):
        self._scrubber.set(self._current_frame / self._total_frames)
        self._time_label.configure(text=self._fmt(self._current_frame / self._fps))

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f"{s // 60:02d}:{s % 60:02d}"
