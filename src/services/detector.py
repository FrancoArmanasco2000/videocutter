import os
import tempfile
from typing import Callable

import cv2
import ffmpeg

# COCO class IDs relevant to sports analysis
COCO_CLASSES = {
    0: "Player",
    32: "Ball",
}

# Default box color per class (BGR) — used when tracking is off
CLASS_COLORS = {
    0: (0, 200, 255),   # orange
    32: (0, 255, 80),   # green
}

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


class Detector:
    def __init__(self):
        self._model = None

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
        on_progress: Callable[[float], None] | None = None,
    ) -> None:
        self._load_model()

        # Tracking needs a fresh model instance per run so IDs reset to #1
        model = self._fresh_model() if tracking else self._model

        cap = cv2.VideoCapture(source)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
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

            annotated = self._draw(frame, results[0], classes, tracking)
            writer.write(annotated)

            frame_idx += 1
            if on_progress:
                on_progress(min(frame_idx / total_frames * 100, 99.0))

        cap.release()
        writer.release()

        duration = end - start
        try:
            video_in = ffmpeg.input(tmp_path)
            audio_in = ffmpeg.input(source, ss=start, t=duration)
            (
                ffmpeg
                .output(
                    video_in.video,
                    audio_in.audio,
                    dest,
                    vcodec="libx264",
                    acodec="aac",
                    crf=18,
                    preset="fast",
                )
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg.Error:
            (
                ffmpeg
                .input(tmp_path)
                .output(dest, vcodec="libx264", crf=18, preset="fast")
                .overwrite_output()
                .run(quiet=True)
            )
        finally:
            os.unlink(tmp_path)

        if on_progress:
            on_progress(100.0)

    @staticmethod
    def _draw(frame, result, classes: list[int], tracking: bool):
        for box in result.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in classes:
                continue

            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            track_id = None
            if tracking and box.id is not None:
                track_id = int(box.id[0])

            # Unique color per ID when tracking; class color otherwise
            if track_id is not None:
                color = TRACK_PALETTE[track_id % len(TRACK_PALETTE)]
            else:
                color = CLASS_COLORS.get(cls_id, (255, 255, 255))

            label = (
                f"#{track_id} {COCO_CLASSES.get(cls_id, cls_id)}"
                if track_id is not None
                else f"{COCO_CLASSES.get(cls_id, cls_id)} {conf:.0%}"
            )

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
