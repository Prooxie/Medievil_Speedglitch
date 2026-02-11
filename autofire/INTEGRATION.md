# Autofire GUI - Full features bundle

Includes:
- Tray icon (custom icon.png)
- Full profile UI (new/save/delete/switch)
- Options:
  - Start minimized to tray (saved)
  - Auto-start with Windows (HKCU Run key)
  - Dark theme toggle (saved)
- Startup checks:
  - dependency/driver sanity checks (best-effort)
  - optional GitHub release check (best-effort; may be blocked offline)

Files written to:
- Profiles: ~/.autofire/profiles/*.json
- Active profile: ~/.autofire/active_profile.json
- App settings: ~/.autofire/settings.json

Install:
1) Copy these files into your autofire/ package (overwrite gui.py; add new modules).
2) pip install PySide6 pygame pynput
3) python -m autofire.gui
