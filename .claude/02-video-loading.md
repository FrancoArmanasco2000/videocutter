# 02 — Video Loading (URL + local file)

## Status
✅ Complete

## Files
- `src/ui/loader_panel.py` — UI component
- `src/services/downloader.py` — yt-dlp service

## How it works

### Local file
1. User clicks **Browse** → `filedialog.askopenfilename` opens native OS picker.
2. Path is inserted into the entry field.
3. User clicks **Load** → path is passed directly to `on_loaded` callback.

### URL
1. User pastes a URL and clicks **Load**.
2. `LoaderPanel._load()` detects `http://` / `https://` prefix.
3. Spawns a `daemon` thread calling `Downloader.download()`.
4. `Downloader` creates a `tempfile.mkdtemp` folder and calls `yt_dlp.YoutubeDL`.
5. Progress hook updates the UI label via `widget.after(0, ...)`.
6. On success, the downloaded file path is returned and passed to `on_loaded`.

## yt-dlp format strategy
```
bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best
```
- Prefers MP4 container so downstream ffmpeg processing is seamless.
- Falls back to `best` single-stream if separate video+audio tracks aren't available.

## Edge cases handled
- yt-dlp may merge tracks and change the file extension; the downloader checks for `.mp4`, `.mkv`, `.webm` variants if the primary filename isn't found.
- Empty source field shows an error without attempting a download.

## Known limitations
- No download cancellation (thread runs to completion).
- Temp files are not cleaned up automatically (OS handles on reboot).
