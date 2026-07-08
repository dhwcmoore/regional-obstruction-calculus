"""
Tests for carrier_matrix_infrastructure.py, using TOY matrices with known
answers -- not real seam-residue data, and not a claim that any candidate
outer-slot discipline works. This infrastructure has to be trusted on its
own terms before candidate_discipline_diagnostic.py (a separate, later
file) leans on it for a real diagnostic.
"""

from fractions import Fraction as F

import pytest

from carrier_matrix_infrastructure import (
    SEAMS, SLOT_NAMES,
    SharedCarrierCoordinate,
    carrier_key,
    all_slot_coordinates,
    delta_matrix,
    verify_delta_matches_closed_form,
    build_R,
    compose_B,
    surviving_coordinate_sharing_check,
    sharing_check_summary,
)


def test_delta_matrix_shape_and_coefficients():
    D, slots, seams = delta_matrix()
    assert len(D) == 4  # dim E
    assert len(D[0]) == 16  # dim S = 4 seams x 4 slots
    assert seams == list(SEAMS)
    # block-diagonal: e12's row is nonzero only on e12's four slot columns
    e12_row = D[seams.index("e12")]
    e12_cols = [i for i, (e, _) in enumerate(slots) if e == "e12"]
    for i, x in enumerate(e12_row):
        if i in e12_cols:
            assert x != 0
        else:
            assert x == 0
    # exact coefficients on e12's own slots, in declared order
    expected = {"UV": F(-1), "VW": F(1), "U_VvW": F(1), "UvV_W": F(-1)}
    for i in e12_cols:
        seam, slot_name = slots[i]
        assert e12_row[i] == expected[slot_name]


def test_delta_matches_real_closed_form_delta():
    assert verify_delta_matches_closed_form() is True


def test_shared_carrier_coordinate_requires_frozensets():
    ok = SharedCarrierCoordinate(key=carrier_key(frozenset({1, 2}), frozenset({2, 3})))
    assert ok.key == (frozenset({1, 2}), frozenset({2, 3}))
    with pytest.raises(TypeError):
        SharedCarrierCoordinate(key=({1, 2}, {2, 3}))  # plain sets, not frozensets


def test_build_R_defaults_absent_entries_to_zero():
    slots = all_slot_coordinates()
    k1 = carrier_key(frozenset({0}), frozenset({1}))
    rule = {("e12", "UV"): {k1: F(3)}}
    R = build_R(rule, [k1], slots)
    assert len(R) == len(slots)
    assert len(R[0]) == 1
    row_idx = slots.index(("e12", "UV"))
    assert R[row_idx][0] == F(3)
    other_row_idx = slots.index(("e12", "VW"))
    assert R[other_row_idx][0] == F(0)


def test_compose_B_is_D_times_R():
    D, slots, seams = delta_matrix()
    k1 = carrier_key(frozenset({0}), frozenset({1}))
    # k1 populates e12's UV slot with coefficient 1 -> should contribute
    # D's UV coefficient (-1) to e12's row, nothing elsewhere.
    rule = {("e12", "UV"): {k1: F(1)}}
    R = build_R(rule, [k1], slots)
    B = compose_B(D, R)
    assert len(B) == 4
    assert len(B[0]) == 1
    assert B[seams.index("e12")][0] == F(-1)
    for seam in ("e23", "e34", "e14"):
        assert B[seams.index(seam)][0] == F(0)


# --- The known failure mode, reproduced in miniature -----------------

def test_coordinate_surviving_in_only_one_seam_row_is_flagged_private_residual():
    """A globally indexed coordinate whose B-column survives in only one
    seam row must fail the sharing check -- this is the 3ad4bbd failure
    mode, made executable and tested here on a toy matrix, not real
    associator data."""
    D, slots, seams = delta_matrix()
    k_private = carrier_key(frozenset({0}), frozenset({1}))
    # Referenced in R only for e12's U_VvW slot -- one placement, one seam.
    rule = {("e12", "U_VvW"): {k_private: F(1)}}
    R = build_R(rule, [k_private], slots)
    B = compose_B(D, R)
    results = surviving_coordinate_sharing_check(B, [k_private], seams)
    assert results[k_private]["status"] == "private_residual"
    assert results[k_private]["nonzero_seams"] == ["e12"]


