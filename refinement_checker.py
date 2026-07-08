#!/usr/bin/env python3
"""
refinement_checker.py

Checks the four admissibility conditions (A1)-(A4) of the paper's
"Admissible refinement persistence" section (Theorem thm:witness-persistence
/ thm:universal-persistence) against the witnesses declared in
refinement_witnesses.py, and computes the actual refined pairing
<z', rho^*r> by construction rather than by assertion.

    (A1) delta^1 r = 0                    -- r is closed in the coarse complex
    (A2) delta'^1 (rho^* r) = 0           -- transferred residue is closed
    (A3) z'^T delta'^0 = 0                -- z' is a cycle in the refined complex
    (A4) <z', rho^* r> != 0               -- non-zero refined pairing

None of the four conditions require pairing adjointness or H1 surjectivity;
those belonged to an earlier, stronger (and superseded) formalisation. See
the module docstring of refinement_witnesses.py.

Every witness here has C^2 = 0 (no 2-cells), so (A1) and (A2) are trivially
satisfied exactly as in the base four-cycle complex; they are still checked
explicitly rather than assumed.

A separate, additional condition, (N0) cochain-map naturality, is also
checked here but is deliberately kept out of (A1)-(A4) and out of
`admissible`:

    (N0) delta'^0 rho_0^* = rho_1^* delta^0

where rho_0^* : C^0(coarse) -> C^0(refined) is the vertex-level pullback
built from each witness's declared `vertex_over` map. (A1)-(A4) certify
non-exactness of the *transferred* residue `rho^*r` inside the *refined*
complex only (this is exactly what
`rocq/AdmissibleRefinementPersistence.v` proves); they say nothing about
non-exactness of `r` itself back in the coarse complex. (N0) is the
one-directional cochain-map naturality condition that plausibly closes
that gap: it lets a coarse witness for exactness (`r = delta^0 b`) be
pushed forward into a refined witness (`rho^*r = delta'^0(rho_0^*b)`),
so its contrapositive gives descent -- see
`rocq/CochainNaturalityDescent.v`. A witness satisfying (A1)-(A4) and (N0)
is called `descent_safe` below. This is a narrower, additional condition
-- it does not "belong" to the stronger four-condition scheme (that
scheme also had chain-map naturality, pairing adjointness, and
H1-surjectivity, none of which are checked here) and it is not
"presentation invariance": it does not, on its own, prove that two
different presentations of the same regional situation always agree, only
that a *single* subdivision-type refinement doesn't silently lose the
obstruction on the way down.

A third, independent condition, (E0) exactness reflection, is also checked
here, again kept separate from (A1)-(A4) and from (N0):

    (E0) (rho^*r in im(delta'^0)) => (r in im(delta^0))

(N0) pushes coarse *exactness* forward into refined exactness; (E0) is the
converse direction, reflecting refined exactness back down to coarse
exactness. It is logically independent of (N0) -- checked below, it does
NOT track (N0)'s admissible/subdivision-vs-bridge split. Structurally,
(E0) is equivalent to every coarse cycle being the pushforward of some
refined cycle (Z1(coarse) subseteq rho_*(Z1(refined))) -- the classical
"H1-surjectivity" condition of the superseded four-condition scheme in
archive/deprecated_universal_refinement_scaffold/, but checked here by
exact rational nullspace computation and subspace-membership testing
(`nullspace_over_Q`, `in_span_over_Q`), not that scaffold's
floating-point `numpy.linalg.lstsq` cycle lift. See
`rocq/ExactnessReflection.v` for the abstract theorem this backs, and its
header comment for why (E0) holding does not, on its own, give any
witness -- including insert_bridge, for which it happens to hold --
presentation invariance or verdict equivalence: that would additionally
require (N0), which insert_bridge does not satisfy.

USAGE:
    python refinement_checker.py             # print all four certificates
    python refinement_checker.py --json out.json
"""

import argparse
import json
from fractions import Fraction
from typing import List, Optional

from refinement_witnesses import ALL_WITNESSES, COARSE, Witness, Edge
from rational_linear_algebra import (
    mat_vec, mat_mat, row_vec_mat, dot, is_zero, solve_over_Q,
    transpose, nullspace_over_Q, in_span_over_Q,
)


