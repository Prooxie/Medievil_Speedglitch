
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

APP_DIR = Path.home() / ".autofire"
PROFILES_DIR = APP_DIR / "profiles"
ACTIVE_FILE = APP_DIR / "active_profile.json"

class ConfigManager:
    def __init__(self):
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    def list_profiles(self):
        return [p.stem for p in PROFILES_DIR.glob("*.json")]

    def save_profile(self, name: str, data: Dict[str, Any]) -> None:
        path = PROFILES_DIR / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_profile(self, name: str) -> Dict[str, Any]:
        path = PROFILES_DIR / f"{name}.json"
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def set_active(self, name: str):
        ACTIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ACTIVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"active": name}, f)

    def get_active(self) -> str | None:
        if not ACTIVE_FILE.exists():
            return None
        with open(ACTIVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("active")
