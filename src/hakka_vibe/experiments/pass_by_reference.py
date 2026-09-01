"""Experiment 2a-2c: pass by reference (self-built harness).

Compares three ways of getting a large dataset in front of the model: the
full text in context (2a), an in-process DataFrame behind a DataRef (2b), and
a SQLite connection behind a DataRef (2c). Pass/fail is whether the analysis
answer is numerically correct — independent of how the data reached the model.
"""

import dataclasses
import random
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from anthropic import Anthropic

from hakka_vibe.agents.analyst import analyse
from hakka_vibe.harness.dataref import DataRef
from hakka_vibe.measurement.run_record import DEFAULT_RESULTS_ROOT, RunRecord, write_run_record
from hakka_vibe.runner import RUNS_PER_ARM, ArmSummary, summarise


def generate_orders(*, rows: int, seed: int) -> pd.DataFrame:
    """A synthetic, seeded orders table: reproducible, so runs stay comparable."""
    rng = random.Random(seed)
    return pd.DataFrame(
        {
            "customer_id": [rng.randrange(1, rows // 20 + 1) for _ in range(rows)],
            "amount": [round(rng.uniform(1, 500), 2) for _ in range(rows)],
        }
    )


@dataclass(frozen=True)
class TopCustomer:
    customer_id: int
    total: float


def top_customer_by_total(orders: pd.DataFrame) -> TopCustomer:
    """The known-correct answer, independent of whichever method — pandas,
    SQL, a hand loop — the agent under measurement chooses to use."""
    totals = orders.groupby("customer_id")["amount"].sum()
    winner = totals.idxmax()
    return TopCustomer(customer_id=int(winner), total=round(float(totals[winner]), 2))


def orders_as_sqlite(orders: pd.DataFrame) -> sqlite3.Connection:
    """The same data, as a SQLite connection, for arm 2c."""
    connection = sqlite3.connect(":memory:")
    orders.to_sql("orders", connection, index=False)
    return connection


_ANSWER_LINE = re.compile(r"ANSWER:\s*(\d+)\s+([\d.]+)")


def parse_answer(text: str) -> TopCustomer | None:
    """Read the agent's final "ANSWER: <customer_id> <total>" line, if present.

    None means no parseable answer — a fail, distinct from a wrong answer, but
    both fail the gate.
    """
    match = _ANSWER_LINE.search(text)
    if match is None:
        return None
    return TopCustomer(customer_id=int(match.group(1)), total=float(match.group(2)))


def matches_expected(
    answer: TopCustomer, expected: TopCustomer, *, tolerance: float = 0.01
) -> bool:
    """Whether an answer counts as correct: right customer, total within a cent."""
    return (
        answer.customer_id == expected.customer_id
        and abs(answer.total - expected.total) <= tolerance
    )


def orders_as_csv_text(orders: pd.DataFrame) -> str:
    """The dataset serialized whole, for arm 2a's pass-by-value baseline."""
    return orders.to_csv(index=False)


@dataclass(frozen=True)
class ArmSetup:
    """What one arm gives the analyst: a live reference or not, and the task
    context text it starts from."""

    data: DataRef | None
    task_context: str


def build_arms(orders: pd.DataFrame) -> dict[str, ArmSetup]:
    """The three ways of presenting ``orders`` to the analyst, keyed by arm id."""
    return {
        "2a": ArmSetup(
            data=None,
            task_context=f"Dataset (CSV):\n{orders_as_csv_text(orders)}",
        ),
        "2b": ArmSetup(
            data=DataRef(name="orders", raw=orders),
            task_context="The dataset is available as the variable `orders` (a pandas DataFrame).",
        ),
        "2c": ArmSetup(
            data=DataRef(name="orders_db", raw=orders_as_sqlite(orders)),
            task_context=(
                "The dataset is available as a SQLite connection named `orders_db`, "
                "with one table `orders` (columns: customer_id, amount)."
            ),
        ),
    }


def run_pass_by_reference_experiment(
    client: Anthropic,
    *,
    rows: int = 2_000,
    seed: int = 20260826,
    model: str,
    results_root: Path | None = None,
) -> dict[str, ArmSummary]:
    """Run 2a through 2c and return each arm's summary, keyed by arm id.

    No fixture copy is needed between runs: the dataset is read-only, and
    each run starts with its own fresh namespace, so nothing carries over by
    accident.
    """
    orders = generate_orders(rows=rows, seed=seed)
    expected = top_customer_by_total(orders)
    arms = build_arms(orders)

    summaries: dict[str, ArmSummary] = {}
    for arm, setup in arms.items():
        records: list[RunRecord] = []
        for run in range(1, RUNS_PER_ARM + 1):
            record, text = analyse(
                client,
                model,
                task_context=setup.task_context,
                data=setup.data,
                experiment="2",
                arm=arm,
                run=run,
            )
            answer = parse_answer(text)
            gated = dataclasses.replace(
                record, passed=answer is not None and matches_expected(answer, expected)
            )
            root = results_root if results_root is not None else DEFAULT_RESULTS_ROOT
            write_run_record(gated, root=root)
            records.append(gated)
        summaries[arm] = summarise(arm, records)
    return summaries
