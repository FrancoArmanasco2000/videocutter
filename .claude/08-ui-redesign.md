# 08 — Professional UI Redesign

## Status
✅ Complete

## Goal
Redesign the entire UI for a professional sports analysis audience (coaches, analysts).
Reference aesthetic: Hudl / Wyscout / sports analytics dashboards.

## Files changed
- `src/ui/theme.py` — new centralized design token system
- `src/ui/main_window.py` — fixed header band, dark root
- `src/ui/loader_panel.py` — styled with section header
- `src/ui/video_player.py` — wider preview (880×495), styled controls
- `src/ui/trim_panel.py` — monospace time inputs
- `src/ui/clips_panel.py` — table layout with alternating rows
- `src/ui/detection_panel.py` — styled switches and sliders
- `src/ui/export_panel.py` — prominent CTA button

## Design system (theme.py)

| Token | Value | Use |
|---|---|---|
| BG_ROOT | #0d1117 | Window background |
| BG_PANEL | #161b22 | Card/panel backgrounds |
| BG_INSET | #010409 | Inputs, canvas |
| BG_ROW | #1c2129 | Alternating table rows |
| BORDER | #30363d | All borders |
| ACCENT | #f97316 | Primary CTA, scrubber, active states |
| SUCCESS | #22c55e | Set Start button |
| DANGER | #ef4444 | Set End button |
| TEXT_PRIMARY | #e6edf3 | Main text |
| TEXT_MUTED | #8b949e | Labels, secondary |
| TEXT_DIM | #484f58 | Section headers, placeholders |

## Key design decisions
- **Section headers** in small all-caps (`TEXT_DIM`) establish clear hierarchy without chrome
- **Monospace font (Courier)** for all time codes — professional, scannable
- **Orange accent** chosen over blue: high contrast on dark, common in sports broadcast branding
- **Preview 880×495** (16:9 at nearly full panel width) — cinematic, fills the space
- **Set Start = green / Set End = red** — universal in video editing tools
- **Fixed header band** at the top — app identity without relying on the OS title bar
