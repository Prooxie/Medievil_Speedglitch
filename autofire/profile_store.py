from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import AutofireConfig

APP_DIR = Path.home() / ".autofire"
PROFILES_DIR = APP_DIR / "profiles"
SETTINGS_FILE = APP_DIR / "settings.json"
ACTIVE_FILE = APP_DIR / "active_profile.json"

DEFAULT_PROFILE_NAME = "default"


class ProfileStore:
    """Human-editable JSON profiles + app settings.

    Profiles contain ONLY AutofireConfig fields.
    App settings are separate (theme, autostart, start_minimized, update urls).
    """

    def __init__(self) -> None:
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        APP_DIR.mkdir(parents=True, exist_ok=True)
        if not self.list_profiles():
            self.save_profile(DEFAULT_PROFILE_NAME, AutofireConfig())
            self.set_active_profile(DEFAULT_PROFILE_NAME)

    # ---------- Profiles ----------
    def list_profiles(self) -> List[str]:
        return sorted([p.stem for p in PROFILES_DIR.glob("*.json")])

    def profile_path(self, name: str) -> Path:
        return PROFILES_DIR / f"{name}.json"

    def load_profile_dict(self, name: str) -> Dict[str, Any]:
        p = self.profile_path(name)
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def load_profile(self, name: str) -> AutofireConfig:
        d = self.load_profile_dict(name)
        if not d:
            return AutofireConfig()
        # allow forward-compat by filtering keys
        allowed = set(asdict(AutofireConfig()).keys())
        filtered = {k: v for k, v in d.items() if k in allowed}
        return AutofireConfig(**filtered)

    def save_profile(self, name: str, cfg: AutofireConfig) -> None:
        p = self.profile_path(name)
        p.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")

    def delete_profile(self, name: str) -> None:
        p = self.profile_path(name)
        if p.exists():
            p.unlink()

    def get_active_profile(self) -> Optional[str]:
        if not ACTIVE_FILE.exists():
            return None
        try:
            return json.loads(ACTIVE_FILE.read_text(encoding="utf-8")).get("active")
        except Exception:
            return None

    def set_active_profile(self, name: str) -> None:
        ACTIVE_FILE.write_text(json.dumps({"active": name}, indent=2), encoding="utf-8")

    # ---------- App settings ----------
    def load_settings(self) -> Dict[str, Any]:
        if not SETTINGS_FILE.exists():
            return {}
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save_settings(self, settings: Dict[str, Any]) -> None:
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
