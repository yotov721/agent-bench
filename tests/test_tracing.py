import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tracing


def test_tracing_is_off_without_langfuse_keys(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert not tracing.enabled()


def test_disabled_session_has_no_trace_id_and_accepts_updates(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    with tracing.session() as session, tracing.generation("m", []) as gen, tracing.tool_span("t", {}) as span:
        gen.update(output=[])
        span.update(output="x", is_error=True)
        assert session.trace_id is None


def test_placeholder_keys_from_env_example_are_not_set():
    # A copied .env.example must not switch tracing on with invalid keys.
    env_example = (Path(__file__).resolve().parent.parent / ".env.example").read_text()
    active = [l for l in env_example.splitlines() if l.startswith("LANGFUSE_")]
    assert active == []
