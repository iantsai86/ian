# Investigate

You owe an answer, not a change. Make no edits.

1. Restate the question, and name what would settle it: a code path, a run, a plan, or history.
2. Trace the path from where it starts (a pipeline trigger, a job, a CLI call) to where it ends (an external call or a resource). Cite a `file:line` at each hop. Send wide surveys to a `worker` and keep only the summary.
3. For a "why" question, read the history: `git log -L` or `git blame` on the lines, then the commit messages and merge request discussion. Keep what the record says apart from what you infer.
4. Raise the key claim to P2 or P3 when that's cheap: call the function, run the parser, or run a plan.
5. Answer first. Then give the path with its citations, then what you couldn't confirm.

If the answer shows a change is needed, name the playbook that comes next and stop.

**Report:** the answer, the cited path, the proof level of the key claim, and the open questions.
