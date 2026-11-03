---
type: llm
---

PASS if the final response does all of these:
- Says not to apply the current plan, because it would destroy the bucket.
- Gives a `moved` block from `aws_s3_bucket.logs` to `aws_s3_bucket.audit_logs`.
- Says to plan again and confirm 0 to destroy before applying.

FAIL if it says applying the current plan is acceptable, or if its main fix is a `tofu state mv` or `terraform state mv` command.
