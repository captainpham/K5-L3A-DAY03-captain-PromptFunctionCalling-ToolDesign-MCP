from __future__ import annotations

from typing import Any


def deduplicate_items(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Keep the first item for each exact, whitespace-trimmed nonempty URL."""
    if items is None:
        items = []
    if not isinstance(items, list):
        return {"tool": "deduplicate", "error": "ValueError", "message": "items must be a list of objects"}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return {"tool": "deduplicate", "error": "ValueError", "message": f"items[{index}] must be an object"}
        if item.get("url") is not None and not isinstance(item["url"], str):
            return {"tool": "deduplicate", "error": "ValueError", "message": f"items[{index}].url must be a string or null"}

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    missing_url_indices: list[int] = []
    for index, item in enumerate(items):
        url = (item.get("url") or "").strip()
        if not url:
            missing_url_indices.append(index)
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        unique.append(dict(item))
    result = {
        "tool": "deduplicate",
        "items": unique,
        "item_count": len(unique),
        "removed_count": len(items) - len(unique),
    }
    if missing_url_indices:
        result["warnings"] = [{
            "code": "missing_url",
            "item_indices": missing_url_indices,
            "message": "Items without a nonempty URL were preserved separately; duplicates cannot be determined for them.",
        }]
    return result
