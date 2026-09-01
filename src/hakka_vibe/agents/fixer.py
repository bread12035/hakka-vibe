"""The agent under measurement: it fixes a failing test in a fixture.

One public entry point, ``fix``. The four things a model can do to the
workspace — list, read, write, run tests — are never called by anything
except this module's own tool-dispatch loop inside ``fix``: nothing points at
them if they were deleted from the public interface, so they stay plain
functions rather than a class's public API. The deletion test, applied to
each of the old design's four "capability methods," is what actually shrinks
this module's interface down to one function.

No seam of its own beyond that. Whether the task succeeded is the fixture's
own pytest exit code — asserting past that would mean asserting on model
output, which is a different, unwinnable kind of test.
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam, ToolParam, ToolResultBlockParam

from hakka_vibe.fixture.generate import fixture_fingerprint
from hakka_vibe.harness.call import (
    DEFAULT_CACHE_TTL,
    DEFAULT_EFFORT,
    DEFAULT_MAX_TOKENS,
    CacheTtl,
    Effort,
)
from hakka_vibe.harness.decoy_tools import generate_decoy_tools
from hakka_vibe.harness.output_style import OutputStyle
from hakka_vibe.harness.prompt_layout import PromptLayout, assemble_messages
from hakka_vibe.harness.prompts import PromptSet
from hakka_vibe.harness.tool_schema import schema_of
from hakka_vibe.measurement.run_record import Call, RunRecord

DEFAULT_MAX_TURNS = 40


@dataclass(frozen=True)
class TestOutcome:
    """What the fixture's own suite said."""

    passed: bool
    output: str


def check(workspace: Path) -> TestOutcome:
    """Run the fixture's suite. Its exit code is the only measure of success."""
    completed = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return TestOutcome(passed=completed.returncode == 0, output=completed.stdout)


# ── the four things a model can do to the workspace ────────────────────────
# ``workspace`` is an ambient binding a caller supplies, the same role ``self``
# played in a class — never something the model chooses, so schema_of excludes
# it from what the model sees.


def list_files(workspace: Path, directory: str) -> str:
    """List the files under a directory, relative to the project root."""
    target = workspace / directory
    if not target.is_dir():
        return f"no such directory: {directory}"
    return "\n".join(
        sorted(str(p.relative_to(workspace)) for p in target.rglob("*") if p.is_file())
    )


def read_file(workspace: Path, path: str) -> str:
    """Read a file, relative to the project root."""
    target = workspace / path
    if not target.is_file():
        return f"no such file: {path}"
    return target.read_text()


def write_file(workspace: Path, path: str, content: str) -> str:
    """Replace a file's entire contents, relative to the project root."""
    target = workspace / path
    if not target.is_file():
        return f"no such file: {path}"
    target.write_text(content)
    return f"wrote {path}"


def run_tests(workspace: Path) -> str:
    """Run the project's test suite and return what it printed."""
    return check(workspace).output


_CAPABILITIES = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_tests": run_tests,
}


def _invoke(name: str, arguments: dict[str, Any], *, workspace: Path) -> str:
    return str(_CAPABILITIES[name](workspace, **arguments))  # type: ignore[operator]


# ── pure composition: the same functions build a real request and answer a
# no-call test, so there is exactly one place each gets assembled ──────────


def system_blocks(
    *,
    prompts: PromptSet | None = None,
    cache_ttl: CacheTtl = DEFAULT_CACHE_TTL,
    output_style: OutputStyle | None = None,
) -> list[TextBlockParam]:
    """The frozen system prompt, with an optional style appended after it —
    never mixed into it, which would invalidate the cache prefix the task
    instructions rely on. Experiment 5's variable, testable without a call."""
    text = (prompts or PromptSet()).render("fixer.system")
    if output_style is not None:
        text = f"{text}\n\n{output_style.instruction}"
    return [
        TextBlockParam(
            type="text", text=text, cache_control={"type": "ephemeral", "ttl": cache_ttl}
        )
    ]


def dynamic_note(*, turns_taken: int, max_turns: int) -> str:
    """A per-turn progress note derived from state, not written by the model —
    deterministic, so experiment 1's placement is testable without a call."""
    return f"PROGRESS: turn {turns_taken} of {max_turns}."


