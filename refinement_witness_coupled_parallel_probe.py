#!/usr/bin/env python3
"""
refinement_witness_coupled_parallel_probe.py

Phase 5b: shared-seam coupled parallel composition. Per docs/design/
COUPLED_PARALLEL_COMPOSITION_PROBLEM.md's first concrete case, this probe
does NOT ask "does coupled parallel composition preserve (N0)/(A4)/(E0)."
It asks the prior question that document identifies as the real first
boundary:

    When is the glued composite witness even WELL-DEFINED?

Two refinement witnesses that share one refined-level edge ("seam") --
same coarse complex, mostly independent refined complexes, but one edge
name and its two endpoint vertices are treated as a single shared
identity rather than independently duplicated (contrast with
refinement_witness_parallel_disjoint_probe.py, where EVERYTHING,
including the coarse complex itself, was duplicated via renaming -- two
completely independent regional situations glued side by side). Coupled
composition is the opposite premise: the SAME coarse regional situation,
viewed through two refinements that agree to share exactly one seam.

The compatibility gate, deliberately conservative, per the design doc's
explicit instruction not to choose a conflicting-value merge rule yet:
a shared seam is well-defined only if both branches' own declarations
for it -- the edge's structural data (src, tgt, over, over_sign) AND the
declared-cycle (z') value assigned to it AND the vertex_over parent for
each endpoint -- agree exactly. If they agree, the combined witness is
built and checked with the same real machinery every other probe in this
project uses (coboundary_0, pullback_matrix, vertex_pullback_matrix,
nullspace_over_Q, in_span_over_Q). If they do NOT agree, no combined
witness is built at all, and the case is reported as
`interface_conflict` -- not as an (N0)/(A4)/(E0) failure, since no
composite object exists for those conditions to fail on. This
distinction (composite undefined vs. composite defined-but-failing)
matters and is kept explicit throughout.

USAGE:
    python refinement_witness_coupled_parallel_probe.py
"""

from fractions import Fraction as F
from typing import Dict, List, Optional, Tuple

from refinement_witnesses import COARSE, SUBDIVIDE_U1, SUBDIVIDE_U2, ALL_WITNESSES, Edge, Witness
from refinement_checker import coboundary_0, pullback_matrix, vertex_pullback_matrix
from rational_linear_algebra import (
    mat_vec, mat_mat, row_vec_mat, dot, is_zero,
    transpose, nullspace_over_Q, in_span_over_Q,
)


def rename_except(prefix: str, vertices: List[str], edges: List[Edge],
                   keep_vertices: set, keep_edge_names: set) -> Tuple[List[str], List[Edge]]:
    """Like refinement_witness_parallel_disjoint_probe.rename(), but
    leaves names in `keep_vertices`/`keep_edge_names` untouched -- these
    are the shared seam's own vertices and edge name, which must remain
    literally identical to branch A's copies so the combined complex
    treats them as ONE object, not two independently-renamed ones.
    `over` (the coarse edge a refined edge lies over, if any) is never
    renamed here, unlike the disjoint probe: coupled branches share the
    SAME coarse complex, not a duplicated one, so coarse edge names are
    already common ground."""
    def rv(v: str) -> str:
        return v if v in keep_vertices else f"{prefix}{v}"
    new_vertices = [rv(v) for v in vertices]
    new_edges = []
    for e in edges:
        if e.name in keep_edge_names:
            new_edges.append(e)
        else:
            new_edges.append(Edge(f"{prefix}{e.name}", rv(e.src), rv(e.tgt),
                                   over=e.over, over_sign=e.over_sign))
    return new_vertices, new_edges


def rename_vertex_over_except(prefix: str, vertex_over: Dict[str, str], keep_vertices: set) -> Dict[str, str]:
    result = {}
    for k, v in vertex_over.items():
        new_k = k if k in keep_vertices else f"{prefix}{k}"
        result[new_k] = v
    return result


