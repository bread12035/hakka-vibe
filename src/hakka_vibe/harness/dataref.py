"""Experiment 2's variable: a thin, in-process reference to data too large to
put in a prompt.

Deliberately no query, describe, or sample methods — adding one would restore
a per-call round trip for every question the model wants answered, exactly the
cost pass-by-reference exists to remove. The model instead writes its own code
against ``raw`` (run by harness/sandbox.py), and only what that code chooses
to print becomes prompt characters.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any

import pandas as pd

_PREVIEW_LIMIT = 2_000


@dataclass(frozen=True)
class DataRef:
    """A named reference to a live object: what it is, never what it contains."""

    name: str
    raw: Any

    def preview(self) -> str:
        """A bounded description safe to put in a prompt: shape, not content."""
        if isinstance(self.raw, pd.DataFrame):
            described = (
                f"DataFrame '{self.name}': {len(self.raw)} rows, "
                f"columns={list(self.raw.columns)}, dtypes={self.raw.dtypes.to_dict()}"
            )
        elif isinstance(self.raw, sqlite3.Connection):
            tables = [
                row[0]
                for row in self.raw.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            described = f"SQLite connection '{self.name}': tables={tables}"
        else:
            described = f"{self.name}: {type(self.raw).__name__}"
        return described[:_PREVIEW_LIMIT]
