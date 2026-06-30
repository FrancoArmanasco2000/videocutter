# 05 — Video Preview with Scrubber

## Status
✅ Complete

## Files
- `src/ui/video_player.py` — video player component (new)
- `src/ui/trim_panel.py` — added `set_start()` / `set_end()` methods
- `src/ui/main_window.py` — added VideoPlayer, window height → 920px

## Layout

```
┌──────────────────────────────────────────────────────────┐
│                  VIDEO CANVAS (640×360)                  │
│              letterbox / pillarbox on black              │
├──────────────────────────────────────────────────────────┤
│  00:12   [══════════|══════════════════════════]  05:30  │
├──────────────────────────────────────────────────────────┤
│   [⏮]   [▶ / ⏸]   [⏭]      [Set Start]  [Set End]    │
└──────────────────────────────────────────────────────────┘
```

## Playback loop
Uses `widget.after(delay_ms, callback)` — no background thread needed.
`delay_ms = max(1, int(1000 / fps))` keeps playback at correct speed.
All canvas updates happen on the main thread (Tkinter requirement).

## Frame rendering
```python
img.thumbnail((640, 360), Image.LANCZOS)   # fit preserving aspect ratio
bg = Image.new("RGB", (640, 360), (26,26,26))  # black background
bg.paste(img, (centered_x, centered_y))    # center the frame
self._photo = ImageTk.PhotoImage(bg)       # must hold reference
self._canvas.create_image(0, 0, ...)
```
`self._photo` is stored as an instance attribute — if it were local, Python's GC
would collect it before Tkinter renders the image (blank frame bug).

## Scrubber seeking
- Dragging the slider pauses playback, seeks to the target frame, then resumes if it was playing.
- Seeking uses `cap.set(CAP_PROP_POS_FRAMES, n)` + one `cap.read()` to display the frame.

## Set Start / Set End
Buttons call `on_set_start(seconds)` / `on_set_end(seconds)` callbacks.
`MainWindow` forwards these to `TrimPanel.set_start()` / `set_end()`.
This decouples VideoPlayer from TrimPanel — VideoPlayer has no import of TrimPanel.

## Known limitations
- Playback may drop frames on slow machines (after() scheduling isn't frame-locked).
- No volume / audio playback (preview is silent — audio is preserved in the export).
- Seeking can be slightly imprecise for variable frame rate videos.
