"""Tools the coding agent can call. All file paths are confined to the workspace root."""

import subprocess
from pathlib import Path

MAX_OUTPUT_CHARS = 20_000

TOOLS = [
    {
        "name": "list_dir",
        "description": "List files and directories at a path (relative to the workspace root).",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Directory path, '.' for the root."}},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_file",
        "description": "Read a text file and return its contents.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content. Creates parent directories.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "edit_file",
        "description": (
            "Replace one exact occurrence of old_string with new_string in a file. "
            "Fails if old_string is missing or appears more than once, so include enough context to be unique."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
            },
            "required": ["path", "old_string", "new_string"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run_shell",
        "description": "Run a shell command in the workspace root and return exit code, stdout and stderr. The user must approve each command.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
            "additionalProperties": False,
        },
    },
]

# Tools that change state and need user approval before running.
NEEDS_APPROVAL = {"write_file", "edit_file", "run_shell"}


class ToolError(Exception):
    """Raised for expected failures; the message is returned to the model as an error result."""


def _resolve(root: Path, path: str) -> Path:
    full = (root / path).resolve()
    if full != root and root not in full.parents:
        raise ToolError(f"Path '{path}' is outside the workspace.")
    return full


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n... [truncated {len(text) - MAX_OUTPUT_CHARS} chars]"


def describe_call(name: str, args: dict) -> str:
    """Human-readable summary used for approval prompts and logs."""
    if name == "run_shell":
        return f"run_shell: {args['command']}"
    if name == "edit_file":
        return f"edit_file: {args['path']}"
    if name == "write_file":
        return f"write_file: {args['path']} ({len(args['content'])} chars)"
    return f"{name}: {args.get('path', '')}"


def execute(root: Path, name: str, args: dict) -> str:
    """Run a tool and return its text result. Raises ToolError on expected failures."""
    if name == "list_dir":
        target = _resolve(root, args["path"])
        if not target.is_dir():
            raise ToolError(f"'{args['path']}' is not a directory.")
        entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        return "\n".join(f"{p.name}/" if p.is_dir() else p.name for p in entries) or "(empty)"

    if name == "read_file":
        target = _resolve(root, args["path"])
        if not target.is_file():
            raise ToolError(f"'{args['path']}' is not a file.")
        try:
            return _truncate(target.read_text())
        except UnicodeDecodeError:
            raise ToolError(f"'{args['path']}' is not a text file.")

    if name == "write_file":
        target = _resolve(root, args["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(args["content"])
        return f"Wrote {len(args['content'])} chars to {args['path']}."

    if name == "edit_file":
        target = _resolve(root, args["path"])
        if not target.is_file():
            raise ToolError(f"'{args['path']}' is not a file.")
        text = target.read_text()
        count = text.count(args["old_string"])
        if count == 0:
            raise ToolError("old_string not found.")
        if count > 1:
            raise ToolError(f"old_string appears {count} times; add more context to make it unique.")
        target.write_text(text.replace(args["old_string"], args["new_string"], 1))
        return f"Edited {args['path']}."

    if name == "run_shell":
        try:
            proc = subprocess.run(
                args["command"], shell=True, cwd=root, capture_output=True, text=True, timeout=120
            )
        except subprocess.TimeoutExpired:
            raise ToolError("Command timed out after 120s.")
        return _truncate(f"exit code: {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")

    raise ToolError(f"Unknown tool '{name}'.")
