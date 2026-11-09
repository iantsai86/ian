# Security policy

ian's guard asks before some shell commands change shared state, and its scripts fail a change that breaks one of its rules. A report showing either of them doing less than the README says is welcome.

## Reporting a vulnerability

Report privately: open the **Security** tab of this repository and choose **Report a vulnerability**. Please don't open a public issue for a security problem, because that discloses it before a fix exists.

Include the command or input, what ian did, and what you expected it to do.

## In scope

- A shell command the README says the guard covers ("Rules and what enforces them") that runs without a prompt.
- Input that makes `check_shell.py` or `plan_summary.py` report success when it should fail.
- Anything in this repository that runs code or sends data the user did not ask for.

## Known limits

These are documented and are not treated as vulnerabilities.

- The guard reads shell commands only, and it asks rather than blocks. MCP tool calls, CLIs it has no rule for (such as `kubectl`, `helm`, and `databricks`), `az rest`, and writes made inside a script get no prompt.
- `check_shell.py` does not detect argument lists that run a shell (`["bash", "-c", cmd]`), `from os import *`, calls made through `getattr`, or `shell=True` passed through `**kwargs`.

## Response

ian is maintained for my own use. I read every report, but there is no promised response time or fix.

## Supported versions

Only the latest version on `main`.
