"""Experiment 4a-4b arm configuration tests."""

from hakka_vibe.experiments.tool_search import ARMS


def test_4a_exposes_decoys_directly() -> None:
    assert ARMS["4a"].decoy_tools == ARMS["4b"].decoy_tools
    assert ARMS["4a"].use_tool_search is False


def test_4b_defers_the_same_number_of_decoys() -> None:
    assert ARMS["4b"].use_tool_search is True
    assert ARMS["4b"].decoy_tools > 0
