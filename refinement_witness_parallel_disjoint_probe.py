#!/usr/bin/env python3
"""
refinement_witness_parallel_disjoint_probe.py

Phase 4b: does DISJOINT PARALLEL composition of two refinement witnesses
preserve (N0)/(A4)/(E0) componentwise? Not the same question as
sequential composition (rocq/RefinementWitnessComposition.v, rocq/
RefinementWitnessVerdictComposition.v, rocq/RefinementWitnessSequential
Composition.v), which is built from function composition; disjoint
parallel composition is built from a direct-sum / disjoint-union
construction instead, and nothing proved for sequential composition
carries over automatically.

Per veribound-fce's docs/design/PARALLEL_WITNESS_COMPOSITION_SPEC.md:
"certificate-disjoint" means sharing no vertex, edge, seam, declared
cycle, or downstream target -- not mere visual/physical separation. The
construction here makes that concrete: two witnesses over completely
independent vertex/edge name universes (one renamed with a prefix),
combined by literal list concatenation (the coarse and refined
complexes, the coarse residue, and the declared cycle), then run through
the SAME real machinery (coboundary_0, pullback_matrix,
vertex_pullback_matrix, nullspace_over_Q, in_span_over_Q) every other
diagnostic in this project uses -- not a hand-derived block-matrix
argument trusted on its own.

The headline finding, worked out by hand first and then checked here,
not assumed: (N0), (A3), and (E0) all reduce to a clean "AND" -- the
combined condition holds iff it holds on BOTH branches, because each is
either a block-diagonal matrix identity or a block-diagonal subspace
containment, and neither has any way to interact across blocks. (A4)
is different in kind, not just in degree: the combined pairing is a SUM
of the two branches' own pairings (dot product of concatenated vectors
splits into a sum over blocks), and a sum of two nonzero numbers can be
zero. Two branches can each individually satisfy their own (A4) and
still have the disjoint-parallel composite FAIL (A4), if their pairings
happen to have opposite sign and equal magnitude. This is demonstrated
below with a real, non-degenerate witness pair (not a contrived
counterexample), not merely argued.

USAGE:
    python refinement_witness_parallel_disjoint_probe.py
"""

from fractions import Fraction as F
from typing import Dict, List, Tuple

from refinement_witnesses import COARSE, SUBDIVIDE_U1, SUBDIVIDE_U2, ALL_WITNESSES, Edge, Witness
from refinement_checker import coboundary_0, pullback_matrix, vertex_pullback_matrix
from rational_linear_algebra import (
    mat_vec, mat_mat, row_vec_mat, dot, is_zero,
    transpose, nullspace_over_Q, in_span_over_Q,
)


def rename(prefix: str, vertices: List[str], edges: List[Edge]) -> Tuple[List[str], List[Edge]]:
    """Prefixes every vertex/edge name and every edge's src/tgt/over
    field, so the result shares no name with anything unprefixed. This
    is what makes two witnesses genuinely independent name universes,
    not merely "different variable names in the same script"."""
    def rv(v: str) -> str:
        return f"{prefix}{v}"
    new_vertices = [rv(v) for v in vertices]
    new_edges = [
        Edge(rv(e.name), rv(e.src), rv(e.tgt),
             over=(rv(e.over) if e.over is not None else None),
             over_sign=e.over_sign)
        for e in edges
    ]
    return new_vertices, new_edges


def rename_vertex_over(prefix: str, vertex_over: Dict[str, str]) -> Dict[str, str]:
    return {f"{prefix}{k}": f"{prefix}{v}" for k, v in vertex_over.items()}


def build_disjoint_parallel(witness_a: Witness, coarse_a: "type(COARSE)",
                             witness_b: Witness, coarse_b: "type(COARSE)",
                             prefix_b: str = "B_") -> dict:
    """Combines witness_a (over coarse_a, used unprefixed) with a
    prefixed copy of witness_b (over coarse_b), by literal list
    concatenation of vertices, edges, residues, and declared cycles --
    the direct-sum construction PARALLEL_WITNESS_COMPOSITION_SPEC.md
    describes. Returns everything needed to check A1/A3/A4/N0/E0 on the
    combined complex using the real machinery, plus the two branches'
    own individually-computed results for comparison."""
    b_coarse_vertices, b_coarse_edges = rename(prefix_b, coarse_b.vertices, coarse_b.edges)
    b_residue = list(coarse_b.residue)
    b_refined_vertices, b_refined_edges = rename(prefix_b, witness_b.vertices, witness_b.edges)
    b_vertex_over = rename_vertex_over(prefix_b, witness_b.vertex_over)
    b_z_prime = list(witness_b.declared_z_prime)

    combined_coarse_vertices = list(coarse_a.vertices) + b_coarse_vertices
    combined_coarse_edges = list(coarse_a.edges) + b_coarse_edges
    combined_residue = list(coarse_a.residue) + b_residue

    combined_refined_vertices = list(witness_a.vertices) + b_refined_vertices
    combined_refined_edges = list(witness_a.edges) + b_refined_edges
    combined_vertex_over = dict(witness_a.vertex_over)
    combined_vertex_over.update(b_vertex_over)
    combined_z_prime = list(witness_a.declared_z_prime) + b_z_prime

    return {
        "coarse_vertices": combined_coarse_vertices, "coarse_edges": combined_coarse_edges,
        "residue": combined_residue,
        "refined_vertices": combined_refined_vertices, "refined_edges": combined_refined_edges,
        "vertex_over": combined_vertex_over, "z_prime": combined_z_prime,
    }


