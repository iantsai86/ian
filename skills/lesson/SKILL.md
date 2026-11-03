---
name: lesson
description: Turn a correction or a repeated mistake into something that prevents it - a guard rule, a script or lint check, a test, or, last, text in a playbook or principle. Use when the user corrects the agent, when a mistake happens twice, or after a task that went wrong.
---

# Lesson

1. **Name the mistake class** in one sentence, with its evidence: the moment in the conversation, the commit, or the review comment. A one-off slip is not a class. Two occurrences, or one that did real damage, is.
2. **Pick the highest level that would have stopped it**, and say why each higher level doesn't work.
   1. Guard: a command pattern the hook asks about (`${CLAUDE_PLUGIN_ROOT}/hooks/guard.py`).
   2. Check: a script or lint rule that fails on the mistake (`${CLAUDE_PLUGIN_ROOT}/scripts/`, or the repo's own linter config).
   3. Test: a test that fails when the behavior regresses.
   4. Text: a playbook step or a principle. Use text only for judgment calls nothing can check.
3. **Decide where it lives.** It goes in tstack when it holds for any repo. It goes in the repo (its agent instructions, lint config, or tests) when it is specific to that repo. Repo-specific facts never go into tstack.
4. **Implement it, then prove it.** Run the new check against the bad version and paste the failure (P2 or higher).
5. **If you changed tstack:** work in a checkout of the tstack repo, not the installed copy. Update the matching principle's "Enforced by" line, run `python3 scripts/check_skills.py` and `python3 -m pytest -q` there, and bump `version` in `.claude-plugin/plugin.json`.

**Report:** the class with its evidence, the level you chose and why higher levels didn't work, and the proof.
