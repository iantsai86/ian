---
name: impact
description: Find what a change to automation code breaks outside its diff - callers of a script, consumers of a CI template or OpenTofu module, and state addresses - and prove the one fact it is safe because of. Use before merging a change to anything shared, or when asked for the blast radius.
---

# Impact

Listing call sites is the easy half. The job is to find the breakage a grep won't show, and to prove the one fact that makes the change safe.

1. **Name the contract surface the change touches**, before and after.
   - Script: CLI flags, environment variables read, exit codes, stdout lines other tools parse, files and artifact names written, and the external commands it runs.
   - CI template or YAML: job names, `spec:inputs` and their defaults, variables, `rules:`, `needs:`, artifacts, and stages.
   - OpenTofu module: variables (type, default, validation), outputs, resource addresses, and provider requirements.
2. **Find the consumers.** Inside this repo, grep. Outside it, search for the include or component path, or the module `source`, in local clones and through the forge's code search when you have it. Record where you looked, including the searches that found nothing.
3. **Decide each consumer's outcome:** unaffected, broken, or behaving differently. Look for these in particular:
   - A removed or renamed input.
   - A changed default. It changes behavior for every consumer that didn't set the input.
   - A new required input.
   - A changed exit code or output line.
   - A changed resource address. Without a `moved` block it becomes a delete and a create in every state.
4. **Find the one fact the change is safe because of**, such as "no consumer sets this input" or "the new default equals the old effective value". Prove it at P2 or higher with a script, a test, or a plan that would fail if the fact were false.
5. **Pick the canary:** the one consumer whose real run exercises the changed path. Name the job, and the log line that will show the change working.

**Report:** a table of consumer, outcome, proof level, and evidence. Then the safety fact with its proof, the places you searched, and the canary.
