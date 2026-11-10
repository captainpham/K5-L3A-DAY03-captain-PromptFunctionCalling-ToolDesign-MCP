from copy import deepcopy

import pytest

from tools import TOOL_FUNCTIONS


deduplicate = TOOL_FUNCTIONS["deduplicate"]


def test_removes_duplicate_urls_preserving_first_metadata_and_order():
    items = [
        {"title": "First", "url": "https://example.com/a", "summary": "Original"},
        {"title": "Second", "url": "https://example.com/b"},
        {"title": "Repeated", "url": " https://example.com/a "},
    ]
    before = deepcopy(items)
    result = deduplicate(items)
    assert result == {"tool": "deduplicate", "items": items[:2], "item_count": 2, "removed_count": 1}
    assert items == before
    result["items"][0]["title"] = "Changed"
    assert items == before


@pytest.mark.parametrize("items", [None, []])
def test_empty_input_returns_empty_result(items):
    assert deduplicate(items) == {"tool": "deduplicate", "items": [], "item_count": 0, "removed_count": 0}


def test_missing_or_blank_urls_are_not_collapsed():
    items = [{"title": "A"}, {"title": "B"}, {"url": " "}, {"url": None}, {"url": ""}]
    result = deduplicate(items)
    assert result["items"] == items
    assert result["removed_count"] == 0
    assert result["warnings"][0]["code"] == "missing_url"
    assert result["warnings"][0]["item_indices"] == [0, 1, 2, 3, 4]


def test_distinct_paths_and_query_parameters_remain_distinct():
    urls = ["https://example.com/A", "https://example.com/a", "https://example.com/a?x=1", "https://example.com/a?x=2"]
    result = deduplicate([{"url": url} for url in urls])
    assert [item["url"] for item in result["items"]] == urls
    assert result["removed_count"] == 0


@pytest.mark.parametrize("items, message", [
    ("", "items must be a list"),
    ({"url": "https://example.com"}, "items must be a list"),
    (["bad item"], "items[0] must be an object"),
    ([{"url": 123}], "items[0].url must be a string or null"),
])
def test_invalid_input_returns_error_dictionary(items, message):
    result = deduplicate(items)
    assert result["tool"] == "deduplicate"
    assert result["error"] == "ValueError"
    assert message in result["message"]
    assert "items" not in result


def test_whitespace_url_comparison_preserves_original_first_url():
    # Adapted from tranminhnhat's deduplicate_sources test contract.
    first = {"url": " https://example.com/a ", "summary": "Keep this"}
    result = deduplicate([first, {"url": "https://example.com/a"}])
    assert result["items"] == [first]
    assert result["removed_count"] == 1
    assert "warnings" not in result


@pytest.mark.parametrize("items", ["sources", {}, 5])
def test_invalid_containers_return_error_without_mutation(items):
    # Ported from tranminhnhat; use captain's error dictionary convention.
    before = deepcopy(items)
    result = deduplicate(items)
    assert result["error"] == "ValueError"
    assert items == before


def test_missing_url_warning_uses_original_input_indices_after_removals():
    result = deduplicate([
        {"url": "https://example.com/a"},
        {"url": "https://example.com/a"},
        {"title": "Unknown source"},
    ])
    assert result["item_count"] == 2
    assert result["warnings"][0]["item_indices"] == [2]
