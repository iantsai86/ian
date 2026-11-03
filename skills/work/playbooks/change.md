# Change

New or changed behavior in a script, a job, or a CI template.

1. Write the contract before the code.
   - Inputs: each environment variable, CLI flag, and `spec:inputs` entry, with its type and whether it is required or defaulted.
   - Outputs: exit codes, stdout that other tools parse, files, and artifacts.
   - Side effects: the commands run and the APIs called, each with its target.
   - Failure modes: each one with its exit code and message.
   Keep the contract. It becomes the merge request description.
2. If anything outside this repo consumes the code, run impact now, while the design can still change.
3. Shape the code. One entry point parses every input into a typed object (principle 3). Decisions are pure functions over that object. Side effects sit in a thin layer that takes argument lists (principle 5). The YAML calls the entry point and nothing else (principle 2).
4. Write tests from the contract: the success path, each failure mode's exit code and message, each skip path (principle 8), and a rerun (principle 7). Mock only the subprocess or API boundary, and assert the exact argv.
5. Write the smallest implementation that passes.
6. Run the verify skill. If the change touches credentials, deploy targets, trigger rules, or a shared template, run attack and resolve every proven finding.
7. Run it for real (P4): a pipeline on a branch, or the canary consumer that impact named. Read the log line that shows the new behavior.

**Report:** the contract, what changed, the proof table, and the consumers affected.
