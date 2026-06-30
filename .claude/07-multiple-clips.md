# 07 — Multiple Clips Export

## Status
✅ Complete

## Files
- `src/ui/clips_panel.py` — clip queue UI (new)
- `src/ui/export_panel.py` — multi-clip export logic
- `src/ui/main_window.py` — added ClipsPanel row, window height → 1020px

## UX flow

```
1. Load video
2. Navigate with scrubber → Set Start → Set End
3. Click "+ Add clip"  →  appears in the queue as #1
4. Repeat for more segments
5. Click "Export"
   ├─ If queue has clips → asks for base name → exports clip_01.mp4, clip_02.mp4 ...
   └─ If queue is empty  → single clip fallback (original behavior)
```

## File naming (multi-clip)
User picks `game.mp4` as base name. Output:
```
game_01.mp4
game_02.mp4
game_03.mp4
```
`os.path.splitext` splits base and extension; `f"{base}_{i+1:02d}{ext}"` builds each path.

## Progress (multi-clip)
Overall progress bar spans 0→1 across all clips:
```python
overall = (clip_index + clip_percent / 100) / total_clips
```
Status label shows "Clip 2/4  67%" during processing.

## Architecture note
ClipsPanel reads from TrimPanel via `get_current_trim` callback — it has no direct
import of TrimPanel. ExportPanel receives `get_clips` callback from MainWindow.
No circular dependencies; MainWindow is the only orchestrator.

## Known limitations
- No reordering of clips in the queue (remove and re-add to change order).
- Clips are not validated against video duration at add time.
- Queue resets if a new video is loaded (intentional — clips belong to one source).
