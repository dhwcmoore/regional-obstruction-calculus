#!/usr/bin/env python3
"""
lattice_ie_diagnostic.py

Fourth realisability diagnostic: the ordered inclusion-exclusion outer-
slot discipline. See docs/diagnostics/LATTICE_IE_DIAGNOSTIC.md for the full write-up
and docs/design/COUPLED_GENERATOR_SPEC.md / docs/diagnostics/REALISABILITY_DIAGNOSTICS.md for
how this fits into the broader realisability line.

The construction
-----------------
Reuses the shared four-region point-set cover already verified in
coupled_realisability_diagnostic.py (REGIONS: U1..U4 as subsets of one
point universe, with genuine single-point cyclic-triple overlaps). mu is
indexed not by seam label and not by atomic region alone, but by
*ordered pairs of canonical supports* -- frozensets of points in the
shared universe, so that the same lattice-derived support (e.g. U2 n U3)
resolves to the same shared parameter everywhere it is referenced, not a
seam-private one:

    mu_key(A, B) = (frozenset(A), frozenset(B))

For triple (X, Y, Z), the four real SeamCorrectionData slots are
populated by ordered inclusion-exclusion over that shared mu dict:

    mu_UV      = mu[X, Y]
    mu_VW      = mu[Y, Z]
    mu_U_VvW   = mu[X, Y] + mu[X, Z] - mu[X, Y n Z]
    mu_UvV_W   = mu[X, Z] + mu[Y, Z] - mu[X n Y, Z]

This is a genuine hypothesis about a shared, non-private, non-zero rule
for the outer slots -- tested here against the real code, not assumed.

The verified negative result
------------------------------
Substituting these into the already-verified closed form
(Delta = mu_VW - mu_UvV_W + mu_U_VvW - mu_UV, cross-checked internally by
compute_seam_residue on every call) and simplifying algebraically:

    Delta = mu[X n Y, Z] - mu[X, Y n Z]

every other term cancels exactly -- mu_UV, mu_VW, and the plain diagonal
mu[X,Z] all vanish from the final formula, regardless of value. This
module does not take that cancellation on faith: verify_cancellation()
below checks it directly against the real basis-probed matrix, not
symbolic algebra, and verify_reduction_against_real_code() spot-checks it
against compute_seam_residue directly under random rational parameters,
on two different triples with different role assignments (an earlier
Boolean-rule "witness" in this same project failed exactly this kind of
check -- see docs/diagnostics/BOOLEAN_PROPER_CROSSING_DIAGNOSTIC.md -- so nothing
here is accepted without it).

Because only the two composite (meet-based) keys per triple survive, and
those composite supports never coincide across two different theta-
triples in this four-region cover (each triple's X n Y and Y n Z are
distinct point-sets from every other triple's), the induced map has full
rank: this discipline is globally shared at the *parameter* level but
recreates seam-local independence in disguised form. See diagnose() for
the exact numbers and the corrected verdict (an earlier informal read of
"quotient dimension 1" as "useful" was wrong -- see its docstring).

USAGE:
    python lattice_ie_diagnostic.py
"""

from fractions import Fraction
from typing import Dict, FrozenSet, List, Tuple

from regional_composition import VennTriple, SeamCorrectionData
from associator_residue import SeamAssociatorInstance, compute_seam_residue
from coupled_realisability_diagnostic import REGIONS
from rational_linear_algebra import (
    solve_over_Q, nullspace_over_Q, transpose, in_span_over_Q, mat_vec,
)

SEAMS = ("e12", "e23", "e34", "e14")
# Local to this module, matching the paper's actual seam labels/orientation
# (e14: U1->U4) -- NOT coupled_realisability_diagnostic.THETA's "e41" label
# (U4->U1). Same triple, different name; using the wrong one silently
# raises KeyError rather than giving a wrong answer, which is how this
# was actually caught during development.
THETA: Dict[str, Tuple[str, str, str]] = {
    "e12": ("U1", "U2", "U3"),
    "e23": ("U2", "U3", "U4"),
    "e34": ("U3", "U4", "U1"),
    "e14": ("U4", "U1", "U2"),
}

