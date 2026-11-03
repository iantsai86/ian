#!/usr/bin/env python3
"""PreToolUse hook: ask the user before Bash commands that change shared state.

Reads the hook payload on stdin. Prints an "ask" decision when any rule matches,
and prints nothing otherwise. This is a seatbelt for honest mistakes, not a sandbox.
"""
from __future__ import annotations

import json
import os
import shlex
import sys
from typing import Callable, Dict, Iterator, List, Optional

CONTROL_TOKENS = {"&&", "||", ";", "|", "&", ";;", "(", ")", "|&"}
WRAPPERS = {"sudo", "command", "time", "nohup", "exec", "builtin"}
SHELLS = {"bash", "sh", "zsh", "dash"}

Rule = Callable[[List[str]], Optional[str]]


def tokenize(command: str) -> List[str]:
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def split_segments(tokens: List[str]) -> Iterator[List[str]]:
    segment: List[str] = []
    for token in tokens:
        if token in CONTROL_TOKENS:
            if segment:
                yield segment
            segment = []
        else:
            segment.append(token)
    if segment:
        yield segment


def strip_prefixes(segment: List[str]) -> List[str]:
    rest = list(segment)
    while rest:
        head = rest[0]
        if "=" in head and not head.startswith("-") and head.split("=", 1)[0].isidentifier():
            rest.pop(0)
        elif head in WRAPPERS:
            rest.pop(0)
        elif head == "env":
            rest.pop(0)
            while rest and (rest[0].startswith("-") or "=" in rest[0]):
                rest.pop(0)
        else:
            break
    return rest


def positionals(args: List[str], takes_value: frozenset = frozenset()) -> List[str]:
    found: List[str] = []
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg in takes_value:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        found.append(arg)
    return found


def tofu_rule(args: List[str]) -> Optional[str]:
    words = positionals(args)
    if not words:
        return None
    sub = words[0]
    if sub in ("apply", "destroy"):
        return f"`tofu {sub}` changes real infrastructure"
    if sub == "import":
        return "`tofu import` writes state directly; use an `import` block in a reviewed change"
    if sub in ("taint", "untaint", "force-unlock"):
        return f"`tofu {sub}` edits state directly"
    if sub == "state" and len(words) > 1 and words[1] in ("rm", "mv", "push", "replace-provider"):
        return f"`tofu state {words[1]}` edits state directly; use `moved` or `removed` blocks"
    if sub == "workspace" and len(words) > 1 and words[1] == "delete":
        return "`tofu workspace delete` removes a workspace and its state"
    if sub == "fmt":
        checks = any(a == "-check" or a.startswith("-check=") and a != "-check=false" for a in args)
        names_files = any(a.endswith((".tf", ".tfvars", ".tftest.hcl")) for a in args)
        if not checks and not names_files:
            return "`tofu fmt` rewrites every file in the directory; use `-check -diff` or name the file"
    return None


GIT_OPTIONS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace"})


def git_rule(args: List[str]) -> Optional[str]:
    words = positionals(args, GIT_OPTIONS_WITH_VALUE)
    if not words:
        return None
    sub = words[0]
    if sub == "push":
        forced = any(a in ("-f", "--force", "--force-with-lease") or a.startswith("--force-with-lease=") for a in args)
        forced = forced or any(w.startswith("+") for w in words[1:])
        if forced:
            return "force-push rewrites history on the remote"
        return "`git push` publishes commits to a remote"
    if sub == "reset" and "--hard" in args:
        return "`git reset --hard` discards uncommitted work"
    if sub == "clean" and any(a == "--force" or (a.startswith("-") and not a.startswith("--") and "f" in a) for a in args):
        return "`git clean -f` deletes untracked files"
    return None


def method_flag(args: List[str]) -> Optional[str]:
    for index, arg in enumerate(args):
        if arg in ("-X", "--method", "--request") and index + 1 < len(args):
            return args[index + 1].upper()
        for prefix in ("-X", "--method=", "--request="):
            if arg.startswith(prefix) and len(arg) > len(prefix):
                return arg[len(prefix):].upper()
    return None


def forge_rule(tool: str, args: List[str]) -> Optional[str]:
    words = positionals(args, frozenset({"-R", "--repo", "-X", "--method", "-H", "--header", "-f", "-F", "--field", "--raw-field"}))
    if not words:
        return None
    sub = words[0]
    action = words[1] if len(words) > 1 else ""
    if sub in ("mr", "pr") and action == "merge":
        return f"`{tool} {sub} merge` merges into the target branch"
    if sub == "api":
        method = method_flag(args)
        has_fields = any(a in ("-f", "-F", "--field", "--raw-field", "--input") for a in args)
        if (method and method != "GET") or (method is None and has_fields):
            return f"`{tool} api` with a write method changes data on the forge"
    if (sub, action) in {("ci", "run"), ("ci", "retry"), ("workflow", "run"), ("run", "rerun")}:
        return f"`{tool} {sub} {action}` starts a pipeline, which may deploy"
    if sub in ("variable", "secret") and action in ("set", "update", "delete", "remove"):
        return f"`{tool} {sub} {action}` changes CI/CD settings"
    if sub in ("release", "repo") and action == "delete":
        return f"`{tool} {sub} delete` deletes data on the forge"
    return None


