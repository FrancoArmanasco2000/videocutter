import os
import tempfile
from typing import Callable

import cv2

from services.annotator import burn_drawings, mux_audio

# COCO class IDs relevant to sports analysis
COCO_CLASSES = {
    0: "Player",
    32: "Ball",
}

# Default box color per class (BGR) — used when tracking/teams are off
CLASS_COLORS = {
    0: (0, 200, 255),   # orange
    32: (0, 255, 80),   # green
}

# Team box colors (BGR) — used when team classification is on
TEAM_COLORS = [
    (255, 191, 0),   # cyan-ish — Team A
    (0, 128, 255),   # orange-ish — Team B
]
TEAM_LABELS = ["Team A", "Team B"]

# Palette for unique per-ID colors when tracking is on
TRACK_PALETTE = [
    (255,  80,  80),  # red
    ( 80,  80, 255),  # blue
    ( 80, 255,  80),  # lime
    (255, 200,   0),  # yellow
    (200,   0, 255),  # violet
    (  0, 200, 255),  # cyan
    (255, 120,   0),  # orange
    (  0, 255, 200),  # teal
    (255,   0, 160),  # pink
    (160, 255,   0),  # chartreuse
]

# How close (as a fraction of frame width) a player must be to the ball
# to be considered "in possession" for that frame
POSSESSION_RADIUS_FRACTION = 0.08

# Color-distance threshold (BGR, 0-255 scale) used to tell two jerseys apart
TEAM_DIST_THRESHOLD = 60.0


