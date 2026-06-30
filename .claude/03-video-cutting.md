# 03 — Video Cutting (Trim & Export)

## Status
✅ Complete

## Files
- `src/ui/trim_panel.py` — Start / End time inputs
- `src/ui/export_panel.py` — Export button + progress
- `src/services/cutter.py` — ffmpeg-python wrapper

## How it works

### Trim Panel
- When a video is loaded, `TrimPanel.set_video(path)` probes the file with `ffmpeg.probe()` to read `format.duration`.
- The **End** field is pre-filled with the total duration in seconds.
- User edits **Start** and **End** fields manually (seconds, decimals allowed).

### Export Panel
1. User clicks **Export clip**.
2. Native "Save As" dialog opens (`.mp4` default).
3. `get_trim()` is called to read start/end from `TrimPanel`.
4. A `daemon` thread runs `Cutter.cut(source, dest, start, end)`.
5. An indeterminate `CTkProgressBar` spins during export.
6. On completion the bar hides and a status label confirms success.

### Cutter service
```python
ffmpeg.input(source, ss=start, t=duration).output(dest, c="copy").run()
```
- `ss` (seek) is applied as an **input** option — faster than output seek, though slightly less precise.
- `t` is duration (not end time), so `duration = end - start`.
- `c="copy"` = stream copy; no re-encoding, so export is near-instant.

## Why input seek (`-ss` before `-i`)
Placing `-ss` before `-i` lets ffmpeg seek using keyframes (fast). Placing it after `-i` forces frame-by-frame decode to the exact timestamp (slow but frame-accurate). For this use case, fast input seek is the right default.

## Known limitations
- Cuts snap to the nearest keyframe, not the exact second entered.
- No progress percentage (ffmpeg stream copy doesn't emit meaningful progress events; indeterminate bar is used).
- Overwrites output file without warning if user confirms in the dialog.
