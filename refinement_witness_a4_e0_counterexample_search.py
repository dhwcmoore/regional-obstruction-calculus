#!/usr/bin/env python3
"""
refinement_witness_a4_e0_counterexample_search.py

Phase 2 of the refinement-witness composition line (see
docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md): (N0)-composability
is now a proved theorem (rocq/RefinementWitnessComposition.v). (A4)
nonzero pairing and (E0) exactness reflection composability are not --
refinement_witness_composition_probe.py tested exactly two hand-built
composed witnesses and both preserved A4/E0. This file replaces "more
positive examples" with an actual SEARCH: many composed witnesses,
generated systematically rather than hand-picked one at a time, checked
against the real machinery, looking for the six things a genuine
composition theory needs to know:

    1. Does N0 always compose? (Already proved -- included here only as
       a live sanity check against the search's own generated examples,
       not as new evidence.)
    2. Under what side conditions does A4 compose?
    3. Under what side conditions does E0 compose?
    4. Can A4 pass while E0 fails, at the composite level?
    5. Can E0 pass while A4 fails?
    6. Can both A4 and E0 fail while N0 still composes?

Two generic second-step operations, applicable to ANY complex (not
hand-coded per vertex name the way refinement_witnesses.py's four
witnesses are): subdividing a vertex (rerouting ALL its incoming edges
through a new "_a" copy and ALL its outgoing edges through a new "_b"
copy, joined by an internal edge -- this is the general form of what
SUBDIVIDE_U1/U2/ALL do by hand for a simple cycle) and inserting a
bridge between two existing vertices (the general form of INSERT_BRIDGE).
For each generated second-level complex, every basis cycle of its own
cycle space (not just one hand-picked cycle) is tried as the declared
witness cycle, since a complex can have more than one independent cycle
once bridges accumulate.

USAGE:
    python refinement_witness_a4_e0_counterexample_search.py
"""

from fractions import Fraction as F
from itertools import combinations
from typing import Dict, List, Tuple

from refinement_witnesses import COARSE, ALL_WITNESSES, Edge, Witness
from refinement_checker import coboundary_0, pullback_matrix, vertex_pullback_matrix
from rational_linear_algebra import (
    mat_vec, mat_mat, row_vec_mat, dot, is_zero,
    transpose, nullspace_over_Q,
)


def generic_subdivide(vertices: List[str], edges: List[Edge], target: str
                       ) -> Tuple[List[str], List[Edge], Dict[str, str]]:
    """Splits `target` into `target_a` (incoming half) / `target_b`
    (outgoing half), joined by an internal edge. ALL edges incident to
    `target` are rerouted, not just one in / one out -- the general form
    of what SUBDIVIDE_U1/U2/ALL do by hand on a simple cycle."""
    a, b = f"{target}_a", f"{target}_b"
    new_vertices = [v for v in vertices if v != target] + [a, b]
    new_edges = []
    for e in edges:
        src = b if e.src == target else e.src
        tgt = a if e.tgt == target else e.tgt
        new_edges.append(Edge(e.name, src, tgt, over=e.name, over_sign=F(1)))
    new_edges.append(Edge(f"s_{target}", a, b, over=None))
    vertex_over = {v: (target if v in (a, b) else v) for v in new_vertices}
    return new_vertices, new_edges, vertex_over


def generic_insert_bridge(vertices: List[str], edges: List[Edge], v1: str, v2: str, tag: str
                           ) -> Tuple[List[str], List[Edge], Dict[str, str]]:
    """Adds a new edge v1->v2, identity pullback on everything else --
    the general form of INSERT_BRIDGE."""
    new_edges = [Edge(e.name, e.src, e.tgt, over=e.name, over_sign=F(1)) for e in edges]
    new_edges.append(Edge(f"bridge_{tag}", v1, v2, over=None))
    vertex_over = {v: v for v in vertices}
    return list(vertices), new_edges, vertex_over


def check_step(coarse_vertices, coarse_edges, coarse_residue,
               fine_vertices, fine_edges, vertex_over, z_prime
               ) -> dict:
    """A1-A4/N0 for one refinement step (coarse -> fine), given a
    specific declared cycle z_prime in the fine complex."""
    delta0_coarse = coboundary_0(coarse_vertices, coarse_edges)
    delta0_fine = coboundary_0(fine_vertices, fine_edges)
    rho_star = pullback_matrix(coarse_edges, fine_edges)
    rho0_star = vertex_pullback_matrix(coarse_vertices, fine_vertices, vertex_over)
    rho_star_r = mat_vec(rho_star, coarse_residue)
    a3 = is_zero(row_vec_mat(z_prime, delta0_fine))
    pairing = dot(z_prime, rho_star_r)
    a4 = pairing != 0
    n0 = mat_mat(delta0_fine, rho0_star) == mat_mat(rho_star, delta0_coarse)
    return {
        "rho_star": rho_star, "rho0_star": rho0_star, "rho_star_r": rho_star_r,
        "delta0_fine": delta0_fine, "A3": a3, "A4": a4, "pairing": pairing, "N0": n0,
    }


