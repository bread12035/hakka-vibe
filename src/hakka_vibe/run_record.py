"""Run records: what one run of one arm cost, and the raw usage behind it.

This is the seam the experiments are tested at. Two adapters feed it — the API
response and a Claude Code session transcript — and both report usage under the
same field names, so the parsing below serves either.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hakka_vibe.cost import ZERO_COST, Cost, TokenCounts, cost_of

__all__ = [
    "DEFAULT_RESULTS_ROOT",
    "Call",
    "RunRecord",
    "read_run_record",
    "token_counts_from_usage",
    "write_run_record",
]

DEFAULT_RESULTS_ROOT = Path("results")
"""Where run records live, relative to the repo root, and under version control.

Every run of every arm is kept, so a later question can be answered by
re-reading the raw usage instead of re-running 72 billable runs.
"""


class UsageFieldMissing(KeyError):
    """A usage mapping lacked a field the cost model prices.

    Raised rather than defaulting to zero: a silently absent field prices that
    token class at $0, which does not fail, does not warn, and quietly
    invalidates every conclusion drawn from the run.
    """


def _required(mapping: Mapping[str, Any], field: str, *, within: str) -> Any:
    if field not in mapping:
        raise UsageFieldMissing(
            f"{within} has no {field!r}: refusing to price it as zero. "
            f"Present fields: {sorted(mapping)}"
        )
    return mapping[field]


def _nested_count(usage: Mapping[str, Any], container: str, field: str) -> int:
    """Read a count out of an optional nested detail object.

    The container is absent-as-null when there is nothing to report, but when it
    is present the field inside it must be too.
    """
    nested = _required(usage, container, within="usage")
    if nested is None:
        return 0
    return _required(nested, field, within=container) or 0


def token_counts_from_usage(usage: Mapping[str, Any]) -> TokenCounts:
    """Read token counts out of a usage mapping.

    Cache writes come from the per-TTL split rather than
    ``cache_creation_input_tokens``, which is their sum: the two TTLs are priced
    differently, so a blended total cannot be priced correctly.
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

    Priced per call rather than once for the whole run: a Claude Code session
    can switch models mid-conversation — confirmed on this project's own
    transcripts — and pricing a mixed run at one model over- or undercharges
    whichever calls ran on the other one.
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
    """One run of one arm: what it was, whether it passed, and what it cost."""

    experiment: str
    arm: str
    run: int
    model: str
    """The model this run was configured for. Reporting label, not the pricing
    input — each call carries and is priced at its own model."""
    calls: tuple[Call, ...]
    """Every call the run took, in order, verbatim.

    A run is a whole task, so it spans many calls. They are kept separately
    because summing before storing loses where in a task the cost went.
    """
    passed: bool | None = None
    """Whether the run met its task's gate, or None where no gate applies."""

    fixture: str | None = None
    """Fingerprint of the fixture this run was measured on.

    A fixture is deepened and regenerated when it proves too easy, and results
    from before that are not comparable with results from after. Recording which
    version a run used is what keeps the two apart.
    """

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
    """Store a run record under its experiment and arm, and return where it went.

    Only the raw usage is stored. Token counts and cost are derived on read, so a
    correction to the cost model reprices every past run instead of stranding
    them at whatever the model said on the day they were written.
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
        fixture=stored["fixture"],
        calls=tuple(Call(model=c["model"], usage=c["usage"]) for c in stored["calls"]),
    )
