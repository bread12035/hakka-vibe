"""Prompts, loaded from files rather than written into Python.

Keeping prompt text out of ``.py`` files means one place to change what the
model is told, and no chance of a literal drifting away from the version anyone
reviewed. The full registry — versioned, delivered by CD, with a contract test
binding keys to signatures — is not built yet; this is the smallest shape that
holds the rule from the first commit, when moving prompts out later would be
expensive.
"""

from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROMPT_ROOT = Path("prompts")


class PromptMissing(KeyError):
    """No prompt is registered under that key."""


@dataclass(frozen=True)
class PromptSet:
    """The prompts one agent may use, addressed by key."""

    root: Path = DEFAULT_PROMPT_ROOT

    def render(self, key: str, **values: object) -> str:
        """Return the prompt at ``key`` with its placeholders filled in."""
        path = self.root / f"{key}.md"
        if not path.is_file():
            raise PromptMissing(f"no prompt at {key!r} (looked in {path})")
        return path.read_text().format(**values).strip()
