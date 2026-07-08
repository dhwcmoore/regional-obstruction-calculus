"""
Tests for repeated_triple_support_diagnostic.py: Candidate 3b run on a
repeated-triple-support cover, the first positive linear/rational
diagnostic in this realisability line.
"""

from fractions import Fraction as F

from repeated_triple_support_diagnostic import (
    THETA,
    CANONICAL_REGIONS,
    verify_opposite_pair_sharing_forces_global,
    check_nondegenerate,
    check_triple_overlaps_singleton_and_equal,
    triple_support,
    all_carrier_coordinates,
    induced_B,
    diagnose,
    verify_B_matches_real_generator,
    verify_reduction_against_real_code,
    richness_invariance_check,
    _build_enriched_cover,
)
from carrier_matrix_infrastructure import carrier_key


def test_opposite_pair_distinct_sharing_is_structurally_impossible():
    """The key structural fact this whole diagnostic depends on: forcing
    a point into two theta-triples' overlaps forces it into all four --
    ruling out an independent second shared point for the other pair."""
    assert verify_opposite_pair_sharing_forces_global() is True


def test_canonical_cover_is_nondegenerate():
    ok, problems = check_nondegenerate(CANONICAL_REGIONS)
    assert ok, problems
    for region in CANONICAL_REGIONS.values():
        assert len(region) == 5


def test_canonical_cover_triple_overlaps_singleton_and_equal():
    ok, overlaps = check_triple_overlaps_singleton_and_equal(CANONICAL_REGIONS)
    assert ok
    assert len(set(overlaps.values())) == 1
    (only_point,) = list(overlaps.values())[0]
    for seam in THETA:
        assert overlaps[seam] == frozenset({only_point})


def test_four_carrier_coordinates_no_collisions():
    coords = all_carrier_coordinates(CANONICAL_REGIONS)
    assert len(coords) == 4
    assert len(set(coords)) == 4


def test_B_matches_independent_real_generator_basis_probe():
    assert verify_B_matches_real_generator(CANONICAL_REGIONS) is True


def test_reduction_formula_verified_against_real_code():
    for seam in ("e12", "e23", "e34", "e14"):
        assert verify_reduction_against_real_code(CANONICAL_REGIONS, seam) is True


def test_sharing_check_reports_all_genuinely_shared():
    result = diagnose(CANONICAL_REGIONS)
    assert result["sharing_summary"] == {
        "zero_column": 0,
        "private_residual": 0,
        "genuinely_shared": 4,
    }


def test_partial_rank_nontrivial_quotient_verdict():
    """The headline result: rank(B)=2 (neither 0 nor full rank 4),
    dim(im(B) n im(delta0))=1, dim(quotient)=1 -- genuinely partial."""
    result = diagnose(CANONICAL_REGIONS)
    assert result["rank_B"] == 2
    assert result["full_rank"] is False
    assert result["dim_intersection"] == 1
    assert result["dim_quotient_raw"] == 1
    assert result["verdict"] == "genuinely_partial_nontrivial_quotient"


def test_induced_B_shape():
    B, carrier_coords, seams = induced_B(CANONICAL_REGIONS)
    assert len(B) == 4
    assert len(carrier_coords) == 4
    assert len(B[0]) == 4


def test_opposite_seam_rows_are_negatives_of_each_other():
    """r_e12 = -r_e34 and r_e23 = -r_e14, the exact structural form the
    docstring predicts from the theta-role pairing."""
    B, carrier_coords, seams = induced_B(CANONICAL_REGIONS)
    e12, e23, e34, e14 = (seams.index(s) for s in ("e12", "e23", "e34", "e14"))
    for col in range(len(carrier_coords)):
        assert B[e12][col] == -B[e34][col]
        assert B[e23][col] == -B[e14][col]


def test_richness_invariance_across_enriched_covers():
    """The claim that enrichment cannot change the verdict, checked
    directly rather than argued by hand -- reruns diagnose() on covers up
    to |Ui|=12."""
    assert richness_invariance_check() is True


def test_enriched_cover_still_nondegenerate_and_repeated_support():
    regions = _build_enriched_cover(extra_private=2, extra_pairwise=2, seed=999)
    ok_nd, _ = check_nondegenerate(regions)
    ok_overlap, overlaps = check_triple_overlaps_singleton_and_equal(regions)
    assert ok_nd
    assert ok_overlap
    assert len(set(overlaps.values())) == 1


def test_distinct_support_cover_is_not_repeated_support():
    """Sanity boundary check: the standard distinct-triple-support cover
    (candidate_discipline_diagnostic's, via coupled_realisability_
    diagnostic.REGIONS) must NOT satisfy the repeated-support condition --
    confirms this diagnostic's precondition is a real dividing line, not
    vacuously true of every cover."""
    from coupled_realisability_diagnostic import REGIONS as DISTINCT_REGIONS
    ok, overlaps = check_triple_overlaps_singleton_and_equal(DISTINCT_REGIONS)
    assert ok is False
    assert len(set(overlaps.values())) == 4


def test_tamper_breaks_reduction_check():
    """A tampered claimed formula (missing sign) must fail the real-code
    check -- confirms the check is actually discriminating."""
    import random
    from regional_composition import VennTriple, SeamCorrectionData
    from associator_residue import SeamAssociatorInstance, compute_seam_residue

    rng = random.Random(1)
    seam = "e12"
    xk, yk, zk = THETA[seam]
    X, Y, Z = CANONICAL_REGIONS[xk], CANONICAL_REGIONS[yk], CANONICAL_REGIONS[zk]
    T = triple_support(X, Y, Z)
    kx, kz = carrier_key(X, T), carrier_key(Z, T)
    rho = {
        kx: F(rng.randint(-5, 5), rng.randint(1, 3)),
        kz: F(rng.randint(-5, 5), rng.randint(1, 3)),
    }
    corr = SeamCorrectionData(
        mu_UV=F(0), mu_VW=F(0),
        mu_U_VvW=rho[kx], mu_UvV_W=rho[kz],
    )
    triple = VennTriple(U=X, V=Y, W=Z)
    inst = SeamAssociatorInstance(seam=seam, mu=corr, triple=triple)
    real_r = compute_seam_residue(inst)
    tampered_claim = rho[kx] + rho[kz]  # wrong sign
    if rho[kz] != 0:
        assert real_r != tampered_claim
