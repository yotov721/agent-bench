"""Run the coding agent on each task in evals/tasks and grade it with the task's hidden check.

Usage:
  python evals/run_evals.py --validate                 # sanity-check the tasks themselves
  python evals/run_evals.py --model <id> [--trials 3]  # evaluate a model
"""

import argparse
import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TASKS_DIR = ROOT / "evals" / "tasks"
RESULTS_DIR = ROOT / "evals" / "results"
CHECK_TIMEOUT = 60


def task_dirs(names: list[str] | None) -> list[Path]:
    dirs = sorted(p for p in TASKS_DIR.iterdir() if p.is_dir())
    if names:
        dirs = [d for d in dirs if any(n in d.name for n in names)]
    return dirs


def grade(task: Path, workdir: Path) -> tuple[bool, str]:
    """Run the hidden check against `workdir`. The check script never lives inside the workdir."""
    try:
        proc = subprocess.run(
            [sys.executable, str(task / "check.py")],
            cwd=workdir, capture_output=True, text=True, timeout=CHECK_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, "check timed out"
    return proc.returncode == 0, (proc.stderr or proc.stdout).strip()[-500:]


def validate(tasks: list[Path]) -> bool:
    """Every task must fail untouched and pass with its reference solution."""
    ok = True
    for task in tasks:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "p"
            shutil.copytree(task / "project", work)
            before, _ = grade(task, work)
            shutil.copytree(task / "solution", work, dirs_exist_ok=True)
            after, detail = grade(task, work)
        status = "ok" if (not before and after) else "BROKEN"
        if status == "BROKEN":
            ok = False
        print(f"{task.name:28} fails before: {not before!s:5}  passes after solution: {after!s:5}  {status}")
        if not after:
            print(f"    {detail}")
    return ok


def run_trial(task: Path, model: str) -> dict:
    import openai

    import agent
    import tracing

    prompt = (task / "task.md").read_text().strip()
    result = {"task": task.name, "passed": False, "error": None}
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp).resolve() / "p"
        shutil.copytree(task / "project", work)
        started = time.time()
        stats = {}
        try:
            with tracing.session(), contextlib.redirect_stdout(io.StringIO()):
                stats = agent.respond(model, [{"role": "user", "content": prompt}], work, auto_approve=True)
        except openai.APIError as e:
            result["error"] = f"{type(e).__name__}: {e}"[:300]
        result["seconds"] = round(time.time() - started, 1)
        result.update(stats)
        if result["error"] is None:
            result["passed"], result["check_output"] = grade(task, work)
    return result


def summarize(results: list[dict]) -> str:
    rows = ["| Task | Passed | Avg steps | Avg tokens | Avg seconds |", "|---|---|---|---|---|"]
    for name in sorted({r["task"] for r in results}):
        rs = [r for r in results if r["task"] == name]
        passed = sum(r["passed"] for r in rs)
        n = len(rs)
        avg = lambda key: sum(r.get(key, 0) for r in rs) / n
        tokens = avg("prompt_tokens") + avg("completion_tokens")
        rows.append(f"| {name} | {passed}/{n} | {avg('steps'):.1f} | {tokens:,.0f} | {avg('seconds'):.0f} |")
    total = sum(r["passed"] for r in results)
    rows.append(f"| **total** | **{total}/{len(results)}** | | | |")
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--validate", action="store_true", help="check the tasks, no model calls")
    parser.add_argument("--model", help="OpenRouter model id")
    parser.add_argument("--trials", type=int, default=1, help="runs per task (models are flaky, use 3+)")
    parser.add_argument("--tasks", nargs="*", help="only tasks whose name contains one of these")
    args = parser.parse_args()

    tasks = task_dirs(args.tasks)
    if args.validate:
        sys.exit(0 if validate(tasks) else 1)
    if not args.model:
        parser.error("--model is required (or use --validate)")

    import agent  # noqa: F401  (loads .env)
    import tracing

    results = []
    for task in tasks:
        for trial in range(1, args.trials + 1):
            r = run_trial(task, args.model)
            r["trial"] = trial
            results.append(r)
            mark = "PASS" if r["passed"] else ("ERROR" if r["error"] else "FAIL")
            print(f"{task.name:28} trial {trial}  {mark:5}  steps={r.get('steps', '-')}  {r['seconds']}s", flush=True)
            if r["error"]:
                print(f"    {r['error']}")
    tracing.flush()

    RESULTS_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", args.model).strip("-")
    out = RESULTS_DIR / f"{slug}-{datetime.now():%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps({"model": args.model, "trials": args.trials, "results": results}, indent=2))
    print("\n" + summarize(results))
    print(f"\nSaved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
