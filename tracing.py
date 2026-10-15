"""Langfuse tracing. Everything here is a no-op unless LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set."""

import os
import uuid
from contextlib import contextmanager, nullcontext
from typing import Any


def enabled() -> bool:
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def _client():
    from langfuse import get_client

    return get_client()


def _plain(value: Any) -> Any:
    """Convert SDK objects (pydantic models) nested in messages into plain JSON-able data."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value


class _NoopObservation:
    def update(self, **_: Any) -> None:
        pass


class _Observation:
    def __init__(self, obs: Any):
        self._obs = obs

    def update(self, **fields: Any) -> None:
        usage = fields.pop("usage", None)
        if usage is not None:
            fields["usage_details"] = {
                "input": usage.prompt_tokens,
                "output": usage.completion_tokens,
            }
        if "output" in fields:
            fields["output"] = _plain(fields["output"])
        if fields.pop("is_error", False):
            fields["level"] = "ERROR"
        self._obs.update(**fields)


@contextmanager
def session():
    """Root observation for one interactive session; groups every turn under a single session id."""
    if not enabled():
        yield _NoopObservation()
        return
    from langfuse import propagate_attributes

    session_id = uuid.uuid4().hex
    with propagate_attributes(session_id=session_id):
        with _client().start_as_current_observation(name="agent-session", as_type="agent") as root:
            yield _Observation(root)


@contextmanager
def generation(model: str, messages: list):
    """One model call."""
    if not enabled():
        yield _NoopObservation()
        return
    with _client().start_as_current_observation(
        name="messages.create", as_type="generation", model=model, input=_plain(messages)
    ) as gen:
        yield _Observation(gen)


@contextmanager
def tool_span(name: str, args: dict):
    """One tool execution."""
    if not enabled():
        yield _NoopObservation()
        return
    with _client().start_as_current_observation(name=name, as_type="tool", input=args) as span:
        yield _Observation(span)


def flush() -> None:
    if enabled():
        _client().flush()
