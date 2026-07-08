#!/usr/bin/env python3
"""
boolean_crossing_diagnostic.py

A diagnostic witness, not a theorem: a non-degenerate four-region shared-P
cover on which the "Boolean proper-crossing" outer-slot rule produces a
genuine, non-repairable first-order associator residue. See
docs/BOOLEAN_PROPER_CROSSING_DIAGNOSTIC.md for the full write-up, and
docs/COUPLED_GENERATOR_SPEC.md / docs/REALISABILITY_ROADMAP.md for how
this fits into the still-open coupled-generator question.

This is a genuinely different construction from
coupled_realisability_diagnostic.py's shared-adjacent-mu test: that one
probed a *linear* parameter space (free rational mu12..mu41) and computed
a rank/quotient. This one has no free parameters at all -- the outer and
inner correction slots are *derived*, deterministically, from the region
lattice itself:

    mu(A, B) = 1  iff  A and B properly cross (A n B != empty, and
                        neither A subseteq B nor B subseteq A)
    mu(A, B) = 0  otherwise

applied to populate all four SeamCorrectionData slots per triple. Because
there is no free parameter, there is no matrix and no rank to compute;
the only question is whether the one resulting residue vector, for a
given choice of P and U1..U4, is a coboundary or not. This module answers
that for exactly one recorded, non-degenerate witness, verified through
six gates against the real repository code -- not a hand-evaluated
scalar formula (see the module docstring history: an earlier hand-checked
"witness" for this same rule failed gate 1 on three of its four seams
when actually run through compute_seam_residue; nothing here is accepted
without that step).

The six gates
-------------
Gate 0 (non-degeneracy): |Ui| > 1 for all i; no Ui subseteq Uj for any
    i != j; the four adjacent pairs (U1,U2), (U2,U3), (U3,U4), (U4,U1)
    are genuine proper crossings. Without this gate, a region can
    collapse to a single point contained in every other region and
    produce curvature "for free" -- see search_for_witness's docstring
    for the degenerate witness this gate was added to exclude.
Gate 1 (support validity): all four cyclic-successor theta-triples have
    a genuine single-point overlap (Theorem thm:triple-localisation's
    modelling requirement, enforced by compute_seam_residue itself).
Gate 2: the Boolean rule populates the actual SeamCorrectionData slots.
Gate 3: associator_residue.compute_seam_residue actually succeeds on all
    four seams (raises on failure; a candidate that raises is rejected,
    not patched).
Gate 4: the assembled real residue vector is not a coboundary of the
    paper's own coboundary_0 matrix (exact solve_over_Q, not a naive
    coordinate-sum heuristic -- see WARNING below).
Gate 5: residue_classifier.classify() independently confirms
    nontrivial_H1_obstruction (a second, unrelated check of the same
    fact, in the same spirit as this repository's other two-certificate
    disciplines).

WARNING -- orientation convention
----------------------------------
The naive coordinate sum r_e12+r_e23+r_e34+r_e14 is NOT the coboundary
test for this seam ordering. That "sum = 0" shortcut only coincided with
being a coboundary in coupled_realisability_diagnostic.py's all-forward
cyclic orientation (e41 : U4->U1). The paper's actual seam order has e14
running U1->U4 (not cyclic-forward U4->U1), so "sum = 0" is not the right
invariant here and may be misleading if read as one. The authoritative
test is gate 4 (exact solve_over_Q against the real coboundary_0 matrix)
and gate 5 (the classifier), both computed directly below, never a sum.

USAGE:
    python boolean_crossing_diagnostic.py            # verify the recorded witness
    python boolean_crossing_diagnostic.py --search    # re-run the search that found it
"""

import argparse
from fractions import Fraction
from typing import Dict, FrozenSet, Tuple

from regional_composition import VennTriple, SeamCorrectionData
from associator_residue import SeamAssociatorInstance, compute_seam_residue
from residue_classifier import classify
from rational_linear_algebra import solve_over_Q

SEAMS = ("e12", "e23", "e34", "e14")
THETA: Dict[str, Tuple[str, str, str]] = {
    "e12": ("U1", "U2", "U3"),
    "e23": ("U2", "U3", "U4"),
    "e34": ("U3", "U4", "U1"),
    "e14": ("U4", "U1", "U2"),
}

