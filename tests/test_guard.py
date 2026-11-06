import json
import subprocess
import sys
from pathlib import Path

import pytest

import guard

GUARD = Path(__file__).resolve().parent.parent / "hooks" / "guard.py"


def run_hook(payload):
    result = subprocess.run([sys.executable, str(GUARD)], input=payload, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout) if result.stdout else None


def bash(command):
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/tmp"})


@pytest.mark.parametrize(
    "command",
    [
        "tofu apply",
        "tofu -chdir=envs/dev apply -auto-approve",
        "terraform destroy -target=aws_s3_bucket.logs",
        "tofu import aws_s3_bucket.logs logs-bucket",
        "tofu state rm module.old",
        "tofu state mv a.b c.d",
        "tofu force-unlock 1234",
        "tofu fmt",
        "tofu fmt -recursive",
        "git push origin feature",
        "git push --force-with-lease",
        "git -C repo push origin +main",
        "git reset --hard HEAD~1",
        "git clean -fdx",
        "glab mr merge 12",
        "gh pr merge 12 --squash",
        "glab api -X PUT projects/1/variables/X",
        "gh api repos/o/r/issues -f title=x",
        "glab ci run",
        "gh workflow run deploy.yml",
        "glab variable set TOKEN abc",
        "curl -X DELETE https://example.test/api/thing",
        "curl --data '{}' https://example.test/api",
        "curl -XPOST https://example.test/api",
        "az account set --subscription prod",
        "az functionapp restart -n app -g rg",
        "az storage blob upload --account-name a -c c -n n -f f",
        "aws configure set region us-east-1",
        "aws s3 rm s3://bucket/key",
        "aws s3 cp ./file s3://bucket/key",
        "aws iam put-role-policy --role-name r --policy-name p --policy-document file://p.json",
        "cd envs/dev && tofu apply",
        "FOO=1 tofu apply",
        "sudo -n true; git push",
        "bash -c 'tofu apply -auto-approve'",
        "echo hi | tofu apply",
    ],
)
def test_asks_for_commands_that_change_shared_state(command):
    decision = run_hook(bash(command))
    assert decision is not None, command
    output = decision["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "ask"
    assert output["permissionDecisionReason"].startswith("ian guard: ")


@pytest.mark.parametrize(
    "command",
    [
        "tofu plan -out=plan.bin",
        "tofu show -json plan.bin",
        "tofu validate",
        "tofu test",
        "tofu init -backend=false",
        "tofu state list",
        "tofu state show aws_s3_bucket.logs",
        "tofu fmt -check -diff -recursive",
        "tofu fmt main.tf",
        "git status",
        "git diff --stat origin/main",
        "git log --oneline -5",
        "git commit -m 'push the fix'",
        "glab mr view 12",
        "gh pr view 12 --json state",
        "glab api projects/1/pipelines",
        "curl -s https://example.test/api",
        "az storage blob tag list --account-name a -c c -n n",
        "az account show",
        "az login",
        "aws s3 ls s3://bucket",
        "aws s3 cp s3://bucket/key ./file",
        "aws sts get-caller-identity",
        "python3 -m pytest -q",
        "echo 'tofu apply is dangerous'",
        "grep -rn 'git push' .",
    ],
)
def test_allows_read_only_and_local_commands(command):
    assert run_hook(bash(command)) is None, command


def test_ignores_other_tools():
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "x", "content": "tofu apply"}})
    assert run_hook(payload) is None


def test_lists_every_reason_once():
    decision = run_hook(bash("tofu apply && git push && tofu apply"))
    reason = decision["hookSpecificOutput"]["permissionDecisionReason"]
    assert reason.count("tofu apply") == 1
    assert "git push" in reason


def test_force_push_is_named_as_force():
    reason = run_hook(bash("git push -f origin main"))["hookSpecificOutput"]["permissionDecisionReason"]
    assert "force-push" in reason


def test_unreadable_payload_asks_instead_of_allowing():
    decision = run_hook("not json")
    assert decision["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert "could not check" in decision["hookSpecificOutput"]["permissionDecisionReason"]


def test_unbalanced_quotes_still_checked():
    assert guard.reasons_for("tofu apply 'unterminated")
