from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err

MAX_LIMIT = 20
SORTS = {"stars", "updated"}


def _limit(value: Any, default: int = 5) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(number, MAX_LIMIT)) if number > 0 else default


def search_github_repos(query: str = "", sort: str = "stars", limit: int = 5) -> dict[str, Any]:
    """Search public GitHub repositories. Works without a key; GITHUB_TOKEN raises the rate limit."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query is required")
        sort = sort if sort in SORTS else "stars"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "AI20k-Day03-Research-Agent"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": sort, "order": "desc", "per_page": _limit(limit)},
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = [{
            "title": repo.get("full_name") or "",
            "url": repo.get("html_url") or "",
            "source": "github.com",
            "summary": (repo.get("description") or "").strip(),
            "stars": repo.get("stargazers_count"),
            "language": repo.get("language"),
            "date": repo.get("updated_at"),
        } for repo in response.json().get("items", []) if repo.get("html_url")]
        return {"tool": "search_github_repos", "query": query, "sort": sort, "items": items}
    except Exception as exc:
        return err("search_github_repos", exc)
