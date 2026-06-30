# 01 — Project Setup & Architecture

## Status
✅ Complete

## Goal
Bootstrap a cross-platform (Windows / macOS) desktop video cutter app.

## Stack decisions

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Best ecosystem for video processing; cross-platform |
| GUI | CustomTkinter 5.x | Modern look, no external C deps, simpler than PyQt |
| Video download | yt-dlp | Supports 1 000+ sites, actively maintained |
| Video cutting | ffmpeg-python | Wraps ffmpeg; `c=copy` does lossless stream copy |
| Packaging | PyInstaller (future) | Produces `.exe` / `.app` bundles |

## Directory structure

```
video-cutter/
├── .claude/                  # Audit docs (this folder)
├── src/
│   ├── main.py               # Entry point — sets CTk theme, starts MainWindow
│   ├── ui/
│   │   ├── main_window.py    # Root window, owns layout and video state
│   │   ├── loader_panel.py   # URL input + file browse + download trigger
│   │   ├── trim_panel.py     # Start/End time inputs + duration display
│   │   └── export_panel.py   # Progress bar + Export button
│   └── services/
│       ├── downloader.py     # yt-dlp wrapper (runs in thread)
│       └── cutter.py         # ffmpeg-python wrapper (stream copy)
└── requirements.txt
```

## Architecture notes

- **Threading**: downloads and exports run in `daemon` threads to keep the UI responsive. Results are sent back via `widget.after(0, callback)` — the only safe way to update Tkinter from a background thread.
- **State ownership**: `MainWindow` owns the loaded video path and passes it down to `TrimPanel` and `ExportPanel` via callbacks / setter methods. No global state.
- **`c=copy` (stream copy)**: ffmpeg cuts without re-encoding. This means cuts are nearly instant and lossless, but the cut point must be near a keyframe. For frame-accurate cuts, re-encoding would be needed (future enhancement).

## Known limitations (v1)
- No video preview / thumbnail
- Trim is time-based only (no visual timeline scrubber)
- Single clip export per session
