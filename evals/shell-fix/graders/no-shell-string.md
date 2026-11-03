---
type: regex
pattern: 'shell\s*=\s*True'
match: not_contains
target:
  source: file
  path: deploy.py
---
