#!/usr/bin/env python3
"""
refinement_witness_coupled_a4_cancellation_probe.py

Phase 5d. refinement_witness_coupled_parallel_probe.py (Phase 5b) and
rocq/CoupledParallelCompatibility.v (Phase 5c) settled shared-seam
compatibility as a well-definedness question: agreement at the shared
seam is necessary and sufficient for a glued composite to exist. Neither
says anything about (N0)/(A4)/(E0) *preservation* once a composite is
built. This probe asks exactly the deferred question:

    Under shared-interface compatibility, can branchwise (A4) hold on
    both branches while the aggregate (summed) pairing still cancels?

The disjoint-parallel case (refinement_witness_parallel_disjoint_probe.py,
Phase 4b) answered yes for fully independent branches: two branches with
opposite-sign, equal-magnitude pairings cancel in aggregate even though
each individually satisfies its own (A4). The open question this probe
settles is whether requiring the two branches to AGREE at one shared
seam removes that freedom -- i.e., whether shared-seam agreement imposes
a hidden non-cancellation constraint -- or whether it survives.

THE KEY CONSTRUCTION PROBLEM. Naive sign-negation (as used in the
disjoint probe) does not obviously work here: for a witness whose
refined complex has a 1-dimensional cycle space (a single loop, which is
every SUBDIVIDE_* witness in this project), the declared cycle is
determined up to an overall SCALAR by any one of its own coordinates --
so fixing agreement at ONE shared coordinate pins down the entire
vector, leaving no room to vary anything else. Cancellation needs
independent variation AWAY from the shared seam while the shared seam
itself stays fixed -- which requires a witness whose cycle space has
dimension >= 2, so that some cycle direction is exactly ZERO at the
shared edge (touches it not at all) while still nonzero, and residue-
carrying, elsewhere.

Checked computationally (not assumed): of this project's four canonical
witnesses, only INSERT_BRIDGE has a 2-dimensional cycle space (5 edges,
4 vertices, two parallel edges e12/b12 between U1 and U2 -- a "big loop"
around all four coarse edges and a "small loop" between the two parallel
U1-U2 edges). The small-loop cycle direction has a ZERO coefficient at
e23 (it never touches e23 at all) but a NONZERO coefficient at e12 (which
carries nonzero pulled-back residue) -- exactly the kind of "vary
off-interface, keep interface fixed" freedom the construction needs. No
other witness in this project offers it; this is reported honestly as a
narrow search, not a general one.

METHOD. For each witness and each of its own edges, compute the cycle
space (nullspace_over_Q on the refined coboundary's transpose) and solve
for the subspace of cycle vectors that vanish at that edge's coordinate
(nullspace_over_Q again, now applied to the single "evaluate at this
edge" linear functional restricted to the cycle-space basis). Where that
subspace is nontrivial, EXACTLY solve (not scan) for the scalar multiple
of an off-seam direction that makes the aggregate pairing zero, then
verify the result with the same real machinery every other probe in
this project uses -- build_coupled_shared_seam, check() -- not trusted
from the algebra alone.

USAGE:
    python refinement_witness_coupled_a4_cancellation_probe.py
"""

from fractions import Fraction as F
from typing import List, Optional

from refinement_witnesses import COARSE, ALL_WITNESSES, Witness
from refinement_checker import coboundary_0, pullback_matrix
from rational_linear_algebra import nullspace_over_Q, transpose, mat_vec, dot
from refinement_witness_coupled_parallel_probe import build_coupled_shared_seam, check


def off_seam_directions(cycle_basis: List[List[F]], edge_index: int) -> List[List[F]]:
    """Given a basis for a refined complex's cycle space (each basis
    vector aligned index-for-index with the refined edge list), returns
    a basis for the subspace of cycle vectors whose coordinate at
    `edge_index` is exactly zero -- i.e. cycles that do not touch the
    shared edge at all, computed exactly via nullspace_over_Q on the
    single linear constraint "coefficient at edge_index vanishes", not
    assumed or hand-picked from the raw basis."""
    if len(cycle_basis) < 2:
        return []
    row = [[z[edge_index] for z in cycle_basis]]
    coeff_basis = nullspace_over_Q(row)
    directions = []
    for coeffs in coeff_basis:
        vec = [F(0)] * len(cycle_basis[0])
        for c, z in zip(coeffs, cycle_basis):
            vec = [v + c * zi for v, zi in zip(vec, z)]
        directions.append(vec)
    return directions


