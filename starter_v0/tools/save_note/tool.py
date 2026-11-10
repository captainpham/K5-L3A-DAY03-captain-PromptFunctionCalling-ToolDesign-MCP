from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from tools._shared import ROOT, err, fold_text

NOTES_DIR = ROOT / "notes"
MAX_CHARS = 20000


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", fold_text(value)).strip("-")
    return slug[:60] or "note"


def save_note(content: str = "", title: str = "") -> dict[str, Any]:
    """Write a markdown note to the local notes/ folder. Never leaves the machine."""
    try:
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content is required")
        if len(content) > MAX_CHARS:
            raise ValueError(f"content is too long ({len(content)} chars, max {MAX_CHARS})")
        title = title.strip() if isinstance(title, str) else ""
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        path = NOTES_DIR / f"{stamp}_{_slug(title)}.md"
        body = (f"# {title}\n\n" if title else "") + content.strip() + "\n"
        path.write_text(body, encoding="utf-8")
        return {"tool": "save_note", "status": "saved", "path": str(path), "chars": len(body)}
    except Exception as exc:
        return err("save_note", exc)
