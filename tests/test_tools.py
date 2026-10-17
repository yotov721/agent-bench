import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tools
from tools import MAX_OUTPUT_CHARS, NEEDS_APPROVAL, TOOLS, ToolError, describe_call, execute


@pytest.fixture
def root(tmp_path):
    return tmp_path.resolve()  # resolved so macOS /var -> /private/var symlinks don't confuse the path check


def test_write_then_read_roundtrip(root):
    assert "Wrote 5 chars" in execute(root, "write_file", {"path": "a.txt", "content": "hello"})
    assert execute(root, "read_file", {"path": "a.txt"}) == "hello"


def test_write_creates_parent_directories(root):
    execute(root, "write_file", {"path": "x/y/z.txt", "content": "deep"})
    assert (root / "x" / "y" / "z.txt").read_text() == "deep"


def test_write_overwrites_existing_file(root):
    execute(root, "write_file", {"path": "a.txt", "content": "one"})
    execute(root, "write_file", {"path": "a.txt", "content": "two"})
    assert (root / "a.txt").read_text() == "two"


def test_read_missing_file_errors(root):
    with pytest.raises(ToolError, match="not a file"):
        execute(root, "read_file", {"path": "nope.txt"})


def test_read_binary_file_errors(root):
    (root / "b.bin").write_bytes(b"\xff\xfe\x00\x80")
    with pytest.raises(ToolError, match="not a text file"):
        execute(root, "read_file", {"path": "b.bin"})


def test_read_truncates_large_files(root):
    (root / "big.txt").write_text("x" * (MAX_OUTPUT_CHARS + 500))
    out = execute(root, "read_file", {"path": "big.txt"})
    assert len(out) < MAX_OUTPUT_CHARS + 100
    assert "truncated 500 chars" in out


def test_list_dir_sorts_directories_first(root):
    (root / "b.txt").write_text("")
    (root / "a.txt").write_text("")
    (root / "zdir").mkdir()
    assert execute(root, "list_dir", {"path": "."}).splitlines() == ["zdir/", "a.txt", "b.txt"]


def test_list_dir_empty_and_not_a_directory(root):
    assert execute(root, "list_dir", {"path": "."}) == "(empty)"
    (root / "f.txt").write_text("")
    with pytest.raises(ToolError, match="not a directory"):
        execute(root, "list_dir", {"path": "f.txt"})


def test_edit_replaces_single_occurrence(root):
    (root / "f.txt").write_text("hello world")
    execute(root, "edit_file", {"path": "f.txt", "old_string": "world", "new_string": "there"})
    assert (root / "f.txt").read_text() == "hello there"


def test_edit_missing_string_errors_and_leaves_file(root):
    (root / "f.txt").write_text("hello")
    with pytest.raises(ToolError, match="not found"):
        execute(root, "edit_file", {"path": "f.txt", "old_string": "zzz", "new_string": "x"})
    assert (root / "f.txt").read_text() == "hello"


def test_edit_ambiguous_string_errors_and_leaves_file(root):
    (root / "f.txt").write_text("aa aa")
    with pytest.raises(ToolError, match="2 times"):
        execute(root, "edit_file", {"path": "f.txt", "old_string": "aa", "new_string": "b"})
    assert (root / "f.txt").read_text() == "aa aa"


def test_edit_missing_file_errors(root):
    with pytest.raises(ToolError, match="not a file"):
        execute(root, "edit_file", {"path": "nope.txt", "old_string": "a", "new_string": "b"})


@pytest.mark.parametrize("path", ["../outside.txt", "a/../../outside.txt", "/etc/passwd"])
def test_paths_outside_workspace_are_rejected(root, path):
    for name, args in [
        ("read_file", {"path": path}),
        ("write_file", {"path": path, "content": "x"}),
        ("list_dir", {"path": path}),
    ]:
        with pytest.raises(ToolError, match="outside the workspace"):
            execute(root, name, args)
    assert not (root.parent / "outside.txt").exists()


def test_symlink_escaping_workspace_is_rejected(root, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside").resolve()
    (outside / "secret.txt").write_text("secret")
    (root / "link").symlink_to(outside)
    with pytest.raises(ToolError, match="outside the workspace"):
        execute(root, "read_file", {"path": "link/secret.txt"})


def test_paths_inside_workspace_with_dotdot_are_allowed(root):
    (root / "sub").mkdir()
    execute(root, "write_file", {"path": "sub/../a.txt", "content": "ok"})
    assert (root / "a.txt").read_text() == "ok"


def test_shell_reports_exit_code_stdout_and_stderr(root):
    out = execute(root, "run_shell", {"command": "echo out; echo err >&2; exit 3"})
    assert "exit code: 3" in out
    assert "out" in out and "err" in out


def test_shell_runs_in_workspace_root(root):
    (root / "marker.txt").write_text("")
    assert "marker.txt" in execute(root, "run_shell", {"command": "ls"})


def test_shell_timeout_becomes_tool_error(root, monkeypatch):
    real_run = tools.subprocess.run

    def fast_timeout(*args, **kwargs):
        return real_run(*args, **{**kwargs, "timeout": 0.2})

    monkeypatch.setattr(tools.subprocess, "run", fast_timeout)
    with pytest.raises(ToolError, match="timed out"):
        execute(root, "run_shell", {"command": "sleep 5"})


def test_unknown_tool_errors(root):
    with pytest.raises(ToolError, match="Unknown tool"):
        execute(root, "format_disk", {})


def test_describe_call_summaries():
    assert describe_call("run_shell", {"command": "ls"}) == "run_shell: ls"
    assert describe_call("edit_file", {"path": "a.py", "old_string": "x", "new_string": "y"}) == "edit_file: a.py"
    assert describe_call("write_file", {"path": "a.py", "content": "abc"}) == "write_file: a.py (3 chars)"
    assert describe_call("read_file", {"path": "a.py"}) == "read_file: a.py"


def test_only_state_changing_tools_need_approval():
    assert NEEDS_APPROVAL == {"write_file", "edit_file", "run_shell"}


def test_every_tool_definition_is_wellformed_and_dispatchable(root):
    names = [t["name"] for t in TOOLS]
    assert len(names) == len(set(names))
    for tool in TOOLS:
        schema = tool["input_schema"]
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) <= set(schema["properties"])
        # The name must be handled by execute(): any error other than "Unknown tool" is fine here.
        try:
            execute(root, tool["name"], {k: "" for k in schema["properties"]})
        except ToolError as e:
            assert "Unknown tool" not in str(e)
        except (OSError, KeyError):
            pass
