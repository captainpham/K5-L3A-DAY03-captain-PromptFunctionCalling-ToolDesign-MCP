from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

MAX_LIMIT = 5
LANGS = {"vi", "en"}
USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab)"


def _limit(value: Any, default: int = 1) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(number, MAX_LIMIT)) if number > 0 else default


def wikipedia_summary(query: str = "", lang: str = "vi", limit: int = 1) -> dict[str, Any]:
    """Return the intro paragraph of the best-matching Wikipedia article(s)."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query is required")
        lang = lang if lang in LANGS else "vi"
        response = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query", "format": "json",
                "generator": "search", "gsrsearch": query, "gsrlimit": _limit(limit),
                "prop": "extracts|info", "exintro": 1, "explaintext": 1, "exlimit": "max", "inprop": "url",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages") or {}
        ordered = sorted(pages.values(), key=lambda page: page.get("index", 0))
        items = [{
            "title": page.get("title") or "",
            "url": page.get("fullurl") or "",
            "source": f"{lang}.wikipedia.org",
            "summary": (page.get("extract") or "").strip()[:1500],
        } for page in ordered]
        return {"tool": "wikipedia_summary", "query": query, "lang": lang, "items": items}
    except Exception as exc:
        return err("wikipedia_summary", exc)
