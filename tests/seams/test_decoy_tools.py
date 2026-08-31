"""Decoy tool generation: the noise experiment 4 buries the real tools in."""

from hakka_vibe.seams.decoy_tools import generate_decoy_tools


def test_it_generates_the_requested_count() -> None:
    assert len(generate_decoy_tools(count=30, seed=1)) == 30


def test_every_decoy_has_a_distinct_name() -> None:
    tools = generate_decoy_tools(count=40, seed=1)

    assert len({tool["name"] for tool in tools}) == 40


def test_the_same_seed_produces_the_same_tools() -> None:
    # Runs are spread over days; a drifting tool set makes runs incomparable.
    assert generate_decoy_tools(count=20, seed=5) == generate_decoy_tools(count=20, seed=5)
