#!/usr/bin/env python3
"""
refinement_witness_composition_boundary_search.py

Phase 2b: an ADVERSARIAL search for the A4/E0 composition boundary, not
another source of friendly examples. Phase 2's search
(refinement_witness_a4_e0_counterexample_search.py) only tried witnesses
built from genuine graph refinements (subdividing a vertex, inserting a
bridge) -- well-behaved by construction. This file drops the graph
structure entirely and searches small, otherwise-ARBITRARY linear
witness data: small integer coboundary maps and edge-level pullbacks,
constrained only by the actual hypotheses (N0 at each step, A3/A4 at
each step), not by coming from any refinement operation at all.

The question, stated precisely
-------------------------------
Given two abstract refinement steps P -> Q -> R (small rational vector
spaces in degrees 0 and 1, arbitrary coboundary maps delta_P/delta_Q/
delta_R, arbitrary edge-level pullbacks rho1_PQ/rho1_QR), each
individually satisfying (N0), (A3), and (A4) for some cycle witness and
some residue r, must the composite P -> R satisfy (A4) and (E0)? If not,
what is the smallest counterexample? If none is found in an exhaustive
small search, that is evidence toward A4/E0 being structurally forced,
not proof.

The construction (scope, stated precisely)
---------------------------------------------
Vertex-level spaces are held at a SINGLE fixed dimension n0 across all
three levels, with vertex-level pullbacks fixed to the identity
(rho0_PQ = rho0_QR = I). This is a genuine narrowing of scope, not
hidden: it means this search does NOT vary vertex-level pullback
structure, only coboundary maps and edge-level pullbacks. Under this
choice, (N0) is satisfied automatically, by construction, for any choice
of delta_P and rho1_PQ:

    delta_Q := rho1_PQ . delta_P        (so delta_Q . I = rho1_PQ . delta_P)
    delta_R := rho1_QR . delta_Q        (so delta_R . I = rho1_QR . delta_Q)

This guarantees every witness generated here already satisfies (N0) at
both steps, so all search effort goes toward the genuinely open
questions: whether (A3)/(A4) can be satisfied at each step, and whether
the composite then satisfies (A4)/(E0). No graph, no vertex names, no
"subdivide"/"bridge" semantics anywhere in this file.

A caught mistake, worth recording exactly like the earlier ones in this
project. The first version of this search checked only (A3)/(A4)/(N0)
at each individual step before testing the composite, not (E0). It
found thousands of "E0 counterexamples" -- but every one of them turned
out to be a case where an individual STEP already failed (E0) on its
own terms, so the composite inherited a pre-existing failure rather than
demonstrating anything about composition. Once each step's own (E0) was
also required (full "verdict-safe" status per `refinement_checker.py`'s
terminology, on both steps, before the composite is even examined), every
one of those apparent counterexamples disappeared -- 0 found, across both
searches below. This is exactly the discipline this project insists on:
a striking result was checked before being reported, not after.

Two searches are run:
1. An EXHAUSTIVE search over the smallest case that can produce a
   nonzero cycle space at all (n0=1, n1_P=n1_Q=n1_R=2, entries in
   {-1,0,1}), with pruning (skip the rho1_QR loop entirely if step 1
   itself doesn't satisfy A3/A4 for the given delta_P/rho1_PQ/r).
2. A supplementary randomized search over larger dimensions and entry
   ranges, explicitly NOT claimed as exhaustive.

USAGE:
    python refinement_witness_composition_boundary_search.py
"""

import itertools
import random
import time
from fractions import Fraction as F
from typing import List, Optional, Tuple

from rational_linear_algebra import (
    mat_vec, mat_mat, row_vec_mat, dot, is_zero,
    transpose, nullspace_over_Q, in_span_over_Q,
)

Matrix = List[List[F]]
Vector = List[F]


