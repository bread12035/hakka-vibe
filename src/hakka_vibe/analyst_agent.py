"""The agent under measurement for experiment 2: one factual question, one tool.

Structure follows ADR-0001, same as FixerAgent. The two are different kinds of
agent — one edits files against a test suite, this one runs code against a
dataset — so they are separate classes rather than one class doing both.
"""

import inspect
from dataclasses import dataclass, field
from typing import Any

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam, ToolParam, ToolResultBlockParam

from hakka_vibe.agent import DEFAULT_EFFORT, Effort
from hakka_vibe.call import DEFAULT_CACHE_TTL, DEFAULT_MAX_TOKENS, CacheTtl
from hakka_vibe.dataref import DataRef
from hakka_vibe.prompts import PromptSet
from hakka_vibe.run_record import Call, RunRecord
from hakka_vibe.sandbox import execute_python


def _run_code_schema() -> ToolParam:
    return ToolParam(
        name="run_code",
        description=inspect.getdoc(AnalystAgent.run_code) or "",
        input_schema={
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
            "additionalProperties": False,
        },
    )


@dataclass
class AnalystAgent:
    """Answers one question about a dataset by writing and running Python.

    ``data`` is the arm's variable: a live DataRef for arms 2b/2c, or None for
    2a, where the dataset instead arrives as text inside the task prompt and
    there is nothing live in the namespace to query.
    """

    client: Anthropic
    model: str
    prompts: PromptSet = field(default_factory=PromptSet)
    max_turns: int = 20
    cache_ttl: CacheTtl = DEFAULT_CACHE_TTL
    effort: Effort = DEFAULT_EFFORT
    data: DataRef | None = None

    turns_taken: int = 0
    calls: list[Call] = field(default_factory=list)
    namespace: dict[str, Any] = field(default_factory=dict)
    """Persists across turns within this run: a result derived on one turn
    stays live for the next, rather than being re-derived or re-serialized."""

    def run_code(self, code: str) -> str:
        """Run Python and return what it printed. State carries to your next call."""
        return execute_python(code, namespace=self.namespace)

    def _system_blocks(self) -> list[TextBlockParam]:
        return [
            TextBlockParam(
                type="text",
                text=self.prompts.render("analyst.system"),
                cache_control={"type": "ephemeral", "ttl": self.cache_ttl},
            )
        ]

    def analyse(self, *, task_context: str, experiment: str, arm: str, run: int) -> tuple[RunRecord, str]:
        """Work the question until an answer line appears or the turn budget runs out.

        Returns the run record and the agent's final text, for the caller to
        gate with parse_answer/matches_expected — the harness's judgement, kept
        out of the agent's own capabilities.
        """
        if self.data is not None:
            self.namespace[self.data.name] = self.data.raw
            task_context = f"{task_context}\n\n{self.data.preview()}"

        messages: list[MessageParam] = [
            {"role": "user", "content": self.prompts.render("analyst.task", context=task_context)}
        ]
        final_text = ""

        while self.turns_taken < self.max_turns:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=DEFAULT_MAX_TOKENS,
                system=self._system_blocks(),
                output_config={"effort": self.effort},
                tools=[_run_code_schema()],
                messages=messages,
            )
            self.turns_taken += 1
            self.calls.append(Call(model=self.model, usage=response.usage.model_dump()))

            final_text = "\n".join(
                block.text for block in response.content if block.type == "text"
            )
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
                            content=self.run_code(**dict(request.input)),  # type: ignore[arg-type]
                        )
                        for request in requests
                    ],
                )
            )

        return (
            RunRecord(
                experiment=experiment,
                arm=arm,
                run=run,
                model=self.model,
                calls=tuple(self.calls),
            ),
            final_text,
        )
