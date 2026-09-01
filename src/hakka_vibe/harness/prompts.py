"""Prompts, loaded from files rather than written into Python.

One place to change what the model is told, with no chance of a `.py` literal
drifting away from the version anyone reviewed. A full registry — versioned,
delivered by CD, bound to a contract test — is out of scope for this build;
this is the smallest shape that holds the "no prompt strings in Python" rule
from the first line of code, since moving prompts out later would be
expensive.
"""

from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROMPT_ROOT = Path("prompts")


class PromptMissing(KeyError):
    """No prompt file exists at the requested key."""


@dataclass(frozen=True)
class PromptSet:
    """The prompts one agent may render, addressed by key."""

    root: Path = DEFAULT_PROMPT_ROOT

    def render(self, key: str, **values: object) -> str:
        """Return the prompt at ``key`` with its ``{placeholders}`` filled in."""
        path = self.root / f"{key}.md"
        if not path.is_file():
            raise PromptMissing(f"no prompt at {key!r} (looked in {path})")
        return path.read_text().format(**values).strip()
