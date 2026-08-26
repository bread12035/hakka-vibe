"""Subagent delegation: experiment 3's three architectures.

The main agent (Opus) delegates investigation to a cheaper model (Sonnet).
What varies between arms is what context reaches the subagent on each
delegation, not the subagent's own capabilities.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam, ToolParam, ToolResultBlockParam

from hakka_vibe.agent import DEFAULT_EFFORT, Effort
from hakka_vibe.call import DEFAULT_CACHE_TTL, DEFAULT_MAX_TOKENS, CacheTtl
from hakka_vibe.prompts import PromptSet
from hakka_vibe.run_record import Call
from hakka_vibe.tool_schema import schema_of


class DelegationMode(Enum):
    """Arm 3a-3c's variable: what a delegation call sends as context."""

    FRESH_FULL = "3a"
    """A brand new subagent every call, given the complete history each time —
    it has no memory of its own, so the whole thing travels with every ask."""

    FRESH_COMPRESSED = "3b"
    """A brand new subagent every call, given only a summary the orchestrator
    already compressed. The compression's own cost belongs to this arm, not
    the subagent's call — see ADR-0002."""

    PERSISTENT = "3c"
    """One subagent object across every call in a run. Only the first call
    needs the full history; later calls send just what is new since the last
    one, because the subagent's own conversation already holds the rest."""


def context_for_call(
    history: Sequence[str],
    *,
    mode: DelegationMode,
    call_index: int,
    compressed: str | None = None,
    new_turns: Sequence[str] = (),
) -> list[str]:
    """What one delegation call sends, given the mode and how far in it is.

    Pure function of the mode and the caller's bookkeeping — no subagent state
    is needed to answer this, which is what makes it testable without a call.
    """
    if mode is DelegationMode.FRESH_FULL:
        return list(history)
    if mode is DelegationMode.FRESH_COMPRESSED:
        return [compressed] if compressed is not None else []
    # PERSISTENT
    return list(history) if call_index == 0 else list(new_turns)


@dataclass
class Subagent:
    """A cheap-model helper that investigates the fixture and reports back in text."""

    client: Anthropic
    model: str
    workspace: (
        Any  # Path — kept loose to avoid importing agent's Path-typed workspace concept twice
    )
    prompts: PromptSet = field(default_factory=PromptSet)
    max_turns: int = 6
    cache_ttl: CacheTtl = DEFAULT_CACHE_TTL
    effort: Effort = DEFAULT_EFFORT

    calls: list[Call] = field(default_factory=list)
    conversation: list[MessageParam] = field(default_factory=list)
    """Only populated for DelegationMode.PERSISTENT — carries state across asks."""

    def read_file(self, path: str) -> str:
        """Read a file, relative to the project root."""
        target = self.workspace / path
        if not target.is_file():
            return f"no such file: {path}"
        return str(target.read_text())

    def _tools(self) -> list[ToolParam]:
        return [schema_of(type(self).read_file)]

    def _system_blocks(self) -> list[TextBlockParam]:
        return [
            TextBlockParam(
                type="text",
                text=self.prompts.render("subagent.system"),
                cache_control={"type": "ephemeral", "ttl": self.cache_ttl},
            )
        ]

    def ask(self, instruction: str, *, context: Sequence[str]) -> str:
        """Investigate and answer one instruction, given some prior context as text."""
        turns = 0
        messages: list[MessageParam] = [
            *self.conversation,
            {"role": "user", "content": "\n\n".join([*context, instruction])},
        ]
        final_text = ""

        while turns < self.max_turns:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=DEFAULT_MAX_TOKENS,
                system=self._system_blocks(),
                output_config={"effort": self.effort},
                tools=self._tools(),
                messages=messages,
            )
            turns += 1
            self.calls.append(Call(model=self.model, usage=response.usage.model_dump()))

            final_text = "\n".join(block.text for block in response.content if block.type == "text")
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
                            content=self.read_file(**dict(request.input)),  # type: ignore[arg-type]
                        )
                        for request in requests
                    ],
                )
            )

        self.conversation = messages + (
            [MessageParam(role="assistant", content=final_text)] if final_text else []
        )
        return final_text
