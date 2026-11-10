"""Unit tests for the team's new tools: hackernews, wikipedia, github_repos, save_note.

Per tool: happy path (mocked HTTP), bad input from the model, failure path -> error dict.
"""
from __future__ import annotations

import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
from tools.save_note import tool as save_note_module

hackernews_tool = TOOL_FUNCTIONS["hackernews"]
wikipedia_tool = TOOL_FUNCTIONS["wikipedia"]
github_tool = TOOL_FUNCTIONS["github_repos"]
save_note_tool = TOOL_FUNCTIONS["save_note"]


# ---------------- hackernews ----------------

HN_PAYLOAD = {"hits": [
    {"objectID": "101", "title": "Show HN: Agent", "url": "https://www.example.com/agent",
     "points": 120, "num_comments": 45, "author": "pg", "created_at": "2026-01-01T00:00:00Z"},
    {"objectID": "102", "title": "Ask HN: no link", "url": None, "points": None, "num_comments": None, "author": None},
    {"title": "hit without id"},
]}


def test_hackernews_sends_query_and_maps_hits(fake_http) -> None:
    calls = fake_http(FakeResponse(HN_PAYLOAD))

    result = hackernews_tool(query="AI agents", limit=3)

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"query": "AI agents", "tags": "story", "hitsPerPage": 3}
    assert len(result["items"]) == 2  # the hit without objectID is skipped
    assert result["items"][0]["title"] == "Show HN: Agent"
    assert result["items"][0]["source"] == "example.com"
    assert result["items"][0]["summary"] == "120 points, 45 comments, by pg"
    assert result["items"][0]["discussion_url"] == "https://news.ycombinator.com/item?id=101"


def test_hackernews_story_without_url_links_to_discussion(fake_http) -> None:
    fake_http(FakeResponse(HN_PAYLOAD))

    item = hackernews_tool(query="AI")["items"][1]

    assert item["url"] == "https://news.ycombinator.com/item?id=102"
    assert item["summary"] == "0 points, 0 comments, by unknown"


def test_hackernews_sort_date_uses_search_by_date_endpoint(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))

    hackernews_tool(query="AI", sort="date")

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"


def test_hackernews_bad_sort_and_limit_fall_back_to_safe_values(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))

    result = hackernews_tool(query="AI", sort="hottest", limit="abc")
    hackernews_tool(query="AI", limit=0)
    hackernews_tool(query="AI", limit=999)
    hackernews_tool(query="AI", limit="7")

    assert result["sort"] == "relevance"
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert [call["params"]["hitsPerPage"] for call in calls] == [5, 5, 20, 7]


def test_hackernews_empty_query_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))

    result = hackernews_tool(query="   ")

    assert result["error"] == "ValueError"
    assert calls == []


def test_hackernews_http_error_and_timeout_return_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    assert hackernews_tool(query="AI")["error"] == "HTTPError"

    fake_http(requests.Timeout("timed out"))
    assert hackernews_tool(query="AI")["error"] == "Timeout"


# ---------------- wikipedia ----------------

WIKI_PAYLOAD = {"query": {"pages": {
    "20": {"index": 2, "title": "Second", "extract": "second extract", "fullurl": "https://vi.wikipedia.org/wiki/Second"},
    "10": {"index": 1, "title": "First", "extract": "  first extract  ", "fullurl": "https://vi.wikipedia.org/wiki/First"},
}}}


def test_wikipedia_sends_search_request_and_orders_by_rank(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_PAYLOAD))

    result = wikipedia_tool(query="Transformer", lang="vi", limit=2)

    assert calls[0]["url"] == "https://vi.wikipedia.org/w/api.php"
    assert calls[0]["params"]["gsrsearch"] == "Transformer"
    assert calls[0]["params"]["gsrlimit"] == 2
    assert "User-Agent" in calls[0]["headers"]
    assert [item["title"] for item in result["items"]] == ["First", "Second"]
    assert result["items"][0] == {
        "title": "First", "url": "https://vi.wikipedia.org/wiki/First",
        "source": "vi.wikipedia.org", "summary": "first extract",
    }


def test_wikipedia_lang_en_uses_english_host(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_PAYLOAD))

    result = wikipedia_tool(query="Transformer", lang="en")

    assert calls[0]["url"] == "https://en.wikipedia.org/w/api.php"
    assert result["items"][0]["source"] == "en.wikipedia.org"


def test_wikipedia_unknown_lang_falls_back_to_vi(fake_http) -> None:
    # An out-of-enum lang must not be interpolated into the host name.
    calls = fake_http(FakeResponse(WIKI_PAYLOAD))

    result = wikipedia_tool(query="Transformer", lang="evil.example.com/x")

    assert calls[0]["url"] == "https://vi.wikipedia.org/w/api.php"
    assert result["lang"] == "vi"


def test_wikipedia_truncates_long_extract(fake_http) -> None:
    fake_http(FakeResponse({"query": {"pages": {"1": {"index": 1, "title": "Long", "extract": "y" * 3000}}}}))

    assert len(wikipedia_tool(query="Long")["items"][0]["summary"]) == 1500


