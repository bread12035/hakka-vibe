"""The agent under measurement: it fixes a failing test in a fixture.

Structure follows ADR-0001 — one agent is one class, its capabilities are
methods, its state is typed fields, and prompts come from the registry rather
than from string literals here.

The agent gets no seam of its own. Whether it worked is the fixture's own pytest
exit code, and testing past that would mean asserting on model output.
"""

import inspect
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam, ToolParam, ToolResultBlockParam

from hakka_vibe.call import DEFAULT_CACHE_TTL, DEFAULT_MAX_TOKENS, CacheTtl
from hakka_vibe.decoy_tools import generate_decoy_tools
from hakka_vibe.fixture import fixture_fingerprint
from hakka_vibe.output_style import OutputStyle
from hakka_vibe.prompt_layout import PromptLayout, assemble_messages

Effort = Literal["low", "medium", "high", "xhigh", "max"]
DEFAULT_EFFORT: Effort = "high"
"""Anthropic's own default, used whenever an arm does not vary effort."""
from hakka_vibe.prompts import PromptSet
from hakka_vibe.run_record import Call, RunRecord

_JSON_TYPES = {str: "string", int: "integer", bool: "boolean"}


def _schema_of(method: Any) -> ToolParam:
    """Derive a tool schema from a method's signature.

    Derived rather than hand-written so the schema cannot drift away from the
    code it describes: a hand-maintained copy silently stops matching.
    """
    signature = inspect.signature(method)
    hints = inspect.get_annotations(method, eval_str=True)
    properties = {
        name: {"type": _JSON_TYPES[hints[name]]} for name in signature.parameters if name != "self"
    }
    return ToolParam(
        name=method.__name__,
        description=inspect.getdoc(method) or "",
        input_schema={
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
    )


@dataclass
class TestOutcome:
    """What the fixture's own suite said."""

    passed: bool
    output: str


@dataclass
class FixerAgent:
    """Reads a broken project, edits it, and runs its tests until they pass."""

    client: Anthropic
    workspace: Path
    model: str
    prompts: PromptSet = field(default_factory=PromptSet)
    max_turns: int = 40
    cache_ttl: CacheTtl = DEFAULT_CACHE_TTL
    effort: Effort = DEFAULT_EFFORT
    output_style: OutputStyle | None = None
    """Experiment 5's variable: a style block appended to the system prompt.

    None reproduces Anthropic's default voice, which is arm 5a's baseline.
    """
    prompt_layout: PromptLayout = PromptLayout.BASELINE
    """Experiment 1's variable: where the dynamic progress note sits in messages."""
    compaction: bool = False
    """Experiment 1d: opt into server-side compaction (beta) for this run."""
    decoy_tools: int = 0
    """Experiment 4's variable: how many never-called tools inflate the tool
    surface. 0 reproduces the plain four-capability tool set."""
    use_tool_search: bool = False
    """Arm 4b: defer the decoys behind tool search rather than exposing them
    directly. The task's own four capabilities stay non-deferred — they are
    needed on every turn, not something worth searching for."""

    turns_taken: int = 0
    """How many model turns this run has spent."""

    calls: list[Call] = field(default_factory=list)
    """Raw usage from every call, in order."""

    # ── capabilities the model can call ──────────────────────────────────────

    def list_files(self, directory: str) -> str:
        """List the files under a directory, relative to the project root."""
        target = self.workspace / directory
        if not target.is_dir():
            return f"no such directory: {directory}"
        return "\n".join(
            sorted(str(p.relative_to(self.workspace)) for p in target.rglob("*") if p.is_file())
        )

    def read_file(self, path: str) -> str:
        """Read a file, relative to the project root."""
        target = self.workspace / path
        if not target.is_file():
            return f"no such file: {path}"
        return target.read_text()

    def write_file(self, path: str, content: str) -> str:
        """Replace a file's entire contents, relative to the project root."""
        target = self.workspace / path
        if not target.is_file():
            return f"no such file: {path}"
        target.write_text(content)
        return f"wrote {path}"

    def run_tests(self) -> str:
        """Run the project's test suite and return what it printed."""
        return self.check().output

    # ── deterministic, not model-facing ──────────────────────────────────────

    def check(self) -> TestOutcome:
        """Run the fixture's suite. Its exit code is the only measure of success."""
        completed = subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "-q"],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return TestOutcome(passed=completed.returncode == 0, output=completed.stdout)

    def _system_blocks(self) -> list[TextBlockParam]:
        text = self.prompts.render("fixer.system")
        if self.output_style is not None:
            text = f"{text}\n\n{self.output_style.instruction}"
        return [
            TextBlockParam(
                type="text",
                text=text,
                cache_control={"type": "ephemeral", "ttl": self.cache_ttl},
            )
        ]

    def _dynamic_note(self) -> str:
        """A per-turn progress note, derived from state rather than written by the
        model: turn count against the budget. Deterministic, so its placement
        (experiment 1's variable) can be tested without a call."""
        return f"PROGRESS: turn {self.turns_taken} of {self.max_turns}."

    def messages_for_test(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Expose the assembled messages for the no-call layout tests."""
        return assemble_messages(history, self._dynamic_note(), layout=self.prompt_layout)

    def system_blocks_for_test(self) -> list[TextBlockParam]:
        """Expose the assembled system blocks for the deterministic, no-call tests.

        Not part of the model-facing interface — it is here so the frozen
        prompt and the style append can be pinned down without a call.
        """
        return self._system_blocks()

    def tools_for_test(self) -> list[ToolParam]:
        """Expose the assembled tool list for the no-call arm-configuration tests."""
        return self._tools()

    def _tools(self) -> list[Any]:
        core = [
            _schema_of(type(self).list_files),
            _schema_of(type(self).read_file),
            _schema_of(type(self).write_file),
            _schema_of(type(self).run_tests),
        ]
        if self.decoy_tools == 0:
            return core

        decoys = generate_decoy_tools(count=self.decoy_tools, seed=hash(self.model) & 0xFFFF)
        if not self.use_tool_search:
            return [*core, *decoys]

        from anthropic.types import ToolSearchToolBm25_20251119Param

        search_tool = ToolSearchToolBm25_20251119Param(
            type="tool_search_tool_bm25_20251119", name="tool_search_tool_bm25"
        )
        deferred = [ToolParam(**{**tool, "defer_loading": True}) for tool in decoys]
        return [search_tool, *core, *deferred]

    def _invoke(self, name: str, arguments: Any) -> str:
        capability = getattr(self, name)
        return str(capability(**arguments))

    # ── the loop: ordinary Python, editable, not hidden in a framework ───────

    def fix(self, *, experiment: str, arm: str, run: int) -> RunRecord:
        """Work the task until the suite passes or the turn budget runs out."""
        messages: list[MessageParam] = [
            {
                "role": "user",
                "content": self.prompts.render("fixer.task", workspace=self.workspace),
            }
        ]

        while self.turns_taken < self.max_turns:
            create = (
                self.client.beta.messages.create if self.compaction else self.client.messages.create
            )
            request: dict[str, Any] = {
                "model": self.model,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "system": self._system_blocks(),
                "output_config": {"effort": self.effort},
                "tools": self._tools(),
                "messages": assemble_messages(
                    messages, self._dynamic_note(), layout=self.prompt_layout
                ),
            }
            if self.compaction:
                request["betas"] = ["compact-2026-01-12"]
                request["context_management"] = {"edits": [{"type": "compact_20260112"}]}
            response = create(**request)
            self.turns_taken += 1
            self.calls.append(Call(model=self.model, usage=response.usage.model_dump()))

            requests = [block for block in response.content if block.type == "tool_use"]
            if not requests:
                break

            messages.append(MessageParam(role="assistant", content=response.content))
            messages.append(
                MessageParam(
                    role="user",
                    content=[
                        ToolResultBlockParam(
                            type="tool_result",
                            tool_use_id=request.id,
                            content=self._invoke(request.name, dict(request.input)),
                        )
                        for request in requests
                    ],
                )
            )

        # The verdict is a fresh run of the suite, never the agent's own account
        # of how it went. Running out of turns is recorded as a failure, not as
        # an error: an arm that cannot finish inside its budget is a result.
        return RunRecord(
            experiment=experiment,
            arm=arm,
            run=run,
            model=self.model,
            calls=tuple(self.calls),
            passed=self.check().passed,
            fixture=fixture_fingerprint(self.workspace),
        )
