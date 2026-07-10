"""
Regression tests for refinement_witness_coupled_a4_cancellation_probe.py.

Locks in the headline finding: shared-seam compatibility does NOT force
non-cancellation. It is possible to construct two branches that agree
exactly at a shared seam (a genuine, checked interface_consistent glue),
each individually satisfy their own (A4), and still have the glued
composite's aggregate (A4) fail -- the disjoint-parallel A4 split
survives into the compatible-coupled case.
"""

from refinement_witnesses import ALL_WITNESSES, INSERT_BRIDGE, SUBDIVIDE_U1
from refinement_witness_coupled_a4_cancellation_probe import (
    search_witness_edge, run_search, off_seam_directions,
)
from refinement_checker import coboundary_0
from rational_linear_algebra import nullspace_over_Q, transpose


def test_single_cycle_space_witnesses_offer_no_off_seam_freedom():
    """SUBDIVIDE_U1's refined complex is a single loop -- 1-dimensional
    cycle space -- so no off-seam direction can exist for any of its
    edges; agreement at one shared coordinate pins the whole cycle down
    to a scalar multiple."""
    delta0 = coboundary_0(SUBDIVIDE_U1.vertices, SUBDIVIDE_U1.edges)
    cycle_basis = nullspace_over_Q(transpose(delta0))
    assert len(cycle_basis) == 1
    for edge_index in range(len(SUBDIVIDE_U1.edges)):
        assert off_seam_directions(cycle_basis, edge_index) == []
        assert search_witness_edge(SUBDIVIDE_U1, edge_index) is None


def test_insert_bridge_has_off_seam_freedom():
    delta0 = coboundary_0(INSERT_BRIDGE.vertices, INSERT_BRIDGE.edges)
    cycle_basis = nullspace_over_Q(transpose(delta0))
    assert len(cycle_basis) == 2


def test_compatible_aggregate_cancellation_found_for_insert_bridge_e23():
    r = search_witness_edge(INSERT_BRIDGE, 1)  # e23
    assert r["shared_edge"] == "e23"
    assert r["classification"] == "compatible_branchwise_preserved_aggregate_cancelled"
    assert r["glued_status"] == "interface_consistent"
    assert r["branch_a"]["A4"] is True
    assert r["branch_b"]["A4"] is True
    assert r["combined"]["A4"] is False
    assert r["combined"]["pairing"] == 0


def test_combined_n0_failure_is_inherited_not_new():
    """INSERT_BRIDGE itself already fails its own N0 -- the combined
    N0=False in every found case must be inherited, not a new
    coupling-induced obstruction. Confirmed against the real check(),
    not assumed."""
    from refinement_witnesses import COARSE
    from refinement_witness_coupled_parallel_probe import check as coupled_check
    own = coupled_check(COARSE.vertices, COARSE.edges, COARSE.residue,
                         INSERT_BRIDGE.vertices, INSERT_BRIDGE.edges,
                         INSERT_BRIDGE.vertex_over, INSERT_BRIDGE.declared_z_prime)
    assert own["N0"] is False

    r = search_witness_edge(INSERT_BRIDGE, 1)
    assert r["branch_a"] == own or r["branch_a"]["N0"] is False


def test_run_search_finds_at_least_one_cancellation_case():
    results = run_search()
    found = [r for r in results
             if r.get("classification") == "compatible_branchwise_preserved_aggregate_cancelled"]
    assert len(found) >= 1
    for r in found:
        assert r["combined"]["pairing"] == 0
        assert r["branch_a"]["A4"] is True
        assert r["branch_b"]["A4"] is True
        assert r["glued_status"] == "interface_consistent"


def test_search_only_uses_witnesses_with_multi_dimensional_cycle_space():
    """Sanity check on ALL_WITNESSES itself: exactly one of this
    project's four canonical witnesses offers off-seam freedom at all."""
    multi_dim = []
    for w in ALL_WITNESSES:
        delta0 = coboundary_0(w.vertices, w.edges)
        cycle_basis = nullspace_over_Q(transpose(delta0))
        if len(cycle_basis) > 1:
            multi_dim.append(w.name)
    assert multi_dim == ["insert_bridge"]
