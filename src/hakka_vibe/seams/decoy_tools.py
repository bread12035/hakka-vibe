"""Decoy tools: noise for experiment 4's tool-surface comparison.

The task only ever needs FixerAgent's four real capabilities. These exist
purely to inflate the tool count, so 4a (all exposed directly) and 4b (all
deferred behind tool search) have something to actually differ on.
"""

import random

from anthropic.types import ToolParam

_VERBS = ["fetch", "sync", "archive", "audit", "rotate", "compress", "validate", "reconcile"]
_NOUNS = ["invoice", "webhook", "ledger", "snapshot", "quota", "manifest", "report", "session"]


def generate_decoy_tools(*, count: int, seed: int) -> list[ToolParam]:
    """A deterministic set of plausible-sounding, never-called tool definitions."""
    rng = random.Random(seed)
    names_seen: set[str] = set()
    tools: list[ToolParam] = []
    while len(tools) < count:
        name = f"{rng.choice(_VERBS)}_{rng.choice(_NOUNS)}"
        if name in names_seen:
            continue
        names_seen.add(name)
        tools.append(
            ToolParam(
                name=name,
                description=f"Internal utility to {name.replace('_', ' ')}. Not used by this task.",
                input_schema={
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                    "additionalProperties": False,
                },
            )
        )
    return tools
