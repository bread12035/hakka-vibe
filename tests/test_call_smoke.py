"""Smoke test for the run entry point.

Exactly one test lives here, because every execution costs a real call. The
pricing and parsing this exercises are covered by fast tests elsewhere; what
this proves is only that the whole path joins up.
"""

import os
from pathlib import Path

import pytest

from hakka_vibe.call import record_one_call
from hakka_vibe.run_record import read_run_record, write_run_record

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="needs credentials: this test makes a real, billable call",
)


def test_one_call_lands_on_disk_priced(tmp_path: Path) -> None:
    from anthropic import Anthropic

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
    import shutil

    from anthropic import Anthropic

    from hakka_vibe.agent import FixerAgent

    workspace = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", workspace)

    agent = FixerAgent(client=Anthropic(), workspace=workspace, model="claude-opus-5")
    record = agent.fix(experiment="smoke", arm="smoke", run=1)

    assert record.passed is True
    assert agent.turns_taken > 1, "a one-turn fix means the fixture is too easy"
    assert len(record.calls) == agent.turns_taken
    assert record.cost.total > 0


def test_an_arm_runs_three_times_and_summarises(tmp_path: Path) -> None:
    # The one smoke test for the runner entry: three billable runs, so it proves
    # the path joins up and nothing more. What it computes is covered by the
    # fast tests over ArmSummary.
    import shutil

    from anthropic import Anthropic

    from hakka_vibe.agent import FixerAgent
    from hakka_vibe.experiment import RUNS_PER_ARM, run_arm

    def fresh_fixture(run: int) -> Path:
        workspace = tmp_path / f"run-{run}"
        shutil.copytree("fixtures/pipeline", workspace)
        return workspace

    client = Anthropic()

    def agent_for(run: int) -> FixerAgent:
        return FixerAgent(client=client, workspace=fresh_fixture(run), model="claude-opus-5")

    summary = run_arm(
        experiment="smoke",
        arm="smoke",
        agent_for=agent_for,
        results_root=tmp_path / "results",
    )

    assert summary.runs == RUNS_PER_ARM
    assert summary.lowest_cost <= summary.median_cost <= summary.highest_cost
    assert len(list((tmp_path / "results" / "smoke" / "smoke").glob("*.json"))) == RUNS_PER_ARM


def test_the_effort_sweep_runs_all_four_arms(tmp_path: Path) -> None:
    import shutil

    from anthropic import Anthropic

    from hakka_vibe.experiments.effort_sweep import ARMS, run_effort_sweep

    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    summaries = run_effort_sweep(
        Anthropic(), fixture=fixture, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == set(ARMS)
    for summary in summaries.values():
        assert summary.runs == 3


def test_the_output_style_experiment_runs_all_three_arms(tmp_path: Path) -> None:
    import shutil

    from anthropic import Anthropic

    from hakka_vibe.experiments.output_style import ARMS, run_output_style_experiment

    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    summaries = run_output_style_experiment(
        Anthropic(), fixture=fixture, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == set(ARMS)
    for summary in summaries.values():
        assert summary.runs == 3


def test_the_pass_by_reference_experiment_runs_all_three_arms(tmp_path: Path) -> None:
    from anthropic import Anthropic

    from hakka_vibe.experiments.pass_by_reference import run_pass_by_reference_experiment

    summaries = run_pass_by_reference_experiment(
        Anthropic(), rows=200, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == {"2a", "2b", "2c"}
    for summary in summaries.values():
        assert summary.runs == 3


def test_the_prompt_ordering_experiment_runs_all_five_arms(tmp_path: Path) -> None:
    import shutil

    from anthropic import Anthropic

    from hakka_vibe.experiments.prompt_ordering import ARMS, run_prompt_ordering_experiment

    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    summaries = run_prompt_ordering_experiment(
        Anthropic(), fixture=fixture, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == set(ARMS)
    for summary in summaries.values():
        assert summary.runs == 3


def test_the_tool_search_experiment_runs_both_arms(tmp_path: Path) -> None:
    import shutil

    from anthropic import Anthropic

    from hakka_vibe.experiments.tool_search import ARMS, run_tool_search_experiment

    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    summaries = run_tool_search_experiment(
        Anthropic(), fixture=fixture, model="claude-opus-5", results_root=tmp_path / "results"
    )

    assert set(summaries) == set(ARMS)
    for summary in summaries.values():
        assert summary.runs == 3
