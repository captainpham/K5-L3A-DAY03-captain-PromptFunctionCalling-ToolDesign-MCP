---
name: wikipedia
track: bonus
kind: live_api
provider: Wikipedia (MediaWiki API)
requires_env: []
inputs: [query, lang, limit]
outputs: [items]
side_effect: false
---
# wikipedia

Looks up the intro paragraph of the best-matching Wikipedia article(s) for a
concept, person, or organisation. No API key. `lang` is `vi` or `en`
(anything else falls back to `vi`); `limit` is clamped to 1..5; each summary
is cut to 1500 chars. Background knowledge only — not for today's news. An
empty query returns an error dict without calling the network.
