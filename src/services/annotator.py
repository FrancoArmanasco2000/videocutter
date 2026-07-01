import os
import tempfile
from typing import Callable

import cv2
import ffmpeg

# How long a telestrator shape stays burned into the export after it was drawn
DRAW_BURN_SECONDS = 4.0


def hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return b, g, r


def mux_audio(tmp_video_path: str, source: str, dest: str, start: float, duration: float) -> None:
    try:
        video_in = ffmpeg.input(tmp_video_path)
        audio_in = ffmpeg.input(source, ss=start, t=duration)
        (
            ffmpeg
            .output(video_in.video, audio_in.audio, dest,
                    vcodec="libx264", acodec="aac", crf=18, preset="fast")
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error:
        (
            ffmpeg
            .input(tmp_video_path)
            .output(dest, vcodec="libx264", crf=18, preset="fast")
            .overwrite_output()
            .run(quiet=True)
        )


def burn_drawings(frame, drawings: list[dict], abs_frame: int, fps: float):
    """Overlays telestrator shapes onto `frame` in-place, for shapes whose
    display window (a few seconds starting at the frame they were drawn on)
    covers `abs_frame` — the absolute frame index in the source video."""
    if not drawings:
        return frame
    h, w = frame.shape[:2]
    window_frames = DRAW_BURN_SECONDS * fps

    for d in drawings:
        if not (d["frame"] <= abs_frame < d["frame"] + window_frames):
            continue
        color = hex_to_bgr(d["color"])
        pts = [(int(nx * w), int(ny * h)) for nx, ny in d["points"]]

        if d["mode"] == "pen":
            for p1, p2 in zip(pts, pts[1:]):
                cv2.line(frame, p1, p2, color, 3, cv2.LINE_AA)
        elif d["mode"] == "arrow":
            cv2.arrowedLine(frame, pts[0], pts[-1], color, 3, cv2.LINE_AA, tipLength=0.15)
        elif d["mode"] == "circle":
            x0, y0 = pts[0]
            x1, y1 = pts[-1]
            center = ((x0 + x1) // 2, (y0 + y1) // 2)
            axes = (max(abs(x1 - x0) // 2, 1), max(abs(y1 - y0) // 2, 1))
            cv2.ellipse(frame, center, axes, 0, 0, 360, color, 3, cv2.LINE_AA)
        elif d["mode"] == "rect":
            cv2.rectangle(frame, pts[0], pts[-1], color, 3)

    return frame


def burn_clip(
    source: str, dest: str, start: float, end: float,
    drawings: list[dict],
    on_progress: Callable[[float], None] | None = None,
) -> None:
    """Cuts [start, end] from `source` into `dest`, burning telestrator shapes
    in. No AI model involved — used when detection is off but drawings exist."""
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

        burn_drawings(frame, drawings, start_frame + frame_idx, fps)
        writer.write(frame)

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
