# agent-bench

A small coding agent and a benchmark for measuring how well different LLMs drive it.

The agent is a plain tool-use loop (read, write and edit files, run shell commands) that works with any
OpenAI-compatible API. The benchmark gives it ten small programming tasks, grades each result with a hidden
test, and reports pass rate, steps, tokens and time per model. It is set up to compare **free** models on
[OpenRouter](https://openrouter.ai), with every run traced in [Langfuse](https://langfuse.com).

## How it works

```
agent.py          the agent loop: model call -> tool calls -> results -> repeat
tools.py          list_dir, read_file, write_file, edit_file, run_shell (confined to the project folder)
tracing.py        optional Langfuse tracing; does nothing unless the Langfuse keys are set
evals/
  run_evals.py    runs every task against a model and grades the result
  tasks/NN_name/
    task.md       the instruction the agent receives
    project/      the starting files the agent works on
    solution/     a reference fix, used only to validate the task
    check.py      hidden grader; the agent never sees it
```

For each task the runner copies `project/` to a temp folder, lets the agent work with auto-approved tools,
then runs `check.py` in that folder. Exit code 0 is a pass. Nobody judges the output by eye.

## The tasks

| # | Task | What it tests |
|---|---|---|
| 01 | Make functions return `None` on empty input | A small, well-specified bug fix |
| 02 | Add a `--json` flag to a CLI | New code that matches existing style, without changing default output |
| 03 | Fix failing tests with one root cause | Diagnosing a float-truncation bug; the tests must not be edited |
| 04 | Split a module in two | Multi-file refactor that keeps the old imports working |
| 05 | Write tests for a module | Graded by mutation: the tests must pass on the real code and catch at least 5 of 6 injected bugs |
| 06 | Fix a crash on messy CSV data | Error recovery; the data file is restored before grading, so it cannot be "fixed" |
| 07 | Fix pagination | Two bugs at once: an off-by-one and a rounding-down page count |
| 08 | Implement `parse_duration` from a docstring | Building to a spec, including invalid-input handling |
| 09 | Rename a function everywhere | Multi-file edits, including docstrings and aliased imports |
| 10 | Fix state leaking between calls | A trap: a shallow copy looks right but fails on nested data |

## Keeping the benchmark honest

- **Every task is validated.** `python evals/run_evals.py --validate` checks that each task fails before any
  changes and passes with its reference solution, so a broken grader can't skew the results.
- **Hidden graders.** `check.py` lives outside the agent's working folder.
- **No credit for API trouble.** Rate-limit and API errors are retried and reported in their own column. They are
  never counted as the model failing a task.
- **Resumable.** Results are saved after every trial. Rerunning the same command skips finished trials and
  redoes the ones that hit errors, and the run stops cleanly if the daily free-request limit is reached.
- **Multiple trials.** Models are non-deterministic. Use `--trials 3` or more and read pass rates, not single runs.

## Results

Results are not published yet. The first full runs were cut short by OpenRouter's free-tier limit of 50
requests per day, and I'd rather publish nothing than numbers from a partial run. They will be added here as a table of
pass rate, average steps, tokens and time per model.

## Quick start

Requires Python 3.10+ and a free [OpenRouter key](https://openrouter.ai/keys).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then fill in OPENROUTER_API_KEY

# chat with the agent in a project folder (it asks before writing files or running commands)
.venv/bin/python agent.py --root /path/to/project

# check the benchmark tasks themselves (no model calls)
.venv/bin/python evals/run_evals.py --validate

# evaluate a model: 2 trials per task, results in evals/results/
.venv/bin/python evals/run_evals.py --model poolside/laguna-s-2.1:free --trials 2
```

Free model availability changes often. To see which tool-calling models are free right now:

```bash
curl -s "https://openrouter.ai/api/v1/models?supported_parameters=tools" \
  | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin)['data'] if float(m['pricing']['prompt'])==0]"
```

## Tracing

Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_HOST` in `.env` and each run appears in Langfuse as
one trace, with every model call (messages, tokens) and tool call (arguments, output, errors) nested inside it.
Without those variables, tracing is switched off.

## Limitations

- The tasks are small, single-folder Python projects. They show whether a model can drive the agent loop, not how
  it handles large codebases.
- The agent has no sandbox: shell commands run on your machine. Approval prompts are on by default in
  interactive mode, but the benchmark auto-approves them, so run it in a throwaway environment.
- Free models are rate-limited and change without notice, so results are a snapshot, not a ranking.
