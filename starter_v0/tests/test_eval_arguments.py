"""Regression coverage for evaluating tools accepting source item arrays."""
from run_eval import compare_subset


def test_source_item_arrays_compare_without_sorting_dicts():
    items = [{"url": "https://example.com/b"}, {"url": "https://example.com/a"}]
    assert compare_subset({"items": items}, {"items": items}) == (True, [], 1, 1)


def test_source_item_arrays_preserve_order_and_duplicates():
    items = [{"url": "https://example.com/a"}, {"url": "https://example.com/b"},
             {"url": "https://example.com/a"}]
    assert not compare_subset({"items": items}, {"items": list(reversed(items[:2]))})[0]
    assert not compare_subset({"items": items}, {"items": items[:2]})[0]


def test_scalar_lists_keep_existing_case_insensitive_unordered_comparison():
    assert compare_subset({"tags": ["AI", "news"]}, {"tags": ["NEWS", "ai"]})[0]
