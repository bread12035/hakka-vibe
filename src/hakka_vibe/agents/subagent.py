"""Subagent: a cheap-model helper delegated to during experiment 3.

Its own capabilities are fixed across all three delegation arms; what varies
is only the context each delegation call sends, decided by
hakka_vibe.seams.delegation.context_for_call before Subagent.ask() is called.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam, ToolParam, ToolResultBlockParam

from hakka_vibe.agents.fixer import DEFAULT_EFFORT, Effort
from hakka_vibe.measurement.call import DEFAULT_CACHE_TTL, DEFAULT_MAX_TOKENS, CacheTtl
from hakka_vibe.measurement.run_record import Call
from hakka_vibe.prompts import PromptSet
from hakka_vibe.tool_schema import schema_of


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