COARSE_D0 = [
    [Fraction(-1), Fraction(1), Fraction(0), Fraction(0)],
    [Fraction(0), Fraction(-1), Fraction(1), Fraction(0)],
    [Fraction(0), Fraction(0), Fraction(-1), Fraction(1)],
    [Fraction(-1), Fraction(0), Fraction(0), Fraction(1)],
]

MuKey = Tuple[FrozenSet[int], FrozenSet[int]]


def mu_key(A: FrozenSet[int], B: FrozenSet[int]) -> MuKey:
    return (frozenset(A), frozenset(B))


def seam_correction_ie(mu: Dict[MuKey, Fraction], X, Y, Z) -> SeamCorrectionData:
    """The ordered inclusion-exclusion slot-population rule (a hypothesis
    tested elsewhere in this module, not assumed here)."""
    def m(A, B):
        return mu.get(mu_key(A, B), Fraction(0))
    XnY, YnZ = X & Y, Y & Z
    return SeamCorrectionData(
        mu_UV=m(X, Y),
        mu_VW=m(Y, Z),
        mu_U_VvW=m(X, Y) + m(X, Z) - m(X, YnZ),
        mu_UvV_W=m(X, Z) + m(Y, Z) - m(XnY, Z),
    )


def residue_for(mu: Dict[MuKey, Fraction]) -> List[Fraction]:
    """Runs the real generator (compute_seam_residue, internally
    cross-checked against closed_form_delta) for all four seams under the
    given shared mu dict. Unset keys default to 0."""
    residues = {}
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
        corr = seam_correction_ie(mu, X, Y, Z)
        triple = VennTriple(U=X, V=Y, W=Z)
        inst = SeamAssociatorInstance(seam=seam, mu=corr, triple=triple)
        residues[seam] = compute_seam_residue(inst)
    return [residues[s] for s in SEAMS]


def all_global_keys() -> List[MuKey]:
    """Every distinct mu key referenced across all four triples' slot
    rules, in first-seen order."""
    keys: List[MuKey] = []
    seen = set()
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
        XnY, YnZ = X & Y, Y & Z
        for key in [mu_key(X, Y), mu_key(Y, Z), mu_key(X, Z), mu_key(X, YnZ), mu_key(XnY, Z)]:
            if key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


def basis_probe() -> Tuple[List[List[Fraction]], List[MuKey]]:
    """Builds B_IE (4 rows = seam residues, len(all_global_keys()) columns
    = shared parameters) by actually running the real generator on each
    unit parameter vector -- not a hand-derived matrix."""
    keys = all_global_keys()
    columns = []
    for key in keys:
        mu = {key: Fraction(1)}
        columns.append(residue_for(mu))
    return transpose(columns), keys


def verify_reduction_against_real_code(seam: str, trials: int = 8, seed: int = 20260708) -> bool:
    """Spot-checks Delta = mu[XnY,Z] - mu[X,YnZ] against compute_seam_residue
    directly, under random rational parameters, for one named triple. Does
    NOT trust the symbolic cancellation; this is an independent numerical
    check for that specific seam."""
    import random
    rng = random.Random(seed)
    xk, yk, zk = THETA[seam]
    X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
    XnY, YnZ = X & Y, Y & Z
    keys = [mu_key(X, Y), mu_key(Y, Z), mu_key(X, Z), mu_key(X, YnZ), mu_key(XnY, Z)]
    for _ in range(trials):
        mu = {k: Fraction(rng.randint(-5, 5), rng.randint(1, 3)) for k in keys}
        real_r = residue_for(mu)[SEAMS.index(seam)]
        claimed_r = mu[mu_key(XnY, Z)] - mu[mu_key(X, YnZ)]
        if real_r != claimed_r:
            return False
    return True


def verify_cancellation() -> bool:
    """Checks the cancellation claim directly against the real
    basis-probed matrix (not symbolic algebra): every column corresponding
    to an adjacent-pair or plain-diagonal key must be entirely zero across
    all four rows -- only the composite (meet-based) columns may be
    nonzero."""
    matrix, keys = basis_probe()
    # composite keys are exactly those appearing as mu[X, YnZ] or mu[XnY, Z]
    # in the collection order -- identify them structurally: a key (P, Q) is
    # composite iff P or Q is a proper intersection of two of the four
    # region sets (not itself one of U1..U4).
    atomic_sets = set(frozenset(v) for v in REGIONS.values())
    for col_idx, key in enumerate(keys):
        P, Q = key
        is_composite = (P not in atomic_sets) or (Q not in atomic_sets)
        col = [matrix[row][col_idx] for row in range(len(matrix))]
        if not is_composite and any(x != 0 for x in col):
            return False
    return True


