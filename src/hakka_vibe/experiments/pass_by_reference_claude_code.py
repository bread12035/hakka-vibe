"""Experiment 2d-2e: pass by reference, run under Claude Code.

Unlike 2a-2c, this harness cannot execute these arms itself — that would mean
this session spawning another copy of itself to drive. What this module
provides is everything around that manual step: the materials each arm's
Claude Code session is started from, and grading the transcript that session
produces.

Operator procedure, once materials are written:

1. Start a fresh Claude Code session for the arm.
2. Paste ``prompt_2d`` (or ``prompt_2e``) as the first message.
3. When the session ends, note its transcript path
   (``~/.claude/projects/<project>/<session-id>.jsonl``).
4. Call ``grade_transcript`` with that path and ``materials.expected``.

Repeat three times per arm, per the spec's run count.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from hakka_vibe.claude_code_adapter import final_assistant_text, run_record_from_transcript
from hakka_vibe.experiments.pass_by_reference import (
    TopCustomer,
    generate_orders,
    matches_expected,
    orders_as_csv_text,
    parse_answer,
    top_customer_by_total,
)
from hakka_vibe.run_record import RunRecord

_ANSWER_INSTRUCTION = (
    "When you have the answer, reply with a final line in exactly this form, "
    "with no other text on that line:\n\nANSWER: <customer_id> <total>"
)


@dataclass(frozen=True)
class Materials:
    """What one operator run of arms 2d/2e needs: the data and both prompts."""

    orders: pd.DataFrame
    expected: TopCustomer
    csv_path: Path
    prompt_2d: str
    prompt_2e: str


def write_materials(root: Path, *, rows: int, seed: int) -> Materials:
    """Write the dataset to disk and build both arms' starting prompts."""
    orders = generate_orders(rows=rows, seed=seed)
    csv_path = root / "orders.csv"
    csv_path.write_text(orders_as_csv_text(orders))

    question = "Which customer_id has the highest total amount, and what is that total?"

    prompt_2d = (
        f"The dataset is at {csv_path.name}, in this directory. {question}\n\n{_ANSWER_INSTRUCTION}"
    )
    prompt_2e = (
        f"Dataset (CSV):\n{orders_as_csv_text(orders)}\n\n{question}\n\n{_ANSWER_INSTRUCTION}"
    )

    return Materials(
        orders=orders,
        expected=top_customer_by_total(orders),
        csv_path=csv_path,
        prompt_2d=prompt_2d,
        prompt_2e=prompt_2e,
    )


def grade_transcript(transcript: Path, *, expected: TopCustomer, arm: str, run: int) -> RunRecord:
    """Turn a completed Claude Code session into a graded, priced run record."""
    answer = parse_answer(final_assistant_text(transcript))
    passed = answer is not None and matches_expected(answer, expected)
    return run_record_from_transcript(transcript, experiment="2", arm=arm, run=run, passed=passed)
