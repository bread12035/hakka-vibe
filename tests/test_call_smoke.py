"""Smoke tests for every real entry point: one execution each, because every
execution costs a real call. The pricing, parsing, and arm-configuration
logic these exercise are covered by fast tests elsewhere; what this proves is
only that each path joins up end to end.
"""

import os
import shutil
from pathlib import Path

import pytest
from anthropic import Anthropic

from hakka_vibe.agents.fixer import fix
from hakka_vibe.agents.subagent import DelegationMode
from hakka_vibe.experiments.effort_and_workflow import ARMS as EFFORT_AND_WORKFLOW_ARMS
from hakka_vibe.experiments.effort_and_workflow import run_effort_and_workflow_experiment
from hakka_vibe.experiments.output_style import ARMS as OUTPUT_STYLE_ARMS
from hakka_vibe.experiments.output_style import run_output_style_experiment
from hakka_vibe.experiments.pass_by_reference import run_pass_by_reference_experiment
from hakka_vibe.experiments.prompt_ordering import ARMS as PROMPT_ORDERING_ARMS
from hakka_vibe.experiments.prompt_ordering import run_prompt_ordering_experiment
from hakka_vibe.experiments.subagent_architecture import run_subagent_experiment
from hakka_vibe.experiments.tool_search import ARMS as TOOL_SEARCH_ARMS
from hakka_vibe.experiments.tool_search import run_tool_search_experiment
from hakka_vibe.harness.call import record_one_call
from hakka_vibe.measurement.run_record import RunRecord, read_run_record, write_run_record
from hakka_vibe.runner import RUNS_PER_ARM, run_arm

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="needs credentials: these tests make real, billable calls",
)


def test_one_call_lands_on_disk_priced(tmp_path: Path) -> None:
    record = record_one_call(
        Anthropic(),
        prompt="Reply with the single word: ok",
        model="claude-haiku-4-5",
        experiment="smoke",
        arm="smoke",
        run=1,
    )
    path = write_run_record(record, root=tmp_path)

    record = read_run_record(path)
    assert record.tokens.input > 0
    assert record.tokens.output > 0
    assert record.cost.total > 0


def test_the_agent_fixes_the_fixture_and_records_what_it_cost(tmp_path: Path) -> None:
    workspace = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", workspace)

    record = fix(Anthropic(), workspace, "claude-opus-5", experiment="smoke", arm="smoke", run=1)

    assert record.passed is True
    assert len(record.calls) > 1, "a one-turn fix means the fixture is too easy"
    assert record.cost.total > 0


def test_an_arm_runs_three_times_and_summarises(tmp_path: Path) -> None:
    # The one smoke test for the runner entry: three billable runs, so it
    # proves the path joins up and nothing more. What it computes is covered
    # by the fast tests over ArmSummary.
    client = Anthropic()

    def fresh_fixture(run: int) -> Path:
        workspace = tmp_path / f"run-{run}"
        shutil.copytree("fixtures/pipeline", workspace)
        return workspace

    def run_for(run: int) -> RunRecord:
        return fix(
            client, fresh_fixture(run), "claude-opus-5", experiment="smoke", arm="smoke", run=run
        )

    summary = run_arm(
        experiment="smoke", arm="smoke", run_for=run_for, results_root=tmp_path / "results"
    )

    assert summary.runs == RUNS_PER_ARM
    assert summary.lowest_cost <= summary.median_cost <= summary.highest_cost
    assert len(list((tmp_path / "results" / "smoke" / "smoke").glob("*.json"))) == RUNS_PER_ARM


def test_the_effort_and_workflow_experiment_runs_all_six_arms(tmp_path: Path) -> None:
    # Merging the effort sweep (6a-6d) and workflow decomposition (6e-6f) into
    # one module means this single smoke test now covers six arms — pricier
    # than the four- or two-arm smoke tests below, but it's the actual entry
    # point a real run would use.
    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    summaries = run_effort_and_workflow_experiment(
        Anthropic(), fixture=fixture, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == set(EFFORT_AND_WORKFLOW_ARMS)
    for summary in summaries.values():
        assert summary.runs == 3


def test_the_output_style_experiment_runs_all_three_arms(tmp_path: Path) -> None:
    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    summaries = run_output_style_experiment(
        Anthropic(), fixture=fixture, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == set(OUTPUT_STYLE_ARMS)
    for summary in summaries.values():
        assert summary.runs == 3


def test_the_pass_by_reference_experiment_runs_all_three_arms(tmp_path: Path) -> None:
    summaries = run_pass_by_reference_experiment(
        Anthropic(), rows=200, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == {"2a", "2b", "2c"}
    for summary in summaries.values():
        assert summary.runs == 3


def test_the_prompt_ordering_experiment_runs_all_five_arms(tmp_path: Path) -> None:
    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    summaries = run_prompt_ordering_experiment(
        Anthropic(), fixture=fixture, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == set(PROMPT_ORDERING_ARMS)
    for summary in summaries.values():
        assert summary.runs == 3


def test_the_tool_search_experiment_runs_both_arms(tmp_path: Path) -> None:
    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    summaries = run_tool_search_experiment(
        Anthropic(), fixture=fixture, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == set(TOOL_SEARCH_ARMS)
    for summary in summaries.values():
        assert summary.runs == 3


def test_the_subagent_architecture_experiment_runs_all_three_arms(tmp_path: Path) -> None:
    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    summaries = run_subagent_experiment(
        Anthropic(), fixture=fixture, results_root=tmp_path / "results"
    )

    assert set(summaries) == {mode.value for mode in DelegationMode}
    for summary in summaries.values():
        assert summary.runs == 3
