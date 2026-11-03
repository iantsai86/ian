# CI red

A pipeline failed. Classify it before you change or retry anything.

1. Read the failing job's log. Find the first error, not the last line. Note the commit, the runner, and the job's image.
2. Classify the failure, quoting the log line that shows the class.
   - **Change.** It fails in code or config that this change touched.
   - **Base.** It fails in code the change didn't touch. Check whether the branch is behind with `git merge-base --is-ancestor origin/<default> HEAD`.
   - **Environment.** A runner, network, registry, quota, expired credential, or missing variable or permission.
   - **Flaky.** The same commit passed before, or passes on a retry, and no code path explains the difference.
3. Act on the class.
   - Change: run the fix playbook.
   - Base: report that the branch needs updating. Don't patch unrelated code.
   - Environment: name the exact variable, permission, or service, and who owns it. Don't change shared CI settings or variables yourself.
   - Flaky: retry once. If it fails the same way again, it isn't flaky, so classify it again.
4. After any push, watch the new pipeline until it finishes, and read the job that failed before.

**Report:** the class with its log line, the action, and the final pipeline state with its link.