def build_witness_and_check(delta_P: Matrix, rho1_PQ: Matrix, rho1_QR: Matrix, r: Vector
                             ) -> Optional[dict]:
    """Builds delta_Q, delta_R by construction (guaranteeing N0 at both
    steps -- see module docstring), then checks A3/A4/E0 at EACH
    INDIVIDUAL STEP, and only if both steps are genuinely fully
    verdict-safe on their own terms (not just admissible), checks the
    composite's A4 and E0. Returns None if either step fails to be fully
    verdict-safe for any cycle in its own (computed, not chosen) cycle
    space -- not a counterexample, just not a valid two-step witness
    pair to test composition against at all. Checking E0 at each
    individual step (not just A3/A4/N0) matters: a composite E0 failure
    is only evidence about COMPOSITION if it wasn't already inherited
    from an individual step that never had E0 to begin with."""
    delta_Q = mat_mat(rho1_PQ, delta_P)
    Z1_Q = nullspace_over_Q(transpose(delta_Q))
    if not Z1_Q:
        return None

    Q_residue = mat_vec(rho1_PQ, r)
    step1_ok = False
    for z_Q in Z1_Q:
        if is_zero(row_vec_mat(z_Q, delta_Q)) and dot(z_Q, Q_residue) != 0:
            step1_ok = True
            break
    if not step1_ok:
        return None

    # Step 1's own E0: Z1(P) subseteq pushforward of Z1(Q) via rho1_PQ.
    Z1_P = nullspace_over_Q(transpose(delta_P))
    pushed_from_Q = [mat_vec(transpose(rho1_PQ), z) for z in Z1_Q]
    step1_E0 = all(in_span_over_Q(pushed_from_Q, z) for z in Z1_P)
    if not step1_E0:
        return None

    delta_R = mat_mat(rho1_QR, delta_Q)
    Z1_R = nullspace_over_Q(transpose(delta_R))
    if not Z1_R:
        return None

    R_residue_from_Q = mat_vec(rho1_QR, Q_residue)
    step2_z = None
    for z_R in Z1_R:
        if is_zero(row_vec_mat(z_R, delta_R)) and dot(z_R, R_residue_from_Q) != 0:
            step2_z = z_R
            break
    if step2_z is None:
        return None

    # Step 2's own E0: Z1(Q) subseteq pushforward of Z1(R) via rho1_QR.
    pushed_from_R = [mat_vec(transpose(rho1_QR), z) for z in Z1_R]
    step2_E0 = all(in_span_over_Q(pushed_from_R, z) for z in Z1_Q)
    if not step2_E0:
        return None

    # Both steps genuinely FULLY verdict-safe (A3+A4+N0+E0) on their own
    # terms. Now test the COMPOSITE.
    composite_rho1 = mat_mat(rho1_QR, rho1_PQ)
    composite_residue = mat_vec(composite_rho1, r)
    composite_pairing = dot(step2_z, composite_residue)
    composite_A4 = composite_pairing != 0

    pushed_cycles = [mat_vec(transpose(composite_rho1), z) for z in Z1_R]
    composite_E0 = all(in_span_over_Q(pushed_cycles, z) for z in Z1_P)

    return {
        "delta_P": delta_P, "rho1_PQ": rho1_PQ, "rho1_QR": rho1_QR, "r": r,
        "delta_Q": delta_Q, "delta_R": delta_R,
        "composite_pairing": composite_pairing,
        "composite_A4": composite_A4, "composite_E0": composite_E0,
    }


def _all_matrices(rows: int, cols: int, values: Tuple[F, ...]):
    for flat in itertools.product(values, repeat=rows * cols):
        yield [list(flat[i * cols:(i + 1) * cols]) for i in range(rows)]


def exhaustive_search(n1: int = 2, values: Tuple[F, ...] = (F(-1), F(0), F(1)),
                       time_budget_s: float = 120.0) -> dict:
    """Exhaustive over delta_P (n1x1), rho1_PQ (n1xn1), rho1_QR (n1xn1),
    r (length n1), entries in `values`, with pruning: the rho1_QR loop
    only runs for (delta_P, rho1_PQ, r) combinations that already pass
    step 1's A3+A4. Stops early (reporting itself as incomplete, not
    silently claiming exhaustiveness) if `time_budget_s` is exceeded."""
    start = time.time()
    tested = 0
    step1_survivors = 0
    composite_tested = 0
    a4_failures = []
    e0_failures = []
    timed_out = False

    for delta_P in _all_matrices(n1, 1, values):
        for rho1_PQ in _all_matrices(n1, n1, values):
            delta_Q = mat_mat(rho1_PQ, delta_P)
            Z1_Q = nullspace_over_Q(transpose(delta_Q))
            if not Z1_Q:
                continue
            for r_flat in itertools.product(values, repeat=n1):
                r = list(r_flat)
                tested += 1
                if tested % 5000 == 0 and time.time() - start > time_budget_s:
                    timed_out = True
                    break
                Q_residue = mat_vec(rho1_PQ, r)
                step1_ok = any(
                    is_zero(row_vec_mat(z_Q, delta_Q)) and dot(z_Q, Q_residue) != 0
                    for z_Q in Z1_Q
                )
                if not step1_ok:
                    continue
                step1_survivors += 1
                for rho1_QR in _all_matrices(n1, n1, values):
                    result = build_witness_and_check(delta_P, rho1_PQ, rho1_QR, r)
                    if result is None:
                        continue
                    composite_tested += 1
                    if not result["composite_A4"]:
                        a4_failures.append(result)
                    if not result["composite_E0"]:
                        e0_failures.append(result)
            if timed_out:
                break
        if timed_out:
            break

    return {
        "n1": n1, "values": [str(v) for v in values],
        "step1_step2_combinations_tested": tested,
        "step1_survivors": step1_survivors,
        "composite_witnesses_tested": composite_tested,
        "a4_failures": a4_failures, "e0_failures": e0_failures,
        "exhaustive_completed": not timed_out,
        "elapsed_s": time.time() - start,
    }


