---
name: github_repos
track: bonus
kind: live_api
provider: GitHub REST API
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# github_repos

Searches public GitHub repositories (`/search/repositories`). Works without a
key (about 10 requests/minute); setting the optional `GITHUB_TOKEN` env var
raises the rate limit. `sort` is `stars` or `updated` (anything else falls
back to `stars`); `limit` is clamped to 1..20. An empty query returns an
error dict without calling the network.
