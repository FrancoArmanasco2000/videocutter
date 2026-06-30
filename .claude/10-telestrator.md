# 10 — Telestrator (Live Drawing Overlay)

## Status
✅ Complete

## Files
- `src/ui/video_player.py` — drawing toolbar + canvas bindings + render fix

## Behavior
- Video **paused** → drawing is active. Coach draws on the frozen frame.
- Video **plays** → drawings are cleared automatically.
- Drawings are **never exported** — they're only for live presentation.

## Tools
| Tool | Canvas primitive |
|---|---|
| Pen | `create_line` segments on drag (capstyle=ROUND) |
| Arrow | `create_line` with `arrow=LAST`, arrowshape=(14,18,6) |
| Circle | `create_oval` with outline only |
| Rect | `create_rectangle` with outline only |

## Colors
White / Red / Blue / Yellow / Green — chosen for visibility on both light and dark video.
Active color shown with white border ring on the color button.

## Key technical fix — itemconfig instead of create_image
Previous `_render()` called `canvas.create_image()` on every frame, which stacked
new image items on top of drawing items. Fixed by storing `self._video_item_id`
and using `canvas.itemconfig(id, image=photo)` + `canvas.tag_lower(id)` to always
keep the video frame below the drawing layer.

## Drawing item lifecycle
All drawing primitives are tagged `"drawing"`.
`canvas.delete("drawing")` removes them all at once.
Triggered by: play button, load new video.

## Known limitations
- No undo — Clear removes all drawings at once.
- Line width is fixed at 3px (no thickness slider).
- No text annotation tool yet.
