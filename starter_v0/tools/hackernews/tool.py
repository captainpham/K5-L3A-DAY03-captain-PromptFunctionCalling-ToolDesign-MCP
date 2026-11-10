from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err

MAX_LIMIT = 20
ENDPOINTS = {
    "relevance": "https://hn.algolia.com/api/v1/search",
    "date": "https://hn.algolia.com/api/v1/search_by_date",
}


def _limit(value: Any, default: int = 5) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(number, MAX_LIMIT)) if number > 0 else default


def search_hackernews(query: str = "", sort: str = "relevance", limit: int = 5) -> dict[str, Any]:
    """Search Hacker News stories through the public Algolia API (no key needed)."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query is required")
        sort = sort if sort in ENDPOINTS else "relevance"
        response = requests.get(
            ENDPOINTS[sort],
            params={"query": query, "tags": "story", "hitsPerPage": _limit(limit)},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = []
        for hit in response.json().get("hits", []):
            story_id = hit.get("objectID")
            if not story_id:
                continue
            discussion = f"https://news.ycombinator.com/item?id={story_id}"
            url = hit.get("url") or discussion
            items.append({
                "title": hit.get("title") or "",
                "url": url,
                "source": domain(url),
                "summary": f"{hit.get('points') or 0} points, {hit.get('num_comments') or 0} comments, by {hit.get('author') or 'unknown'}",
                "discussion_url": discussion,
                "date": hit.get("created_at"),
            })
        return {"tool": "search_hackernews", "query": query, "sort": sort, "items": items}
    except Exception as exc:
        return err("search_hackernews", exc)
