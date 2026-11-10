from run_eval import compare_subset


def test_item_dictionary_arrays_compare_without_sorting_error():
    expected = {"items": [{"title": "A", "url": "https://example.com/a"}, {"title": "B"}]}
    actual = {"items": [{"title": "B"}, {"url": "https://example.com/a", "title": "A"}]}
    assert compare_subset(expected, actual) == (True, [], 1, 1)


def test_item_comparison_still_detects_missing_duplicate_input():
    item = {"title": "A", "url": "https://example.com/a"}
    passed, failures, correct, total = compare_subset({"items": [item, item]}, {"items": [item]})
    assert not passed
    assert failures
    assert (correct, total) == (0, 1)


def test_item_comparison_detects_changed_url():
    passed, failures, _, _ = compare_subset(
        {"items": [{"url": "https://example.com/a"}]},
        {"items": [{"url": "https://example.com/b"}]},
    )
    assert not passed
    assert failures