# The paper's actual coboundary_0 (examples/four_cycle.json), NOT the
# all-forward cyclic convention used in coupled_realisability_diagnostic.py.
COARSE_D0 = [
    [Fraction(-1), Fraction(1), Fraction(0), Fraction(0)],
    [Fraction(0), Fraction(-1), Fraction(1), Fraction(0)],
    [Fraction(0), Fraction(0), Fraction(-1), Fraction(1)],
    [Fraction(-1), Fraction(0), Fraction(0), Fraction(1)],
]
CYCLE = [Fraction(-1), Fraction(-1), Fraction(-1), Fraction(1)]

# The recorded non-degenerate witness (Gate 0-5, all passed -- see
# docs/BOOLEAN_PROPER_CROSSING_DIAGNOSTIC.md).
WITNESS: Dict[str, FrozenSet[int]] = {
    "U1": frozenset({0, 1, 2}),
    "U2": frozenset({0, 1, 3}),
    "U3": frozenset({0, 2, 3}),
    "U4": frozenset({1, 2, 3, 4}),
}


def properly_crosses(A: FrozenSet[int], B: FrozenSet[int]) -> bool:
    """The Boolean proper-crossing rule: True iff A and B intersect and
    neither contains the other."""
    inter = A & B
    if not inter:
        return False
    return inter != A and inter != B


def contains_or_contained(A: FrozenSet[int], B: FrozenSet[int]) -> bool:
    inter = A & B
    return inter == A or inter == B


def check_gate0_nondegeneracy(regions: Dict[str, FrozenSet[int]]) -> Tuple[bool, list]:
    failures = []
    for name, region in regions.items():
        if len(region) <= 1:
            failures.append(f"{name} has size {len(region)} <= 1")
    names = list(regions)
    for i in range(len(names)):
        for j in range(len(names)):
            if i == j:
                continue
            if contains_or_contained(regions[names[i]], regions[names[j]]):
                failures.append(f"{names[i]} and {names[j]} are contained one in the other")
    adjacent = [("U1", "U2"), ("U2", "U3"), ("U3", "U4"), ("U4", "U1")]
    for x, y in adjacent:
        if not properly_crosses(regions[x], regions[y]):
            failures.append(f"adjacent pair ({x},{y}) does not properly cross")
    return not failures, failures


def check_gate1_support(regions: Dict[str, FrozenSet[int]]) -> Tuple[bool, dict]:
    overlaps = {}
    ok = True
    for seam, (x, y, z) in THETA.items():
        overlap = regions[x] & regions[y] & regions[z]
        overlaps[seam] = overlap
        if len(overlap) != 1:
            ok = False
    return ok, overlaps


def _seam_correction_via_boolean_rule(regions: Dict[str, FrozenSet[int]], x: str, y: str, z: str) -> SeamCorrectionData:
    """Gate 2: populate the real SeamCorrectionData slots from the
    Boolean proper-crossing rule -- no free parameters, no hand-picked
    values."""
    Ux, Uy, Uz = regions[x], regions[y], regions[z]

    def mu(A, B):
        return Fraction(1) if properly_crosses(A, B) else Fraction(0)

    return SeamCorrectionData(
        mu_VW=mu(Uy, Uz),
        mu_UvV_W=mu(Ux | Uy, Uz),
        mu_U_VvW=mu(Ux, Uy | Uz),
        mu_UV=mu(Ux, Uy),
    )


def verify_witness(regions: Dict[str, FrozenSet[int]]) -> dict:
    """
    Runs all six gates against the given regions, using the real
    repository code throughout (gate 3 calls
    associator_residue.compute_seam_residue directly; gate 5 calls
    residue_classifier.classify() directly). Returns a structured result;
    does not raise merely because a gate fails, so callers can inspect
    exactly where a candidate was rejected.
    """
    gate0_ok, gate0_failures = check_gate0_nondegeneracy(regions)
    gate1_ok, overlaps = check_gate1_support(regions)

    result = {
        "regions": {k: sorted(v) for k, v in regions.items()},
        "gate0_nondegenerate": gate0_ok,
        "gate0_failures": gate0_failures,
        "gate1_support_valid": gate1_ok,
        "triple_overlaps": {s: sorted(v) for s, v in overlaps.items()},
    }
    if not gate1_ok:
        result["gate3_all_seams_computed"] = False
        return result

    residues = {}
    gate3_ok = True
    gate3_error = None
    for seam, (x, y, z) in THETA.items():
        mu = _seam_correction_via_boolean_rule(regions, x, y, z)
        triple = VennTriple(U=regions[x], V=regions[y], W=regions[z])
        instance = SeamAssociatorInstance(seam=seam, mu=mu, triple=triple)
        try:
            residues[seam] = compute_seam_residue(instance)  # gate 2 + gate 3
        except Exception as e:
            gate3_ok = False
            gate3_error = repr(e)
            break

    result["gate3_all_seams_computed"] = gate3_ok
    if not gate3_ok:
        result["gate3_error"] = gate3_error
        return result

    r_vec = [residues[s] for s in SEAMS]
    result["residue_vector"] = [str(x) for x in r_vec]

    is_coboundary, _ = solve_over_Q(COARSE_D0, r_vec)
    result["gate4_not_coboundary"] = not is_coboundary

    cert = classify({
        "name": "boolean-crossing witness",
        "complex": {
            "name": "four-cycle (boolean crossing witness)",
            "coboundary_0": [[str(x) for x in row] for row in COARSE_D0],
            "coboundary_1": [],
        },
        "residue": [str(x) for x in r_vec],
        "cycle_witness": [str(x) for x in CYCLE],
    })
    result["gate5_classifier_verdict"] = cert["verdict"]
    result["pairing"] = cert["pairing"]
    result["all_gates_passed"] = bool(
        gate0_ok and gate1_ok and gate3_ok
        and result["gate4_not_coboundary"]
        and cert["verdict"] == "nontrivial_H1_obstruction"
    )
    return result