def assemble_task(
    *,
    prompts: PromptSet | None = None,
    workspace: Path,
    briefing: str = "",
    plan: str | None = None,
) -> str:
    """Compose the initial task message: the task prompt, an optional briefing
    (experiment 3) and an optional plan (experiment 6e/6f). Pure given its
    inputs, which is what makes it testable without a call."""
    task = (prompts or PromptSet()).render("fixer.task", workspace=workspace)
    if briefing:
        task = f"{task}\n\nA colleague already looked into this and reported:\n{briefing}"
    if plan:
        task = f"{task}\n\nFollow this plan step by step:\n{plan}"
    return task


def tool_schemas(
    *, decoy_tools: int = 0, use_tool_search: bool = False, model: str = ""
) -> list[Any]:
    """The tool list one arm exposes: the four real capabilities, plus
    experiment 4's decoys — direct, or deferred behind tool search."""
    core = [
        schema_of(list_files),
        schema_of(read_file),
        schema_of(write_file),
        schema_of(run_tests),
    ]
    if decoy_tools == 0:
        return core

    decoys = generate_decoy_tools(count=decoy_tools, seed=hash(model) & 0xFFFF)
    if not use_tool_search:
        return [*core, *decoys]

    from anthropic.types import ToolSearchToolBm25_20251119Param

    search_tool = ToolSearchToolBm25_20251119Param(
        type="tool_search_tool_bm25_20251119", name="tool_search_tool_bm25"
    )
    deferred = [ToolParam(**{**tool, "defer_loading": True}) for tool in decoys]
    return [search_tool, *core, *deferred]


# ── the loop: ordinary Python, no framework to look through ────────────────


def fix(
    client: Anthropic,
    workspace: Path,
    model: str,
    *,
    experiment: str,
    arm: str,
    run: int,
    prompts: PromptSet | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
    cache_ttl: CacheTtl = DEFAULT_CACHE_TTL,
    effort: Effort = DEFAULT_EFFORT,
    output_style: OutputStyle | None = None,
    prompt_layout: PromptLayout = PromptLayout.BASELINE,
    compaction: bool = False,
    decoy_tools: int = 0,
    use_tool_search: bool = False,
    briefing: str = "",
    workflow: bool = False,
) -> RunRecord:
    """Work the task until the suite passes or the turn budget runs out."""
    registry = prompts or PromptSet()
    calls: list[Call] = []

    plan_text: str | None = None
    if workflow:
        plan_response = client.messages.create(
            model=model,
            max_tokens=DEFAULT_MAX_TOKENS,
            system=system_blocks(prompts=registry, cache_ttl=cache_ttl, output_style=output_style),
            output_config={"effort": effort},
            messages=[{"role": "user", "content": registry.render("fixer.plan")}],
        )
        calls.append(Call(model=model, usage=plan_response.usage.model_dump()))
        plan_text = "\n".join(block.text for block in plan_response.content if block.type == "text")

    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": assemble_task(
                prompts=registry, workspace=workspace, briefing=briefing, plan=plan_text
            ),
        }
    ]

    turns_taken = 0
    while turns_taken < max_turns:
        create = client.beta.messages.create if compaction else client.messages.create
        request: dict[str, Any] = {
            "model": model,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "system": system_blocks(
                prompts=registry, cache_ttl=cache_ttl, output_style=output_style
            ),
            "output_config": {"effort": effort},
            "tools": tool_schemas(
                decoy_tools=decoy_tools, use_tool_search=use_tool_search, model=model
            ),
            "messages": assemble_messages(
                messages,
                dynamic_note(turns_taken=turns_taken, max_turns=max_turns),
                layout=prompt_layout,
            ),
        }
        if compaction:
            request["betas"] = ["compact-2026-01-12"]
            request["context_management"] = {"edits": [{"type": "compact_20260112"}]}
        response = create(**request)
        turns_taken += 1
        calls.append(Call(model=model, usage=response.usage.model_dump()))

        tool_uses = [block for block in response.content if block.type == "tool_use"]
        if not tool_uses:
            break

        messages.append(MessageParam(role="assistant", content=response.content))
        messages.append(
            MessageParam(
                role="user",
                content=[
                    ToolResultBlockParam(
                        type="tool_result",
                        tool_use_id=use.id,
                        content=_invoke(use.name, dict(use.input), workspace=workspace),
                    )
                    for use in tool_uses
                ],
            )
        )

    # The verdict is a fresh run of the suite, never the agent's own account of
    # how it went. Running out of turns is a failure, not an error: an arm
    # that can't finish inside its budget is itself a result.
    return RunRecord(
        experiment=experiment,
        arm=arm,
        run=run,
        model=model,
        calls=tuple(calls),
        passed=check(workspace).passed,
        fixture=fixture_fingerprint(workspace),
    )
