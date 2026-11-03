import shutil
from pathlib import Path

import check_skills

ROOT = Path(__file__).resolve().parent.parent


def test_repository_passes_its_own_checks():
    assert check_skills.check(ROOT) == []


def copy_repo(tmp_path):
    target = tmp_path / "tstack"
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "results"))
    return target


def test_detects_unlinked_playbook(tmp_path):
    root = copy_repo(tmp_path)
    (root / "skills" / "work" / "playbooks" / "orphan.md").write_text("# Orphan\n")
    assert "skills/work/playbooks/orphan.md: not linked from the router" in check_skills.check(root)


def test_detects_name_mismatch_and_broken_link(tmp_path):
    root = copy_repo(tmp_path)
    skill = root / "skills" / "verify" / "SKILL.md"
    skill.write_text(skill.read_text().replace("name: verify", "name: verify-all", 1) + "\n[x](missing.md)\n")
    problems = check_skills.check(root)
    assert any("name is 'verify-all', expected 'verify'" in p for p in problems)
    assert "skills/verify/SKILL.md: broken link missing.md" in problems


def test_version_lives_only_in_plugin_json(tmp_path):
    root = copy_repo(tmp_path)
    market = root / ".claude-plugin" / "marketplace.json"
    market.write_text(market.read_text().replace('"source": "./",', '"source": "./",\n      "version": "0.1.0",', 1))
    assert ".claude-plugin/marketplace.json: set version only in plugin.json" in check_skills.check(root)


def test_detects_missing_plugin_root_path(tmp_path):
    root = copy_repo(tmp_path)
    (root / "scripts" / "plan_summary.py").unlink()
    problems = check_skills.check(root)
    assert any("skills/work/SKILL.md: references missing ${CLAUDE_PLUGIN_ROOT}/scripts/plan_summary.py" in p for p in problems)
