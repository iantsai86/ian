import json

import plan_summary


def resource(address, actions, before=None, after=None, after_unknown=None, previous_address=None, importing=None):
    entry = {
        "address": address,
        "change": {"actions": actions, "before": before, "after": after, "after_unknown": after_unknown or {}},
    }
    if previous_address:
        entry["previous_address"] = previous_address
    if importing:
        entry["change"]["importing"] = importing
    return entry


PLAN = {
    "format_version": "1.2",
    "resource_changes": [
        resource("aws_s3_bucket.new", ["create"], after={"bucket": "new"}),
        resource("aws_s3_bucket.logs", ["update"], before={"tags": {"a": "1"}, "bucket": "logs"},
                 after={"tags": {"a": "2"}, "bucket": "logs"}),
        resource("aws_iam_role.old", ["delete"], before={"name": "old"}),
        resource("aws_instance.web", ["delete", "create"], before={"ami": "1"}, after={"ami": "2"}),
        resource("aws_s3_bucket.renamed", ["no-op"], before={}, after={}, previous_address="aws_s3_bucket.legacy"),
        resource("aws_s3_bucket.adopted", ["no-op"], before={}, after={}, importing={"id": "adopted"}),
    ],
    "resource_drift": [resource("aws_s3_bucket.logs", ["update"])],
    "output_changes": {"bucket_arn": {"actions": ["update"]}, "same": {"actions": ["no-op"]}},
}


def write(tmp_path, plan):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return str(path)


def test_counts_each_kind():
    summary = plan_summary.summarize(PLAN)
    assert plan_summary.headline(summary) == (
        "Plan: 1 to add, 1 to change, 1 to replace, 1 to destroy, 1 moved, 1 imported, 1 drifted"
    )


def test_update_lists_only_changed_attribute_names_never_values():
    text = plan_summary.render_text(plan_summary.summarize(PLAN))
    assert "aws_s3_bucket.logs (tags)" in text
    assert "'2'" not in text and '"2"' not in text


def test_unknown_after_apply_counts_as_changed():
    change = {"before": {"arn": "x", "id": "1"}, "after": {"id": "1"}, "after_unknown": {"arn": True, "tags": {}}}
    assert plan_summary.changed_attributes(change) == ["arn"]


def test_unapproved_delete_and_replace_exit_2(tmp_path, capsys):
    assert plan_summary.main([write(tmp_path, PLAN)]) == 2
    out = capsys.readouterr().out
    assert "aws_iam_role.old  NOT APPROVED" in out
    assert "aws_instance.web  NOT APPROVED" in out


def test_approved_deletes_exit_0(tmp_path):
    args = [write(tmp_path, PLAN), "--allow-delete", "aws_iam_role.old", "--allow-delete", "aws_instance.web"]
    assert plan_summary.main(args) == 0


def test_moves_and_imports_are_listed(tmp_path, capsys):
    plan_summary.main([write(tmp_path, PLAN)])
    out = capsys.readouterr().out
    assert "aws_s3_bucket.legacy -> aws_s3_bucket.renamed" in out
    assert "Imported:\n    aws_s3_bucket.adopted" in out
    assert "Outputs changed: bucket_arn" in out


def test_clean_refactor_plan_passes(tmp_path):
    plan = {"resource_changes": [resource("a.b", ["no-op"], previous_address="a.c")]}
    assert plan_summary.main([write(tmp_path, plan)]) == 0


def test_markdown_table(tmp_path, capsys):
    plan_summary.main([write(tmp_path, PLAN), "--markdown"])
    out = capsys.readouterr().out
    assert "| delete (not approved) | `aws_iam_role.old` |  |" in out
    assert "- `aws_s3_bucket.legacy` → `aws_s3_bucket.renamed`" in out


def test_state_json_is_rejected(tmp_path, capsys):
    assert plan_summary.main([write(tmp_path, {"values": {"root_module": {}}})]) == 1
    assert "not a plan" in capsys.readouterr().err


def test_binary_plan_is_rendered_with_an_argument_list(tmp_path, monkeypatch):
    plan_file = tmp_path / "plan.bin"
    plan_file.write_bytes(b"PK\x03\x04\xff\xfe")
    calls = []

    class Result:
        returncode = 0
        stdout = json.dumps({"resource_changes": []})
        stderr = ""

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return Result()

    monkeypatch.setattr(plan_summary.subprocess, "run", fake_run)
    assert plan_summary.main([str(plan_file)]) == 0
    assert calls[0][0] == ["tofu", "show", "-json", str(plan_file)]
    assert "shell" not in calls[0][1]
