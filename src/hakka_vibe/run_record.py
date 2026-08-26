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

from hakka_vibe.cost import Cost, TokenCounts, cost_of

__all__ = [
    "Cost",
    "RunRecord",
    "TokenCounts",
    "cost_of",
    "read_run_record",
    "token_counts_from_usage",
    "write_run_record",
]


def token_counts_from_usage(usage: Mapping[str, Any]) -> TokenCounts:
    """Read token counts out of a usage mapping.

    Cache writes come from the per-TTL split rather than
    ``cache_creation_input_tokens``, which is their sum: the two TTLs are priced
    differently, so a blended total cannot be priced correctly.
    """
    cache_write = usage.get("cache_creation") or {}
    output_details = usage.get("output_tokens_details") or {}

    return TokenCounts(
        input=usage.get("input_tokens", 0),
        output=usage.get("output_tokens", 0),
        thinking=output_details.get("thinking_tokens", 0),
        cache_read=usage.get("cache_read_input_tokens", 0),
        cache_write_5m=cache_write.get("ephemeral_5m_input_tokens", 0),
        cache_write_1h=cache_write.get("ephemeral_1h_input_tokens", 0),
    )


@dataclass(frozen=True)
class RunRecord:
    """One run of one arm: what it was, whether it passed, and what it cost."""

    experiment: str
    arm: str
    run: int
    model: str
    usage: Mapping[str, Any]
    passed: bool | None = None
    """Whether the run met its task's gate, or None where no gate applies."""

    @property
    def tokens(self) -> TokenCounts:
        return token_counts_from_usage(self.usage)

    @property
    def cost(self) -> Cost:
        return cost_of(self.tokens, model=self.model)


def write_run_record(record: RunRecord, *, root: Path) -> Path:
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
                "usage": record.usage,
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
        usage=stored["usage"],
    )
