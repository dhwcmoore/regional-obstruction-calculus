"""
Regression tests for refinement_witness_composition_probe.py -- locks in
the two concrete composition results and the N0-associativity check, so
future changes to the underlying machinery don't silently change these
findings without notice. See docs/design/REFINEMENT_WITNESS_COMPOSITION_
STATUS.md: this is a probed, not proved, open question. These tests
protect the specific numbers found so far, not a general theorem.
"""

from refinement_witness_composition_probe import (
    verify_n0_composability_is_associativity,
    _second_subdivision_scenario,
    _bridge_insertion_scenario,
)


def test_n0_composability_associativity_identity_holds():
    assert verify_n0_composability_is_associativity() is True


def test_two_subdivisions_compose_verdict_safe():
    r = _second_subdivision_scenario()
    assert r["step1_admissible"] is True
    assert r["step1_descent_safe"] is True
    assert r["step2_admissible"] is True
    assert r["step2_descent_safe"] is True
    assert r["composite_admissible"] is True
    assert r["composite_N0"] is True
    assert r["composite_descent_safe"] is True
    assert r["composite_E0"] is True
    assert r["composite_verdict_safe"] is True


def test_bridge_insertion_composite_fails_only_N0():
    r = _bridge_insertion_scenario()
    assert r["step2_N0"] is False
    assert r["composite_admissible"] is True
    assert r["composite_N0"] is False
    assert r["composite_descent_safe"] is False
    assert r["composite_E0"] is True
    assert r["composite_verdict_safe"] is False
    assert r["N0_failure_propagated"] is True
