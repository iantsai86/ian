#!/usr/bin/env python3
"""Check ian's own structure: frontmatter, links, playbook coverage, manifests, and plugin-root paths.

Run from anywhere: `python3 scripts/check_skills.py [ROOT]`. Exit 1 lists every problem.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
PLUGIN_ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"'`)\\]+)")
MAX_DESCRIPTION = 1024


def frontmatter(text: str) -> Optional[Dict[str, str]]:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    fields: Dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields


def check_frontmatter(path: Path, expected_name: str, problems: List[str]) -> None:
    fields = frontmatter(path.read_text(encoding="utf-8"))
    if fields is None:
        problems.append(f"{path}: missing frontmatter")
        return
    if fields.get("name") != expected_name:
        problems.append(f"{path}: name is {fields.get('name')!r}, expected {expected_name!r}")
    description = fields.get("description", "")
    if not description:
        problems.append(f"{path}: missing description")
    elif len(description) > MAX_DESCRIPTION:
        problems.append(f"{path}: description is {len(description)} chars, limit {MAX_DESCRIPTION}")


def check_links(path: Path, root: Path, problems: List[str]) -> None:
    for target in LINK.findall(path.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        resolved = (path.parent / target.split("#", 1)[0]).resolve()
        if not resolved.exists():
            problems.append(f"{path.relative_to(root)}: broken link {target}")


def check_router(root: Path, problems: List[str]) -> None:
    router = root / "skills" / "work" / "SKILL.md"
    playbooks = root / "skills" / "work" / "playbooks"
    if not router.exists():
        problems.append("skills/work/SKILL.md: router missing")
        return
    linked = {(router.parent / t).resolve() for t in LINK.findall(router.read_text(encoding="utf-8"))}
    for playbook in sorted(playbooks.glob("*.md")):
        if playbook.resolve() not in linked:
            problems.append(f"{playbook.relative_to(root)}: not linked from the router")


def check_manifests(root: Path, problems: List[str]) -> None:
    plugin_path = root / ".claude-plugin" / "plugin.json"
    try:
        plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f"{plugin_path.relative_to(root)}: {error}")
        return
    for key in ("name", "version", "description"):
        if not plugin.get(key):
            problems.append(f".claude-plugin/plugin.json: missing {key}")
    market_path = root / ".claude-plugin" / "marketplace.json"
    if market_path.exists():
        market = json.loads(market_path.read_text(encoding="utf-8"))
        entries = [p for p in market.get("plugins", []) if p.get("name") == plugin.get("name")]
        if not entries:
            problems.append(".claude-plugin/marketplace.json: no entry for this plugin")
        for entry in entries:
            if "version" in entry:
                problems.append(".claude-plugin/marketplace.json: set version only in plugin.json")


def check_hooks(root: Path, problems: List[str]) -> None:
    hooks_path = root / "hooks" / "hooks.json"
    if not hooks_path.exists():
        return
    try:
        json.loads(hooks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        problems.append(f"hooks/hooks.json: {error}")


def check_plugin_root_refs(path: Path, root: Path, problems: List[str]) -> None:
    for relative in PLUGIN_ROOT_REF.findall(path.read_text(encoding="utf-8")):
        if not (root / relative.rstrip(".,")).exists():
            problems.append(f"{path.relative_to(root)}: references missing ${{CLAUDE_PLUGIN_ROOT}}/{relative}")


def check(root: Path) -> List[str]:
    problems: List[str] = []
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        check_frontmatter(skill, skill.parent.name, problems)
    for agent in sorted((root / "agents").glob("*.md")):
        check_frontmatter(agent, agent.stem, problems)
    for markdown in sorted(list(root.glob("*.md")) + list((root / "skills").rglob("*.md")) + list((root / "agents").glob("*.md"))):
        check_links(markdown, root, problems)
        check_plugin_root_refs(markdown, root, problems)
    if (root / "hooks" / "hooks.json").exists():
        check_plugin_root_refs(root / "hooks" / "hooks.json", root, problems)
    check_router(root, problems)
    check_manifests(root, problems)
    check_hooks(root, problems)
    return problems


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
    problems = check(root)
    for problem in problems:
        print(problem)
    print(f"check_skills: {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
