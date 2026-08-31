"""Output styles: experiment 5's variable.

A style is a short instruction appended after the frozen system prompt, never a
rewrite of it — rewriting the frozen block would invalidate the cache prefix the
task's own instructions rely on.
"""

from dataclasses import dataclass
from pathlib import Path

DEFAULT_STYLE_ROOT = Path("prompts/styles")


@dataclass(frozen=True)
class OutputStyle:
    """One arm's output-style instruction."""

    name: str
    instruction: str


def load_style(name: str, *, root: Path = DEFAULT_STYLE_ROOT) -> OutputStyle:
    """Load a style's instruction text by name (e.g. "caveman", "ste100")."""
    path = root / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"no output style {name!r} at {path}")
    return OutputStyle(name=name, instruction=path.read_text().strip())
