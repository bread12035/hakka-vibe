"""Experiment 2's agent: answers one question about a dataset by writing and
running Python.

One public entry point, ``analyse``. Its one tool, ``run_code``, is never
called by anything except this module's own dispatch — same shape as
agents/fixer.py, applied to a different task.
"""

from typing import Any

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam, ToolResultBlockParam

from hakka_vibe.harness.call import (
    DEFAULT_CACHE_TTL,
    DEFAULT_EFFORT,
    DEFAULT_MAX_TOKENS,
    CacheTtl,
    Effort,
)
from hakka_vibe.harness.dataref import DataRef
from hakka_vibe.harness.prompts import PromptSet
from hakka_vibe.harness.sandbox import execute_python
from hakka_vibe.harness.tool_schema import schema_of
from hakka_vibe.measurement.run_record import Call, RunRecord

DEFAULT_MAX_TURNS = 20


def run_code(namespace: dict[str, Any], code: str) -> str:
    """Run Python and return what it printed. State carries to your next call."""
    return execute_python(code, namespace=namespace)


def system_blocks(
    *, prompts: PromptSet | None = None, cache_ttl: CacheTtl = DEFAULT_CACHE_TTL
) -> list[TextBlockParam]:
    return [
        TextBlockParam(
            type="text",
            text=(prompts or PromptSet()).render("analyst.system"),
            cache_control={"type": "ephemeral", "ttl": cache_ttl},
        )
    ]


def analyse(
    client: Anthropic,
    model: str,
    *,
    task_context: str,
    experiment: str,
    arm: str,
    run: int,
    data: DataRef | None = None,
    prompts: PromptSet | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    cache_ttl: CacheTtl = DEFAULT_CACHE_TTL,
    effort: Effort = DEFAULT_EFFORT,
) -> tuple[RunRecord, str]:
    """Work the question until an answer line appears or the turn budget runs out.

    Returns the run record and the final text, so the caller can gate it with
    its own parse_answer/matches_expected — that judgement stays out of this
    module's capabilities, which only need to answer, not grade themselves.
    """
    registry = prompts or PromptSet()
    namespace: dict[str, Any] = {}
    if data is not None:
        namespace[data.name] = data.raw
        task_context = f"{task_context}\n\n{data.preview()}"

    messages: list[MessageParam] = [
        {"role": "user", "content": registry.render("analyst.task", context=task_context)}
    ]
    calls: list[Call] = []
    final_text = ""
    turns_taken = 0

    while turns_taken < max_turns:
        response = client.messages.create(
            model=model,
            max_tokens=DEFAULT_MAX_TOKENS,
            system=system_blocks(prompts=registry, cache_ttl=cache_ttl),
            output_config={"effort": effort},
            tools=[schema_of(run_code)],
            messages=messages,
        )
        turns_taken += 1
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
                        content=run_code(namespace, **dict(use.input)),  # type: ignore[arg-type]
                    )
                    for use in tool_uses
                ],
            )
        )

    return (
        RunRecord(experiment=experiment, arm=arm, run=run, model=model, calls=tuple(calls)),
        final_text,
    )
