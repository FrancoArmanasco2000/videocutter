# 04 — Object Detection (AI Labels)

## Status
✅ Complete

## Goal
Detect and label persons, players, and ball in video clips using a pre-trained YOLO model.
Annotations are burned into the exported MP4.

## Files
- `src/services/detector.py` — detection + frame rendering + export pipeline
- `src/ui/detection_panel.py` — UI toggle, class checkboxes, confidence slider
- `src/ui/export_panel.py` — updated to route to detector when detection is enabled
- `src/ui/main_window.py` — added DetectionPanel between TrimPanel and ExportPanel

## Stack additions
| Package | Version | Role |
|---|---|---|
| ultralytics | 8.3.0 | YOLOv8 inference |
| opencv-python | 4.10.0.84 | Frame read/write/draw |

## COCO classes used
| Class ID | Label | Color (BGR) |
|---|---|---|
| 0 | Person / Player | Orange `(0, 200, 255)` |
| 32 | Ball | Green `(0, 255, 80)` |

No model training required — `yolov8n.pt` is pre-trained on COCO 80 classes.
**First run downloads the model (~6 MB) automatically** via ultralytics.

## Detection pipeline

```
source video
    │
    ├─ cv2.VideoCapture → seek to start_frame
    │
    ├─ per frame:
    │     YOLO inference (filtered to selected classes + confidence)
    │     draw bounding boxes + label + confidence %
    │     write to temp_noaudio.mp4 (mp4v codec)
    │
    └─ ffmpeg merge:
          annotated frames (video) + original source (audio segment ss=start t=duration)
          → re-encode: libx264 crf=18 + aac
          → delete temp file
```

## Why re-encode on detection export
OpenCV's VideoWriter writes raw frames — no audio. ffmpeg merges the annotated video
with the audio segment from the original source. This requires re-encoding (libx264),
unlike the plain export which uses `c=copy` (stream copy). Detection export is slower.

## Audio fallback
If the source has no audio track, ffmpeg raises an error on the merge step.
The detector catches `ffmpeg.Error` and falls back to a video-only output.

## Progress reporting
Frame-by-frame progress is emitted via `on_progress(percent)` callback and shown
in the export panel's `CTkProgressBar` (determinate mode, 0–100%).

## Known limitations
- `yolov8n` (nano) is fast but less accurate than `yolov8s` / `yolov8m`
- Ball detection accuracy drops for small or fast-moving balls
- Bounding boxes are drawn on every frame independently — no tracking/smoothing
- Re-encoding takes longer than stream copy (varies with video length and hardware)
