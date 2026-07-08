"""
Locks in the ordered inclusion-exclusion diagnostic's result: full rank,
i.e. "too free by disguised independence" -- a third, structurally
distinct failure mode from the independent generator's explicit private
freedom and the shared-adjacent-mu construction's coboundary collapse.

Also locks in the two independent checks the headline result depends on
(the cancellation identity against the real matrix, and the reduction
formula against compute_seam_residue directly under random parameters),
so a future change can't silently break the reasoning while leaving the
rank number looking unchanged.
"""

from fractions import Fraction as F

from lattice_ie_diagnostic import (
    diagnose,
    basis_probe,
    verify_cancellation,
    verify_reduction_against_real_code,
    residue_for,
    mu_key,
    all_global_keys,
)
from coupled_realisability_diagnostic import REGIONS


def test_full_rank_too_free_verdict():
    result = diagnose()
    assert result["n_params"] == 16
    assert result["dim_C1"] == 4
    assert result["rank_B"] == 4
    assert result["full_rank"] is True
    assert result["verdict"] == "TOO_FREE_full_rank"


def test_cancellation_identity_holds_against_real_matrix():
    """Every adjacent-pair / plain-diagonal column of the real
    basis-probed matrix is exactly zero -- checked structurally against
    the matrix, not assumed from the symbolic reduction."""
    assert verify_cancellation() is True


def test_reduction_formula_holds_on_two_independent_triples():
    assert verify_reduction_against_real_code("e12") is True
    assert verify_reduction_against_real_code("e34") is True


def test_only_composite_keys_are_nonzero_in_the_matrix():
    """Direct structural check: of the 16 global keys, only the 8
    composite (meet-based) ones have any nonzero entry anywhere in B_IE."""
    matrix, keys = basis_probe()
    atomic_sets = {frozenset(v) for v in REGIONS.values()}
    nonzero_key_count = 0
    for col_idx, key in enumerate(keys):
        P, Q = key
        is_composite = (P not in atomic_sets) or (Q not in atomic_sets)
        col = [matrix[row][col_idx] for row in range(len(matrix))]
        has_nonzero = any(x != 0 for x in col)
        if has_nonzero:
            nonzero_key_count += 1
            assert is_composite, f"non-composite key {key} unexpectedly nonzero"
    assert nonzero_key_count == 8


def test_no_composite_key_is_shared_across_two_triples():
    """The specific reason the map is full rank: each triple's two
    surviving composite keys are structurally unique to it -- no
    composite key appears in more than one row of the matrix."""
    matrix, keys = basis_probe()
    for col_idx in range(len(keys)):
        nonzero_rows = [r for r in range(len(matrix)) if matrix[r][col_idx] != 0]
        assert len(nonzero_rows) <= 1, f"key {keys[col_idx]} is shared across rows {nonzero_rows}"


def test_raw_quotient_equals_H1_dimension_not_partial_selectivity():
    """Regression guard against the exact misreading this diagnostic
    corrected: dim(quotient)=1 here is just dim H^1(N;Q), not evidence of
    structural selectivity, precisely because the map is fully
    surjective."""
    result = diagnose()
    assert result["dim_quotient_raw"] == 1
    assert result["dim_C1"] - result["rank_delta0"] == result["dim_quotient_raw"]
    assert result["full_rank"] is True  # <- why the raw number above is a red herring


def test_setting_only_adjacent_keys_gives_zero_residue():
    """Direct demonstration of the cancellation claim: populating ONLY
    the (non-composite) adjacent/diagonal keys, leaving every composite
    key at its default of zero, produces the all-zero residue -- those
    parameters are provably inert."""
    keys = all_global_keys()
    atomic_sets = {frozenset(v) for v in REGIONS.values()}
    mu = {}
    for k in keys:
        P, Q = k
        if P in atomic_sets and Q in atomic_sets:
            mu[k] = F(3)  # arbitrary nonzero value on adjacent/diagonal keys only
    r = residue_for(mu)
    assert r == [F(0), F(0), F(0), F(0)]
