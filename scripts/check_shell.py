#!/usr/bin/env python3
"""Find Python calls that run shell strings: `shell=True`, `os.system`, `os.popen`, `subprocess.getoutput`.

Two modes:
  check_shell.py PATH...       check every line of the given files or directories
  check_shell.py --base REF    check only lines changed since the merge base with REF,
                               including uncommitted and untracked files

A finding is allowed when its line carries a comment `allow-shell: <reason>`.
Exit codes: 0 clean, 1 findings, 2 error.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

SHELL_FUNCTIONS = {
    ("os", "system"),
    ("os", "popen"),
    ("subprocess", "getoutput"),
    ("subprocess", "getstatusoutput"),
}
ALLOW = re.compile(r"#.*\ballow-shell:\s*\S")
SKIP_DIRS = {".git", ".venv", "venv", ".tox", "node_modules", "site-packages", "build", "dist"}
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def dotted(node: ast.AST) -> Optional[tuple]:
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return (node.value.id, node.attr)
    return None


def scan_source(path: str, source: str) -> List[Finding]:
    tree = ast.parse(source, filename=path)
    lines = source.splitlines()
    findings: List[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = dotted(node.func)
        if name in SHELL_FUNCTIONS:
            findings.append(Finding(path, node.lineno, f"{name[0]}.{name[1]} runs a shell string; pass an argument list to subprocess.run"))
        for keyword in node.keywords:
            if keyword.arg == "shell" and not (isinstance(keyword.value, ast.Constant) and keyword.value.value is False):
                findings.append(Finding(path, keyword.value.lineno, "shell= is not False; pass an argument list and drop shell="))
    return [f for f in findings if not allowed(lines, f.line)]


def allowed(lines: Sequence[str], line: int) -> bool:
    return 0 < line <= len(lines) and bool(ALLOW.search(lines[line - 1]))


def git(args: Sequence[str]) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def parse_diff(diff: str) -> Dict[str, Set[int]]:
    changed: Dict[str, Set[int]] = {}
    current: Optional[str] = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            target = line[4:]
            current = target[2:] if target.startswith("b/") else None
            if current is not None:
                changed.setdefault(current, set())
            continue
        match = HUNK.match(line)
        if match and current is not None:
            start = int(match.group(1))
            count = int(match.group(2)) if match.group(2) is not None else 1
            changed[current].update(range(start, start + count))
    return changed


def changed_lines(base: str) -> Dict[str, Optional[Set[int]]]:
    root = git(["rev-parse", "--show-toplevel"]).strip()
    merge_base = git(["merge-base", "HEAD", base]).strip()
    diff = git(["-C", root, "diff", "-U0", "--no-color", "--no-ext-diff", merge_base, "--", "*.py"])
    result: Dict[str, Optional[Set[int]]] = {
        str(Path(root) / path): lines for path, lines in parse_diff(diff).items() if lines
    }
    untracked = git(["-C", root, "ls-files", "--others", "--exclude-standard", "--", "*.py"])
    for path in untracked.splitlines():
        result[str(Path(root) / path)] = None
    return result


def python_files(paths: Iterable[str]) -> List[str]:
    files: List[str] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(str(p) for p in sorted(path.rglob("*.py")) if not SKIP_DIRS.intersection(p.parts))
        elif path.suffix == ".py":
            files.append(str(path))
    return files


def run(targets: Dict[str, Optional[Set[int]]]) -> List[Finding]:
    findings: List[Finding] = []
    for path, lines in sorted(targets.items()):
        file = Path(path)
        if not file.exists():
            continue
        found = scan_source(os.path.relpath(path), file.read_text(encoding="utf-8"))
        findings.extend(f for f in found if lines is None or f.line in lines)
    return findings


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="files or directories to check in full")
    parser.add_argument("--base", help="check only lines changed since the merge base with this ref")
    args = parser.parse_args(argv)
    if bool(args.paths) == bool(args.base):
        parser.error("pass either PATH... or --base REF")
    try:
        targets = changed_lines(args.base) if args.base else {path: None for path in python_files(args.paths)}
        findings = run(targets)
    except (RuntimeError, SyntaxError, UnicodeDecodeError) as error:
        print(f"check_shell: {error}", file=sys.stderr)
        return 2
    for finding in findings:
        print(finding)
    scope = f"changed lines since {args.base}" if args.base else "all lines"
    print(f"check_shell: {len(targets)} file(s), {scope}, {len(findings)} finding(s)", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