def search() -> List[dict]:
    results = []
    delta0_C = coboundary_0(COARSE.vertices, COARSE.edges)
    Z1_coarse = nullspace_over_Q(transpose(delta0_C))

    for w1 in ALL_WITNESSES:
        Q_vertices, Q_edges = w1.vertices, w1.edges
        rho_star_CQ = pullback_matrix(COARSE.edges, Q_edges)
        rho0_star_CQ = vertex_pullback_matrix(COARSE.vertices, Q_vertices, w1.vertex_over)
        Q_residue = mat_vec(rho_star_CQ, COARSE.residue)
        step1_N0 = mat_mat(coboundary_0(Q_vertices, Q_edges), rho0_star_CQ) == mat_mat(rho_star_CQ, delta0_C)

        second_steps = []
        for v in Q_vertices:
            second_steps.append(("subdivide", v, generic_subdivide(Q_vertices, Q_edges, v)))
        for v1, v2 in combinations(Q_vertices, 2):
            second_steps.append(("bridge", f"{v1}-{v2}", generic_insert_bridge(Q_vertices, Q_edges, v1, v2, f"{v1}_{v2}")))

        for op_name, op_target, (R_vertices, R_edges, R_vertex_over) in second_steps:
            delta0_R = coboundary_0(R_vertices, R_edges)
            Z1_R = nullspace_over_Q(transpose(delta0_R))
            if not Z1_R:
                continue  # no cycle at all in R -- degenerate, skip

            rho_star_QR = pullback_matrix(Q_edges, R_edges)
            rho0_star_QR = vertex_pullback_matrix(Q_vertices, R_vertices, R_vertex_over)

            for z_prime in Z1_R:
                step2 = check_step(Q_vertices, Q_edges, Q_residue,
                                    R_vertices, R_edges, R_vertex_over, z_prime)
                if not (step2["A3"] and step2["A4"] and step2["N0"]):
                    continue  # step 2 itself isn't a full admissible+descent-safe
                               # witness for this cycle -- not a useful composition test

                composite_rho_star = mat_mat(rho_star_QR, rho_star_CQ)
                composite_rho0_star = mat_mat(rho0_star_QR, rho0_star_CQ)
                composite_rho_star_r = mat_vec(composite_rho_star, COARSE.residue)
                pairing_comp = dot(z_prime, composite_rho_star_r)
                a4_comp = pairing_comp != 0
                n0_comp = mat_mat(delta0_R, composite_rho0_star) == mat_mat(composite_rho_star, delta0_C)

                pushed_cycles = [mat_vec(transpose(composite_rho_star), z) for z in Z1_R]
                from rational_linear_algebra import in_span_over_Q
                e0_comp = all(in_span_over_Q(pushed_cycles, z) for z in Z1_coarse)

                results.append({
                    "step1": w1.name, "step2_op": op_name, "step2_target": op_target,
                    "step1_N0": step1_N0, "step2_N0": step2["N0"],
                    "composite_A4": a4_comp, "composite_pairing": pairing_comp,
                    "composite_N0": n0_comp, "composite_E0": e0_comp,
                })
    return results


def verify_n0_theorem_consistency(results: List[dict]) -> bool:
    """Cross-checks the search's own data against N0_composes
    (rocq/RefinementWitnessComposition.v): every composite N0 failure
    must trace to step1's OWN N0 failing (step2's N0 is already required
    True to reach this point) -- the theorem says N0 composes whenever
    BOTH steps hold, so a composite failure is only consistent with the
    theorem if at least one step already failed individually."""
    for r in results:
        if not r["composite_N0"] and r["step1_N0"] and r["step2_N0"]:
            return False  # would contradict N0_composes
    return True


def print_report() -> None:
    results = search()
    n = len(results)
    a4_fail = [r for r in results if not r["composite_A4"]]
    e0_fail = [r for r in results if not r["composite_E0"]]
    n0_fail = [r for r in results if not r["composite_N0"]]
    a4_pass_e0_fail = [r for r in results if r["composite_A4"] and not r["composite_E0"]]
    e0_pass_a4_fail = [r for r in results if r["composite_E0"] and not r["composite_A4"]]
    both_fail_n0_ok = [r for r in results if not r["composite_A4"] and not r["composite_E0"] and r["composite_N0"]]

    print(f"Refinement witness A4/E0 composition search")
    print(f"  total composed witnesses tested (step1 x step2 x cycle choice): {n}")
    print(f"  N0_composes cross-check against this search's own data: "
          f"{verify_n0_theorem_consistency(results)}")
    print(f"  composite A4 failures: {len(a4_fail)}")
    print(f"  composite E0 failures: {len(e0_fail)}")
    print(f"  composite N0 failures: {len(n0_fail)}")
    print(f"  A4 passes while E0 fails: {len(a4_pass_e0_fail)}")
    print(f"  E0 passes while A4 fails: {len(e0_pass_a4_fail)}")
    print(f"  both A4 and E0 fail while N0 composes: {len(both_fail_n0_ok)}")
    print()
    if a4_fail:
        print("First A4 counterexample:")
        r = a4_fail[0]
        print(f"  {r}")
    if e0_fail:
        print("First E0 counterexample:")
        r = e0_fail[0]
        print(f"  {r}")
    if not a4_fail and not e0_fail:
        print("No A4 or E0 counterexample found in this search.")
        print("This is evidence, not a proof -- see docs/design/")
        print("REFINEMENT_WITNESS_COMPOSITION_STATUS.md for what would")
        print("be needed to go further.")


if __name__ == "__main__":
    print_report()