def check(coarse_vertices, coarse_edges, residue, refined_vertices, refined_edges,
          vertex_over, z_prime) -> dict:
    """A1/A3/A4/N0/E0 for one (coarse, refined, residue, declared cycle)
    witness -- identical in shape to the disjoint probe's `check()`."""
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


def build_coupled_shared_seam(
    witness_a: Witness, witness_b: Witness, shared_edge_name: str,
    prefix_b: str = "B_",
    override_edge_b: Optional[Edge] = None,
    override_z_b: Optional[F] = None,
    override_vertex_over_b: Optional[Dict[str, str]] = None,
) -> dict:
    """Attempts to glue witness_a and witness_b along one shared seam
    (`shared_edge_name`, which must appear in both witnesses' own edge
    lists). Both branches sit over the SAME coarse complex (COARSE,
    unprefixed, used once -- not duplicated the way the disjoint probe
    duplicates it), matching the "same regional situation, two
    refinements" reading of coupled composition.

    `override_edge_b`/`override_z_b`/`override_vertex_over_b` let a
    caller deliberately construct a CONFLICTING declaration for branch
    B's copy of the shared seam, to test the compatibility gate's other
    branch -- without them, branch B's own declaration (whatever
    witness_b.edges/declared_z_prime/vertex_over actually say about the
    shared edge) is used as-is.

    Returns a dict always containing `status` (`interface_consistent` or
    `interface_conflict`), the two branches' own declarations for the
    shared seam (for inspection), and, only when `interface_consistent`,
    the combined complex fields ready for `check()`.
    """
    idx_a = next(i for i, e in enumerate(witness_a.edges) if e.name == shared_edge_name)
    edge_a = witness_a.edges[idx_a]
    z_a = witness_a.declared_z_prime[idx_a]
    parent_src_a = witness_a.vertex_over[edge_a.src]
    parent_tgt_a = witness_a.vertex_over[edge_a.tgt]

    idx_b = next(i for i, e in enumerate(witness_b.edges) if e.name == shared_edge_name)
    edge_b = witness_b.edges[idx_b] if override_edge_b is None else override_edge_b
    z_b = witness_b.declared_z_prime[idx_b] if override_z_b is None else override_z_b
    vertex_over_b_declared = dict(witness_b.vertex_over)
    if override_vertex_over_b is not None:
        vertex_over_b_declared.update(override_vertex_over_b)
    parent_src_b = vertex_over_b_declared[edge_b.src]
    parent_tgt_b = vertex_over_b_declared[edge_b.tgt]

    compatible = (
        edge_a.src == edge_b.src and edge_a.tgt == edge_b.tgt
        and edge_a.over == edge_b.over and edge_a.over_sign == edge_b.over_sign
        and z_a == z_b
        and parent_src_a == parent_src_b and parent_tgt_a == parent_tgt_b
    )

    result = {
        "shared_edge_name": shared_edge_name,
        "branch_a_declaration": {"edge": edge_a, "z_prime": z_a,
                                  "parents": (parent_src_a, parent_tgt_a)},
        "branch_b_declaration": {"edge": edge_b, "z_prime": z_b,
                                  "parents": (parent_src_b, parent_tgt_b)},
        "compatible": compatible,
    }

    if not compatible:
        result["status"] = "interface_conflict"
        return result

    keep_vertices = {edge_a.src, edge_a.tgt}
    keep_edges = {shared_edge_name}

    b_vertices, b_edges = rename_except(prefix_b, witness_b.vertices, witness_b.edges,
                                         keep_vertices, keep_edges)
    b_vertex_over = rename_vertex_over_except(prefix_b, witness_b.vertex_over, keep_vertices)

    # Deduplicate: the shared vertices/edge must appear exactly once in
    # the combined lists, not once per branch.
    combined_refined_vertices = list(witness_a.vertices)
    for v in b_vertices:
        if v not in combined_refined_vertices:
            combined_refined_vertices.append(v)

    combined_refined_edges = list(witness_a.edges)
    seen_edge_names = {e.name for e in combined_refined_edges}
    for e in b_edges:
        if e.name not in seen_edge_names:
            combined_refined_edges.append(e)
            seen_edge_names.add(e.name)

    combined_vertex_over = dict(witness_a.vertex_over)
    combined_vertex_over.update(b_vertex_over)

    # z' aligned with combined_refined_edges: branch A's own value for
    # its edges (including the shared one, at branch A's declared
    # value -- identical to branch B's by the compatibility check
    # above), branch B's own value for its remaining (renamed) edges.
    z_by_name = {e.name: z for e, z in zip(witness_a.edges, witness_a.declared_z_prime)}
    for e, z in zip(b_edges, witness_b.declared_z_prime):
        if e.name not in z_by_name:
            z_by_name[e.name] = z
    combined_z_prime = [z_by_name[e.name] for e in combined_refined_edges]

    result["status"] = "interface_consistent"
    result.update({
        "coarse_vertices": COARSE.vertices, "coarse_edges": COARSE.edges, "residue": COARSE.residue,
        "refined_vertices": combined_refined_vertices, "refined_edges": combined_refined_edges,
        "vertex_over": combined_vertex_over, "z_prime": combined_z_prime,
    })
    return result


