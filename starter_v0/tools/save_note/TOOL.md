---
name: save_note
track: bonus
kind: action
provider: local filesystem
requires_env: []
inputs: [content, title]
outputs: [status, path, chars]
side_effect: local_file_write
---
# save_note

Writes a markdown note to `starter_v0/notes/<timestamp>_<slug>.md` (folder is
gitignored). Local only: nothing is sent anywhere, so it needs no
confirmation, unlike `send`. The file name is built from a timestamp and a
slug of `title`, so the model cannot choose a path outside `notes/`. Empty
content or content over 20000 chars returns an error dict and writes nothing.
