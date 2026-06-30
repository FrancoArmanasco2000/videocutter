# 11 — Frame-by-Frame Navigation + Keyboard Shortcuts

## Status
✅ Complete

## Files
- `src/ui/video_player.py` — botones ‹ ›, métodos step, _bind_keys

## Controls added

| Action | Button | Keyboard |
|---|---|---|
| Frame anterior | ‹ | ← |
| Frame siguiente | › | → |
| Play / Pause | ▶ / ⏸ | Espacio |

Layout de controles actualizado:
```
[⏮] [‹] [▶ Play] [›] [⏭]   [◀ Set Start] [Set End ▶]
```

## Keyboard binding
`winfo_toplevel().bind()` registra los atajos en la ventana raíz.
Se ejecuta via `self.after(200, ...)` para garantizar que el widget
ya esté adjunto al árbol de ventanas antes de llamar a `winfo_toplevel()`.

Guard contra Entry: si el foco está en un campo de texto (URL, Start, End),
los atajos no se activan — `isinstance(event.widget, tk.Entry)` cubre
tanto `tk.Entry` como el widget interno de `ctk.CTkEntry`.

## Step logic
```python
_step_backward → seek(max(0, current_frame - 1))
_step_forward  → seek(min(total_frames - 1, current_frame + 1))
```
Ambos pausan el video antes de buscar el frame.