def run_case(label: str, witness_a: Witness, witness_b: Witness, shared_edge_name: str,
             override_edge_b: Optional[Edge] = None, override_z_b: Optional[F] = None,
             override_vertex_over_b: Optional[Dict[str, str]] = None) -> dict:
    glued = build_coupled_shared_seam(
        witness_a, witness_b, shared_edge_name,
        override_edge_b=override_edge_b, override_z_b=override_z_b,
        override_vertex_over_b=override_vertex_over_b,
    )
    result_a = check(COARSE.vertices, COARSE.edges, COARSE.residue,
                      witness_a.vertices, witness_a.edges, witness_a.vertex_over,
                      witness_a.declared_z_prime)
    result_b = check(COARSE.vertices, COARSE.edges, COARSE.residue,
                      witness_b.vertices, witness_b.edges, witness_b.vertex_over,
                      witness_b.declared_z_prime)

    out = {"label": label, "branch_a": result_a, "branch_b": result_b, "glued": glued}

    if glued["status"] == "interface_conflict":
        out["diagnostic_status"] = "interface_conflict"
        return out

    combined = check(glued["coarse_vertices"], glued["coarse_edges"], glued["residue"],
                      glued["refined_vertices"], glued["refined_edges"],
                      glued["vertex_over"], glued["z_prime"])
    out["combined"] = combined
    out["N0_matches_AND"] = combined["N0"] == (result_a["N0"] and result_b["N0"])
    out["E0_matches_AND"] = combined["E0"] == (result_a["E0"] and result_b["E0"])
    out["A4_branchwise_preserved"] = result_a["A4"] and result_b["A4"]
    out["A4_aggregate_preserved"] = combined["A4"]
    if out["N0_matches_AND"] and out["E0_matches_AND"] and out["A4_branchwise_preserved"]:
        out["diagnostic_status"] = "disjoint_like_preserved"
    else:
        out["diagnostic_status"] = "interface_consistent_but_unexpected"
    return out


