"""Experiment 6e-6f arm configuration tests."""

from pathlib import Path

from hakka_vibe.experiments.workflow_decomposition import ARMS


def test_6e_is_high_effort() -> None:
    assert ARMS["6e"].effort == "high"


def test_6f_is_low_effort() -> None:
    # The hypothesis: an explicit plan lets low effort hold up where it
    # otherwise wouldn't — the comparison point is 6a (plain low effort, no
    # plan) from the effort sweep.
    assert ARMS["6f"].effort == "low"


def test_both_arms_build_an_agent_with_workflow_enabled(tmp_path: Path) -> None:
    # Both 6e and 6f are the plan-first arms; the no-plan baseline lives in
    # ticket 06 as 6a/6c, not here.
    import shutil

    from anthropic import Anthropic

    from hakka_vibe.experiments.workflow_decomposition import build_agent

    fixture = tmp_path / "pipeline"
    shutil.copytree("fixtures/pipeline", fixture)

    for arm in ("6e", "6f"):
        agent = build_agent(
            arm, 1, client=Anthropic(api_key="unused"), fixture=fixture, model="claude-opus-5"
        )
        assert agent.workflow is True
        assert agent.effort == ARMS[arm].effort
