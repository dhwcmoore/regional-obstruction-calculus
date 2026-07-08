#!/usr/bin/env python3
"""
candidate_discipline_diagnostic.py

Fifth realisability diagnostic: Candidate 3b, the ordered
restriction-to-triple-support outer-slot discipline. The first candidate
run through carrier_matrix_infrastructure.py (`9e2ded6`), which is
otherwise infrastructure only and tests no rule of its own.

The construction
-----------------
Reuses the same shared four-region point-set cover already verified in
coupled_realisability_diagnostic.py / lattice_ie_diagnostic.py (REGIONS,
THETA, in the paper's e14:U4->U1... convention -- see those modules'
docstrings for why THETA is redefined locally rather than imported from
coupled_realisability_diagnostic, which uses "e41").

For each seam context theta(e) = (X, Y, Z), let T = X n Y n Z (the
triple's own support). Carrier coordinates are ordered restriction
parameters rho_{A,T}, keyed exactly like carrier_matrix_infrastructure's
CarrierCoordinate (a canonical pair of frozensets):

    rho_{A,T} := carrier_key(A, T)

Only the two OUTER slots are populated (the adjacent slots mu_UV, mu_VW
are pinned to zero -- deliberately, so this candidate cannot degenerate
into the coupled_realisability_diagnostic adjacency-gradient case):

    mu_UV      = 0
    mu_VW      = 0
    mu_U_VvW   = rho_{X,T}
    mu_UvV_W   = rho_{Z,T}

Under the fixed closed-form coefficients (mu_U_VvW: +1, mu_UvV_W: -1),
this gives

    Delta_e = rho_{X,T} - rho_{Z,T}

per seam -- an ordered restriction difference, not a cyclic gradient of a
single shared 0-cochain, and not the inclusion-exclusion cancellation
pattern of lattice_ie_diagnostic.py either.

The anticipated catch, tested here rather than assumed
---------------------------------------------------------
For rho_{A,T} to be genuinely shared across two seam rows (the
carrier_matrix_infrastructure.surviving_coordinate_sharing_check
criterion), the same (A, T) pair must recur as an X-or-Z role in more
than one theta-triple. In THIS cover, every cyclic triple's overlap T is
a distinct single point (T12={a}, T23={b}, T34={c}, T14={d} -- see
coupled_realisability_diagnostic's module docstring, verified there by
check_shared_cover()), so no two seams' rho_{A,T} keys can coincide: A
differs and T differs simultaneously across every pair of seams. The
sharing check is therefore expected to report all coordinates as
private_residual, not genuinely_shared, under this specific cover -- not
a flaw in the rule itself, but a property of this cover's triple-overlap
geometry. See diagnose() for the resulting rank and verdict, computed
from the real generator, not assumed from this reasoning.

USAGE:
    python candidate_discipline_diagnostic.py
"""

from fractions import Fraction
from typing import Dict, List, Tuple

from regional_composition import VennTriple, SeamCorrectionData
from associator_residue import SeamAssociatorInstance, compute_seam_residue
from coupled_realisability_diagnostic import REGIONS
from rational_linear_algebra import (
    nullspace_over_Q, transpose, mat_vec, mat_mat,
)
from carrier_matrix_infrastructure import (
    CarrierCoordinate,
    carrier_key,
    all_slot_coordinates,
    delta_matrix,
    build_R,
    compose_B,
    surviving_coordinate_sharing_check,
    sharing_check_summary,
)
from lattice_ie_diagnostic import COARSE_D0

SEAMS = ("e12", "e23", "e34", "e14")
# Local to this module, matching the paper's actual seam labels/orientation,
# same convention as lattice_ie_diagnostic.THETA and
# boolean_crossing_diagnostic.THETA -- NOT
# coupled_realisability_diagnostic.THETA's "e41" label. See those modules'
# docstrings for why this is redefined locally rather than imported.
THETA: Dict[str, Tuple[str, str, str]] = {
    "e12": ("U1", "U2", "U3"),
    "e23": ("U2", "U3", "U4"),
    "e34": ("U3", "U4", "U1"),
    "e14": ("U4", "U1", "U2"),
}


