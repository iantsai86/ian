# ian

A Claude Code plugin for automation engineering: Python that runs in CI/CD pipelines, the CI YAML that calls it, and OpenTofu.

Automation code runs unattended with real credentials. A mistake doesn't crash in front of anyone. It ships, reruns on every pipeline, and touches shared infrastructure. ian makes the agent work in a way where every claim can be checked, and stops it before it changes anything shared without asking.

## Install

From GitHub (Claude Code uses your git credentials, so a private repo works over SSH):

```bash
claude plugin marketplace add iantsai86/ian
claude plugin install ian@ian
```

For one session from a local checkout, without installing:

```bash
claude --plugin-dir path/to/ian
```

Run `/reload-plugins` after editing. Don't also register the local checkout as a marketplace: two marketplaces can't share the name `ian`.

The plugin adds about 400 tokens to every session (`claude plugin details ian`). The playbooks and principles load only when a skill runs.

## Use

Start a task with the router:

```text
/ian:work the upload script fails on Windows runners when the artifact name has a space. fix it.
/ian:work add a required `environment` input to the deploy template and reject unknown values.
/ian:work rename module.storage to module.artifacts in every state without recreating anything.
```

The router restates your goal, picks a playbook, copies its steps into a todo list, and ends with a report in a fixed shape: goal, result, proof, not proven, principles, next.

You can also call the method skills directly:

| Skill | Does |
|---|---|
| `/ian:verify` | Runs the repo's lint and tests, `check_shell.py` on changed lines, YAML parsing, and `tofu fmt`, `validate`, `test`, and plan summary. |
| `/ian:impact` | Finds what a change breaks outside its diff, and proves the one fact it is safe because of. |
| `/ian:attack` | Three reviewers try to break the change through trust, failure, and contract lenses. Only findings proven by a run survive. |
| `/ian:lesson` | Turns a repeated mistake into a guard rule, a check, a test, or, last, text. |

## Playbooks

| Playbook | Use when |
|---|---|
| [investigate](skills/work/playbooks/investigate.md) | You owe an answer, not a change. |
| [fix](skills/work/playbooks/fix.md) | A script or job is broken. |
| [change](skills/work/playbooks/change.md) | A script, job, or template needs new or changed behavior. |
| [ci-red](skills/work/playbooks/ci-red.md) | A pipeline failed and the cause is not known yet. |
| [tofu-change](skills/work/playbooks/tofu-change.md) | OpenTofu resources, modules, inputs, or providers change. |
| [tofu-refactor](skills/work/playbooks/tofu-refactor.md) | Resources are renamed, moved, imported, or dropped from state without changing infrastructure. |

## Proof levels

Every claim in a report carries one of these.

| Level | Name | What it takes |
|---|---|---|
| P0 | claimed | You said so. |
| P1 | cited | A `file:line`, a doc, or a log line. |
| P2 | tested | A test fails without the change and passes with it. |
| P3 | exercised | The real code, or a real plan, ran on its own. |
| P4 | observed | It ran where it will run: a pipeline job log, or an applied resource read back. |

## Rules and what enforces them

The [principles](skills/work/principles.md) are fourteen short rules. Where a tool can enforce a rule, a tool does:

| Rule | Enforced by |
|---|---|
| No shell strings | `scripts/check_shell.py`, on the lines a change touches |
| The plan is the change | `scripts/plan_summary.py`, which exits 2 on a delete nobody approved |
| Explicit target, and state changes are code | `hooks/guard.py`, which asks before `az account set`, `tofu state rm`, and the rest |
| Ask before changing shared state | `hooks/guard.py`: `tofu apply`/`destroy`, `git push`, merges, forge API writes, pipeline triggers, cloud CLI writes |
| Every playbook is reachable and every link resolves | `scripts/check_skills.py`, in CI |

The guard asks; it never blocks outright, so you stay in charge. It is a seatbelt for honest mistakes, not a sandbox.

## Layout

```text
.claude-plugin/   plugin and marketplace manifests
agents/worker.md  delegate that reads the router before it works
hooks/            guard.py and its registration
skills/work/      the router, principles.md, and playbooks/
skills/verify/ skills/impact/ skills/attack/ skills/lesson/
scripts/          check_shell.py, plan_summary.py, check_skills.py
evals/            cases for `claude plugin eval`
tests/            pytest for every script and the hook
```

## Develop

```bash
python3 -m pytest -q
python3 scripts/check_skills.py
python3 scripts/check_shell.py hooks scripts tests
claude plugin validate .
```

### Evals

`evals/` holds cases for `claude plugin eval`. Each case runs with and without the plugin, so the report shows what ian changes. Every run is a full Claude session billed to you, so start with one run per case:

```bash
claude plugin eval . --runs 1 --allow-tools Write Edit "Bash(python3:*)"
```

| Case | Checks |
|---|---|
| `shell-fix` | A shell-string bug is fixed with an argument list, a test is written, and the report says how each claim was verified. |
| `tofu-rename` | A rename that plans as a destroy gets a `moved` block, not an apply or a `state mv`. |

In eval runs the guard's "ask" becomes a denial, because nobody is there to answer.

When you change anything users get, bump `version` in `.claude-plugin/plugin.json`. Set it only there; `check_skills.py` fails if the marketplace entry sets it too.
