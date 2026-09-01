"""Subagent architecture experiment: what's testable without a call."""

from hakka_vibe.agents.subagent import DelegationMode


def test_the_three_modes_map_to_the_spec_arm_ids() -> None:
    assert {mode.value for mode in DelegationMode} == {"3a", "3b", "3c"}
