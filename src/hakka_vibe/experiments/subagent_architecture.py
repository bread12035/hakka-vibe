"""Experiment 3a-3c: subagent architecture.

Before fixing the fixture, the orchestrator delegates two investigation
questions to a cheaper-model subagent — one per non-entry module — and folds
the findings into its own briefing. What varies between arms is only how each
delegation's context is assembled and whether the subagent's conversation
persists; the investigation questions, the orchestrator model, and the
eventual fix loop are identical across arms.
"""

import dataclasses
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import MessageParam

from hakka_vibe.agents.fixer import fix
from hakka_vibe.agents.subagent import DelegationMode, ask, context_for_call
from hakka_vibe.harness.compress import compress
from hakka_vibe.measurement.run_record import (
    DEFAULT_RESULTS_ROOT,
    Call,
    RunRecord,
    write_run_record,
)
from hakka_vibe.runner import RUNS_PER_ARM, ArmSummary, fresh_copy_of, summarise

INVESTIGATION_QUESTIONS = [
    "In two sentences, summarise what src/pipeline/stage_1.py does.",
    "In two sentences, summarise what src/pipeline/stage_2.py does, and note anything that looks off.",
]

ORCHESTRATOR_MODEL = "claude-opus-5"
SUBAGENT_MODEL = "claude-sonnet-5"
"""The subagent runs on the cheaper model per the spec; that model variable is
kept separate from the architecture variable when results are analysed."""


def _delegate_investigation(
    client: Anthropic, *, mode: DelegationMode, workspace: Path
) -> tuple[list[str], list[Call]]:
    """Run the fixed investigation sequence under one delegation mode.

    Returns the findings and every call spent getting them — subagent calls,
    plus any compression calls the mode required — so the caller can fold
    both into the run's total.
    """
    findings: list[str] = []
    history: list[str] = []
    spent: list[Call] = []
    conversation: list[MessageParam] = []

    for index, question in enumerate(INVESTIGATION_QUESTIONS):
        if mode is not DelegationMode.PERSISTENT:
            # A brand new subagent every call has no memory of its own.
            conversation = []

        compressed = None
        if mode is DelegationMode.FRESH_COMPRESSED and history:
            compressed, compress_call = compress(
                client, ORCHESTRATOR_MODEL, text="\n\n".join(history)
            )
            spent.append(compress_call)
        elif mode is DelegationMode.FRESH_COMPRESSED:
            compressed = ""

        context = context_for_call(
            history,
            mode=mode,
            call_index=index,
            compressed=compressed,
            new_turns=history[-1:] if index > 0 else [],
        )

        answer, ask_calls, conversation = ask(
            client, SUBAGENT_MODEL, workspace, question, context=context, conversation=conversation
        )
        spent.extend(ask_calls)

        findings.append(answer)
        history.append(f"Q: {question}\nA: {answer}")

    return findings, spent


def run_subagent_experiment(
    client: Anthropic,
    *,
    fixture: Path,
    results_root: Path | None = None,
) -> dict[str, ArmSummary]:
    """Run 3a through 3c and return each arm's summary, keyed by arm id."""
    summaries: dict[str, ArmSummary] = {}
    for mode in DelegationMode:
        arm = mode.value
        records: list[RunRecord] = []
        for run in range(1, RUNS_PER_ARM + 1):
            workspace = fresh_copy_of(fixture, arm, run)
            findings, delegation_calls = _delegate_investigation(
                client, mode=mode, workspace=workspace
            )

            record = fix(
                client,
                workspace,
                ORCHESTRATOR_MODEL,
                experiment="3",
                arm=arm,
                run=run,
                briefing="\n".join(findings),
            )
            gated = dataclasses.replace(record, calls=(*delegation_calls, *record.calls))
            write_run_record(
                gated, root=results_root if results_root is not None else DEFAULT_RESULTS_ROOT
            )
            records.append(gated)
        summaries[arm] = summarise(arm, records)
    return summaries
