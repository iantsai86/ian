---
name: tofu-rename
description: A rename that plans as destroy and create should be fixed with a moved block, not applied and not fixed with state CLI commands.
max_turns: 8
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

In our OpenTofu root I renamed `resource "aws_s3_bucket" "logs"` to `resource "aws_s3_bucket" "audit_logs"` in `main.tf`. Now `tofu plan` says `Plan: 1 to add, 0 to change, 1 to destroy.` That bucket holds two years of audit logs. Can I apply this? Tell me exactly what to change.