class Detector:
    def __init__(self):
        self._model = None
        self._team_refs: list[tuple[float, float, float]] = []
        self._team_track_cache: dict[int, int] = {}

    def _load_model(self):
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO("yolov8n.pt")

    def _fresh_model(self):
        from ultralytics import YOLO
        return YOLO("yolov8n.pt")

    def process_video(
        self,
        source: str,
        dest: str,
        start: float,
        end: float,
        classes: list[int],
        confidence: float = 0.4,
        tracking: bool = False,
        teams: bool = False,
        drawings: list[dict] | None = None,
        on_progress: Callable[[float], None] | None = None,
    ) -> dict | None:
        self._load_model()
        self._team_refs = []
        self._team_track_cache = {}

        # Tracking needs a fresh model instance per run so IDs reset to #1
        model = self._fresh_model() if tracking else self._model

        track_possession = teams and 0 in classes and 32 in classes
        possession = {"a": 0, "b": 0, "fps": 0.0}

        cap = cv2.VideoCapture(source)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        possession["fps"] = fps
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        start_frame = int(start * fps)
        end_frame = int(end * fps)
        total_frames = max(end_frame - start_frame, 1)

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        tmp_fd, tmp_path = tempfile.mkstemp(suffix="_noaudio.mp4")
        os.close(tmp_fd)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(tmp_path, fourcc, fps, (width, height))

        frame_idx = 0
        while cap.isOpened():
            if cap.get(cv2.CAP_PROP_POS_FRAMES) > end_frame:
                break

            ret, frame = cap.read()
            if not ret:
                break

            if tracking:
                results = model.track(
                    frame,
                    classes=classes,
                    conf=confidence,
                    persist=True,
                    tracker="bytetrack.yaml",
                    verbose=False,
                )
            else:
                results = model(
                    frame,
                    classes=classes,
                    conf=confidence,
                    verbose=False,
                )

            dets = self._parse_detections(frame, results[0], classes, tracking, teams)
            annotated = self._draw(frame, dets, tracking, teams)
            if track_possession:
                self._accumulate_possession(dets, possession, width)
            burn_drawings(annotated, drawings or [], start_frame + frame_idx, fps)
            writer.write(annotated)

            frame_idx += 1
            if on_progress:
                on_progress(min(frame_idx / total_frames * 100, 99.0))

        cap.release()
        writer.release()

        try:
            mux_audio(tmp_path, source, dest, start, end - start)
        finally:
            os.unlink(tmp_path)

        if on_progress:
            on_progress(100.0)

        return possession if track_possession else None

    # ── per-frame detection parsing ──────────────────────────────────────────

    def _parse_detections(self, frame, result, classes: list[int], tracking: bool, teams: bool) -> list[dict]:
        dets = []
        for box in result.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in classes:
                continue

            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            track_id = int(box.id[0]) if (tracking and box.id is not None) else None

            team = None
            if teams and cls_id == 0:
                team = self._classify_team(frame, x1, y1, x2, y2, track_id)

            dets.append({
                "cls_id": cls_id, "conf": conf,
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "track_id": track_id, "team": team,
            })
        return dets

    # ── team classification ──────────────────────────────────────────────────

    def _classify_team(self, frame, x1: int, y1: int, x2: int, y2: int, track_id: int | None) -> int | None:
        if track_id is not None and track_id in self._team_track_cache:
            return self._team_track_cache[track_id]

        color = self._sample_jersey_color(frame, x1, y1, x2, y2)
        if color is None:
            return None

        team = self._assign_team(color)
        if track_id is not None:
            self._team_track_cache[track_id] = team
        return team

    @staticmethod
    def _sample_jersey_color(frame, x1: int, y1: int, x2: int, y2: int):
        h, w = frame.shape[:2]
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return None

        # Chest band: skips the head and the shorts/socks
        box_h = y2 - y1
        top = y1 + int(box_h * 0.15)
        bottom = y1 + int(box_h * 0.45)
        band = frame[top:bottom, x1:x2]
        if band.size == 0:
            return None

        mean = band.reshape(-1, 3).mean(axis=0)
        return float(mean[0]), float(mean[1]), float(mean[2])

    def _assign_team(self, color: tuple[float, float, float]) -> int:
        if not self._team_refs:
            self._team_refs.append(color)
            return 0

        dists = [self._color_dist(color, ref) for ref in self._team_refs]
        nearest = min(range(len(dists)), key=lambda i: dists[i])

        if len(self._team_refs) == 1 and dists[nearest] > TEAM_DIST_THRESHOLD:
            self._team_refs.append(color)
            return 1

        # Nudge the matched team's reference color towards this sample
        alpha = 0.1
        old = self._team_refs[nearest]
        self._team_refs[nearest] = tuple(o * (1 - alpha) + c * alpha for o, c in zip(old, color))
        return nearest

    @staticmethod
    def _color_dist(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
        return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5

    # ── possession ────────────────────────────────────────────────────────────

    @staticmethod
    def _accumulate_possession(dets: list[dict], possession: dict, frame_w: int) -> None:
        ball = max((d for d in dets if d["cls_id"] == 32), key=lambda d: d["conf"], default=None)
        players = [d for d in dets if d["cls_id"] == 0 and d["team"] is not None]
        if not ball or not players:
            return

        bx = (ball["x1"] + ball["x2"]) / 2
        by = (ball["y1"] + ball["y2"]) / 2

        nearest, nearest_dist = None, float("inf")
        for p in players:
            px = (p["x1"] + p["x2"]) / 2
            py = (p["y1"] + p["y2"]) / 2
            dist = ((px - bx) ** 2 + (py - by) ** 2) ** 0.5
            if dist < nearest_dist:
                nearest, nearest_dist = p, dist

        threshold = frame_w * POSSESSION_RADIUS_FRACTION
        if nearest and nearest_dist <= threshold:
            key = "a" if nearest["team"] == 0 else "b"
            possession[key] += 1

    # ── rendering ─────────────────────────────────────────────────────────────

    def _draw(self, frame, dets: list[dict], tracking: bool, teams: bool):
        for d in dets:
            cls_id, track_id, team = d["cls_id"], d["track_id"], d["team"]
            x1, y1, x2, y2 = d["x1"], d["y1"], d["x2"], d["y2"]

            if track_id is not None:
                color = TRACK_PALETTE[track_id % len(TRACK_PALETTE)]
            elif teams and team is not None:
                color = TEAM_COLORS[team]
            else:
                color = CLASS_COLORS.get(cls_id, (255, 255, 255))

            if teams and team is not None:
                base_label = TEAM_LABELS[team]
            else:
                base_label = COCO_CLASSES.get(cls_id, str(cls_id))

            label = f"#{track_id} {base_label}" if track_id is not None else f"{base_label} {d['conf']:.0%}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
            cv2.putText(
                frame, label,
                (x1 + 3, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 0, 0), 1, cv2.LINE_AA,
            )

        return frame