CURL_DATA_FLAGS = ("-d", "--data", "--data-raw", "--data-binary", "--data-urlencode", "-F", "--form", "--json", "-T", "--upload-file")


def curl_rule(args: List[str]) -> Optional[str]:
    method = method_flag(args)
    if method in ("POST", "PUT", "PATCH", "DELETE"):
        return f"`curl -X {method}` sends a write request"
    if method is None and any(a in CURL_DATA_FLAGS or a.startswith(tuple(f + "=" for f in CURL_DATA_FLAGS if f.startswith("--"))) for a in args):
        return "`curl` with a request body sends a write request"
    return None


AZ_LOCAL_GROUPS = {"login", "logout", "extension", "config", "cache", "version", "upgrade", "find", "interactive", "bicep"}
AZ_WRITE_VERBS = {
    "create", "delete", "update", "set", "restart", "start", "stop", "deploy", "purge", "remove",
    "add", "upload", "upload-batch", "swap", "import", "assign", "rotate", "regenerate", "renew", "invoke",
}
AZ_OPTIONS_WITH_VALUE = frozenset({"--subscription", "-g", "--resource-group", "-n", "--name", "--query", "-o", "--output"})


def az_rule(args: List[str]) -> Optional[str]:
    words = positionals(args, AZ_OPTIONS_WITH_VALUE)
    if not words or words[0] in AZ_LOCAL_GROUPS:
        return None
    if words[:2] == ["account", "set"]:
        return "`az account set` changes the CLI's global default subscription; pass `--subscription` on each command"
    verb = next((w for w in words if w in AZ_WRITE_VERBS), None)
    if verb:
        return f"`az {' '.join(words[:words.index(verb) + 1])}` changes cloud resources"
    return None


AWS_WRITE_PREFIXES = (
    "create-", "delete-", "put-", "update-", "modify-", "terminate-", "stop-", "start-", "reboot-",
    "attach-", "detach-", "associate-", "disassociate-", "tag-", "untag-", "run-", "send-", "register-",
    "deregister-", "revoke-", "authorize-", "enable-", "disable-", "reset-", "restore-", "copy-",
    "import-", "upload-", "set-", "add-", "remove-", "cancel-", "replace-", "rotate-", "apply-", "invoke",
    "publish", "deploy",
)
AWS_OPTIONS_WITH_VALUE = frozenset({"--profile", "--region", "--output", "--query", "--endpoint-url"})


def aws_rule(args: List[str]) -> Optional[str]:
    words = positionals(args, AWS_OPTIONS_WITH_VALUE)
    if not words:
        return None
    if words[:2] == ["configure", "set"]:
        return "`aws configure set` changes the CLI's shared profile; pass `--profile` and `--region` per command"
    if words[0] == "s3" and len(words) > 1:
        verb = words[1]
        if verb in ("rm", "rb", "mb"):
            return f"`aws s3 {verb}` changes S3"
        if verb in ("cp", "mv", "sync") and words[-1].startswith("s3://"):
            return f"`aws s3 {verb}` writes to S3"
        return None
    if len(words) > 1 and words[1].startswith(AWS_WRITE_PREFIXES):
        return f"`aws {words[0]} {words[1]}` changes cloud resources"
    return None


RULES: Dict[str, Rule] = {
    "tofu": tofu_rule,
    "terraform": tofu_rule,
    "git": git_rule,
    "glab": lambda a: forge_rule("glab", a),
    "gh": lambda a: forge_rule("gh", a),
    "curl": curl_rule,
    "az": az_rule,
    "aws": aws_rule,
}


def reasons_for(command: str, depth: int = 0) -> List[str]:
    found: List[str] = []
    for segment in split_segments(tokenize(command)):
        words = strip_prefixes(segment)
        if not words:
            continue
        program = os.path.basename(words[0])
        args = words[1:]
        if program in SHELLS and "-c" in args and depth < 3:
            index = args.index("-c")
            if index + 1 < len(args):
                found.extend(reasons_for(args[index + 1], depth + 1))
            continue
        if program == "eval" and depth < 3:
            found.extend(reasons_for(" ".join(args), depth + 1))
            continue
        rule = RULES.get(program)
        if rule:
            reason = rule(args)
            if reason:
                found.append(reason)
    return found


def decide(payload: dict) -> Optional[dict]:
    if payload.get("tool_name") != "Bash":
        return None
    command = (payload.get("tool_input") or {}).get("command") or ""
    reasons = reasons_for(command)
    if not reasons:
        return None
    unique = list(dict.fromkeys(reasons))
    return ask("tstack guard: " + "; ".join(unique) + ".")


def ask(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        decision = decide(payload)
    except Exception as error:  # noqa: BLE001 - a broken guard must ask, not silently allow
        decision = ask(f"tstack guard could not check this command ({type(error).__name__}: {error}).")
    if decision:
        json.dump(decision, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