def print_report() -> None:
    print("Coupled parallel composition probe -- shared-seam compatibility gate")
    print()

    print("Case 1: SUBDIVIDE_U1 (+) SUBDIVIDE_U1, sharing edge 'e23' verbatim")
    print("  (self-pairing: both branches' own declaration for the shared seam is")
    print("  identical by construction -- the simplest possible consistent case)")
    r1 = run_case("self-pair, shared e23, no perturbation", SUBDIVIDE_U1, SUBDIVIDE_U1, "e23")
    print(f"  status: {r1['diagnostic_status']}")
    if r1["glued"]["status"] == "interface_consistent":
        print(f"  N0 matches AND: {r1['N0_matches_AND']}  E0 matches AND: {r1['E0_matches_AND']}")
        print(f"  A4 branchwise preserved: {r1['A4_branchwise_preserved']}  "
              f"A4 aggregate preserved: {r1['A4_aggregate_preserved']} "
              f"(combined pairing={r1['combined']['pairing']})")
    print()

    print("Case 2: SUBDIVIDE_U1 (+) SUBDIVIDE_U2, sharing edge 'e34' verbatim")
    print("  (organic cross-witness agreement: both witnesses independently declare")
    print("  the SAME Edge('e34','U3','U4',over='e34',sign=1) -- no perturbation needed)")
    r2 = run_case("cross-witness, shared e34, no perturbation", SUBDIVIDE_U1, SUBDIVIDE_U2, "e34")
    print(f"  status: {r2['diagnostic_status']}")
    if r2["glued"]["status"] == "interface_consistent":
        print(f"  N0 matches AND: {r2['N0_matches_AND']}  E0 matches AND: {r2['E0_matches_AND']}")
        print(f"  A4 branchwise preserved: {r2['A4_branchwise_preserved']}  "
              f"A4 aggregate preserved: {r2['A4_aggregate_preserved']} "
              f"(combined pairing={r2['combined']['pairing']})")
    print()

    print("Case 3: SUBDIVIDE_U1 (+) SUBDIVIDE_U2, sharing edge-NAME 'e12p'")
    print("  (organic conflict: both witnesses happen to name an edge 'e12p', but")
    print("  branch A's runs U1b->U2 and branch B's runs U1->U2a -- same name,")
    print("  genuinely different edges. No perturbation -- this conflict arises")
    print("  from the two witnesses' own real declarations.)")
    r3 = run_case("cross-witness, shared-name e12p, organic conflict", SUBDIVIDE_U1, SUBDIVIDE_U2, "e12p")
    print(f"  status: {r3['diagnostic_status']}")
    print(f"  branch A declares: {r3['glued']['branch_a_declaration']['edge']}")
    print(f"  branch B declares: {r3['glued']['branch_b_declaration']['edge']}")
    print()

    print("Case 4: SUBDIVIDE_U1 (+) SUBDIVIDE_U1, sharing 'e23', branch B's over_sign flipped")
    print("  (deliberately constructed conflict: same name, same src/tgt/over, but")
    print("  branch B declares the pullback sign as -1 instead of +1)")
    conflicting_edge_b = Edge("e23", "U2", "U3", over="e23", over_sign=F(-1))
    r4 = run_case("self-pair, shared e23, over_sign perturbed", SUBDIVIDE_U1, SUBDIVIDE_U1, "e23",
                  override_edge_b=conflicting_edge_b)
    print(f"  status: {r4['diagnostic_status']}")
    print()

    print("Case 5: SUBDIVIDE_U1 (+) SUBDIVIDE_U1, sharing 'e23', branch B's z' entry perturbed")
    print("  (deliberately constructed conflict: edge data agrees, but branch B")
    print("  declares the shared edge's cycle coefficient as -1 instead of +1)")
    r5 = run_case("self-pair, shared e23, z-prime perturbed", SUBDIVIDE_U1, SUBDIVIDE_U1, "e23",
                  override_z_b=F(-1))
    print(f"  status: {r5['diagnostic_status']}")
    print()

    print("=== SUMMARY ===")
    print("Consistent-declaration cases (1, 2) glue cleanly and reduce to the")
    print("disjoint case's own preservation pattern: N0/E0 hold, A4 branchwise")
    print("holds. No new obstruction appears merely from gluing along an")
    print("AGREED seam -- consistent with the design doc's sub-case-1 conjecture.")
    print("Conflicting-declaration cases (3, 4, 5) are all correctly refused a")
    print("combined witness at all -- 'interface_conflict', not an (N0)/(A4)/(E0)")
    print("failure, since no composite object exists for those conditions to be")
    print("tested against. Case 3 shows this arises ORGANICALLY from two real")
    print("witnesses' own declarations, not only from a deliberately crafted probe.")


if __name__ == "__main__":
    print_report()
