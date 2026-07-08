"""
Tests for candidate_discipline_diagnostic.py: Candidate 3b, the ordered
restriction-to-triple-support outer-slot discipline, run through
carrier_matrix_infrastructure.py against the real generator.
"""

from fractions import Fraction as F

from candidate_discipline_diagnostic import (
    THETA,
    triple_support,
    all_carrier_coordinates,
    induced_B,
    diagnose,
    verify_B_matches_real_generator,
    verify_reduction_against_real_code,
)
from coupled_realisability_diagnostic import REGIONS
from carrier_matrix_infrastructure import carrier_key


def test_every_triple_overlap_is_a_distinct_singleton():
    """Documents the anticipated catch: this cover's cyclic triple
    overlaps are four distinct single points, so no rho_{A,T} coordinate
    can recur across two seams under Candidate 3b."""
    supports = []
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
        T = triple_support(X, Y, Z)
        assert len(T) == 1
        supports.append(T)
    assert len(set(supports)) == 4


def test_eight_distinct_carrier_coordinates_no_collisions():
    coords = all_carrier_coordinates()
    assert len(coords) == 8
    assert len(set(coords)) == 8


def test_B_matches_independent_real_generator_basis_probe():
    assert verify_B_matches_real_generator() is True


def test_reduction_formula_verified_against_real_code():
    for seam in ("e12", "e23", "e34", "e14"):
        assert verify_reduction_against_real_code(seam) is True


def test_sharing_check_reports_all_private_residual():
    """The anticipated failure mode, confirmed computationally: with no
    repeated triple support in this cover, every rho_{A,T} coordinate
    survives in exactly one seam row."""
    result = diagnose()
    assert result["sharing_summary"] == {
        "zero_column": 0,
        "private_residual": 8,
        "genuinely_shared": 0,
    }


def test_full_rank_verdict():
    """Each seam row has two disjoint private columns (+1/-1), so the
    induced B is block-diagonal across seams and full rank -- the same
    TOO_FREE outcome as lattice_ie_diagnostic.py, reached here for a
    simpler reason (never globally indexed on this cover at all, not
    algebraic cancellation of shared terms)."""
    result = diagnose()
    assert result["rank_B"] == 4
    assert result["full_rank"] is True
    assert result["verdict"] == "TOO_FREE_full_rank"


def test_induced_B_shape():
    B, carrier_coords, seams = induced_B()
    assert len(B) == 4
    assert len(carrier_coords) == 8
    assert len(B[0]) == 8


def test_tamper_breaks_reduction_check():
    """A tampered claimed formula (missing sign) must fail the real-code
    check -- confirms the check is actually discriminating, not
    vacuously true."""
    import random
    from regional_composition import VennTriple, SeamCorrectionData
    from associator_residue import SeamAssociatorInstance, compute_seam_residue

    rng = random.Random(1)
    seam = "e12"
    xk, yk, zk = THETA[seam]
    X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
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