def test_wikipedia_no_match_returns_empty_items(fake_http) -> None:
    fake_http(FakeResponse({"batchcomplete": ""}))

    assert wikipedia_tool(query="zzzzqqqq")["items"] == []


def test_wikipedia_empty_query_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse(WIKI_PAYLOAD))

    assert wikipedia_tool(query="")["error"] == "ValueError"
    assert calls == []


def test_wikipedia_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))

    assert wikipedia_tool(query="Transformer")["error"] == "HTTPError"


# ---------------- github_repos ----------------

GH_PAYLOAD = {"items": [
    {"full_name": "org/agent", "html_url": "https://github.com/org/agent", "description": " An agent framework ",
     "stargazers_count": 4200, "language": "Python", "updated_at": "2026-01-02T00:00:00Z"},
    {"full_name": "org/nodesc", "html_url": "https://github.com/org/nodesc", "description": None},
    {"full_name": "org/nourl"},
]}


def test_github_repos_sends_query_and_maps_repos(monkeypatch, fake_http) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = fake_http(FakeResponse(GH_PAYLOAD))

    result = github_tool(query="llm agent", sort="updated", limit=2)

    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"] == {"q": "llm agent", "sort": "updated", "order": "desc", "per_page": 2}
    assert "Authorization" not in calls[0]["headers"]
    assert len(result["items"]) == 2  # the repo without html_url is skipped
    assert result["items"][0] == {
        "title": "org/agent", "url": "https://github.com/org/agent", "source": "github.com",
        "summary": "An agent framework", "stars": 4200, "language": "Python", "date": "2026-01-02T00:00:00Z",
    }
    assert result["items"][1]["summary"] == ""


def test_github_repos_sends_token_only_when_env_is_set(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    calls = fake_http(FakeResponse({"items": []}))

    github_tool(query="llm")

    assert calls[0]["headers"]["Authorization"] == "Bearer ghp_test"


def test_github_repos_bad_sort_and_limit_fall_back_to_safe_values(monkeypatch, fake_http) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = fake_http(FakeResponse({"items": []}))

    result = github_tool(query="llm", sort="forks", limit=-3)
    github_tool(query="llm", limit=500)

    assert result["sort"] == "stars"
    assert calls[0]["params"]["sort"] == "stars"
    assert [call["params"]["per_page"] for call in calls] == [5, 20]


def test_github_repos_empty_query_returns_error_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({"items": []}))

    assert github_tool(query=None)["error"] == "ValueError"
    assert calls == []


def test_github_repos_rate_limit_returns_error_dict(monkeypatch, fake_http) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    fake_http(FakeResponse(status_code=403))

    assert github_tool(query="llm")["error"] == "HTTPError"


# ---------------- save_note ----------------

def test_save_note_writes_markdown_file_with_title(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(save_note_module, "NOTES_DIR", tmp_path / "notes")

    result = save_note_tool(content="- tin 1\n- tin 2", title="Bản tin AI hôm nay")

    files = list((tmp_path / "notes").glob("*.md"))
    assert result["status"] == "saved"
    assert len(files) == 1
    assert str(files[0]) == result["path"]
    assert files[0].name.endswith("_ban-tin-ai-hom-nay.md")
    assert files[0].read_text(encoding="utf-8") == "# Bản tin AI hôm nay\n\n- tin 1\n- tin 2\n"


def test_save_note_does_not_call_network(monkeypatch, tmp_path, fake_http) -> None:
    monkeypatch.setattr(save_note_module, "NOTES_DIR", tmp_path / "notes")
    calls = fake_http(FakeResponse({}))

    save_note_tool(content="local only")

    assert calls == []


def test_save_note_empty_or_non_string_content_writes_nothing(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(save_note_module, "NOTES_DIR", tmp_path / "notes")

    for bad in ("", "   ", None, ["a", "b"]):
        assert save_note_tool(content=bad)["error"] == "ValueError"
    assert not (tmp_path / "notes").exists()


def test_save_note_title_cannot_escape_notes_folder(monkeypatch, tmp_path) -> None:
    notes_dir = tmp_path / "notes"
    monkeypatch.setattr(save_note_module, "NOTES_DIR", notes_dir)

    result = save_note_tool(content="x", title="../../etc/passwd")

    files = list(tmp_path.rglob("*.md"))
    assert result["status"] == "saved"
    assert len(files) == 1
    assert files[0].parent == notes_dir


def test_save_note_too_long_content_returns_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(save_note_module, "NOTES_DIR", tmp_path / "notes")

    result = save_note_tool(content="x" * 20001)

    assert result["error"] == "ValueError"
    assert not (tmp_path / "notes").exists()


def test_save_note_unwritable_folder_returns_error_dict(monkeypatch, tmp_path) -> None:
    blocker = tmp_path / "notes"
    blocker.write_text("i am a file, not a folder", encoding="utf-8")
    monkeypatch.setattr(save_note_module, "NOTES_DIR", blocker)

    result = save_note_tool(content="x")

    assert "error" in result
    assert "status" not in result
