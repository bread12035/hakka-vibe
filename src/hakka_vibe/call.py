"""Make one call and record what it cost.

The thinnest complete path through the harness: call, capture usage, price it,
store it. Everything else in the harness thickens this path.

Cache TTL: the self-built harness writes cache at the 5 minute TTL throughout,
so no experiment differs from another by TTL unless it is testing TTL (ADR-0002).
5 minutes is the API default, so the policy is honoured by never sending an
explicit ttl. Experiment 1e, which tests the 1 hour TTL, is the one place that
will override it.
"""

from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.run_record import RunRecord, write_run_record


def record_one_call(
    client: Anthropic,
    *,
    prompt: str,
    model: str,
    experiment: str,
    arm: str,
    run: int,
    max_tokens: int = 1024,
) -> RunRecord:
    """Send one prompt and return a priced record of what it cost."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return RunRecord(
        experiment=experiment,
        arm=arm,
        run=run,
        model=model,
        usage=response.usage.model_dump(),
    )


def record_one_call_to_disk(
    client: Anthropic,
    *,
    prompt: str,
    model: str,
    experiment: str,
    arm: str,
    run: int,
    root: Path,
) -> Path:
    record = record_one_call(
        client, prompt=prompt, model=model, experiment=experiment, arm=arm, run=run
    )
    return write_run_record(record, root=root)
