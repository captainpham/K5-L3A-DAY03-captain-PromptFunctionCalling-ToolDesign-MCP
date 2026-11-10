"""Remove exact duplicate source URLs without fetching any remote content."""
from __future__ import annotations

from typing import Any


def deduplicate_sources(items: Any = None) -> dict[str, Any]:
    if not isinstance(items, list):
        return {"error": "items_must_be_a_list"}
    for item in items:
        if not isinstance(item, dict):
            return {"error": "each_item_must_be_an_object"}
        url = item.get("url")
        if not isinstance(url, str) or not url.strip():
            return {"error": "each_item_requires_a_nonempty_url"}

    unique_items = []
    seen: set[str] = set()
    for item in items:
        url = item["url"].strip()
        if url not in seen:
            seen.add(url)
            unique_items.append(dict(item))
    return {"items": unique_items, "removed_count": len(items) - len(unique_items)}