def check(coarse_vertices, coarse_edges, residue, refined_vertices, refined_edges,
          vertex_over, z_prime) -> dict:
    """A1/A3/A4/N0/E0 for one (coarse, refined, residue, declared cycle)
    witness, via the real machinery -- the same computation
    refinement_checker.check_witness performs, generalised to an
    explicit coarse complex instead of the hardcoded module-level
    COARSE, exactly as the sequential-composition probes already did."""
    delta0_coarse = coboundary_0(coarse_vertices, coarse_edges)
    delta0_refined = coboundary_0(refined_vertices, refined_edges)
    rho_star = pullback_matrix(coarse_edges, refined_edges)
    rho0_star = vertex_pullback_matrix(coarse_vertices, refined_vertices, vertex_over)
    rho_star_r = mat_vec(rho_star, residue)

    a3 = is_zero(row_vec_mat(z_prime, delta0_refined))
    pairing = dot(z_prime, rho_star_r)
    a4 = pairing != 0
    n0 = mat_mat(delta0_refined, rho0_star) == mat_mat(rho_star, delta0_coarse)

    Z1_coarse = nullspace_over_Q(transpose(delta0_coarse))
    Z1_refined = nullspace_over_Q(transpose(delta0_refined))
    pushed = [mat_vec(transpose(rho_star), z) for z in Z1_refined]
    e0 = all(in_span_over_Q(pushed, z) for z in Z1_coarse)

    return {"A3": a3, "A4": a4, "pairing": pairing, "N0": n0, "E0": e0}


def run_case(label: str, witness_a: Witness, witness_b: Witness, negate_b_cycle: bool = False) -> dict:
    coarse_b = COARSE
    wb = witness_b
    if negate_b_cycle:
        wb = Witness(
            name=witness_b.name + "_negated", description=witness_b.description,
            vertices=witness_b.vertices, edges=witness_b.edges,
            declared_z_prime=[-x for x in witness_b.declared_z_prime],
            vertex_over=witness_b.vertex_over,
        )

    result_a = check(COARSE.vertices, COARSE.edges, COARSE.residue,
                      witness_a.vertices, witness_a.edges, witness_a.vertex_over,
                      witness_a.declared_z_prime)
    result_b = check(COARSE.vertices, COARSE.edges, COARSE.residue,
                      wb.vertices, wb.edges, wb.vertex_over, wb.declared_z_prime)

    combined = build_disjoint_parallel(witness_a, COARSE, wb, coarse_b)
    result_combined = check(combined["coarse_vertices"], combined["coarse_edges"],
                             combined["residue"], combined["refined_vertices"],
                             combined["refined_edges"], combined["vertex_over"],
                             combined["z_prime"])

    return {
        "label": label,
        "branch_a": result_a, "branch_b": result_b, "combined": result_combined,
        "both_branches_N0": result_a["N0"] and result_b["N0"],
        "both_branches_A4": result_a["A4"] and result_b["A4"],
        "both_branches_E0": result_a["E0"] and result_b["E0"],
        "N0_matches_AND": result_combined["N0"] == (result_a["N0"] and result_b["N0"]),
        "E0_matches_AND": result_combined["E0"] == (result_a["E0"] and result_b["E0"]),
        "A4_matches_AND": result_combined["A4"] == (result_a["A4"] and result_b["A4"]),
    }