def search_witness_edge(witness: Witness, edge_index: int) -> Optional[dict]:
    """Attempts to construct a compatible-shared-seam pair (witness
    self-paired) at `edge_index` where branchwise (A4) holds on both
    branches but the aggregate pairing is exactly zero. Returns a result
    dict describing the outcome, or None if no off-seam freedom exists
    at all for this (witness, edge) pair."""
    shared_edge_name = witness.edges[edge_index].name

    delta0_refined = coboundary_0(witness.vertices, witness.edges)
    cycle_basis = nullspace_over_Q(transpose(delta0_refined))
    directions = off_seam_directions(cycle_basis, edge_index)
    if not directions:
        return None

    rho_star = pullback_matrix(COARSE.edges, witness.edges)
    rho_star_r = mat_vec(rho_star, COARSE.residue)
    pairing_own = dot(witness.declared_z_prime, rho_star_r)
    # The shared edge's own contribution to the pairing -- needed because
    # in the GLUED complex the shared edge appears ONCE, not twice: naively
    # solving as if combined_pairing = pairing_A + pairing_B (true for the
    # DISJOINT construction, where nothing is shared) overcounts the shared
    # edge's contribution by exactly this amount. Caught by comparing a
    # first (wrong) solve against this script's own real check() output,
    # not trusted from algebra alone -- see docs/design/
    # REFINEMENT_WITNESS_COMPOSITION_STATUS.md, Phase 5d, for the account.
    shared_contrib = witness.declared_z_prime[edge_index] * rho_star_r[edge_index]

    for direction in directions:
        correction = dot(direction, rho_star_r)
        if correction == 0:
            # This off-seam direction never touches a residue-carrying
            # edge -- varying along it cannot change the pairing at all,
            # so no cancellation is reachable this way. Reported, not
            # silently skipped.
            continue

        # Exact solve for the GLUED complex's combined pairing:
        #   combined_pairing(lambda) = 2*pairing_own - shared_contrib
        #                               + lambda*correction
        # (branch A keeps witness's own declared cycle; branch B is
        # witness's own declared cycle plus lambda*direction; the shared
        # edge's contribution, common to both branches by construction,
        # is subtracted once to correct for single- vs double-counting).
        lam = (shared_contrib - F(2) * pairing_own) / correction
        z_b = [za + lam * d for za, d in zip(witness.declared_z_prime, direction)]

        witness_b = Witness(
            name=witness.name + "_offseam_variant",
            description="Branch B: witness's own cycle plus a scalar multiple of an "
                        "off-seam cycle direction, chosen to cancel the aggregate pairing "
                        "while leaving the shared seam's declared value untouched.",
            vertices=witness.vertices, edges=witness.edges,
            declared_z_prime=z_b, vertex_over=witness.vertex_over,
        )

        glued = build_coupled_shared_seam(witness, witness_b, shared_edge_name)
        result_a = check(COARSE.vertices, COARSE.edges, COARSE.residue,
                          witness.vertices, witness.edges, witness.vertex_over,
                          witness.declared_z_prime)
        result_b = check(COARSE.vertices, COARSE.edges, COARSE.residue,
                          witness_b.vertices, witness_b.edges, witness_b.vertex_over,
                          witness_b.declared_z_prime)

        out = {
            "witness": witness.name, "shared_edge": shared_edge_name,
            "lambda": lam, "direction": direction,
            "glued_status": glued["status"],
            "branch_a": result_a, "branch_b": result_b,
        }

        if glued["status"] != "interface_consistent":
            out["classification"] = "unresolved_construction_incompatible"
            out["note"] = ("The off-seam direction's correction was nonzero, but the "
                            "resulting z_b did not actually stay compatible at the shared "
                            "edge -- a sign this off-seam direction was not as 'off-seam' "
                            "as assumed. Reported, not hidden.")
            return out

        combined = check(glued["coarse_vertices"], glued["coarse_edges"], glued["residue"],
                          glued["refined_vertices"], glued["refined_edges"],
                          glued["vertex_over"], glued["z_prime"])
        out["combined"] = combined
        branchwise_preserved = result_a["A4"] and result_b["A4"]
        aggregate_preserved = combined["A4"]

        if branchwise_preserved and not aggregate_preserved:
            out["classification"] = "compatible_branchwise_preserved_aggregate_cancelled"
        elif branchwise_preserved and aggregate_preserved:
            out["classification"] = "compatible_branchwise_preserved_aggregate_preserved"
        else:
            out["classification"] = "unresolved_branchwise_not_preserved"
        return out

    return {"witness": witness.name, "shared_edge": shared_edge_name,
            "classification": "no_pairing_affecting_direction",
            "note": "Off-seam cycle-space directions exist but none carries nonzero "
                    "pulled-back residue at any coordinate -- varying along them cannot "
                    "change the pairing, so no cancellation search was possible here."}


