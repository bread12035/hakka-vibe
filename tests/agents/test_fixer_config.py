"""Deterministic parts of the agent's configuration: no call, no fixture.

The output style and the frozen system prompt are pure inputs to the request,
so they are pinned down here rather than only exercised by a billable smoke
test.
"""

from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agents.fixer import DEFAULT_EFFORT, FixerAgent
from hakka_vibe.seams.output_style import load_style


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


def test_the_agents_layout_setting_is_what_orders_its_messages() -> None:
    from hakka_vibe.seams.prompt_layout import PromptLayout

    history = [{"role": "user", "content": "task"}, {"role": "assistant", "content": "turn 1"}]

    baseline = agent(prompt_layout=PromptLayout.BASELINE).messages_for_test(history)
    dynamic_first = agent(prompt_layout=PromptLayout.DYNAMIC_FIRST).messages_for_test(history)

    assert baseline[-1]["content"].startswith("PROGRESS")
    assert dynamic_first[0]["content"].startswith("PROGRESS")


def test_with_no_decoys_the_tool_set_is_exactly_the_four_capabilities() -> None:
    assert len(agent().tools_for_test()) == 4


def test_arm_4a_exposes_every_decoy_directly() -> None:
    exposed = agent(decoy_tools=30).tools_for_test()

    assert len(exposed) == 34
    assert not any(tool.get("defer_loading") for tool in exposed)


def test_arm_4b_defers_every_decoy_behind_tool_search() -> None:
    exposed = agent(decoy_tools=30, use_tool_search=True).tools_for_test()

    search_tools = [t for t in exposed if str(t.get("type", "")).startswith("tool_search_tool")]
    real_capabilities = [
        t
        for t in exposed
        if t.get("name") in {"list_files", "read_file", "write_file", "run_tests"}
    ]
    decoys = [t for t in exposed if t not in search_tools and t not in real_capabilities]

    assert len(search_tools) == 1
    assert not search_tools[0].get("defer_loading")  # the search tool itself is never deferred
    assert not any(
        t.get("defer_loading") for t in real_capabilities
    )  # the task's own tools stay ready
    assert len(decoys) == 30
    assert all(t.get("defer_loading") for t in decoys)


def test_a_briefing_is_folded_into_the_initial_task_message() -> None:
    # Experiment 3: the orchestrator should not re-derive what a subagent
    # already investigated, so the finding must actually reach the first turn.
    briefed = agent(briefing="stage_2.py adds an off-by-one.")

    assert "stage_2.py adds an off-by-one." in briefed.initial_task_message_for_test()
    assert agent().briefing == ""


def test_a_plan_is_folded_in_after_the_briefing() -> None:
    # Experiment 6e/6f: the plan should reach the first turn the same way the
    # briefing does — composed in, not requiring the loop to re-fetch it.
    task = agent(briefing="stage_2.py looks suspicious.").initial_task_message_for_test(
        plan="1. Read stage_2.py\n2. Compare thresholds\n3. Run tests"
    )

    assert "stage_2.py looks suspicious." in task
    assert "1. Read stage_2.py" in task
    assert task.index("stage_2.py looks suspicious.") < task.index("1. Read stage_2.py")


def test_with_no_plan_the_task_message_is_unaffected() -> None:
    assert "Follow this plan" not in agent().initial_task_message_for_test()


def test_workflow_defaults_to_off() -> None:
    assert agent().workflow is False
