#!/usr/bin/env python3
"""Summarize an OpenTofu or Terraform plan and fail on deletes nobody approved.

Input is a saved plan file (rendered with `tofu show -json`) or the JSON itself.
Prints action counts, every non-create change with the attribute names it touches,
moves, imports, drift, and output changes. Values are never printed.

Exit codes: 0 no unapproved deletes, 2 unapproved delete or replace, 1 error.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

ORDER = ("create", "update", "replace", "delete", "forget", "read")
SYMBOL = {"create": "+", "update": "~", "replace": "-/+", "delete": "-", "forget": "x", "read": "<="}


@dataclass
class Change:
    address: str
    kind: str
    attributes: List[str] = field(default_factory=list)
    previous_address: Optional[str] = None
    importing: bool = False
    allowed: bool = True


@dataclass
class Summary:
    changes: List[Change]
    moved: List[Change]
    imported: List[Change]
    drift: List[Change]
    outputs: List[str]

    def count(self, kind: str) -> int:
        return sum(1 for change in self.changes if change.kind == kind)

    @property
    def blocked(self) -> List[Change]:
        return [change for change in self.changes if not change.allowed]


def classify(actions: Sequence[str]) -> str:
    acts = list(actions)
    if sorted(acts) == ["create", "delete"]:
        return "replace"
    if len(acts) == 1:
        return acts[0]
    return "+".join(acts)


def has_unknown(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, dict):
        return any(has_unknown(v) for v in value.values())
    if isinstance(value, list):
        return any(has_unknown(v) for v in value)
    return False


def changed_attributes(change: dict) -> List[str]:
    before = change.get("before") or {}
    after = change.get("after") or {}
    unknown = change.get("after_unknown") or {}
    if not isinstance(before, dict) or not isinstance(after, dict):
        return []
    if not isinstance(unknown, dict):
        unknown = {}
    keys = set(before) | set(after) | set(unknown)
    return sorted(k for k in keys if before.get(k) != after.get(k) or has_unknown(unknown.get(k)))


def summarize(plan: dict, allow_delete: Sequence[str] = ()) -> Summary:
    allowed = set(allow_delete)
    changes: List[Change] = []
    moved: List[Change] = []
    imported: List[Change] = []
    for resource in plan.get("resource_changes") or []:
        change = resource.get("change") or {}
        address = resource.get("address", "?")
        kind = classify(change.get("actions") or ["no-op"])
        previous = resource.get("previous_address")
        entry = Change(
            address=address,
            kind=kind,
            attributes=changed_attributes(change) if kind == "update" else [],
            previous_address=previous if previous and previous != address else None,
            importing=bool(change.get("importing")),
        )
        if entry.previous_address:
            moved.append(entry)
        if entry.importing:
            imported.append(entry)
        if kind == "no-op":
            continue
        if kind in ("delete", "replace"):
            entry.allowed = address in allowed
        changes.append(entry)
    drift = [
        Change(address=r.get("address", "?"), kind=classify((r.get("change") or {}).get("actions") or ["no-op"]))
        for r in plan.get("resource_drift") or []
    ]
    outputs = sorted(
        name for name, out in (plan.get("output_changes") or {}).items()
        if (out.get("actions") or ["no-op"]) != ["no-op"]
    )
    return Summary(changes=changes, moved=moved, imported=imported, drift=drift, outputs=outputs)


def sort_key(change: Change) -> tuple:
    rank = ORDER.index(change.kind) if change.kind in ORDER else len(ORDER)
    return (rank, change.address)


def headline(summary: Summary) -> str:
    return (
        f"Plan: {summary.count('create')} to add, {summary.count('update')} to change, "
        f"{summary.count('replace')} to replace, {summary.count('delete')} to destroy, "
        f"{len(summary.moved)} moved, {len(summary.imported)} imported, {len(summary.drift)} drifted"
    )


def render_text(summary: Summary) -> str:
    lines = [headline(summary)]
    listed = [c for c in sorted(summary.changes, key=sort_key) if c.kind != "create"]
    if listed:
        lines.append("")
        lines.append("Changes other than create:")
        for change in listed:
            detail = f" ({', '.join(change.attributes)})" if change.attributes else ""
            flag = "  NOT APPROVED" if not change.allowed else ""
            lines.append(f"  {SYMBOL.get(change.kind, '?'):>3} {change.kind:<8} {change.address}{detail}{flag}")
    created = [c.address for c in sorted(summary.changes, key=sort_key) if c.kind == "create"]
    if created:
        lines.append("")
        lines.append("Created:")
        lines.extend(f"    + {address}" for address in created)
    if summary.moved:
        lines.append("")
        lines.append("Moved:")
        lines.extend(f"    {c.previous_address} -> {c.address}" for c in summary.moved)
    if summary.imported:
        lines.append("")
        lines.append("Imported:")
        lines.extend(f"    {c.address}" for c in summary.imported)
    if summary.drift:
        lines.append("")
        lines.append("Drift (changed outside OpenTofu):")
        lines.extend(f"    {c.kind:<8} {c.address}" for c in summary.drift)
    if summary.outputs:
        lines.append("")
        lines.append("Outputs changed: " + ", ".join(summary.outputs))
    if summary.blocked:
        lines.append("")
        lines.append("Blocked: delete or replace not approved. Fix the code (a missing `moved` block?) or pass --allow-delete ADDRESS.")
    return "\n".join(lines)


def render_markdown(summary: Summary) -> str:
    lines = [f"**{headline(summary)}**", ""]
    rows = sorted(summary.changes, key=sort_key)
    if rows:
        lines.append("| Action | Address | Attributes |")
        lines.append("|---|---|---|")
        for change in rows:
            action = change.kind if change.allowed else f"{change.kind} (not approved)"
            lines.append(f"| {action} | `{change.address}` | {', '.join(change.attributes)} |")
    for title, items in (
        ("Moved", [f"`{c.previous_address}` → `{c.address}`" for c in summary.moved]),
        ("Imported", [f"`{c.address}`" for c in summary.imported]),
        ("Drift", [f"{c.kind} `{c.address}`" for c in summary.drift]),
        ("Outputs changed", [f"`{name}`" for name in summary.outputs]),
    ):
        if items:
            lines.append("")
            lines.append(f"{title}:")
            lines.extend(f"- {item}" for item in items)
    return "\n".join(lines)


def load_plan(path: str, tofu_bin: str) -> dict:
    if path == "-":
        return json.load(sys.stdin)
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (UnicodeDecodeError, json.JSONDecodeError):
        rendered = subprocess.run([tofu_bin, "show", "-json", path], capture_output=True, text=True)
        if rendered.returncode != 0:
            raise RuntimeError(f"`{tofu_bin} show -json {path}` failed: {rendered.stderr.strip()}")
        return json.loads(rendered.stdout)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("plan", help="saved plan file, plan JSON, or - for JSON on stdin")
    parser.add_argument("--allow-delete", action="append", default=[], metavar="ADDRESS",
                        help="resource address whose delete or replace is intended (repeatable)")
    parser.add_argument("--markdown", action="store_true", help="render a table for an MR description")
    parser.add_argument("--tofu-bin", default="tofu", help="binary used to render a saved plan (default: tofu)")
    args = parser.parse_args(argv)
    try:
        plan = load_plan(args.plan, args.tofu_bin)
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"plan_summary: {error}", file=sys.stderr)
        return 1
    if "resource_changes" not in plan and "planned_values" not in plan:
        print("plan_summary: input is not a plan (no resource_changes); did you pass state JSON?", file=sys.stderr)
        return 1
    summary = summarize(plan, args.allow_delete)
    print(render_markdown(summary) if args.markdown else render_text(summary))
    return 2 if summary.blocked else 0


if __name__ == "__main__":
    sys.exit(main())
