# Tofu change

OpenTofu resources, modules, inputs, or providers change.

1. Name the target: which root modules, which states, which environments. Start in the lowest environment.
2. Name the shape: the resources added, changed, and removed, and the module's variables (type, required or default, validation) and outputs. Apply principle 11 to every new input and resource.
3. If a module changes, run impact. Every root that calls the module will plan differently.
4. Write or extend `tofu test` for the module's logic (validation rules, conditional resources, computed names) using mock providers. When you add a rule, watch its test fail first.
5. Run `tofu fmt -check -diff`, `tofu validate`, and `tofu test`.
6. Plan against real state for the target environment, then run `plan_summary.py` on the plan. Read every changed address.
   - Every update names only the attributes you meant to change.
   - Every delete or replace is one you can justify by name. Any other delete means the change is wrong.
   - Drift you didn't cause stops the work. Report it.
7. Apply only when the user approves. The guard will ask. After the apply, read one changed resource back with the provider's CLI or API (P4). Then plan again, which must show no changes (principle 7).
8. Promote to higher environments through the repo's own process. Put the `plan_summary.py --markdown` output in the merge request.

**Report:** the target, the shape, the plan summary, the proof table, and what is left for higher environments.