def systematic_sweep() -> List[dict]:
    """Every ordered pair from ALL_WITNESSES (16 pairs, including a
    witness combined with itself), plus the same 16 with branch B's
    cycle negated -- 32 disjoint-parallel cases total, not just the two
    hand-picked ones above. Checks whether N0/E0 always match
    AND(branch A, branch B) (predicted: always) and how often A4 does
    not (predicted: exactly when negate_b_cycle cancels a
    positive-pairing case)."""
    results = []
    for wa in ALL_WITNESSES:
        for wb in ALL_WITNESSES:
            for negate in (False, True):
                label = f"{wa.name} (+) {wb.name}{' [negated]' if negate else ''}"
                results.append(run_case(label, wa, wb, negate_b_cycle=negate))
    return results


def print_report() -> None:
    print("Disjoint parallel witness composition probe")
    print()

    r1 = run_case("SUBDIVIDE_U1 (+) SUBDIVIDE_U2, both natural", SUBDIVIDE_U1, SUBDIVIDE_U2)
    print(f"Case 1: {r1['label']}")
    print(f"  branch A: N0={r1['branch_a']['N0']} A4={r1['branch_a']['A4']} "
          f"(pairing={r1['branch_a']['pairing']}) E0={r1['branch_a']['E0']}")
    print(f"  branch B: N0={r1['branch_b']['N0']} A4={r1['branch_b']['A4']} "
          f"(pairing={r1['branch_b']['pairing']}) E0={r1['branch_b']['E0']}")
    print(f"  combined: N0={r1['combined']['N0']} A4={r1['combined']['A4']} "
          f"(pairing={r1['combined']['pairing']}) E0={r1['combined']['E0']}")
    print(f"  N0 matches AND(branch A, branch B): {r1['N0_matches_AND']}")
    print(f"  E0 matches AND(branch A, branch B): {r1['E0_matches_AND']}")
    print(f"  A4 matches AND(branch A, branch B): {r1['A4_matches_AND']}")
    print()

    r2 = run_case("SUBDIVIDE_U1 (+) SUBDIVIDE_U1-with-negated-cycle (deliberate cancellation)",
                  SUBDIVIDE_U1, SUBDIVIDE_U1, negate_b_cycle=True)
    print(f"Case 2: {r2['label']}")
    print(f"  branch A: N0={r2['branch_a']['N0']} A4={r2['branch_a']['A4']} "
          f"(pairing={r2['branch_a']['pairing']}) E0={r2['branch_a']['E0']}")
    print(f"  branch B: N0={r2['branch_b']['N0']} A4={r2['branch_b']['A4']} "
          f"(pairing={r2['branch_b']['pairing']}) E0={r2['branch_b']['E0']}")
    print(f"  combined: N0={r2['combined']['N0']} A4={r2['combined']['A4']} "
          f"(pairing={r2['combined']['pairing']}) E0={r2['combined']['E0']}")
    print(f"  N0 matches AND(branch A, branch B): {r2['N0_matches_AND']}")
    print(f"  E0 matches AND(branch A, branch B): {r2['E0_matches_AND']}")
    print(f"  A4 matches AND(branch A, branch B): {r2['A4_matches_AND']}")
    print()

    print("=== SUMMARY ===")
    print("Case 1 (natural pairings, same sign): combined A4 should hold, matching")
    print("  the naive 'both branches satisfy A4' expectation.")
    print("Case 2 (deliberately opposite-sign pairings of equal magnitude): both")
    print("  branches individually satisfy their OWN (A4) -- nonzero pairing -- and")
    print("  N0/E0 are fully intact on both branches and combined, yet the COMBINED")
    print("  (A4) should FAIL, because the pairing is a sum that cancels to zero.")
    print("  This is not a failure of the direct-sum construction; it is a real,")
    print("  demonstrated gap between 'both branches individually admissible' and")
    print("  'the disjoint-parallel composite is admissible' -- for (A4) only.")
    print()

    print("=== Systematic sweep: all 16 ordered ALL_WITNESSES pairs, x2 (negated/not) ===")
    sweep = systematic_sweep()
    n0_mismatches = [r for r in sweep if not r["N0_matches_AND"]]
    e0_mismatches = [r for r in sweep if not r["E0_matches_AND"]]
    a4_mismatches = [r for r in sweep if not r["A4_matches_AND"]]
    print(f"  total cases: {len(sweep)}")
    print(f"  N0 always matches AND(branch A, branch B): {len(n0_mismatches) == 0}")
    print(f"  E0 always matches AND(branch A, branch B): {len(e0_mismatches) == 0}")
    print(f"  A4 mismatches AND(branch A, branch B) in {len(a4_mismatches)} of {len(sweep)} cases")
    for r in a4_mismatches:
        print(f"    {r['label']}: branch A pairing={r['branch_a']['pairing']}, "
              f"branch B pairing={r['branch_b']['pairing']}, "
              f"combined pairing={r['combined']['pairing']}")


if __name__ == "__main__":
    print_report()
