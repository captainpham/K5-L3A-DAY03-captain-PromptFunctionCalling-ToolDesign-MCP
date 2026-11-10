---
name: hackernews
track: bonus
kind: live_api
provider: Hacker News (Algolia)
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# hackernews

Searches Hacker News stories through the public Algolia API
(`hn.algolia.com`). No API key. `sort=relevance` ranks by match,
`sort=date` returns the newest stories first. `limit` is clamped to 1..20;
an out-of-enum `sort` falls back to `relevance`. An empty query returns an
error dict without calling the network.
