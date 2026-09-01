"""Deterministic parts of the fixer's request: no call, no fixture.

Under codebase-design there is no agent object to hold this as state — each
piece is a pure function of its inputs, which is also what makes it testable
without a call: the same functions build a real request inside ``fix`` and
answer these tests.
"""

from pathlib import Path

from hakka_vibe.agents import fixer
from hakka_vibe.harness.output_style import load_style
from hakka_vibe.harness.prompt_layout import PromptLayout, assemble_messages

WORKSPACE = Path("fixtures/pipeline")


def test_the_default_arm_carries_no_style_instruction() -> None:
    # Arm 5a is the baseline: Anthropic's own voice, nothing appended.
    blocks = fixer.system_blocks()

    assert len(blocks) == 1
    assert "caveman" not in blocks[0]["text"].lower()


def test_a_style_is_appended_after_the_frozen_prompt_not_mixed_into_it() -> None:
    # Appended, never used to rewrite the frozen block — rewriting it would
    # invalidate the cache prefix the task instructions depend on.
    caveman = fixer.system_blocks(output_style=load_style("caveman"))
    task_prompt = fixer.system_blocks()[0]["text"]

    assert caveman[0]["text"].startswith(task_prompt)
    assert "no articles" in caveman[0]["text"].lower()


def test_the_layout_setting_is_what_orders_the_messages() -> None:
    history = [{"role": "user", "content": "task"}, {"role": "assistant", "content": "turn 1"}]
    note = fixer.dynamic_note(turns_taken=1, max_turns=40)

    baseline = assemble_messages(history, note, layout=PromptLayout.BASELINE)
    dynamic_first = assemble_messages(history, note, layout=PromptLayout.DYNAMIC_FIRST)

    assert baseline[-1]["content"].startswith("PROGRESS")
    assert dynamic_first[0]["content"].startswith("PROGRESS")


def test_with_no_decoys_the_tool_set_is_exactly_the_four_capabilities() -> None:
    assert len(fixer.tool_schemas()) == 4


def test_arm_4a_exposes_every_decoy_directly() -> None:
    exposed = fixer.tool_schemas(decoy_tools=30)

    assert len(exposed) == 34
    assert not any(tool.get("defer_loading") for tool in exposed)


def test_arm_4b_defers_every_decoy_behind_tool_search() -> None:
    exposed = fixer.tool_schemas(decoy_tools=30, use_tool_search=True)

    search_tools = [t for t in exposed if str(t.get("type", "")).startswith("tool_search_tool")]
    real_capabilities = [
        t
        for t in exposed
        if t.get("name") in {"list_files", "read_file", "write_file", "run_tests"}
    ]
    decoys = [t for t in exposed if t not in search_tools and t not in real_capabilities]

    assert len(search_tools) == 1
    assert not search_tools[0].get("defer_loading")
    assert not any(t.get("defer_loading") for t in real_capabilities)
    assert len(decoys) == 30
    assert all(t.get("defer_loading") for t in decoys)


def test_a_briefing_is_folded_into_the_initial_task_message() -> None:
    # Experiment 3: the orchestrator should not re-derive what a subagent
    # already investigated, so the finding must actually reach the first turn.
    task = fixer.assemble_task(workspace=WORKSPACE, briefing="stage_2.py adds an off-by-one.")

    assert "stage_2.py adds an off-by-one." in task
    assert "Follow this plan" not in fixer.assemble_task(workspace=WORKSPACE)


def test_a_plan_is_folded_in_after_the_briefing() -> None:
    # Experiment 6e/6f: the plan reaches the first turn the same way the
    # briefing does — composed in, not requiring the loop to re-fetch it.
    task = fixer.assemble_task(
        workspace=WORKSPACE,
        briefing="stage_2.py looks suspicious.",
        plan="1. Read stage_2.py\n2. Compare thresholds\n3. Run tests",
    )

    assert "stage_2.py looks suspicious." in task
    assert "1. Read stage_2.py" in task
    assert task.index("stage_2.py looks suspicious.") < task.index("1. Read stage_2.py")
