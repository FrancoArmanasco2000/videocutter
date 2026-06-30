# 09 — Speed Control (Slow Motion)

## Status
✅ Complete

## Files
- `src/ui/video_player.py` — added `_speed`, `_speed_btns`, `_set_speed()`, speed row UI

## Speeds available
| Button | Factor | Use case |
|---|---|---|
| 0.25× | ¼ speed | Frame-by-frame tactical detail |
| 0.5×  | ½ speed | Transition / movement analysis |
| 1×    | Normal  | Default |
| 2×    | 2× speed | Quick review of long footage |

## How it works
Playback loop uses `after(delay_ms, callback)` where:
```python
delay = max(1, int(1000 / (fps * speed)))
```
- 0.25× at 30fps → delay = 133ms (7.5 fps rendered)
- 0.5×  at 30fps → delay =  67ms (15 fps rendered)
- 1×    at 30fps → delay =  33ms (30 fps rendered)
- 2×    at 30fps → delay =  16ms (≈60 fps rendered, system-dependent)

Speed change takes effect on the next scheduled frame — no restart needed.
Active speed button is highlighted in ACCENT orange; inactive ones in NEUTRAL.

## Known limitations
- 2× speed is best-effort — Tkinter's `after()` is not frame-locked so actual speed
  depends on render time per frame and OS scheduler precision.
- Frame skipping is not implemented — every frame is decoded and rendered regardless
  of speed. For true 2× you'd skip alternate frames (future enhancement).
