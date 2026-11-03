---
name: verify
description: Run the proof checks for a change to Python CI/CD code, CI YAML, or OpenTofu - the repo's own lint and tests, shell-safety on changed lines, YAML parsing, and tofu fmt, validate, test, and plan summary. Use before calling a change done, or when asked to verify one.
---

# Verify

Run the checks that apply to what changed, and record each result with its proof level. A check you couldn't run is reported as not run, with the reason. It is never reported as passed.

1. **Find what changed.** Pick the base: `git symbolic-ref --short refs/remotes/origin/HEAD`, or `origin/main` when that fails. Run `git status --short` and `git diff --stat $(git merge-base HEAD <base>)`.
2. **Python**, when `.py` files changed.
   - Run the repo's own lint and tests with the same commands its CI uses. Read the CI file to find them; don't guess.
   - Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_shell.py" --base <base>`.
   - When the changed entry point can run without credentials, run it once with realistic arguments and environment (P3).
3. **CI YAML**, when a pipeline file or template changed.
   - Parse it: `python3 -c 'import sys, yaml; yaml.safe_load(open(sys.argv[1]))' <file>`.
   - Lint it with the forge's CLI when one is installed (for example `glab ci lint`). This sends the file to the forge but changes nothing there.
   - Read every changed `script:` block against principle 2.
4. **OpenTofu**, for each root or module directory with changed `.tf`, `.tfvars`, or `.tftest.hcl` files.
   - `tofu fmt -check -diff -recursive`. Never run plain `tofu fmt` on a directory.
   - `tofu init -backend=false`, then `tofu validate`.
   - `tofu test`, when `*.tftest.hcl` files exist.
   - For a root with real state and credentials: name the target environment (principle 6), run the repo's usual init, then `tofu plan -out=<tmp>/plan.bin` and `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/plan_summary.py" <tmp>/plan.bin`. Keep the plan file outside the repo.
5. **Report** a table of check, command, result, and proof level. Then list the checks you didn't run, each with its reason.
