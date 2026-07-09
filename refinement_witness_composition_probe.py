#!/usr/bin/env python3
"""
refinement_witness_composition_probe.py

Tests, rather than assumes, whether admissible/descent-safe/exactness-
reflecting refinement witnesses COOMPOSE: given a first witness C -> Q
and a second witness Q -> R, does the COMPOSITE map C -> R -- built by
matrix-multiplying the two individually-verified pullback maps, not
re-derived from scratch -- itself satisfy (A1)-(A4), (N0), and (E0)?

This is explicitly not assumed anywhere else in this project (see the
"Open directions" section of paper/finite_obstruction_calculus_for_
regional_warrant.tex, and docs/design/REFINEMENT_WITNESS_COMPOSITION_
STATUS.md for the write-up of what this file finds). It is NOT the same
claim as rocq/CommonSubdivisionAgreement.v, which compares two witnesses
sharing a common target rather than composing one witness with another.

What this file establishes, precisely
--------------------------------------
1. N0-composability is PROVABLE, not merely tested: if both individual
   steps satisfy (N0), the composite provably satisfies (N0) too, by
   associativity of matrix multiplication alone --
   verify_n0_composability_is_associativity() checks this identity
   directly against many random matrix triples (a sanity check of the
   algebra, not a proof substitute -- the proof is the one-line
   associativity argument in the module docstring of
   docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md).
2. A4 (nonzero pairing) and E0 (exactness reflection) composability are
   NOT established by any argument this project has -- two concrete
   composed witnesses are tested here (a genuine two-step subdivision,
   and a subdivision composed with a bridge insertion) and both happen
   to preserve A4/E0, but two positive examples are not a theorem. No
   counterexample has been found; none has been proved impossible.

USAGE:
    python refinement_witness_composition_probe.py
"""

from fractions import Fraction as F
import random

from refinement_witnesses import COARSE, SUBDIVIDE_U1, Edge
from refinement_checker import coboundary_0, pullback_matrix, vertex_pullback_matrix, check_witness
from rational_linear_algebra import (
    mat_vec, mat_mat, row_vec_mat, dot, is_zero,
    transpose, nullspace_over_Q, in_span_over_Q,
)


def verify_n0_composability_is_associativity(trials: int = 20, seed: int = 20260709) -> bool:
    """N0 for a single witness is the matrix identity delta'^0 @ rho0^* ==
    rho^* @ delta^0. If this holds for both C->Q and Q->R, it holds for
    the composite C->R (composite_rho0 = rho0_QR @ rho0_CQ, composite_rho
    = rho_QR @ rho_CQ) purely because matrix multiplication is
    associative: delta''^0 @ (rho0_QR @ rho0_CQ)
        = (delta''^0 @ rho0_QR) @ rho0_CQ           [associativity]
        = (rho_QR @ delta'^0) @ rho0_CQ              [N0 at step 2]
        = rho_QR @ (delta'^0 @ rho0_CQ)               [associativity]
        = rho_QR @ (rho_CQ @ delta^0)                 [N0 at step 1]
        = (rho_QR @ rho_CQ) @ delta^0                  [associativity]
    This is not a claim needing empirical support; this function checks
    the associativity identity itself against many random rational
    matrix triples, as a sanity check of mat_mat's own correctness, not
    as evidence for the argument above (which needs none)."""
    rng = random.Random(seed)

    def rand_matrix(rows, cols):
        return [[F(rng.randint(-5, 5), rng.randint(1, 3)) for _ in range(cols)] for _ in range(rows)]

    for _ in range(trials):
        m, n, p, q = (rng.randint(1, 4) for _ in range(4))
        D = rand_matrix(m, n)
        A = rand_matrix(n, p)
        B = rand_matrix(p, q)
        if mat_mat(mat_mat(D, A), B) != mat_mat(D, mat_mat(A, B)):
            return False
    return True


