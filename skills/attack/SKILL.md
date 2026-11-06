---
name: attack
description: Adversarial review of a change to automation code. Three parallel reviewers try to break it through trust and injection, failure and rerun, and contract changes, and a finding survives only if a run demonstrates it. Use for "attack this" or "adversarial review", and before merging anything that touches credentials, deploy targets, trigger rules, or shared templates.
---

# Attack

Reviewers try to break the change. Every finding needs a run that demonstrates it. Report findings; change nothing unless asked.

1. **Scope.** Use what the user named. Otherwise use the diff from the merge base to the working tree. State the change's intent in two sentences, taken from the commits or the merge request text.
2. **Spawn three reviewers in one message.** Use the `ian:worker` agent, each with `isolation: "worktree"`. Give each one the scope, the intent, one lens, the brief below, and the router's path: `${CLAUDE_PLUGIN_ROOT}/skills/work/SKILL.md`.
   - **Trust.** Who controls each input: environment, CI variable, trigger payload, file, API response? Can a caller change where something deploys, what runs, or whether a check runs? Does any value reach a shell, a path, or a URL unvalidated? Follow each trusted value through everything it resolves into.
   - **Failure.** What happens on a crash at each step, on a rerun, on empty input, on a timeout, or on a partial API failure? Is there any path that reports success without doing the work?
   - **Contract.** What does each consumer see differently: inputs, defaults, exit codes, outputs, artifact names, resource addresses?

   The brief: "Find where this change fails. For every finding, run something real that shows it: a failing test, a script, or a plan. Give each finding a title, the command you ran, what it printed, and what the intent says it should print. Omit anything you did not run, including style comments. Finding nothing is an acceptable outcome."
3. **Verify.** Rerun every reported command yourself. Keep a finding only if its output demonstrates a failure that contradicts the intent. Combine findings with the same root cause.

**Report:** the intent. Then each finding with its command, output, why it contradicts the intent, and which lens found it. Then the number of findings dropped per lens, with the reasons.
