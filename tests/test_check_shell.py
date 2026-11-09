import subprocess
import textwrap

import check_shell

BAD = textwrap.dedent(
    """\
    import os
    import subprocess

    subprocess.run(f"az group show -n {name}", shell=True)
    os.system("ls")
    subprocess.check_output(
        "echo hi",
        shell=True,
    )
    subprocess.run(["ls"], shell=False)
    subprocess.run("ls", shell=True)  # allow-shell: fixed literal, no input
    subprocess.run(cmd, shell=use_shell)
    """
)


def test_finds_shell_strings_with_lines():
    findings = check_shell.scan_source("x.py", BAD)
    assert [f.line for f in findings] == [4, 5, 8, 12]


def test_allow_comment_needs_a_reason():
    source = 'import subprocess\nsubprocess.run("ls", shell=True)  # allow-shell:\n'
    assert len(check_shell.scan_source("x.py", source)) == 1


def test_parse_diff_collects_added_lines():
    diff = textwrap.dedent(
        """\
        diff --git a/a.py b/a.py
        --- a/a.py
        +++ b/a.py
        @@ -1,0 +2,3 @@
        @@ -10 +12 @@
        @@ -20,2 +23,0 @@
        diff --git a/gone.py b/gone.py
        --- a/gone.py
        +++ /dev/null
        @@ -1,3 +0,0 @@
        """
    )
    assert check_shell.parse_diff(diff) == {"a.py": {2, 3, 4, 12}}


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_base_mode_reports_only_new_findings(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.test")
    git(repo, "config", "user.name", "t")
    git(repo, "config", "commit.gpgsign", "false")
    old = repo / "old.py"
    old.write_text('import os\nos.system("legacy")\n')
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "base")
    old.write_text('import os\nos.system("legacy")\nos.popen("new")\n')
    (repo / "untracked.py").write_text('import subprocess\nsubprocess.run("x", shell=True)\n')
    monkeypatch.chdir(repo)
    assert check_shell.main(["--base", "main"]) == 1
    out = capsys.readouterr().out.splitlines()
    assert out == [
        "old.py:3: os.popen runs a shell string; pass an argument list to subprocess.run",
        "untracked.py:2: shell= is not False; pass an argument list and drop shell=",
    ]


def test_path_mode_clean_file(tmp_path):
    clean = tmp_path / "clean.py"
    clean.write_text('import subprocess\nsubprocess.run(["ls", "-l"], check=True)\n')
    assert check_shell.main([str(tmp_path)]) == 0


def test_syntax_error_is_an_error_not_a_pass(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("def (:\n")
    assert check_shell.main([str(broken)]) == 2


def test_requires_exactly_one_mode():
    try:
        check_shell.main([])
    except SystemExit as exit_:
        assert exit_.code == 2
    else:
        raise AssertionError("expected usage error")


ALIASED = textwrap.dedent(
    """\
    import asyncio
    import asyncio.subprocess
    import subprocess as sp
    from os import system
    from os import popen as po
    from subprocess import getoutput
    from os import path

    sp.getoutput("ls")
    system("ls")
    po("ls")
    getoutput("ls")
    asyncio.create_subprocess_shell("ls")
    asyncio.subprocess.create_subprocess_shell("ls")
    sp.run(["ls"], check=True)
    path.join("a", "b")
    """
)

TO_RUN = "runs a shell string; pass an argument list to subprocess.run"
TO_EXEC = "runs a shell string; pass an argument list to asyncio.create_subprocess_exec"


def test_finds_aliased_from_imported_and_asyncio_calls(tmp_path, monkeypatch, capsys):
    (tmp_path / "aliased.py").write_text(ALIASED)
    monkeypatch.chdir(tmp_path)
    assert check_shell.main(["aliased.py"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        f"aliased.py:9: subprocess.getoutput {TO_RUN}",
        f"aliased.py:10: os.system {TO_RUN}",
        f"aliased.py:11: os.popen {TO_RUN}",
        f"aliased.py:12: subprocess.getoutput {TO_RUN}",
        f"aliased.py:13: asyncio.create_subprocess_shell {TO_EXEC}",
        f"aliased.py:14: asyncio.subprocess.create_subprocess_shell {TO_EXEC}",
    ]


def test_local_function_named_like_a_shell_call_is_not_flagged(tmp_path):
    local = tmp_path / "local.py"
    local.write_text('def system(command):\n    return command\n\n\nsystem("ls")\n')
    assert check_shell.main([str(local)]) == 0


def make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.test")
    git(repo, "config", "user.name", "t")
    git(repo, "config", "commit.gpgsign", "false")
    return repo


def test_base_mode_checks_files_with_unusual_names(tmp_path, monkeypatch, capsys):
    repo = make_repo(tmp_path)
    tracked = ["my deploy.py", "café.py", 'quote"d.py']
    for name in tracked:
        (repo / name).write_text("import os\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "base")
    for name in tracked:
        (repo / name).write_text('import os\nos.system("x")\n')
    (repo / "naïve new.py").write_text('import os\nos.popen("x")\n')
    monkeypatch.chdir(repo)
    assert check_shell.main(["--base", "main"]) == 1
    assert sorted(capsys.readouterr().out.splitlines()) == sorted([
        f"my deploy.py:2: os.system {TO_RUN}",
        f"café.py:2: os.system {TO_RUN}",
        f'quote"d.py:2: os.system {TO_RUN}',
        f"naïve new.py:2: os.popen {TO_RUN}",
    ])


def test_missing_path_is_an_error_not_a_pass(tmp_path, capsys):
    assert check_shell.main([str(tmp_path / "missing.py")]) == 2
    assert check_shell.main([str(tmp_path / "missing_dir")]) == 2
    err = capsys.readouterr().err
    assert "missing.py" in err
    assert "missing_dir" in err
