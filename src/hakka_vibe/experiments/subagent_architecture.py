"""Experiment 3a-3c: subagent architecture.

Before fixing the fixture, the orchestrator delegates two investigation
questions to a cheaper-model subagent — one per non-entry module — and folds
the findings into its own briefing. What varies between arms is only how each
delegation's context is assembled and whether the subagent persists; the
investigation questions, the orchestrator model, and the eventual fix loop are
identical across arms.
"""

import dataclasses
from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agent import FixerAgent
from hakka_vibe.compress import compress
from hakka_vibe.experiment import RUNS_PER_ARM, ArmSummary, fresh_copy_of, summarise
from hakka_vibe.run_record import DEFAULT_RESULTS_ROOT, Call, RunRecord, write_run_record
from hakka_vibe.subagent import DelegationMode, Subagent, context_for_call

INVESTIGATION_QUESTIONS = [
    "In two sentences, summarise what src/pipeline/stage_1.py does.",
    "In two sentences, summarise what src/pipeline/stage_2.py does, and note anything that looks off.",
]

ORCHESTRATOR_MODEL = "claude-opus-5"
SUBAGENT_MODEL = "claude-sonnet-5"
"""Subagent runs on the cheaper model per the spec; the model variable is kept
separate from the architecture variable when the results are analysed."""


def _delegate_investigation(
    client: Anthropic, *, mode: DelegationMode, workspace: Path
) -> tuple[list[str], list[Call]]:
    """Run the fixed investigation sequence under one delegation mode.

    Returns the findings and every call spent getting them — subagent calls,
    plus any compression calls the mode required — so the caller can fold both
    into the run's total.
    """
    findings: list[str] = []
    history: list[str] = []
    spent: list[Call] = []
    subagent = Subagent(client=client, model=SUBAGENT_MODEL, workspace=workspace)

    for index, question in enumerate(INVESTIGATION_QUESTIONS):
        if mode is not DelegationMode.PERSISTENT:
            subagent = Subagent(client=client, model=SUBAGENT_MODEL, workspace=workspace)

        compressed = None
        if mode is DelegationMode.FRESH_COMPRESSED and history:
            compressed, compress_call = compress(client, ORCHESTRATOR_MODEL, text="\n\n".join(history))
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

        before = len(subagent.calls)
        answer = subagent.ask(question, context=context)
        spent.extend(subagent.calls[before:])

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
            findings, delegation_calls = _delegate_investigation(client, mode=mode, workspace=workspace)

            fixer = FixerAgent(
                client=client,
                workspace=workspace,
                model=ORCHESTRATOR_MODEL,
                briefing="\n".join(findings),
            )
            record = fixer.fix(experiment="3", arm=arm, run=run)
            gated = dataclasses.replace(record, calls=(*delegation_calls, *record.calls))
            write_run_record(gated, root=results_root if results_root is not None else DEFAULT_RESULTS_ROOT)
            records.append(gated)
        summaries[arm] = summarise(arm, records)
    return summaries