def triple_support(X: frozenset, Y: frozenset, Z: frozenset) -> frozenset:
    return X & Y & Z


def all_carrier_coordinates() -> List[CarrierCoordinate]:
    """The rho_{A,T} keys referenced across all four triples, in
    first-seen order: one (X,T) and one (Z,T) key per seam."""
    keys: List[CarrierCoordinate] = []
    seen = set()
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
        T = triple_support(X, Y, Z)
        for key in (carrier_key(X, T), carrier_key(Z, T)):
            if key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


def build_candidate_R() -> Tuple[List[List[Fraction]], List[CarrierCoordinate], List[Tuple[str, str]]]:
    """R for Candidate 3b: mu_UV = mu_VW = 0, mu_U_VvW = rho_{X,T},
    mu_UvV_W = rho_{Z,T}, built via the shared infrastructure's build_R
    (not a hand-assembled matrix)."""
    slots = all_slot_coordinates()
    carrier_coords = all_carrier_coordinates()
    rule: Dict[Tuple[str, str], Dict[CarrierCoordinate, Fraction]] = {}
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
        T = triple_support(X, Y, Z)
        rule[(seam, "U_VvW")] = {carrier_key(X, T): Fraction(1)}
        rule[(seam, "UvV_W")] = {carrier_key(Z, T): Fraction(1)}
    R = build_R(rule, carrier_coords, slots)
    return R, carrier_coords, slots


def induced_B() -> Tuple[List[List[Fraction]], List[CarrierCoordinate], List[str]]:
    """B = D . R for Candidate 3b, via the frozen infrastructure -- not a
    hand-derived matrix."""
    D, slots, seams = delta_matrix()
    R, carrier_coords, _ = build_candidate_R()
    B = compose_B(D, R)
    return B, carrier_coords, seams


def residue_for(rho: Dict[CarrierCoordinate, Fraction]) -> List[Fraction]:
    """Runs the REAL generator (compute_seam_residue, internally
    cross-checked against closed_form_delta) directly from a rho
    assignment -- an independent path from induced_B(), used to verify
    the abstract D/R composition actually matches the real code, not just
    itself."""
    residues = {}
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
        T = triple_support(X, Y, Z)
        corr = SeamCorrectionData(
            mu_UV=Fraction(0),
            mu_VW=Fraction(0),
            mu_U_VvW=rho.get(carrier_key(X, T), Fraction(0)),
            mu_UvV_W=rho.get(carrier_key(Z, T), Fraction(0)),
        )
        triple = VennTriple(U=X, V=Y, W=Z)
        inst = SeamAssociatorInstance(seam=seam, mu=corr, triple=triple)
        residues[seam] = compute_seam_residue(inst)
    return [residues[s] for s in SEAMS]


def verify_B_matches_real_generator() -> bool:
    """Basis-probes the real generator (residue_for, one unit rho at a
    time) and checks it matches induced_B() column for column -- the same
    cross-validation pattern carrier_matrix_infrastructure's own test
    suite used against lattice_ie_diagnostic. Does not trust the D/R
    composition on its own terms."""
    B, carrier_coords, seams = induced_B()
    for col_idx, key in enumerate(carrier_coords):
        rho = {key: Fraction(1)}
        real_col = residue_for(rho)
        abstract_col = [B[row][col_idx] for row in range(len(B))]
        if real_col != abstract_col:
            return False
    return True


def verify_reduction_against_real_code(seam: str, trials: int = 8, seed: int = 20260710) -> bool:
    """Spot-checks Delta_e = rho_{X,T} - rho_{Z,T} against
    compute_seam_residue directly, under random rational rho values, for
    one named seam -- an independent numerical check, not symbolic
    algebra."""
    import random
    rng = random.Random(seed)
    xk, yk, zk = THETA[seam]
    X, Y, Z = REGIONS[xk], REGIONS[yk], REGIONS[zk]
    T = triple_support(X, Y, Z)
    kx, kz = carrier_key(X, T), carrier_key(Z, T)
    for _ in range(trials):
        rho = {
            kx: Fraction(rng.randint(-5, 5), rng.randint(1, 3)),
            kz: Fraction(rng.randint(-5, 5), rng.randint(1, 3)),
        }
        real_r = residue_for(rho)[SEAMS.index(seam)]
        claimed_r = rho[kx] - rho[kz]
        if real_r != claimed_r:
            return False
    return True


