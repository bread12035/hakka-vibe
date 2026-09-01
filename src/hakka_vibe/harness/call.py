"""Shared knobs for a single model call: effort, cache TTL, and token ceiling.

Every agent module needs the same three call-level settings, so they live in
one place rather than being redeclared per agent.
"""

from typing import Literal

from anthropic import Anthropic

from hakka_vibe.measurement.run_record import Call, RunRecord

Effort = Literal["low", "medium", "high", "xhigh", "max"]
DEFAULT_EFFORT: Effort = "high"

CacheTtl = Literal["5m", "1h"]
DEFAULT_CACHE_TTL: CacheTtl = "5m"
"""What every self-built-harness experiment writes cache at, unless the arm is
testing TTL itself (experiment 1e). A 1 hour write costs 2x the input rate
against 1.25x at 5 minutes, so no two arms should differ on this by accident."""

DEFAULT_MAX_TOKENS = 16_000
"""High enough that a response is not truncated mid-answer — a truncated run
still records as a run, so a low ceiling would corrupt a measurement silently."""


def record_one_call(
    client: Anthropic,
    *,
    prompt: str,
    model: str,
    experiment: str,
    arm: str,
    run: int,
    cache_ttl: CacheTtl = DEFAULT_CACHE_TTL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> RunRecord:
    """Send one prompt and return a priced record of what it cost.

    The smallest complete path through the harness: call, capture usage,
    price it, done. Everything else thickens this path with a loop.
    """
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        cache_control={"type": "ephemeral", "ttl": cache_ttl},
        messages=[{"role": "user", "content": prompt}],
    )
    return RunRecord(
        experiment=experiment,
        arm=arm,
        run=run,
        model=model,
        calls=(Call(model=model, usage=response.usage.model_dump()),),
    )
