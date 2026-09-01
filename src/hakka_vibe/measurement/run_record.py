"""RunRecord: what one run of one arm cost, built from raw usage.

This is the project's primary seam. Two real adapters feed it — an Anthropic
API response, and a Claude Code session transcript (measurement/claude_code_
adapter.py) — both reporting usage under the same field names, so one parser
serves either. It is a pure, no-network boundary: pricing errors here would
silently invalidate every run's conclusion, so this is where test density
belongs.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hakka_vibe.measurement.cost import ZERO_COST, Cost, TokenCounts, cost_of

DEFAULT_RESULTS_ROOT = Path("results")
"""Every run of every arm lands here, under version control, keyed by
experiment/arm/run — so a later question can be answered by re-reading raw
usage instead of re-running a billable arm."""


class UsageFieldMissing(KeyError):
    """A usage mapping lacked a field the cost model prices.

    Raised rather than defaulted to zero: a silently-absent field prices that
    token class at $0 with no failure and no warning, quietly invalidating
    every conclusion drawn from the run.
    """


def _required(mapping: Mapping[str, Any], field: str, *, within: str) -> Any:
    if field not in mapping:
        raise UsageFieldMissing(f"{within} has no {field!r}. Present fields: {sorted(mapping)}")
    return mapping[field]


def _nested_count(usage: Mapping[str, Any], container: str, field: str) -> int:
    nested = _required(usage, container, within="usage")
    if nested is None:
        return 0
    return _required(nested, field, within=container) or 0


def token_counts_from_usage(usage: Mapping[str, Any]) -> TokenCounts:
    """Read token counts out of one API-shaped usage mapping.

    Cache writes come from the per-TTL split, not ``cache_creation_input_
    tokens`` (their sum) — the two TTLs price differently, so a blended total
    can't be priced correctly.
    """
    return TokenCounts(
        input=_required(usage, "input_tokens", within="usage"),
        output=_required(usage, "output_tokens", within="usage"),
        thinking=_nested_count(usage, "output_tokens_details", "thinking_tokens"),
        cache_read=_required(usage, "cache_read_input_tokens", within="usage") or 0,
        cache_write_5m=_nested_count(usage, "cache_creation", "ephemeral_5m_input_tokens"),
        cache_write_1h=_nested_count(usage, "cache_creation", "ephemeral_1h_input_tokens"),
    )


@dataclass(frozen=True)
class Call:
    """One call's raw usage and the model that produced it.

    Priced per call, not once for a whole run: a Claude Code session can
    switch models mid-conversation, and pricing a mixed run at one model
    over- or under-charges whichever calls ran on the other.
    """

    model: str
    usage: Mapping[str, Any]

    @property
    def tokens(self) -> TokenCounts:
        return token_counts_from_usage(self.usage)

    @property
    def cost(self) -> Cost:
        return cost_of(self.tokens, model=self.model)


@dataclass(frozen=True)
class RunRecord:
    """One run of one arm: identity, every call it made, and whether it passed."""

    experiment: str
    arm: str
    run: int
    model: str
    """The model this run was configured for — a reporting label; each call is
    still priced at its own model, in case of a mid-run switch."""
    calls: tuple[Call, ...]
    passed: bool | None = None
    fixture: str | None = None
    """Fingerprint of the fixture this run was measured on, so a later
    deepening-and-regeneration can't get silently compared against it."""

    @property
    def tokens(self) -> TokenCounts:
        total = TokenCounts()
        for call in self.calls:
            total = total + call.tokens
        return total

    @property
    def cost(self) -> Cost:
        total = ZERO_COST
        for call in self.calls:
            total = total + call.cost
        return total


def write_run_record(record: RunRecord, *, root: Path = DEFAULT_RESULTS_ROOT) -> Path:
    """Store a run record under its experiment/arm/run, and return the path.

    Only raw usage is stored — cost is derived on read, so a correction to the
    pricing table reprices every past run instead of stranding them at
    whatever it said the day they were written.
    """
    path = root / record.experiment / record.arm / f"{record.run}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "experiment": record.experiment,
                "arm": record.arm,
                "run": record.run,
                "model": record.model,
                "passed": record.passed,
                "fixture": record.fixture,
                "calls": [{"model": call.model, "usage": call.usage} for call in record.calls],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return path


def read_run_record(path: Path) -> RunRecord:
    stored = json.loads(path.read_text())
    return RunRecord(
        experiment=stored["experiment"],
        arm=stored["arm"],
        run=stored["run"],
        model=stored["model"],
        passed=stored["passed"],
        fixture=stored.get("fixture"),
        calls=tuple(Call(model=c["model"], usage=c["usage"]) for c in stored["calls"]),
    )