def diagnose() -> dict:
    """Sharing check, rank(B), and the realisable-obstruction quotient
    relative to im(delta0) -- same computation pattern as
    lattice_ie_diagnostic.diagnose()."""
    B, carrier_coords, seams = induced_B()
    B_columns = transpose(B)
    delta0_columns = [
        mat_vec(COARSE_D0, [Fraction(1) if i == j else Fraction(0) for i in range(4)])
        for j in range(4)
    ]

    def rank_of(vectors):
        if not vectors:
            return 0
        return len(vectors) - len(nullspace_over_Q(transpose(vectors)))

    rank_B = rank_of(B_columns)
    rank_delta0 = rank_of(delta0_columns)
    rank_union = rank_of(B_columns + delta0_columns)
    dim_intersection = rank_B + rank_delta0 - rank_union
    dim_quotient_raw = rank_B - dim_intersection
    full_rank = rank_B == len(B)

    sharing_results = surviving_coordinate_sharing_check(B, carrier_coords, seams)
    summary = sharing_check_summary(sharing_results)

    return {
        "n_params": len(carrier_coords),
        "dim_C1": len(B),
        "rank_B": rank_B,
        "rank_delta0": rank_delta0,
        "dim_intersection": dim_intersection,
        "dim_quotient_raw": dim_quotient_raw,
        "full_rank": full_rank,
        "sharing_summary": summary,
        "verdict": "TOO_FREE_full_rank" if full_rank else (
            "TOO_STRICT_collapses_to_im_delta0" if dim_quotient_raw == 0 else
            "genuinely_partial_nontrivial_quotient"
        ),
        "B_matches_real_generator": verify_B_matches_real_generator(),
        "reduction_verified_e12": verify_reduction_against_real_code("e12"),
        "reduction_verified_e34": verify_reduction_against_real_code("e34"),
    }


def print_report() -> None:
    result = diagnose()
    print("Candidate discipline diagnostic: Candidate 3b, ordered restriction-to-triple-support")
    print(f"  global shared parameters: {result['n_params']}")
    print(f"  dim C^1(N;Q): {result['dim_C1']}")
    print(f"  rank(B): {result['rank_B']}  (full rank = {result['full_rank']})")
    print(f"  rank(delta0): {result['rank_delta0']}")
    print(f"  dim(im(B) n im(delta0)): {result['dim_intersection']}")
    print(f"  dim(quotient), raw: {result['dim_quotient_raw']}")
    print(f"  sharing check summary: {result['sharing_summary']}")
    print(f"  B matches independent real-generator basis probe: {result['B_matches_real_generator']}")
    print(f"  Delta_e = rho_X,T - rho_Z,T verified on e12: {result['reduction_verified_e12']}")
    print(f"  Delta_e = rho_X,T - rho_Z,T verified on e34: {result['reduction_verified_e34']}")
    print()
    print(f"  VERDICT: {result['verdict']}")
    if result["sharing_summary"]["genuinely_shared"] == 0:
        print()
        print("  As anticipated before running this: every cyclic triple overlap in")
        print("  this cover is a distinct single point, so no rho_{A,T} coordinate")
        print("  can recur across two seams -- all coordinates are private_residual,")
        print("  not genuinely shared. This is the SAME failure mode as")
        print("  lattice_ie_diagnostic.py (full rank, disguised independence), but")
        print("  reached for a simpler, more direct reason: this rule was never even")
        print("  globally indexed on this cover, because the triple-support geometry")
        print("  never reuses a support across two contexts. A cover with repeated")
        print("  triple supports (docs/COUPLED_GENERATOR_SPEC.md's option 1) would be")
        print("  needed before this rule's sharing behaviour can be tested at all.")


if __name__ == "__main__":
    print_report()
