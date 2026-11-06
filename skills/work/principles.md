# Principles

Each rule says when it applies, what to do, and what enforces it. A rule a tool enforces is not optional. A rule enforced by review is yours to check before you report.

## Change

**1. Smallest true change.** Any change. Change only what the evidence requires. Delete dead paths before you add new ones. Keep one concern per commit. *Enforced by review: every hunk traces to the goal.*

**2. Thin YAML.** Writing CI YAML. A job's `script:` calls one entry point with explicit arguments. Branches, loops, retries, and string building belong in Python with tests. `rules:` stay declarative. YAML logic has no tests, gets copied between shells, and no linter reads it. *Enforced by review.*

**3. Parse at the boundary.** Reading environment variables, CI variables, CLI arguments, files, or API responses. Parse each input once, at the entry point, into a typed value. Validate its format and its allowed values there. Pass typed values inward. A missing required input fails with the variable's name. *Enforced by tests on the parser.*

## Trust

**4. Callers control variables.** Any decision about who may do something, or where something goes. Assume whoever triggers a pipeline can set every variable, including the predefined ones. Key such decisions on literals written in the config, or on values fetched from an authority with the job's own credentials. Follow the chain: a trusted name that resolves through an overridable variable is not trusted. *Enforced by the attack skill's trust lens.*

**5. No shell strings.** Running a process. Pass an argument list. Never use `shell=True`, `os.system`, or `os.popen`. Pass secrets through the environment or stdin, never through argv. When a shell string is truly needed, mark the line `# allow-shell: <reason>`. *Enforced by `check_shell.py`.*

**6. Explicit target.** Anything that touches a remote system. Name the account, subscription, project, and environment in the command itself. Never rely on a CLI's ambient default, and never change it (`az account set`, `aws configure set`). Give each identity its own CLI config directory when sessions can overlap. *Enforced by the guard hook.*

## Behavior

**7. Converge on rerun.** Any step that changes state. Read the current state and apply only the difference, so a rerun after a crash at any point reaches the same end state. Leave nothing behind that the next run cannot identify as stale. *Enforced by a test that runs the step twice and sees the second run change nothing.*

**8. Fail loud.** A step can skip, fall back, or find nothing to do. A skipped required step exits non-zero. An allowed skip prints what it skipped and why, on its own line. A default that silently turns work off is a bug. Never report success for work that did not run. *Enforced by a test for each skip path.*

## OpenTofu

**9. The plan is the change.** Any OpenTofu change. Read the whole plan. Every changed address has a reason you can state. Every delete or replace is named and justified, or the change is wrong. Drift you didn't cause stops the work. *Enforced by `plan_summary.py`, which exits 2 on an unapproved delete.*

**10. State changes are code.** Renaming, moving, importing, or dropping resources. Use `moved`, `import`, and `removed` blocks in a reviewed change. Don't use `tofu state` write commands or `tofu import`. *Enforced by the guard hook.*

**11. Safe by default.** Writing module inputs and resources. Environment-specific inputs are required, not defaulted. A default picks the safe value: longer retention, private access, deletion protection. Resources that hold data get `prevent_destroy`. *Enforced by review, and by `tofu test` for validation rules.*

## Proof

**12. Test what the caller sees.** Writing tests. Drive the entry point. Assert the exit code, the output, the files written, and the exact argv sent to the subprocess boundary. Mock at that boundary and nowhere else. For modules, use `tofu test` with mock providers for logic and a real plan for wiring. Don't assert on private helpers. *Enforced by review.*

**13. Prove it where it runs.** Before you call anything done. A local pass is P2 or P3. Run the change where it will run, or say in the report that you didn't. A green pipeline proves the job passed, not that it did the work, so read the log line that shows the work. *Enforced by the report format.*

**14. Encode the lesson.** The same mistake happens twice, or once with real damage. Make it impossible, choosing the highest level that can catch it: a guard rule, then a script or lint, then a test, then text. Run the lesson skill. *Enforced by the "Enforced by" line on every rule in this file.*