def diagnose() -> dict:
    """
    Computes rank(B_IE), the intersection/quotient dimensions relative to
    im(delta0), and the CORRECTED verdict. An earlier read of this result
    treated "dim(quotient) > 0" as evidence of useful partial
    realisability -- that reading is wrong whenever rank(B_IE) equals
    dim(C^1): in that case the map is fully surjective, image(B_IE) = all
    of C^1, and the "quotient" im(B_IE)/(im(B_IE) n im(delta0)) is simply
    C^1/im(delta0) = H^1(N;Q), a fact about the fixed graph N, not about
    this generator's selectivity. This function reports both the raw
    numbers and the corrected classification.
    """
    B, keys = basis_probe()
    B_columns = transpose(B)
    delta0_columns = [mat_vec(COARSE_D0, [Fraction(1) if i == j else Fraction(0) for i in range(4)])
                       for j in range(4)]

    def rank_of(vectors):
        if not vectors:
            return 0
        return len(vectors) - len(nullspace_over_Q(transpose(vectors)))

    rank_B = rank_of(B_columns)
    rank_delta0 = rank_of(delta0_columns)
    rank_union = rank_of(B_columns + delta0_columns)
    dim_intersection = rank_B + rank_delta0 - rank_union
    dim_quotient_raw = rank_B - dim_intersection
    full_rank = rank_B == len(B)  # len(B) = dim C^1 = 4

    return {
        "n_params": len(keys),
        "dim_C1": len(B),
        "rank_B": rank_B,
        "rank_delta0": rank_delta0,
        "dim_intersection": dim_intersection,
        "dim_quotient_raw": dim_quotient_raw,
        "full_rank": full_rank,
        "verdict": "TOO_FREE_full_rank" if full_rank else (
            "TOO_STRICT_collapses_to_im_delta0" if dim_quotient_raw == 0 else
            "genuinely_partial_nontrivial_quotient"
        ),
        "cancellation_verified": verify_cancellation(),
        "reduction_verified_e12": verify_reduction_against_real_code("e12"),
        "reduction_verified_e34": verify_reduction_against_real_code("e34"),
    }


def print_report() -> None:
    result = diagnose()
    print("Lattice inclusion-exclusion diagnostic: ordered IE outer-slot rule")
    print(f"  global shared parameters: {result['n_params']}")
    print(f"  dim C^1(N;Q): {result['dim_C1']}")
    print(f"  rank(B_IE): {result['rank_B']}  (full rank = {result['full_rank']})")
    print(f"  rank(delta0): {result['rank_delta0']}")
    print(f"  dim(im(B_IE) n im(delta0)): {result['dim_intersection']}")
    print(f"  dim(quotient), RAW (see caveat below): {result['dim_quotient_raw']}")
    print(f"  cancellation identity verified against real matrix: {result['cancellation_verified']}")
    print(f"  reduction Delta=mu[XnY,Z]-mu[X,YnZ] verified on e12: {result['reduction_verified_e12']}")
    print(f"  reduction Delta=mu[XnY,Z]-mu[X,YnZ] verified on e34: {result['reduction_verified_e34']}")
    print()
    print(f"  VERDICT: {result['verdict']}")
    if result["full_rank"]:
        print()
        print("  CAVEAT: the raw quotient number above is NOT evidence of useful")
        print("  partial realisability. Since rank(B_IE) = dim(C^1), image(B_IE) is")
        print("  literally all of C^1(N;Q), and the quotient im(B_IE)/(im(B_IE) n")
        print("  im(delta0)) is simply C^1/im(delta0) = H^1(N;Q) -- a fixed fact")
        print("  about this graph, true for ANY surjective generator, not a sign")
        print("  this rule is structurally selective. The generator is fully")
        print("  surjective, not structurally selective.")
        print()
        print("  A parameter can be globally indexed and still fail to impose")
        print("  structural dependence, if the associator formula cancels exactly")
        print("  those globally shared coordinates.")


if __name__ == "__main__":
    print_report()