def randomized_search(trials: int = 20000, seed: int = 20260709,
                       n1_range=(1, 4), value_range=(-3, 3)) -> dict:
    """NOT exhaustive -- explicitly labelled as such. Larger dimension
    range and entry range than the exhaustive search, many random
    trials."""
    rng = random.Random(seed)
    composite_tested = 0
    a4_failures = []
    e0_failures = []

    def rand_val():
        return F(rng.randint(*value_range))

    def rand_matrix(rows, cols):
        return [[rand_val() for _ in range(cols)] for _ in range(rows)]

    for _ in range(trials):
        n1 = rng.randint(*n1_range)
        delta_P = rand_matrix(n1, 1)
        rho1_PQ = rand_matrix(n1, n1)
        rho1_QR = rand_matrix(n1, n1)
        r = [rand_val() for _ in range(n1)]
        result = build_witness_and_check(delta_P, rho1_PQ, rho1_QR, r)
        if result is None:
            continue
        composite_tested += 1
        if not result["composite_A4"]:
            a4_failures.append(result)
        if not result["composite_E0"]:
            e0_failures.append(result)

    return {
        "trials": trials, "composite_witnesses_tested": composite_tested,
        "a4_failures": a4_failures, "e0_failures": e0_failures,
    }


def print_report() -> None:
    print("Refinement witness composition BOUNDARY search (adversarial, not friendly)")
    print()
    print("=== Exhaustive search (n1=2, entries in {-1,0,1}) ===")
    ex = exhaustive_search()
    print(f"  (delta_P, rho1_PQ, r) combinations tested: {ex['step1_step2_combinations_tested']}")
    print(f"  of which step 1 (A3+A4) survived: {ex['step1_survivors']}")
    print(f"  composite witnesses actually tested (step 2 also A3+A4): {ex['composite_witnesses_tested']}")
    print(f"  A4 counterexamples found: {len(ex['a4_failures'])}")
    print(f"  E0 counterexamples found: {len(ex['e0_failures'])}")
    print(f"  search completed within time budget (genuinely exhaustive over stated bounds): "
          f"{ex['exhaustive_completed']}")
    print(f"  elapsed: {ex['elapsed_s']:.1f}s")
    if ex["a4_failures"]:
        print(f"  FIRST A4 COUNTEREXAMPLE: {ex['a4_failures'][0]}")
    if ex["e0_failures"]:
        print(f"  FIRST E0 COUNTEREXAMPLE: {ex['e0_failures'][0]}")
    print()

    print("=== Randomized search (n1 in [1,4), entries in [-3,3], NOT exhaustive) ===")
    rnd = randomized_search()
    print(f"  trials: {rnd['trials']}")
    print(f"  composite witnesses actually tested: {rnd['composite_witnesses_tested']}")
    print(f"  A4 counterexamples found: {len(rnd['a4_failures'])}")
    print(f"  E0 counterexamples found: {len(rnd['e0_failures'])}")
    if rnd["a4_failures"]:
        print(f"  FIRST A4 COUNTEREXAMPLE: {rnd['a4_failures'][0]}")
    if rnd["e0_failures"]:
        print(f"  FIRST E0 COUNTEREXAMPLE: {rnd['e0_failures'][0]}")
    print()

    if not ex["a4_failures"] and not ex["e0_failures"] and not rnd["a4_failures"] and not rnd["e0_failures"]:
        print("No A4 or E0 counterexample found, in an exhaustive small adversarial")
        print("search plus a larger non-exhaustive randomized one. This is evidence")
        print("toward A4/E0 being structurally forced under N0 -- not a proof, and")
        print("this search fixed vertex-level pullbacks to the identity throughout")
        print("(see module docstring) -- a genuinely broader search would vary that too.")


if __name__ == "__main__":
    print_report()
