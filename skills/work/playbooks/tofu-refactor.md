# Tofu refactor

Renames, moves between modules, imports, and removals from state, where real infrastructure must not change.

1. Name the target states and save their current addresses: `tofu state list > <tmp>/before.txt`.
2. Write every address change as code. Use `moved` for renames and module moves, `import` to adopt existing resources, and `removed` to stop managing a resource without destroying it. Check your OpenTofu version's syntax for `removed`. Don't use `tofu state` write commands or `tofu import` (principle 10).
3. Plan, then run `plan_summary.py`. The result must show every moved address as moved and every import as imported, with 0 deletes, 0 replaces, and no updates you didn't intend. A delete means a `moved` block is missing. Fix the code; don't approve the delete.
4. Apply with the user's approval, then plan again. It must show no changes. Compare `tofu state list` with `before.txt` and check it matches the intended map.
5. Keep the `moved` blocks until every state that uses this code has applied them. Removing them early turns the next apply somewhere else into a delete and create.

**Report:** the before-to-after address map, the plan summary, and the proof table.
