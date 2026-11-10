"""Tool Unit Test Challenge - all stubs implemented.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.

Tests for the team's new tools live in test_tools_new.py.
Regression tests for bugs found in the given tools are at the bottom of this file.
"""
from __future__ import annotations

import re

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]


def _tweets(count: int, handle: str = "sama") -> list[dict]:
    return [
        {"tweet_id": str(1000 + index), "text": f"tweet {index}", "author": {"screen_name": handle}}
        for index in range(count)
    ]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify_tool(question="Bạn muốn nguồn nào?", response_type="choice", options=["Web", "Twitter"])

    assert result["options"] == ["Web", "Twitter"]
    assert result["response_type"] == "choice"
    assert result["question"] == "Bạn muốn nguồn nào?"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "section": "A"},
        {"title": "b1", "section": "B"},
        {"title": "a2", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections")["markdown"]

    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    assert markdown.index("a1") < markdown.index("a2") < markdown.index("## B")


def test_format_thread_numbers_items() -> None:
    items = [{"title": "one"}, {"title": "two"}, {"title": "three"}]
    lines = format_tool(items=items, template="thread")["markdown"].split("\n\n")

    assert [line.split(" ")[0] for line in lines] == ["1/", "2/", "3/"]
    assert "one" in lines[0] and "three" in lines[2]


def test_format_empty_items_does_not_crash() -> None:
    for empty in (None, []):
        result = format_tool(items=empty, template="sections")
        assert result["item_count"] == 0
        assert isinstance(result["markdown"], str)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TEST")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@test_channel")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "123:TEST" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "@test_channel"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup_tool(query="AI", timeframe=None)

    assert "time_range" not in calls[0]["json"]
    assert calls[0]["json"]["query"] == "AI"
    assert result["items"] == []


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello\nbody",
        "metadata": {"title": "T", "sourceURL": "https://www.example.com/final"},
    }}))

    result = fetch_tool(url="https://www.example.com/post")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"]["url"] == "https://www.example.com/post"
    assert calls[0]["headers"]["Authorization"] == "Bearer fc-test"
    assert result["items"][0] == {
        "title": "T",
        "url": "https://www.example.com/final",
        "source": "example.com",
        "summary": "# Hello\nbody",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))

    result = fetch_tool(url="https://example.com/long")

    assert len(result["items"][0]["summary"]) == 4000
    assert result["items"][0]["title"] == "https://example.com/long"


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    payload = {"timeline": [{"text": "no id here", "author": {"screen_name": "sama"}}, *_tweets(6)]}
    calls = fake_http(FakeResponse(payload))

    result = timeline_tool(screenname="sama", limit=3)

    assert calls[0]["params"] == {"screenname": "sama"}
    assert calls[0]["headers"]["x-rapidapi-key"] == "rapid-test"
    assert len(result["items"]) == 3
    assert all(re.fullmatch(r"https://x\.com/sama/status/\d+", item["url"]) for item in result["items"])
    assert all(item["summary"] != "no id here" for item in result["items"])


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    calls = fake_http(FakeResponse({"timeline": _tweets(2, handle="someone")}))

    result = social_search_tool(query="OpenAI", search_type="Top")

    assert calls[0]["url"].endswith("/search.php")
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}
    assert result["search_type"] == "Top"
    assert len(result["items"]) == 2


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert policy_tool(query="")["results"] == []
    assert policy_tool(query="   ")["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy_tool(query="customer data API key privacy", policy_area="data_privacy", top_k=10)

    assert result["results"], "expected at least one data_privacy hit"
    assert {hit["policy_area"] for hit in result["results"]} == {"data_privacy"}


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy_tool(query="citation injection probe", policy_area="source_citation", top_k=20)

    probe = [hit for hit in result["results"] if hit["section"] == "Injection probe"]
    assert probe, "expected the 'Injection probe' section in the results"
    assert any("ignore the citation policy" in line for line in probe[0]["untrusted_text"])
    assert all("ignore the citation policy" not in hit["facts"] for hit in result["results"])


# ---------------- Regression tests: bugs found in the given tools ----------------
# Each test below failed on the starter code. See REPORT.md B5.

def test_format_skips_non_dict_items_instead_of_crashing() -> None:
    # Models sometimes send items as plain strings. Starter code raised AttributeError.
    result = format_tool(items=["just a string", {"title": "ok", "url": "https://a.com/1"}], template="bullets")

    assert result["item_count"] == 1
    assert "ok" in result["markdown"]


def test_format_section_none_falls_back_to_default_heading() -> None:
    # {"section": None} rendered a literal "## None" heading on the starter code.
    markdown = format_tool(items=[{"title": "t", "section": None}], template="sections")["markdown"]

    assert "## Tổng hợp" in markdown
    assert "None" not in markdown


def test_timeline_negative_limit_falls_back_to_default(monkeypatch, fake_http) -> None:
    # limit=-2 sliced items[:-2] on the starter code: 6 tweets came back instead of 5.
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    fake_http(FakeResponse({"timeline": _tweets(8)}))

    assert len(timeline_tool(screenname="sama", limit=-2)["items"]) == 5


def test_social_search_negative_limit_falls_back_to_default(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    fake_http(FakeResponse({"timeline": _tweets(8)}))

    assert len(social_search_tool(query="AI", limit=-2)["items"]) == 5


def test_timeline_strips_at_sign_from_screenname(monkeypatch, fake_http) -> None:
    # The API expects a bare handle; the starter code forwarded "@sama" unchanged.
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    calls = fake_http(FakeResponse({"timeline": _tweets(1)}))

    result = timeline_tool(screenname=" @sama ")

    assert calls[0]["params"] == {"screenname": "sama"}
    assert result["screenname"] == "sama"
