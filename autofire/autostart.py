from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

APP_NAME = "Autofire"

def _is_windows() -> bool:
    return os.name == "nt"

def get_commandline_for_autostart() -> str:
    # In dev: pythonw.exe -m autofire.gui
    # In packaged exe: sys.executable points to exe, no args needed.
    exe = Path(sys.executable)
    if exe.name.lower().startswith("python"):
        # prefer pythonw if available (no console)
        pyw = exe.with_name("pythonw.exe")
        exe_used = pyw if pyw.exists() else exe
        return f"\"{exe_used}\" -m autofire.gui"
    return f"\"{exe}\""

def is_enabled() -> bool:
    if not _is_windows():
        return False
    try:
        import winreg  # type: ignore
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        try:
            val, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(val)
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False

def set_enabled(enable: bool) -> None:
    if not _is_windows():
        return
    import winreg  # type: ignore
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
    try:
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, get_commandline_for_autostart())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)