def search_for_witness(n: int, time_budget_s: float = 60.0, require_nondegenerate: bool = True):
    """
    Reproduces the search that found WITNESS (or, with
    require_nondegenerate=False, the earlier degenerate existence witness
    it superseded -- kept only to document that a degenerate witness was
    the first thing found, and was deliberately not the one recorded).
    Not exercised by the test suite (it's a search, not a fixed
    computation); see tests/test_boolean_crossing_diagnostic.py for the
    fast regression check against the fixed WITNESS instead.
    """
    import time
    t0 = time.time()
    candidates = [m for m in range(1, 1 << n) if bin(m).count("1") >= (2 if require_nondegenerate else 1)]

    def mask_to_set(m):
        return frozenset(i for i in range(n) if (m >> i) & 1)

    for U1 in candidates:
        for U2 in candidates:
            if require_nondegenerate:
                if contains_or_contained(mask_to_set(U1), mask_to_set(U2)):
                    continue
                if not properly_crosses(mask_to_set(U1), mask_to_set(U2)):
                    continue
            for U3 in candidates:
                if require_nondegenerate:
                    if contains_or_contained(mask_to_set(U1), mask_to_set(U3)):
                        continue
                    if contains_or_contained(mask_to_set(U2), mask_to_set(U3)):
                        continue
                    if not properly_crosses(mask_to_set(U2), mask_to_set(U3)):
                        continue
                regions3 = {"U1": mask_to_set(U1), "U2": mask_to_set(U2), "U3": mask_to_set(U3)}
                if len(regions3["U1"] & regions3["U2"] & regions3["U3"]) != 1:
                    continue
                for U4 in candidates:
                    if time.time() - t0 > time_budget_s:
                        return None
                    regions = {**regions3, "U4": mask_to_set(U4)}
                    ok1, _ = check_gate1_support(regions)
                    if not ok1:
                        continue
                    ok0, _ = check_gate0_nondegeneracy(regions)
                    if require_nondegenerate and not ok0:
                        continue
                    result = verify_witness(regions)
                    if result.get("all_gates_passed"):
                        return regions
    return None


def print_report() -> None:
    result = verify_witness(WITNESS)
    print("Boolean proper-crossing diagnostic: recorded non-degenerate witness")
    print(f"  regions: {result['regions']}")
    print(f"  gate 0 (non-degeneracy): {result['gate0_nondegenerate']}")
    print(f"  gate 1 (support validity): {result['gate1_support_valid']}  overlaps={result['triple_overlaps']}")
    print(f"  gate 3 (real code succeeded on all seams): {result['gate3_all_seams_computed']}")
    if result["gate3_all_seams_computed"]:
        print(f"  residue vector: {result['residue_vector']}")
        print(f"  gate 4 (not a coboundary, exact solve_over_Q): {result['gate4_not_coboundary']}")
        print(f"  gate 5 (classifier verdict): {result['gate5_classifier_verdict']}  pairing={result['pairing']}")
    print(f"  ALL GATES PASSED: {result.get('all_gates_passed', False)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", action="store_true", help="re-run the search instead of verifying the recorded witness")
    parser.add_argument("--n", type=int, default=5, help="point universe size for --search")
    args = parser.parse_args()

    if args.search:
        found = search_for_witness(args.n)
        print(f"search over |P|={args.n}: {'FOUND ' + str(found) if found else 'not found within budget'}")
    else:
        print_report()
