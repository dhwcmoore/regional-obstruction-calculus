"""
Regression tests for refinement_witness_parallel_disjoint_probe.py.
Locks in the headline finding: N0 and E0 always reduce to
AND(branch A, branch B) under disjoint-parallel (direct-sum)
composition; A4 does not, because the combined pairing is a SUM that
can cancel even when both branches individually satisfy their own A4.
"""

from refinement_witnesses import SUBDIVIDE_U1, SUBDIVIDE_U2, ALL_WITNESSES
from refinement_witness_parallel_disjoint_probe import run_case, systematic_sweep


def test_natural_pairing_case_preserves_all_three_conditions():
    r = run_case("natural", SUBDIVIDE_U1, SUBDIVIDE_U2)
    assert r["N0_matches_AND"] is True
    assert r["E0_matches_AND"] is True
    assert r["A4_matches_AND"] is True
    assert r["combined"]["N0"] is True
    assert r["combined"]["A4"] is True
    assert r["combined"]["E0"] is True


def test_negated_cycle_case_demonstrates_A4_cancellation():
    r = run_case("cancellation", SUBDIVIDE_U1, SUBDIVIDE_U1, negate_b_cycle=True)
    assert r["branch_a"]["A4"] is True
    assert r["branch_b"]["A4"] is True
    assert r["combined"]["pairing"] == 0
    assert r["combined"]["A4"] is False
    assert r["A4_matches_AND"] is False
    # N0 and E0 are untouched by the cancellation -- confirms it is
    # specifically a property of A4's sum-based combination rule.
    assert r["N0_matches_AND"] is True
    assert r["E0_matches_AND"] is True


def test_systematic_sweep_N0_and_E0_always_match_AND():
    sweep = systematic_sweep()
    assert len(sweep) == 32
    assert all(r["N0_matches_AND"] for r in sweep)
    assert all(r["E0_matches_AND"] for r in sweep)


def test_systematic_sweep_A4_mismatches_are_exactly_the_sign_cancelling_cases():
    """Every base witness in this cover has |pairing| = 5, so an A4
    mismatch should occur in exactly the cases where the two branches'
    (possibly negated) pairings have opposite sign -- half of all 32
    cases, not more, not fewer, and always with combined pairing = 0."""
    sweep = systematic_sweep()
    mismatches = [r for r in sweep if not r["A4_matches_AND"]]
    assert len(mismatches) == 16
    for r in mismatches:
        assert r["combined"]["pairing"] == 0
        assert r["branch_a"]["A4"] is True
        assert r["branch_b"]["A4"] is True
