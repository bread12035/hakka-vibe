"""Compressing investigation history for subagent arm 3b's handoff.

The compression call runs on the orchestrator's own model, and its cost
belongs to the arm that asked for it — not to whatever the subagent does with
the result. The caller folds the returned ``Call`` into that arm's run record;
this function only produces the summary and the call that made it.
"""

from anthropic import Anthropic

from hakka_vibe.harness.call import (
    DEFAULT_CACHE_TTL,
    DEFAULT_EFFORT,
    DEFAULT_MAX_TOKENS,
    CacheTtl,
    Effort,
)
from hakka_vibe.harness.prompts import PromptSet
from hakka_vibe.measurement.run_record import Call


def compress(
    client: Anthropic,
    model: str,
    *,
    text: str,
    prompts: PromptSet | None = None,
    cache_ttl: CacheTtl = DEFAULT_CACHE_TTL,
    effort: Effort = DEFAULT_EFFORT,
) -> tuple[str, Call]:
    """Summarize ``text`` and return the summary plus the call that produced it."""
    registry = prompts or PromptSet()
    response = client.messages.create(
        model=model,
        max_tokens=DEFAULT_MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": registry.render("compress.system"),
                "cache_control": {"type": "ephemeral", "ttl": cache_ttl},
            }
        ],
        output_config={"effort": effort},
        messages=[{"role": "user", "content": text}],
    )
    summary = "\n".join(block.text for block in response.content if block.type == "text")
    return summary, Call(model=model, usage=response.usage.model_dump())