def test_coordinate_cancelling_to_zero_is_flagged_zero_column():
    """A coordinate genuinely referenced by R in two slots of the SAME
    seam, with D-coefficients that exactly cancel, produces an
    all-zero B-column -- exactly the inclusion-exclusion cancellation
    pattern (mu_UV and mu_U_VvW both referencing the same carrier
    coordinate, D's -1 and +1 coefficients cancelling it out of Delta)."""
    D, slots, seams = delta_matrix()
    k_cancels = carrier_key(frozenset({0}), frozenset({1}))
    # UV has D-coefficient -1, U_VvW has D-coefficient +1: placing the
    # same coordinate in both with coefficient 1 cancels exactly.
    rule = {
        ("e12", "UV"): {k_cancels: F(1)},
        ("e12", "U_VvW"): {k_cancels: F(1)},
    }
    R = build_R(rule, [k_cancels], slots)
    B = compose_B(D, R)
    results = surviving_coordinate_sharing_check(B, [k_cancels], seams)
    assert results[k_cancels]["status"] == "zero_column"
    assert results[k_cancels]["nonzero_seams"] == []


def test_coordinate_shared_across_two_seams_is_genuinely_shared():
    """A coordinate referenced by two DIFFERENT seams' slots, surviving
    nonzero in both, is correctly classified as genuinely shared -- the
    condition a candidate discipline actually needs to satisfy."""
    D, slots, seams = delta_matrix()
    k_shared = carrier_key(frozenset({0}), frozenset({1}))
    rule = {
        ("e12", "VW"): {k_shared: F(1)},
        ("e23", "UV"): {k_shared: F(1)},
    }
    R = build_R(rule, [k_shared], slots)
    B = compose_B(D, R)
    results = surviving_coordinate_sharing_check(B, [k_shared], seams)
    assert results[k_shared]["status"] == "genuinely_shared"
    assert set(results[k_shared]["nonzero_seams"]) == {"e12", "e23"}


def test_sharing_check_summary_counts_correctly():
    D, slots, seams = delta_matrix()
    k1 = carrier_key(frozenset({0}), frozenset({1}))  # private residual
    k2 = carrier_key(frozenset({2}), frozenset({3}))  # zero column
    k3 = carrier_key(frozenset({4}), frozenset({5}))  # genuinely shared
    rule = {
        ("e12", "U_VvW"): {k1: F(1), k2: F(1)},
        ("e12", "UV"): {k2: F(1)},
        ("e12", "VW"): {k3: F(1)},
        ("e23", "UV"): {k3: F(1)},
    }
    R = build_R(rule, [k1, k2, k3], slots)
    B = compose_B(D, R)
    results = surviving_coordinate_sharing_check(B, [k1, k2, k3], seams)
    summary = sharing_check_summary(results)
    assert summary == {"zero_column": 1, "private_residual": 1, "genuinely_shared": 1}


# --- Cross-validation against the already-verified 3ad4bbd result -----

def test_reproduces_the_lattice_ie_result_via_the_new_infrastructure():
    """The strongest trust check for this infrastructure: rebuild the
    ALREADY-VERIFIED ordered inclusion-exclusion matrix
    (lattice_ie_diagnostic.py, commit 3ad4bbd) using D/R/compose_B, and
    confirm it reproduces the exact same B matrix and the exact same
    'too free by disguised independence' pattern -- every adjacent/plain
    key cancels to a zero column, every composite key survives in
    exactly one seam row."""
    from lattice_ie_diagnostic import REGIONS, THETA, mu_key as ie_mu_key

    D, slots, seams = delta_matrix()

    all_keys = []
    seen = set()
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
        XnY, YnZ = X & Y, Y & Z
        for key in [ie_mu_key(X, Y), ie_mu_key(Y, Z), ie_mu_key(X, Z),
                    ie_mu_key(X, YnZ), ie_mu_key(XnY, Z)]:
            if key not in seen:
                seen.add(key)
                all_keys.append(key)

    rule = {}
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
        XnY, YnZ = X & Y, Y & Z
        rule[(seam, "UV")] = {ie_mu_key(X, Y): F(1)}
        rule[(seam, "VW")] = {ie_mu_key(Y, Z): F(1)}
        rule[(seam, "U_VvW")] = {
            ie_mu_key(X, Y): F(1), ie_mu_key(X, Z): F(1), ie_mu_key(X, YnZ): F(-1),
        }
        rule[(seam, "UvV_W")] = {
            ie_mu_key(X, Z): F(1), ie_mu_key(Y, Z): F(1), ie_mu_key(XnY, Z): F(-1),
        }

    R = build_R(rule, all_keys, slots)
    B = compose_B(D, R)

    from lattice_ie_diagnostic import basis_probe
    expected_B, expected_keys = basis_probe()
    assert all_keys == expected_keys
    assert B == expected_B

    results = surviving_coordinate_sharing_check(B, all_keys, seams)
    summary = sharing_check_summary(results)
    # 4 adjacent-pair keys are shared in R but cancel to zero columns;
    # 4 plain-diagonal keys never appear with nonzero net coefficient either;
    # 8 composite keys each survive in exactly one seam row.
    assert summary["genuinely_shared"] == 0
    assert summary["private_residual"] == 8
    assert summary["zero_column"] == 8
