---
name: deduplicate_sources
track: core
kind: local_formatter
provider: none
requires_env: []
inputs: [items]
outputs: [items, removed_count, error]
side_effect: false
---

# deduplicate_sources

Remove duplicate URLs from source items already provided by the user or tools.
Use when asked to remove duplicate sources; do not use to search or fetch URLs.

Compare URLs as exact, case-sensitive strings after trimming surrounding
whitespace. Keep the first item and original order, preserving its metadata.
Do not equate URLs differing in query parameters, fragments, or trailing slashes.
The input is not modified and the tool performs no network or file operations.

Every item must be an object with a nonempty string `url`. Missing input,
non-list input, non-object items, and invalid URLs return an `error` dict.
An empty list returns `items: []` and `removed_count: 0`.