def _second_subdivision_scenario():
    """Step 1: C -> Q (SUBDIVIDE_U1, already verified elsewhere). Step 2:
    Q -> R, a second subdivision splitting Q's own U2 vertex, constructed
    the same way SUBDIVIDE_U2 splits COARSE's U2. Returns a dict of all
    intermediate and composite results."""
    cert1 = check_witness(SUBDIVIDE_U1)

    Q_vertices = SUBDIVIDE_U1.vertices
    Q_edges = SUBDIVIDE_U1.edges
    rho_star_CQ = pullback_matrix(COARSE.edges, Q_edges)
    rho0_star_CQ = vertex_pullback_matrix(COARSE.vertices, Q_vertices, SUBDIVIDE_U1.vertex_over)
    Q_residue = mat_vec(rho_star_CQ, COARSE.residue)

    R_vertices = ["U1a", "U1b", "U2a", "U2b", "U3", "U4"]
    R_edges = [
        Edge("e12pp", "U1b", "U2a", over="e12p", over_sign=F(1)),
        Edge("s2p", "U2a", "U2b", over=None),
        Edge("e23p", "U2b", "U3", over="e23", over_sign=F(1)),
        Edge("e34", "U3", "U4", over="e34", over_sign=F(1)),
        Edge("e14r", "U4", "U1a", over="e14r", over_sign=F(1)),
        Edge("s1", "U1a", "U1b", over="s1", over_sign=F(1)),
    ]
    R_vertex_over = {"U1a": "U1a", "U1b": "U1b", "U2a": "U2", "U2b": "U2", "U3": "U3", "U4": "U4"}
    z_prime_R = [F(1)] * len(R_edges)

    rho_star_QR = pullback_matrix(Q_edges, R_edges)
    rho0_star_QR = vertex_pullback_matrix(Q_vertices, R_vertices, R_vertex_over)

    delta0_Q = coboundary_0(Q_vertices, Q_edges)
    delta0_R = coboundary_0(R_vertices, R_edges)
    rho_star_QR_applied = mat_vec(rho_star_QR, Q_residue)
    a3_QR = is_zero(row_vec_mat(z_prime_R, delta0_R))
    pairing_QR = dot(z_prime_R, rho_star_QR_applied)
    a4_QR = pairing_QR != 0
    n0_QR = mat_mat(delta0_R, rho0_star_QR) == mat_mat(rho_star_QR, delta0_Q)
    descent_safe_QR = bool(a3_QR and a4_QR and n0_QR)

    delta0_C = coboundary_0(COARSE.vertices, COARSE.edges)
    composite_rho_star = mat_mat(rho_star_QR, rho_star_CQ)
    composite_rho0_star = mat_mat(rho0_star_QR, rho0_star_CQ)
    composite_rho_star_r = mat_vec(composite_rho_star, COARSE.residue)
    pairing_comp = dot(z_prime_R, composite_rho_star_r)
    a4_comp = pairing_comp != 0
    admissible_comp = a3_QR and a4_comp
    n0_comp = mat_mat(delta0_R, composite_rho0_star) == mat_mat(composite_rho_star, delta0_C)
    descent_safe_comp = bool(admissible_comp and n0_comp)

    Z1_coarse = nullspace_over_Q(transpose(delta0_C))
    Z1_R = nullspace_over_Q(transpose(delta0_R))
    pushed_cycles = [mat_vec(transpose(composite_rho_star), z) for z in Z1_R]
    e0_comp = all(in_span_over_Q(pushed_cycles, z) for z in Z1_coarse)
    verdict_safe_comp = descent_safe_comp and e0_comp

    return {
        "scenario": "two genuine subdivisions",
        "step1_admissible": cert1["admissible"], "step1_descent_safe": cert1["descent_safe"],
        "step1_E0": cert1["E0_exactness_reflection"],
        "step2_admissible": a3_QR and a4_QR, "step2_descent_safe": descent_safe_QR,
        "composite_admissible": admissible_comp, "composite_pairing": pairing_comp,
        "composite_N0": n0_comp, "composite_descent_safe": descent_safe_comp,
        "composite_E0": e0_comp, "composite_verdict_safe": verdict_safe_comp,
    }


