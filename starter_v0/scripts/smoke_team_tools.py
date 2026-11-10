"""Check the integrated tools against real services and a real local file.

Run from starter_v0: uv run python scripts/smoke_team_tools.py
No model calls or Telegram sends. Public API requests may consume rate limits.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from tools import TOOL_FUNCTIONS


def main() -> None:
    load_lab_env(ROOT)
    checks = []
    requests = [
        ("hackernews", {"query": "AI agents", "sort": "date", "limit": 2}),
        ("wikipedia", {"query": "Python (programming language)", "lang": "en", "limit": 1}),
        ("github_repos", {"query": "llm agent framework", "sort": "stars", "limit": 2}),
        ("save_note", {"title": "Captain live tool check", "content": "Live verification of integrated tools."}),
    ]
    for name, arguments in requests:
        print(f"Checking {name}...", flush=True)
        result = TOOL_FUNCTIONS[name](**arguments)
        passed = not result.get("error")
        if name == "save_note":
            path = Path(result.get("path") or "missing-note")
            passed = passed and result.get("status") == "saved" and path.is_file()
            if passed:
                passed = path.read_text(encoding="utf-8") == "# Captain live tool check\n\nLive verification of integrated tools.\n"
        else:
            items = result.get("items", [])
            passed = passed and 0 < len(items) <= arguments["limit"] and all(item.get("url") for item in items)
        checks.append({"tool": name, "args": arguments, "passed": bool(passed), "result": result})
        print(f"{name}: {'PASS' if passed else 'FAIL'}", flush=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / "analysis" / f"live_tools_{timestamp}.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {output}")
    if not all(item["passed"] for item in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
