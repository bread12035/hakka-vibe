"""Make one call and record what it cost.

The thinnest complete path through the harness: call, capture usage, price it,
store it. Everything else in the harness thickens this path.
"""

from typing import Literal

from anthropic import Anthropic

from hakka_vibe.measurement.run_record import Call, RunRecord

CacheTtl = Literal["5m", "1h"]

DEFAULT_CACHE_TTL: CacheTtl = "5m"
"""The TTL every experiment writes cache at, unless it is testing TTL itself.

Fixed so that no two experiments differ by cache write price without meaning
to: the 1 hour TTL costs twice the input rate to write against 1.25x at 5
minutes (ADR-0002). Experiment 1e overrides it deliberately; nothing else
should.
"""

DEFAULT_MAX_TOKENS = 16_000
"""High enough that a response is not truncated mid-answer.

A truncated run still records as a run, so a low ceiling corrupts a measurement
without ever failing.
"""


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
    """Send one prompt and return a priced record of what it cost."""
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
