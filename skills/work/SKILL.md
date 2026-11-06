---
name: work
description: Start here for non-trivial work on Python CI/CD scripts, GitLab CI YAML, or OpenTofu. Picks a playbook, applies the ian principles, and ends with a report where every claim carries its proof level.
argument-hint: "<task>"
---

# ian

You are writing automation: Python that runs in pipelines, the CI YAML that calls it, and OpenTofu. This code runs unattended with real credentials. Its mistakes ship quietly and repeat on every run, so work in a way where every claim can be checked.

## Start

1. Restate the goal in one or two sentences, from the point of view of whoever depends on the result. Name the smallest change you think will achieve it, and start without asking for a go-ahead. If what you find contradicts the request, stop and show the evidence.
2. Pick one playbook below. Start a todo list with that playbook's steps, copied word for word. Never delete a step you skip; mark it `skip: <reason>`.
3. Read [principles.md](principles.md) once per task. Cite by number the principles that changed a decision.

## Playbooks

| Playbook | Use when |
|---|---|
| [investigate](playbooks/investigate.md) | You owe an answer, not a change. |
| [fix](playbooks/fix.md) | A script or job is broken. |
| [change](playbooks/change.md) | A script, job, or template needs new or changed behavior. |
| [ci-red](playbooks/ci-red.md) | A pipeline failed and the cause is not known yet. |
| [tofu-change](playbooks/tofu-change.md) | OpenTofu resources, modules, inputs, or providers change. |
| [tofu-refactor](playbooks/tofu-refactor.md) | Resources are renamed, moved, imported, or dropped from state, and real infrastructure must not change. |

If two fit, pick the one whose first step you would do first. If none fits, write a plan of five to eight steps where each step ends in a check, and say that you did.

## Proof levels

| Level | Name | What it takes |
|---|---|---|
| P0 | claimed | You said so. |
| P1 | cited | You point at a `file:line`, a doc, or a log line. |
| P2 | tested | A test fails without the change and passes with it. |
| P3 | exercised | You ran the real code, or a real plan, on its own. |
| P4 | observed | It ran where it will run: a pipeline job log, or an applied resource read back. |

A behavior claim in a fix or change needs P2 or higher. An OpenTofu change needs P3: a real plan read through `plan_summary.py`. Every report says whether P4 happened. Never round up. "Should work" is P0.

## Tools

- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_shell.py" --base <ref>` finds shell-string process calls on the lines you changed.
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/plan_summary.py" <plan>` counts plan actions, lists every update with its attribute names and every delete, and exits 2 on a delete nobody approved.

The [verify](../verify/SKILL.md) skill runs them alongside the repo's own lint and tests. [impact](../impact/SKILL.md) finds what a change breaks outside its diff. [attack](../attack/SKILL.md) runs an adversarial review. [lesson](../lesson/SKILL.md) turns a repeated mistake into a check.

## Guard

A hook asks the user before shell commands it recognizes as changing shared state: `tofu` apply and state edits, pushes, merges, forge API writes and pipeline runs, `curl` writes, `az` and `aws` commands with a known write verb, and changes to a CLI's global default account. It reads shell commands only. MCP tool calls, CLIs it has no rule for (`kubectl`, `helm`, `databricks`), `az rest`, and writes made inside a script get no prompt; ask the user yourself before any of those change shared state. Don't work around it. Don't reshape a command to dodge the match, and don't switch tools to make the same write. When it asks, the user decides.

## Deciding

Settle anything you can settle by running something: behavior, output, a plan, a test. Ask the user only about preferences, or about actions that change shared state. When you decide something the user might not expect, say what and why in the report.

## Delegating

Delegate independent, bulky work: reading a long log, surveying consumers, writing tests in parallel. Use the `ian:worker` agent. Give it the goal, the exact scope, the files, the proof level you need, and this file's path: `${CLAUDE_PLUGIN_ROOT}/skills/work/SKILL.md`. Review its diff yourself. Its summary is not evidence.

Keep raw output out of the main thread. Pass large logs and plan JSON through a script or a subagent, and keep only the finding.

## Report

End every task with these sections, in this order:

- **Goal.** The restatement.
- **Result.** What changed, or the answer.
- **Proof.** A table of claim, level, and evidence. Evidence is the command and the key output line, or a `file:line`.
- **Not proven.** Each claim below its required level, and what would raise it.
- **Principles.** The ones that changed a decision, by number.
- **Next.** What the user has to do, such as approve an apply, merge, or run a pipeline. Write "nothing" when nothing is left.

Link only things you read or produced in this session.
