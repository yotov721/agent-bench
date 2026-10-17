"""A small coding agent: a free LLM (via OpenRouter) + a tool-use loop over file and shell tools, traced with Langfuse."""

import argparse
import json
import os
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")  # before tracing/client setup, which read env vars

import tracing
from tools import NEEDS_APPROVAL, TOOLS, ToolError, describe_call, execute

DEFAULT_MODEL = "poolside/laguna-s-2.1:free"
BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
MAX_TOKENS = 8000
MAX_TURNS = 40  # safety cap on model calls per user message

SYSTEM_PROMPT = """You are a coding assistant working inside a project directory.
Use the tools to explore the code before changing it, make focused edits, and run commands (tests, linters) to check your work.
File paths are relative to the project root. Be concise when reporting what you did."""

# Same tool definitions as tools.py, in the OpenAI function-calling format.
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]},
    }
    for t in TOOLS
]

client = openai.OpenAI(base_url=BASE_URL, api_key=os.environ.get("OPENROUTER_API_KEY", "missing"))


def approve(name: str, args: dict, auto_approve: bool) -> bool:
    if name not in NEEDS_APPROVAL or auto_approve:
        return True
    answer = input(f"\n  Allow {describe_call(name, args)}? [y/N] ").strip().lower()
    return answer in ("y", "yes")


def run_tool(root: Path, call, auto_approve: bool) -> dict:
    """Execute one tool call and build the matching tool message."""
    name = call.function.name
    is_error = False
    try:
        args = json.loads(call.function.arguments or "{}")
    except json.JSONDecodeError:
        args, content, is_error = {}, "Error: tool arguments were not valid JSON.", True

    with tracing.tool_span(name, args) as span:
        if not is_error:
            if not approve(name, args, auto_approve):
                content, is_error = "The user declined this action.", True
            else:
                print(f"  -> {describe_call(name, args)}")
                try:
                    content = execute(root, name, args)
                except (ToolError, OSError, KeyError, TypeError) as e:
                    content, is_error = f"Error: {e!r}" if isinstance(e, (KeyError, TypeError)) else f"Error: {e}", True
        span.update(output=content, is_error=is_error)
    return {"role": "tool", "tool_call_id": call.id, "content": content}


def respond(model: str, messages: list, root: Path, auto_approve: bool) -> None:
    """Run the agent loop for the latest user message, appending to `messages` in place."""
    for _ in range(MAX_TURNS):
        with tracing.generation(model, messages) as gen:
            response = client.chat.completions.create(
                model=model,
                max_tokens=MAX_TOKENS,
                tools=OPENAI_TOOLS,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages],
            )
            choice = response.choices[0]
            gen.update(output=choice.message.model_dump(exclude_none=True), usage=response.usage)

        msg = choice.message
        entry = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            entry["tool_calls"] = [
                {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in msg.tool_calls
            ]
        messages.append(entry)

        if msg.content and msg.content.strip():
            print(f"\n{msg.content}")

        if choice.finish_reason == "length":
            print("\n[Response hit the token limit and was cut off.]")
            return
        if not msg.tool_calls:
            return

        for call in msg.tool_calls:
            messages.append(run_tool(root, call, auto_approve))

    print(f"\n[Stopped after {MAX_TURNS} model calls.]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Coding agent")
    parser.add_argument("--root", default=".", help="Project directory the agent works in (default: cwd)")
    parser.add_argument(
        "--model", default=os.environ.get("LLM_MODEL", DEFAULT_MODEL), help=f"Model id (default: {DEFAULT_MODEL})"
    )
    parser.add_argument("--yes", action="store_true", help="Run edits and shell commands without asking")
    args = parser.parse_args()

    if not os.environ.get("OPENROUTER_API_KEY"):
        sys.exit("Set OPENROUTER_API_KEY (free key at https://openrouter.ai/keys).")
    root = Path(args.root).resolve()
    if not root.is_dir():
        sys.exit(f"Not a directory: {root}")

    print(f"Coding agent in {root}  (model: {args.model}, tracing: {'on' if tracing.enabled() else 'off'})")
    print("Type a task, or 'exit' to quit.\n")

    messages: list = []
    with tracing.session():
        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue
            if user_input in ("exit", "quit"):
                break
            turn_start = len(messages)
            messages.append({"role": "user", "content": user_input})
            try:
                respond(args.model, messages, root, args.yes)
            except openai.APIError as e:
                print(f"\n[API error: {e}]")
                del messages[turn_start:]  # drop the failed turn so history stays valid
    tracing.flush()


if __name__ == "__main__":
    main()
