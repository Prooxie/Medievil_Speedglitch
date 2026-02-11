from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class UpdateInfo:
    latest_version: str
    download_url: str
    notes: str = ""

def fetch_latest_github_release(owner: str, repo: str, timeout_s: float = 3.0) -> Optional[UpdateInfo]:
    # Uses GitHub releases API (no extra deps). Returns None if offline / blocked.
    api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        req = urllib.request.Request(api, headers={"User-Agent": "Autofire"})
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            data = json.loads(r.read().decode("utf-8", errors="replace"))
        tag = str(data.get("tag_name") or "").lstrip("v")
        html = str(data.get("html_url") or "")
        body = str(data.get("body") or "")
        if not tag or not html:
            return None
        return UpdateInfo(latest_version=tag, download_url=html, notes=body[:800])
    except Exception:
        return None
