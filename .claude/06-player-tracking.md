# 06 — Player Tracking (ByteTrack)

## Status
✅ Complete

## Files
- `src/services/detector.py` — added `tracking` param, ByteTrack inference, per-ID color palette
- `src/ui/detection_panel.py` — added "Track players (ID)" checkbox
- `src/ui/export_panel.py` — passes `tracking` key to detector

## What changed vs plain detection

| | Detection | Detection + Tracking |
|---|---|---|
| Inference call | `model(frame, ...)` | `model.track(frame, persist=True, tracker="bytetrack.yaml", ...)` |
| Box label | `Player 87%` | `#3 Player` |
| Box color | class color (orange / green) | unique color per track ID |
| Frame independence | yes — IDs reset each frame | no — ID persists across frames |

## ByteTrack integration
`persist=True` tells ultralytics to maintain tracker state between `model.track()` calls on consecutive frames.
`tracker="bytetrack.yaml"` selects ByteTrack — bundled with ultralytics, no extra install.

## Tracker reset between runs
A fresh `YOLO("yolov8n.pt")` instance is created for each tracking export.
This guarantees IDs always start from #1 — without this, IDs would continue from
the previous run because the tracker state lives inside the model instance.
PyTorch caches the weights in memory so the second instantiation is fast.

## Per-ID color palette
10 visually distinct BGR colors cycling by `track_id % 10`.
Players keep the same color for their entire appearance in the clip.

## Known limitations
- ByteTrack can swap IDs when players overlap or leave/re-enter the frame.
- Very fast ball movement may cause the tracker to lose the ball between frames.
- For professional tracking (re-ID across camera cuts) a heavier model like BoT-SORT
  with a Re-ID backbone would be needed.
