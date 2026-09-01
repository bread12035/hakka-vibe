"""Experiment 3's delegate: a cheap-model helper that investigates the
workspace and reports back in text.

``ask`` is a pure function of its inputs, including the prior conversation —
it returns the updated conversation rather than mutating anything held on an
object. Nothing here needs *identity* across calls, only continuity of the
conversation itself, and a caller running DelegationMode.PERSISTENT can
thread that value explicitly between calls just as easily as a class could
carry it on self — more easily to test, since the conversation a call used is
right there in the return value instead of hidden as a side effect.
"""

from collections.abc import Sequence
from enum import Enum
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam, ToolResultBlockParam

from hakka_vibe.harness.call import (
    DEFAULT_CACHE_TTL,
    DEFAULT_EFFORT,
    DEFAULT_MAX_TOKENS,
    CacheTtl,
    Effort,
)
from hakka_vibe.harness.prompts import PromptSet
from hakka_vibe.harness.tool_schema import schema_of
from hakka_vibe.measurement.run_record import Call

DEFAULT_MAX_TURNS = 6


class DelegationMode(Enum):
    """Arms 3a-3c: what a delegation call sends as context."""

    FRESH_FULL = "3a"
    """A brand new subagent every call, given the complete history each time —
    it has no memory of its own, so the whole thing travels with every ask."""

    FRESH_COMPRESSED = "3b"
    """A brand new subagent every call, given only a summary the orchestrator
    already compressed. The compression's own cost belongs to this arm, not
    the subagent's call."""

    PERSISTENT = "3c"
    """One conversation threaded across every call in a run. Only the first
    call needs the full history; later calls send just what is new, because
    the threaded conversation already holds the rest."""


def context_for_call(
    history: Sequence[str],
    *,
    mode: DelegationMode,
    call_index: int,
    compressed: str | None = None,
    new_turns: Sequence[str] = (),
) -> list[str]:
    """What one delegation call sends, given the mode and how far in it is.

    Pure function of the mode and the caller's own bookkeeping — no subagent
    state is needed to answer this, which is what makes it testable without a
    call.
    """
    if mode is DelegationMode.FRESH_FULL:
        return list(history)
    if mode is DelegationMode.FRESH_COMPRESSED:
        return [compressed] if compressed is not None else []
    return list(history) if call_index == 0 else list(new_turns)


def read_file(workspace: Path, path: str) -> str:
    """Read a file, relative to the project root."""
    target = workspace / path
    if not target.is_file():
        return f"no such file: {path}"
    return str(target.read_text())


def system_blocks(
    *, prompts: PromptSet | None = None, cache_ttl: CacheTtl = DEFAULT_CACHE_TTL
) -> list[TextBlockParam]:
    return [
        TextBlockParam(
            type="text",
            text=(prompts or PromptSet()).render("subagent.system"),
            cache_control={"type": "ephemeral", "ttl": cache_ttl},
        )
    ]


def ask(
    client: Anthropic,
    model: str,
    workspace: Path,
    instruction: str,
    *,
    context: Sequence[str] = (),
    conversation: Sequence[MessageParam] = (),
    prompts: PromptSet | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    cache_ttl: CacheTtl = DEFAULT_CACHE_TTL,
    effort: Effort = DEFAULT_EFFORT,
) -> tuple[str, list[Call], list[MessageParam]]:
    """Investigate and answer one instruction, given prior context as text.

    Returns the answer, the calls it spent, and the updated conversation.
    Pass the returned conversation back in as ``conversation`` on the next
    call to keep this subagent "alive" (DelegationMode.PERSISTENT); pass
    nothing to start fresh (FRESH_FULL / FRESH_COMPRESSED).
    """
    registry = prompts or PromptSet()
    messages: list[MessageParam] = [
        *conversation,
        {"role": "user", "content": "\n\n".join([*context, instruction])},
    ]
    calls: list[Call] = []
    final_text = ""
    turns = 0

    while turns < max_turns:
        response = client.messages.create(
            model=model,
            max_tokens=DEFAULT_MAX_TOKENS,
            system=system_blocks(prompts=registry, cache_ttl=cache_ttl),
            output_config={"effort": effort},
            tools=[schema_of(read_file)],
            messages=messages,
        )
        turns += 1
        calls.append(Call(model=model, usage=response.usage.model_dump()))

        final_text = "\n".join(block.text for block in response.content if block.type == "text")
        tool_uses = [block for block in response.content if block.type == "tool_use"]
        if not tool_uses:
            break

        messages.append(MessageParam(role="assistant", content=response.content))
        messages.append(
            MessageParam(
                role="user",
                content=[
                    ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id=use.id,
                        content=read_file(workspace, **dict(use.input)),  # type: ignore[arg-type]
                    )
                    for use in tool_uses
                ],
            )
        )

    updated_conversation = list(messages)
    if final_text:
        updated_conversation.append(MessageParam(role="assistant", content=final_text))
    return final_text, calls, updated_conversation