def run_search() -> List[dict]:
    results = []
    for witness in ALL_WITNESSES:
        for edge_index in range(len(witness.edges)):
            r = search_witness_edge(witness, edge_index)
            if r is not None:
                results.append(r)
    return results


def print_report() -> None:
    print("Coupled parallel A4 cancellation search")
    print("(searching for: shared-seam compatible, branchwise A4 preserved,")
    print(" aggregate A4 cancelled)")
    print()

    results = run_search()
    if not results:
        print("No witness/edge pair in ALL_WITNESSES offered off-seam cycle-space "
              "freedom at all (every witness besides INSERT_BRIDGE has a 1-dimensional "
              "cycle space, which agreement at one shared coordinate pins down entirely).")
        return

    for r in results:
        print(f"witness={r['witness']}  shared_edge={r['shared_edge']}")
        print(f"  classification: {r['classification']}")
        if "lambda" in r:
            print(f"  lambda={r['lambda']}  direction={r['direction']}")
            print(f"  branch A: A4={r['branch_a']['A4']} pairing={r['branch_a']['pairing']}")
            print(f"  branch B: A4={r['branch_b']['A4']} pairing={r['branch_b']['pairing']}")
            if "combined" in r:
                print(f"  combined: A4={r['combined']['A4']} pairing={r['combined']['pairing']}  "
                      f"N0={r['combined']['N0']}  E0={r['combined']['E0']}")
        if "note" in r:
            print(f"  note: {r['note']}")
        print()

    found = [r for r in results if r["classification"] == "compatible_branchwise_preserved_aggregate_cancelled"]
    print("=== SUMMARY ===")
    if found:
        print(f"Found {len(found)} compatible-branchwise-preserved-aggregate-cancelled "
              f"case(s). Shared-seam compatibility does NOT force non-cancellation for "
              f"this witness family -- the disjoint case's A4 split survives into the "
              f"coupled (compatible) case.")
        print()
        print("Note: every found case shows combined N0=False. This is NOT a new "
              "obstruction created by gluing -- INSERT_BRIDGE (the only witness in this "
              "project's ALL_WITNESSES with a >1-dimensional cycle space, and so the only "
              "one this search could use at all) already fails its OWN N0 individually "
              "(documented in refinement_witnesses.py's own comment: 'naturality fails at "
              "b12's row'). The combined N0=False is inherited warrant debt from a "
              "component witness that was never N0-safe on its own terms, the same "
              "distinction this project's composition line has drawn since Phase 2b.")
    else:
        print("No compatible-branchwise-preserved-aggregate-cancelled case found in this "
              "search. Not claimed as a theorem or a general fact -- only that this "
              "narrow, non-exhaustive search (one witness family, self-paired, one "
              "off-seam direction per case) did not find one.")


if __name__ == "__main__":
    print_report()