def _bridge_insertion_scenario():
    """Step 1: C -> Q (SUBDIVIDE_U1). Step 2: Q -> R2, a bridge inserted
    inside Q (the one operation that already fails N0 at a single step,
    analogous to INSERT_BRIDGE). Cycle z'_R2 is derived from R2's own
    nullspace, not hand-copied from INSERT_BRIDGE's declared_z_prime --
    an earlier draft of this probe did copy it, and the real code
    correctly rejected it (A3 failed): R2's edge structure is not
    COARSE's, so that vector is not a cycle here."""
    Q_vertices = SUBDIVIDE_U1.vertices
    Q_edges = SUBDIVIDE_U1.edges
    rho_star_CQ = pullback_matrix(COARSE.edges, Q_edges)
    rho0_star_CQ = vertex_pullback_matrix(COARSE.vertices, Q_vertices, SUBDIVIDE_U1.vertex_over)
    Q_residue = mat_vec(rho_star_CQ, COARSE.residue)
    delta0_Q = coboundary_0(Q_vertices, Q_edges)

    R2_vertices = list(Q_vertices)
    R2_edges = [Edge(e.name, e.src, e.tgt, over=e.name, over_sign=F(1)) for e in Q_edges] \
        + [Edge("b12", "U1b", "U2", over=None)]
    R2_vertex_over = {v: v for v in Q_vertices}

    delta0_R2 = coboundary_0(R2_vertices, R2_edges)
    Z1_R2 = nullspace_over_Q(transpose(delta0_R2))
    z_prime_R2 = Z1_R2[0]

    rho_star_QR2 = pullback_matrix(Q_edges, R2_edges)
    rho0_star_QR2 = vertex_pullback_matrix(Q_vertices, R2_vertices, R2_vertex_over)
    rho_star_QR2_applied = mat_vec(rho_star_QR2, Q_residue)
    a3_QR2 = is_zero(row_vec_mat(z_prime_R2, delta0_R2))
    pairing_QR2 = dot(z_prime_R2, rho_star_QR2_applied)
    a4_QR2 = pairing_QR2 != 0
    n0_QR2 = mat_mat(delta0_R2, rho0_star_QR2) == mat_mat(rho_star_QR2, delta0_Q)

    delta0_C = coboundary_0(COARSE.vertices, COARSE.edges)
    composite_rho_star2 = mat_mat(rho_star_QR2, rho_star_CQ)
    composite_rho0_star2 = mat_mat(rho0_star_QR2, rho0_star_CQ)
    composite_rho_star_r2 = mat_vec(composite_rho_star2, COARSE.residue)
    pairing_comp2 = dot(z_prime_R2, composite_rho_star_r2)
    a4_comp2 = pairing_comp2 != 0
    admissible_comp2 = a3_QR2 and a4_comp2
    n0_comp2 = mat_mat(delta0_R2, composite_rho0_star2) == mat_mat(composite_rho_star2, delta0_C)
    descent_safe_comp2 = bool(admissible_comp2 and n0_comp2)

    Z1_coarse = nullspace_over_Q(transpose(delta0_C))
    pushed_cycles2 = [mat_vec(transpose(composite_rho_star2), z) for z in Z1_R2]
    e0_comp2 = all(in_span_over_Q(pushed_cycles2, z) for z in Z1_coarse)
    verdict_safe_comp2 = descent_safe_comp2 and e0_comp2

    return {
        "scenario": "subdivision composed with bridge insertion",
        "step2_N0": n0_QR2, "step2_N0_expected_false": n0_QR2 is False,
        "composite_admissible": admissible_comp2, "composite_pairing": pairing_comp2,
        "composite_N0": n0_comp2, "composite_descent_safe": descent_safe_comp2,
        "composite_E0": e0_comp2, "composite_verdict_safe": verdict_safe_comp2,
        "N0_failure_propagated": (n0_QR2 is False) and (n0_comp2 is False),
    }


def print_report() -> None:
    print("Refinement witness composition probe")
    print(f"  N0-composability associativity identity checked on 20 random matrix triples: "
          f"{verify_n0_composability_is_associativity()}")
    print()
    r1 = _second_subdivision_scenario()
    print(f"Scenario 1: {r1['scenario']}")
    for k, v in r1.items():
        if k != "scenario":
            print(f"  {k}: {v}")
    print()
    r2 = _bridge_insertion_scenario()
    print(f"Scenario 2: {r2['scenario']}")
    for k, v in r2.items():
        if k != "scenario":
            print(f"  {k}: {v}")
    print()
    print("See docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md for the write-up.")


if __name__ == "__main__":
    print_report()
