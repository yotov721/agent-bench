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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TASKS_DIR = ROOT / "evals" / "tasks"
RESULTS_DIR = ROOT / "evals" / "results"
CHECK_TIMEOUT = 60
RATE_LIMIT_RETRIES = 3
DAILY_LIMIT_MARKER = "free-models-per-day"


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
            with tracing.session() as session, contextlib.redirect_stdout(io.StringIO()):
                result["trace_id"] = session.trace_id  # None when tracing is off; links the trial to its Langfuse trace
                stats = agent.respond(model, [{"role": "user", "content": prompt}], work, auto_approve=True)
        except openai.APIError as e:
            result["error"] = f"{type(e).__name__}: {e}"[:300]
        result["seconds"] = round(time.time() - started, 1)
        result.update(stats)
        if result["error"] is None:
            result["passed"], result["check_output"] = grade(task, work)
    return result


def check_free_quota(model: str) -> None:
    """For free OpenRouter models, show today's remaining free requests and refuse to start at zero."""
    import json as _json
    import os
    import urllib.request

    import agent

    if not model.endswith(":free") or "openrouter.ai" not in agent.BASE_URL:
        return
    req = urllib.request.Request(
        f"{agent.BASE_URL}/key", headers={"Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY', '')}"}
    )
    try:
        quota = _json.load(urllib.request.urlopen(req, timeout=15))["data"]["free_model_daily_requests"]
    except Exception as e:  # the check is advisory; never block a run because it failed
        print(f"(could not check free-request quota: {e})")
        return
    print(f"Free requests today: {quota['remaining']} of {quota['limit']} remaining")
    if quota["remaining"] <= 0:
        sys.exit("No free requests left today (the limit is per account, shared by all free models). Try again later.")
    if quota["remaining"] < 25:
        print("Warning: a single task can use 10+ requests, so this run may stop early. It can be resumed later.")


def summarize(results: list[dict]) -> str:
    """Pass rate counts only trials that ran; API errors are reported separately, not as failures."""
    rows = ["| Task | Passed | API errors | Avg steps | Avg tokens | Avg seconds |", "|---|---|---|---|---|---|"]
    for name in sorted({r["task"] for r in results}):
        rs = [r for r in results if r["task"] == name]
        ran = [r for r in rs if not r["error"]]
        n = len(ran) or 1
        avg = lambda key: sum(r.get(key, 0) for r in ran) / n
        tokens = avg("prompt_tokens") + avg("completion_tokens")
        rows.append(
            f"| {name} | {sum(r['passed'] for r in ran)}/{len(ran)} | {len(rs) - len(ran)} "
            f"| {avg('steps'):.1f} | {tokens:,.0f} | {avg('seconds'):.0f} |"
        )
    ran_all = [r for r in results if not r["error"]]
    rows.append(f"| **total** | **{sum(r['passed'] for r in ran_all)}/{len(ran_all)}** | {len(results) - len(ran_all)} | | | |")
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

    check_free_quota(args.model)

    RESULTS_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", args.model).strip("-")
    out = RESULTS_DIR / f"{slug}.json"

    def save() -> None:
        out.write_text(json.dumps({"model": args.model, "trials": args.trials, "results": results}, indent=2))

    # Resume: keep trials that actually ran (pass or fail); redo the ones that hit API errors.
    results = []
    if out.exists():
        results = [r for r in json.loads(out.read_text())["results"] if not r["error"]]
        if results:
            print(f"Resuming from {out.relative_to(ROOT)}: {len(results)} finished trials kept")
    done = {(r["task"], r["trial"]) for r in results}

    stopped_early = False
    for task in tasks:
        for trial in range(1, args.trials + 1):
            if (task.name, trial) in done:
                continue
            for attempt in range(1, RATE_LIMIT_RETRIES + 2):
                r = run_trial(task, args.model)
                err = r["error"] or ""
                if DAILY_LIMIT_MARKER in err or not err.startswith("RateLimitError") or attempt > RATE_LIMIT_RETRIES:
                    break
                wait = 30 * attempt
                print(f"    rate-limited, retrying in {wait}s ({attempt}/{RATE_LIMIT_RETRIES})", flush=True)
                time.sleep(wait)
            r["trial"] = trial
            mark = "PASS" if r["passed"] else ("ERROR" if r["error"] else "FAIL")
            print(f"{task.name:28} trial {trial}  {mark:5}  steps={r.get('steps', '-')}  {r['seconds']}s", flush=True)
            if r["error"]:
                print(f"    {r['error']}")
            if DAILY_LIMIT_MARKER in (r["error"] or ""):
                stopped_early = True  # every further request would fail too; don't record this trial
                break
            results.append(r)
            save()  # persist after every trial so a crash or limit never loses finished work
        if stopped_early:
            break
    tracing.flush()
    save()

    print("\n" + summarize(results))
    print(f"\nSaved {out.relative_to(ROOT)}")
    if stopped_early:
        print("Stopped: daily free-request limit reached. Re-run the same command later to resume.")
        sys.exit(2)

if __name__ == "__main__":
    main()