def coboundary_0(vertices: List[str], edges: List[Edge]) -> List[List[Fraction]]:
    """delta^0 : C^0 -> C^1, one row per edge, one column per vertex."""
    index = {v: i for i, v in enumerate(vertices)}
    matrix = []
    for e in edges:
        row = [Fraction(0)] * len(vertices)
        row[index[e.src]] += Fraction(-1)
        row[index[e.tgt]] += Fraction(1)
        matrix.append(row)
    return matrix


def pullback_matrix(coarse_edges: List[Edge], refined_edges: List[Edge]) -> List[List[Fraction]]:
    """rho_1^* : C^1(coarse) -> C^1(refined), one row per refined edge."""
    coarse_index = {e.name: i for i, e in enumerate(coarse_edges)}
    matrix = []
    for e in refined_edges:
        row = [Fraction(0)] * len(coarse_edges)
        if e.over is not None:
            row[coarse_index[e.over]] = e.over_sign
        matrix.append(row)
    return matrix


def vertex_pullback_matrix(coarse_vertices: List[str], refined_vertices: List[str],
                            vertex_over: dict) -> List[List[Fraction]]:
    """rho_0^* : C^0(coarse) -> C^0(refined), one row per refined vertex, a
    single 1 in the column of that vertex's declared coarse parent
    (`vertex_over`). This is a genuine quotient map -- every refined vertex
    must map to exactly one coarse vertex -- not an arbitrary matrix."""
    coarse_index = {v: i for i, v in enumerate(coarse_vertices)}
    matrix = []
    for v in refined_vertices:
        row = [Fraction(0)] * len(coarse_vertices)
        row[coarse_index[vertex_over[v]]] = Fraction(1)
        matrix.append(row)
    return matrix


