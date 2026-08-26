"""Experiment 1a-1e arm configuration tests: what varies per arm, without a call."""

from hakka_vibe.experiments.prompt_ordering import ARMS
from hakka_vibe.prompt_layout import PromptLayout


def test_1a_through_1c_vary_layout_only() -> None:
    assert ARMS["1a"].layout is PromptLayout.BASELINE
    assert ARMS["1b"].layout is PromptLayout.DYNAMIC_FIRST
    assert ARMS["1c"].layout is PromptLayout.STATIC_INTERLEAVED
    for arm in ("1a", "1b", "1c"):
        assert ARMS[arm].cache_ttl == "5m"
        assert ARMS[arm].compaction is False


def test_1d_is_the_baseline_layout_with_compaction_enabled() -> None:
    assert ARMS["1d"].layout is PromptLayout.BASELINE
    assert ARMS["1d"].compaction is True
    assert ARMS["1d"].cache_ttl == "5m"


def test_1e_is_the_baseline_layout_at_the_one_hour_ttl() -> None:
    # 1e's only difference from 1a is the TTL — a clean single-variable pair.
    assert ARMS["1e"].layout == ARMS["1a"].layout
    assert ARMS["1e"].compaction == ARMS["1a"].compaction
    assert ARMS["1e"].cache_ttl == "1h"
    assert ARMS["1a"].cache_ttl == "5m"
