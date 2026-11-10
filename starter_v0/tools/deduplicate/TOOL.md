---
name: deduplicate
track: core
kind: local_formatter
provider: local
requires_env: []
inputs: [items]
outputs: [items, item_count, removed_count, warnings]
side_effect: false
---
# deduplicate

Remove duplicate URLs from already-collected research items before formatting a
digest. Keep the first occurrence, its metadata, and the original item order.
This tool does not fetch sources, compare article text, or merge metadata.

Only surrounding URL whitespace is ignored for comparison. Path case, query
parameters, fragments, and trailing slashes remain significant. Missing, null,
or blank URLs are preserved as separate items: there is insufficient evidence
that these items refer to the same source. Original URL values are preserved.
When any input item has no nonempty URL, the result includes `warnings` with
code `missing_url` and its zero-based input `item_indices`. Otherwise this
optional field is omitted. Missing URLs do not fail the request.

Omitted or null `items` returns an empty result. Invalid item containers, item
types, and non-string/non-null URLs return an error dictionary without raising.
The input list and item dictionaries are not modified. No API key is required.