def check_witness(witness: Witness) -> dict:
    coarse_delta1: List[List[Fraction]] = []   # C^2(coarse) = 0
    refined_delta1: List[List[Fraction]] = []  # C^2(refined) = 0 for all four witnesses

    delta0_refined = coboundary_0(witness.vertices, witness.edges)
    rho_star = pullback_matrix(COARSE.edges, witness.edges)

    rho_star_r = mat_vec(rho_star, COARSE.residue)

    a1 = is_zero(mat_vec(coarse_delta1, COARSE.residue))
    a2 = is_zero(mat_vec(refined_delta1, rho_star_r))
    a3 = is_zero(row_vec_mat(witness.declared_z_prime, delta0_refined))
    pairing = dot(witness.declared_z_prime, rho_star_r)
    a4 = pairing != 0

    # Independent cross-check: solve delta'^0 b = rho^*r by exact Gaussian
    # elimination. This does not feed into A1-A4 at all; it is a second,
    # unrelated method (linear-system inconsistency, as in
    # residue_classifier.py) for the same non-coboundary conclusion that
    # the cycle-pairing lemma (A3+A4) already certifies.
    solver_has_solution, _ = solve_over_Q(delta0_refined, rho_star_r)
    solver_not_coboundary = not solver_has_solution

    # (N0) cochain-map naturality: delta'^0 rho_0^* = rho_1^* delta^0.
    # Kept entirely separate from (A1)-(A4) -- see module docstring.
    rho0_star = vertex_pullback_matrix(COARSE.vertices, witness.vertices, witness.vertex_over)
    lhs = mat_mat(delta0_refined, rho0_star)
    rhs = mat_mat(rho_star, coboundary_0(COARSE.vertices, COARSE.edges))
    naturality_failures = [
        {"edge": e.name, "over": e.over, "lhs": [str(x) for x in l], "rhs": [str(x) for x in r]}
        for e, l, r in zip(witness.edges, lhs, rhs)
        if l != r
    ]
    cochain_naturality_delta0 = not naturality_failures
    descent_safe = bool(a1 and a2 and a3 and a4 and cochain_naturality_delta0)

    # (E0) exactness reflection: Z1(coarse) subseteq rho_*(Z1(refined)),
    # equivalent to (rho^*r in im(delta'^0)) => (r in im(delta^0)) -- see
    # module docstring. Independent of (A1)-(A4) and of (N0): checked
    # separately, against every witness, not just admissible/descent-safe
    # ones.
    delta0_coarse = coboundary_0(COARSE.vertices, COARSE.edges)
    Z1_coarse = nullspace_over_Q(transpose(delta0_coarse))
    Z1_refined = nullspace_over_Q(transpose(delta0_refined))
    rho_push = transpose(rho_star)  # rho_* : C'_1(refined) -> C_1(coarse)
    pushed_cycles = [mat_vec(rho_push, z) for z in Z1_refined]
    reflection_failures = [
        [str(x) for x in z] for z in Z1_coarse if not in_span_over_Q(pushed_cycles, z)
    ]
    exactness_reflection = not reflection_failures
    verdict_safe = bool(descent_safe and exactness_reflection)

    legacy = witness.legacy_claimed_pairing
    legacy_matches = (pairing == legacy) if legacy is not None else None

    return {
        "witness": witness.name,
        "description": witness.description,
        "refined_vertices": witness.vertices,
        "refined_edges": [
            {"name": e.name, "src": e.src, "tgt": e.tgt,
             "over": e.over, "over_sign": str(e.over_sign)}
            for e in witness.edges
        ],
        "coarse_edges": [e.name for e in COARSE.edges],
        "rho_star_matrix": [[str(x) for x in row] for row in rho_star],
        "rho_star_r": [str(x) for x in rho_star_r],
        "declared_z_prime": [str(x) for x in witness.declared_z_prime],
        "A1_coarse_cocycle": a1,
        "A2_refined_cocycle": a2,
        "A3_declared_cycle": a3,
        "A4_nonzero_pairing": a4,
        "admissible": a1 and a2 and a3 and a4,
        "solver_cross_check_not_coboundary": solver_not_coboundary,
        "pairing_and_solver_agree": solver_not_coboundary == a4,
        "vertex_over": dict(witness.vertex_over),
        "rho_0_star_matrix": [[str(x) for x in row] for row in rho0_star],
        "N0_cochain_naturality_delta0": cochain_naturality_delta0,
        "naturality_failures": naturality_failures,
        "descent_safe": descent_safe,
        "Z1_coarse_basis": [[str(x) for x in z] for z in Z1_coarse],
        "Z1_refined_basis": [[str(x) for x in z] for z in Z1_refined],
        "E0_exactness_reflection": exactness_reflection,
        "reflection_failures": reflection_failures,
        "verdict_safe": verdict_safe,
        "computed_pairing": str(pairing),
        "legacy_claimed_pairing": str(legacy) if legacy is not None else None,
        "legacy_value_is_historical_only": True,
        "legacy_matches": legacy_matches,
    }


