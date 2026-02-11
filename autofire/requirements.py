from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class RequirementStatus:
    ok: bool
    title: str
    detail: str

def check_import(module_name: str, title: str) -> RequirementStatus:
    try:
        importlib.import_module(module_name)
        return RequirementStatus(True, title, "OK")
    except Exception as e:
        return RequirementStatus(False, title, f"Missing or broken: {module_name} ({e})")

def check_vigem_runtime() -> RequirementStatus:
    # vgamepad is optional; if installed, test whether ViGEmBus is available
    try:
        import vgamepad as vg  # type: ignore
    except Exception:
        return RequirementStatus(True, "ViGEmBus / vgamepad", "Not installed (optional)")
    try:
        vg.VX360Gamepad()
        return RequirementStatus(True, "ViGEmBus / vgamepad", "OK")
    except Exception as e:
        return RequirementStatus(False, "ViGEmBus / vgamepad", f"Installed but not working: {e}")

def check_all() -> List[RequirementStatus]:
    out: List[RequirementStatus] = []
    out.append(check_import("PySide6", "PySide6"))
    out.append(check_import("pygame", "pygame"))
    out.append(check_import("pynput", "pynput"))
    out.append(check_vigem_runtime())
    return out
