"""Deterministic parts of the agent's configuration: no call, no fixture.

The output style and the frozen system prompt are pure inputs to the request,
so they are pinned down here rather than only exercised by a billable smoke
test.
"""

from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agent import DEFAULT_EFFORT, FixerAgent
from hakka_vibe.output_style import load_style


def agent(**overrides: object) -> FixerAgent:
    return FixerAgent(
        client=Anthropic(api_key="not-used-by-these-tests"),
        workspace=Path("fixtures/pipeline"),
        model="claude-opus-5",
        **overrides,  # type: ignore[arg-type]
    )


def test_the_default_arm_carries_no_style_instruction() -> None:
    # Arm 5a is the baseline: Anthropic's own voice, nothing appended.
    blocks = agent().system_blocks_for_test()

    assert len(blocks) == 1
    assert "caveman" not in blocks[0]["text"].lower()


def test_a_style_is_appended_after_the_frozen_prompt_not_mixed_into_it() -> None:
    # Appended, never used to rewrite the frozen block: rewriting it would
    # invalidate the cache prefix the task instructions depend on.
    caveman = agent(output_style=load_style("caveman"))

    blocks = caveman.system_blocks_for_test()
    task_prompt = agent().system_blocks_for_test()[0]["text"]

    assert blocks[0]["text"].startswith(task_prompt)
    assert "no articles" in blocks[0]["text"].lower()


def test_effort_defaults_to_anthropics_own_default() -> None:
    assert agent().effort == DEFAULT_EFFORT


def test_each_arm_can_set_its_own_effort() -> None:
    assert agent(effort="low").effort == "low"