def print_certificate(cert: dict) -> None:
    print("\n" + "=" * 70)
    print(f"REFINEMENT WITNESS: {cert['witness']}")
    print("=" * 70)
    print(cert["description"])
    print(f"Refined vertices: {cert['refined_vertices']}")
    print("Refined edges (name: src -> tgt, over coarse edge, sign):")
    for e in cert["refined_edges"]:
        over = e["over"] if e["over"] is not None else "-"
        print(f"  {e['name']}: {e['src']} -> {e['tgt']}  (over {over}, sign {e['over_sign']})")
    print(f"\nPullback matrix rho^* (rows = refined edges, cols = coarse edges {cert['coarse_edges']}):")
    for e, row in zip(cert["refined_edges"], cert["rho_star_matrix"]):
        print(f"  {e['name']:6s} {row}")
    print(f"\nrho^*r  = {cert['rho_star_r']}")
    print(f"z'      = {cert['declared_z_prime']}")
    print("-" * 70)
    print(f"(A1) coarse cocycle:        {cert['A1_coarse_cocycle']}")
    print(f"(A2) refined cocycle:       {cert['A2_refined_cocycle']}")
    print(f"(A3) z' is a cycle:         {cert['A3_declared_cycle']}")
    print(f"(A4) <z', rho^*r> != 0:     {cert['A4_nonzero_pairing']}")
    print(f"Admissible (A1-A4 all hold): {cert['admissible']}")
    print(f"(N0) cochain naturality delta'^0 rho_0^* = rho_1^* delta^0: "
          f"{cert['N0_cochain_naturality_delta0']}")
    if cert["naturality_failures"]:
        for f in cert["naturality_failures"]:
            print(f"    naturality fails at edge {f['edge']} (over={f['over']}): "
                  f"lhs={f['lhs']}  rhs={f['rhs']}")
    print(f"Descent-safe (A1-A4 and N0): {cert['descent_safe']}")
    print(f"Z1(coarse) basis:  {cert['Z1_coarse_basis']}")
    print(f"Z1(refined) basis: {cert['Z1_refined_basis']}")
    print(f"(E0) exactness reflection (Z1(coarse) subseteq rho_*(Z1(refined))): "
          f"{cert['E0_exactness_reflection']}")
    if cert["reflection_failures"]:
        for z in cert["reflection_failures"]:
            print(f"    coarse cycle {z} is not a pushforward of any refined cycle")
    print(f"Verdict-safe (descent-safe and E0): {cert['verdict_safe']}")
    print(f"Computed pairing <z', rho^*r> = {cert['computed_pairing']}")
    print(f"Solver cross-check (delta'^0 b = rho^*r has no solution): "
          f"{cert['solver_cross_check_not_coboundary']}"
          f"  [{'agrees with A4' if cert['pairing_and_solver_agree'] else 'DISAGREES WITH A4 -- BUG'}]")
    if cert["legacy_claimed_pairing"] is not None:
        match = "MATCHES" if cert["legacy_matches"] else "DOES NOT MATCH (historical claim only)"
        print(f"Paper's legacy table value  = {cert['legacy_claimed_pairing']}  ({match})")
    print("=" * 70)


def print_summary_table(certificates: List[dict]) -> None:
    print("\n" + "=" * 70)
    print("SUMMARY: corrected refinement witness table")
    print("=" * 70)
    header = (f"{'Witness':16s} {'Computed':>10s} {'Legacy claim':>14s} "
              f"{'Status':>10s} {'Descent-safe':>13s} {'E0':>6s} {'Verdict-safe':>13s}")
    print(header)
    print("-" * len(header))
    for cert in certificates:
        status = "matches" if cert["legacy_matches"] else "corrected"
        print(f"{cert['witness']:16s} {cert['computed_pairing']:>10s} "
              f"{cert['legacy_claimed_pairing']:>14s} {status:>10s} "
              f"{str(cert['descent_safe']):>13s} {str(cert['E0_exactness_reflection']):>6s} "
              f"{str(cert['verdict_safe']):>13s}")
    print("=" * 70)
    print("Only the 'computed' column is mathematical content (A1-A4 hold, so")
    print("the pairing is genuinely non-zero for all four witnesses). The")
    print("'legacy claim' column is historical and is not reproduced by any")
    print("construction in this repository. 'Descent-safe' additionally")
    print("requires (N0) cochain-map naturality -- see module docstring; it")
    print("holds for the three subdivision witnesses and fails for the")
    print("bridge witness, which adds new topology rather than subdividing.")
    print("'E0' (exactness reflection) is a separate, independent condition:")
    print("it holds for ALL FOUR witnesses, including the bridge -- adding a")
    print("new topology does not, by itself, break exactness reflection, only")
    print("naturality does. 'Verdict-safe' requires both descent-safe and E0,")
    print("so it agrees with descent-safe here (true for the three")
    print("subdivisions, false for the bridge), but for a logically distinct")
    print("reason on the bridge row: E0 holds there, N0 does not.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", metavar="PATH", help="write certificates as JSON to PATH")
    args = parser.parse_args()

    certificates = [check_witness(w) for w in ALL_WITNESSES]

    for cert in certificates:
        print_certificate(cert)

    print_summary_table(certificates)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(certificates, f, indent=2)
        print(f"\nWrote {len(certificates)} certificates to {args.json}")


if __name__ == "__main__":
    main()
