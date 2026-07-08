"""
Locks in the recorded Boolean proper-crossing witness
(boolean_crossing_diagnostic.WITNESS) against the real repository code --
not a re-run of the search (slow, and search behaviour isn't the claim;
the fixed witness passing all six gates is). Also locks in the earlier
degenerate witness's status, so a future change can't silently make the
degenerate case look acceptable again, and a tamper test confirming the
gates actually reject something.
"""

from fractions import Fraction as F

from boolean_crossing_diagnostic import (
    WITNESS,
    verify_witness,
    check_gate0_nondegeneracy,
    properly_crosses,
    contains_or_contained,
)


def test_recorded_witness_passes_all_six_gates():
    result = verify_witness(WITNESS)
    assert result["gate0_nondegenerate"] is True
    assert result["gate1_support_valid"] is True
    assert result["gate3_all_seams_computed"] is True
    assert result["gate4_not_coboundary"] is True
    assert result["gate5_classifier_verdict"] == "nontrivial_H1_obstruction"
    assert result["all_gates_passed"] is True


def test_recorded_witness_exact_residue_and_pairing():
    result = verify_witness(WITNESS)
    assert result["residue_vector"] == ["0", "-1", "0", "1"]
    assert result["pairing"] == "2"


def test_recorded_witness_triple_overlaps_are_distinct_points():
    """Unlike the earlier degenerate witness (all four overlaps at the
    same point), this one uses four distinct points -- part of why it's
    the non-degenerate case worth recording."""
    result = verify_witness(WITNESS)
    overlaps = result["triple_overlaps"]
    all_points = [p for pts in overlaps.values() for p in pts]
    assert len(set(all_points)) == 4


def test_earlier_degenerate_witness_fails_gate0_but_not_the_other_gates():
    """The first witness found (U1 a single point contained in every
    other region) is NOT the recorded result -- it fails gate 0 even
    though it does pass gates 1, 3, 4, 5. This pins down exactly why it
    was excluded, not just that it was."""
    degenerate = {
        "U1": frozenset({0}),
        "U2": frozenset({0, 1}),
        "U3": frozenset({0, 2}),
        "U4": frozenset({0, 1, 2}),
    }
    ok0, failures = check_gate0_nondegeneracy(degenerate)
    assert ok0 is False
    assert any("U1" in f for f in failures)

    result = verify_witness(degenerate)
    assert result["gate1_support_valid"] is True
    assert result["gate3_all_seams_computed"] is True
    assert result["gate5_classifier_verdict"] == "nontrivial_H1_obstruction"
    # It passes every gate except gate 0 -- which is exactly why gate 0
    # exists and why this witness was never recorded as the result.


def test_tampered_witness_breaking_a_triple_overlap_is_rejected():
    """A tamper test on the gates themselves: shrinking U4 so it no
    longer shares a point with U1 and U2 simultaneously should break
    gate 1 (support validity), and the module should report that
    honestly rather than silently produce a residue anyway."""
    tampered = dict(WITNESS)
    tampered["U4"] = frozenset({2, 3})  # no longer contains point 1 (U4 n U1 n U2's overlap)
    result = verify_witness(tampered)
    assert result["gate1_support_valid"] is False
    assert result["gate3_all_seams_computed"] is False


def test_properly_crosses_and_containment_helpers():
    A, B, C = frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 1, 2})
    assert properly_crosses(A, B) is True          # overlap {1}, neither contains other
    assert properly_crosses(A, C) is False          # A subset of C
    assert contains_or_contained(A, C) is True
    assert properly_crosses(frozenset({5}), frozenset({6})) is False  # disjoint
