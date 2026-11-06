---
name: attack
description: Adversarial review of a change to automation code. Three parallel reviewers try to break it through trust and injection, failure and rerun, and contract changes, and only findings proven by a run survive. Use for "attack this" or "adversarial review", and before merging anything that touches credentials, deploy targets, trigger rules, or shared templates.
---

# Attack

Reviewers try to break the change. A finding counts only when a run proves it. Report the findings; fix them only if asked.

1. **Scope.** Use what the user named. Otherwise use the diff from the merge base to the working tree. State the change's intent in two sentences, taken from the commits or the merge request text.
2. **Spawn three reviewers in one message.** Use the `ian:worker` agent, each with `isolation: "worktree"`. Give each one the scope, the intent, one lens, the brief below, and the router's path: `${CLAUDE_PLUGIN_ROOT}/skills/work/SKILL.md`.
   - **Trust.** Who controls each input: environment, CI variable, trigger payload, file, API response? Can a caller change where something deploys, what runs, or whether a check runs? Does any value reach a shell, a path, or a URL unvalidated? Follow each trusted value through everything it resolves into.
   - **Failure.** What happens on a crash at each step, on a rerun, on empty input, on a timeout, or on a partial API failure? Is there any path that reports success without doing the work?
   - **Contract.** What does each consumer see differently: inputs, defaults, exit codes, outputs, artifact names, resource addresses?

   The brief: "Break this change. Prove each finding by running something against the real code: a failing test, a script, or a plan. For each finding, report a title, the exact command, the output it printed, and the output the intent requires. Leave out anything you didn't run, style included. No findings is a valid result."
3. **Verify.** Rerun every reported command yourself. Keep a finding only when the output shows the failure and the failure breaks the intent. Merge findings that share a root cause.

**Report:** the intent. Then each finding with its command, output, why it breaks the intent, and the lens that found it. Then the number of findings dropped per lens, with the reasons.
