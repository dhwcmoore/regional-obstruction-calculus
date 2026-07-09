"""
Regression tests for refinement_witness_coupled_parallel_probe.py.

Locks in the headline finding: a shared-seam glued composite is only
built when both branches' own declarations for the seam agree exactly
(edge data, declared-cycle value, and vertex parent); when they do not,
no composite is built at all -- the case is reported as
`interface_conflict`, not as an (N0)/(A4)/(E0) failure. When the
composite IS built, it reduces to the disjoint case's own preservation
pattern (N0/E0 hold, A4 branchwise holds).
"""

from fractions import Fraction as F

from refinement_witnesses import SUBDIVIDE_U1, SUBDIVIDE_U2, INSERT_BRIDGE, Edge
from refinement_witness_coupled_parallel_probe import run_case, build_coupled_shared_seam


def test_self_pair_consistent_seam_glues_and_preserves():
    r = run_case("self-pair e23", SUBDIVIDE_U1, SUBDIVIDE_U1, "e23")
    assert r["glued"]["status"] == "interface_consistent"
    assert r["diagnostic_status"] == "disjoint_like_preserved"
    assert r["N0_matches_AND"] is True
    assert r["E0_matches_AND"] is True
    assert r["A4_branchwise_preserved"] is True


def test_cross_witness_organic_agreement_glues_and_preserves():
    r = run_case("cross-witness e34", SUBDIVIDE_U1, SUBDIVIDE_U2, "e34")
    assert r["glued"]["status"] == "interface_consistent"
    assert r["diagnostic_status"] == "disjoint_like_preserved"
    assert r["N0_matches_AND"] is True
    assert r["E0_matches_AND"] is True


def test_cross_witness_organic_conflict_refuses_composite():
    r = run_case("cross-witness e12p", SUBDIVIDE_U1, SUBDIVIDE_U2, "e12p")
    assert r["glued"]["status"] == "interface_conflict"
    assert r["diagnostic_status"] == "interface_conflict"
    # No combined witness -- (N0)/(A4)/(E0) must not even be computed.
    assert "combined" not in r
    a = r["glued"]["branch_a_declaration"]["edge"]
    b = r["glued"]["branch_b_declaration"]["edge"]
    assert a.src != b.src or a.tgt != b.tgt


def test_deliberate_over_sign_conflict_refuses_composite():
    conflicting = Edge("e23", "U2", "U3", over="e23", over_sign=F(-1))
    r = run_case("self-pair e23, over_sign perturbed", SUBDIVIDE_U1, SUBDIVIDE_U1, "e23",
                 override_edge_b=conflicting)
    assert r["glued"]["status"] == "interface_conflict"
    assert "combined" not in r


def test_deliberate_z_prime_conflict_refuses_composite():
    r = run_case("self-pair e23, z-prime perturbed", SUBDIVIDE_U1, SUBDIVIDE_U1, "e23",
                 override_z_b=F(-1))
    assert r["glued"]["status"] == "interface_conflict"
    assert "combined" not in r


def test_organic_conflict_between_subdivide_u1_and_insert_bridge():
    """SUBDIVIDE_U1 declares e23's z' entry as +1; INSERT_BRIDGE declares
    it as -1 -- a real, pre-existing mismatch between two of this
    project's own canonical witnesses, not a constructed one."""
    r = run_case("SUBDIVIDE_U1 (+) INSERT_BRIDGE, shared e23", SUBDIVIDE_U1, INSERT_BRIDGE, "e23")
    assert r["glued"]["status"] == "interface_conflict"
    assert r["glued"]["branch_a_declaration"]["z_prime"] != r["glued"]["branch_b_declaration"]["z_prime"]


def test_missing_combined_fields_absent_on_conflict():
    """build_coupled_shared_seam itself, not just run_case, must not
    fabricate a combined complex on conflict."""
    glued = build_coupled_shared_seam(SUBDIVIDE_U1, SUBDIVIDE_U2, "e12p")
    assert glued["status"] == "interface_conflict"
    assert "refined_vertices" not in glued
    assert "refined_edges" not in glued
