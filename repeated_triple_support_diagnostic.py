#!/usr/bin/env python3
"""
repeated_triple_support_diagnostic.py

Sixth realisability diagnostic, and the first POSITIVE linear/rational
result in this line: Candidate 3b (ordered restriction-to-triple-support
outer-slot coupling, see candidate_discipline_diagnostic.py) run on a
cover whose four theta-triples share a single repeated triple-support
point, instead of the four distinct points of the standard cover. See
docs/REPEATED_TRIPLE_SUPPORT_DIAGNOSTIC.md for the full write-up and
docs/COUPLED_GENERATOR_SPEC.md / docs/REALISABILITY_ROADMAP.md for how
this fits the broader realisability line.

The precise claim
------------------
A linear/rational globally shared outer-slot discipline CAN produce a
genuinely partial, nontrivial obstruction quotient -- neither full rank
nor coboundary collapse -- when the cover has repeated triple support.
This is a diagnostic witness for one candidate rule on one family of
covers, not a general theorem about linear couplings; see "What this
does not show" in the docs write-up.

Why candidate_discipline_diagnostic.py's cover cannot test this rule
-----------------------------------------------------------------------
That module ran the same Candidate 3b rule on the standard cover
(coupled_realisability_diagnostic.REGIONS), where every cyclic triple
overlap is a distinct single point (T12={a}, T23={b}, T34={c}, T14={d}).
Every rho_{A,T} carrier coordinate came back private_residual there --
not because the rule is too free, but because that cover never gives it
a chance to be shared: no two theta-triples' overlaps coincide, so no two
rho_{A,T} keys can ever be equal.

Structural fact, verified below (not assumed)
-------------------------------------------------
In a four-theta-cycle nerve, the four triples are theta(e12)=(U1,U2,U3),
theta(e23)=(U2,U3,U4), theta(e34)=(U3,U4,U1), theta(e14)=(U4,U1,U2) --
each theta-triple is "all four regions minus one", so ANY two distinct
theta-triples' region-sets already union to all four regions. Hence, if a
point lies in two different theta-triples' overlaps, it lies in all four
regions, and therefore in ALL FOUR triple overlaps -- not just the two it
was placed in for. This rules out an "opposite pairs, distinct shared
points" pattern (T12=T34=t, T23=T14=s, s != t): forcing t into T12 and
T34 forces t into T23 and T14 too, contradicting T23=T14={s} unless
s=t. verify_opposite_pair_sharing_forces_global() checks this by direct
construction. The only repeated-triple-support cover consistent with
every theta-triple overlap remaining a genuine singleton (required by
associator_residue.compute_seam_residue) is: all four triple supports
equal to ONE shared global point.

The canonical cover
--------------------
CANONICAL_REGIONS below is a deliberately non-degenerate example of that
unique family: one shared global point t=0, one private point per region
(so no Ui subset of Uj), and one point shared by each of the six
unordered region pairs -- four adjacent, two diagonal (so every pair
properly crosses, in boolean_crossing_diagnostic.properly_crosses's
sense) -- each pairwise point placed in EXACTLY its two regions and
nowhere else, so it never leaks into a third region and breaks that
triple's singleton-overlap requirement. |Ui| = 5 for every region.

The result, and why it is invariant under cover enrichment
---------------------------------------------------------------
On CANONICAL_REGIONS, all four rho_{Ui,t} carrier coordinates come back
genuinely_shared (each shared between exactly two seams: (U1,t) and
(U3,t) via e12/e34; (U2,t) and (U4,t) via e23/e14 -- the "opposite pair"
structure forced above). The induced map B has rank 2 (not full rank 4,
not collapsed to rank 0): r_e12 = -r_e34 = rho_U1,t - rho_U3,t, and
r_e23 = -r_e14 = rho_U2,t - rho_U4,t. dim(im(B) n im(delta0)) = 1,
dim(quotient) = 1 -- a genuine, non-repairable residue this rule can
produce. richness_invariance_check() reruns the same computation across
several more-enriched covers (up to |Ui|=12) and confirms the numbers
never change: the rule only depends on which region plays the X-or-Z
role in which theta-triple (a combinatorial fact about the nerve) and on
the single shared support point, never on what else a region contains.
So there is no "richer witness to search for" in the sense of changing
the verdict -- richness is a variable this construction is provably
indifferent to.

USAGE:
    python repeated_triple_support_diagnostic.py
"""

import random
from fractions import Fraction
from typing import Dict, FrozenSet, List, Tuple

from regional_composition import VennTriple, SeamCorrectionData
from associator_residue import SeamAssociatorInstance, compute_seam_residue
from rational_linear_algebra import nullspace_over_Q, transpose, mat_vec
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
from boolean_crossing_diagnostic import properly_crosses

SEAMS = ("e12", "e23", "e34", "e14")
# Local to this module, same convention as lattice_ie_diagnostic.THETA,
# boolean_crossing_diagnostic.THETA, and candidate_discipline_diagnostic.
# THETA -- NOT coupled_realisability_diagnostic.THETA's "e41" label. See
# those modules' docstrings for why this is redefined locally rather than
# imported.
THETA: Dict[str, Tuple[str, str, str]] = {
    "e12": ("U1", "U2", "U3"),
    "e23": ("U2", "U3", "U4"),
    "e34": ("U3", "U4", "U1"),
    "e14": ("U4", "U1", "U2"),
}
PAIRS: Tuple[Tuple[str, str], ...] = (
    ("U1", "U2"), ("U2", "U3"), ("U3", "U4"), ("U4", "U1"), ("U1", "U3"), ("U2", "U4"),
)

# --- The canonical, hand-audited repeated-triple-support cover ---------
# t=0 (global, shared by all four regions); p1..p4 private (one per
# region); the six pairwise points are each in exactly the two regions of
# their pair.
_t = 0
_p1, _p2, _p3, _p4 = 1, 2, 3, 4
_x12, _x23, _x34, _x14, _x13, _x24 = 5, 6, 7, 8, 9, 10

CANONICAL_REGIONS: Dict[str, FrozenSet[int]] = {
    "U1": frozenset({_t, _p1, _x12, _x14, _x13}),
    "U2": frozenset({_t, _p2, _x12, _x23, _x24}),
    "U3": frozenset({_t, _p3, _x23, _x34, _x13}),
    "U4": frozenset({_t, _p4, _x34, _x14, _x24}),
}


def verify_opposite_pair_sharing_forces_global() -> bool:
    """Direct-construction check of the structural fact in the module
    docstring: forcing a point t into T12 and T34's defining regions
    forces it into T23 and T14 too, ruling out an independent second
    shared point s for the opposite pair. Returns True iff the forced
    membership is confirmed as predicted."""
    t = 0
    U1 = frozenset({t, 11})
    U2 = frozenset({t, 12})
    U3 = frozenset({t, 13})
    U4 = frozenset({t, 14})
    regions = {"U1": U1, "U2": U2, "U3": U3, "U4": U4}
    T12 = regions["U1"] & regions["U2"] & regions["U3"]
    T34 = regions["U3"] & regions["U4"] & regions["U1"]
    T23 = regions["U2"] & regions["U3"] & regions["U4"]
    T14 = regions["U4"] & regions["U1"] & regions["U2"]
    return T12 == {t} and T34 == {t} and t in T23 and t in T14


def check_nondegenerate(regions: Dict[str, FrozenSet[int]]) -> Tuple[bool, List[str]]:
    """Gate 0/1-style validity: every region has size >= 4, no region is
    a subset of another, and every one of the six unordered pairs
    properly crosses (boolean_crossing_diagnostic.properly_crosses)."""
    problems = []
    for name, region in regions.items():
        if len(region) < 4:
            problems.append(f"{name} has size {len(region)} < 4")
    for a in regions:
        for b in regions:
            if a != b and regions[a] <= regions[b]:
                problems.append(f"{a} subset of {b}")
    for a, b in PAIRS:
        if not properly_crosses(regions[a], regions[b]):
            problems.append(f"{a},{b} do not properly cross")
    return not problems, problems


def check_triple_overlaps_singleton_and_equal(regions: Dict[str, FrozenSet[int]]) -> Tuple[bool, Dict[str, FrozenSet[int]]]:
    """Verifies every theta-triple overlap is a genuine singleton AND all
    four coincide -- the repeated-triple-support condition this whole
    diagnostic depends on."""
    overlaps = {}
    for seam, (xk, yk, zk) in THETA.items():
        overlaps[seam] = regions[xk] & regions[yk] & regions[zk]
    ok = all(len(o) == 1 for o in overlaps.values()) and len(set(overlaps.values())) == 1
    return ok, overlaps


def triple_support(X: FrozenSet[int], Y: FrozenSet[int], Z: FrozenSet[int]) -> FrozenSet[int]:
    return X & Y & Z


def all_carrier_coordinates(regions: Dict[str, FrozenSet[int]]) -> List[CarrierCoordinate]:
    """The rho_{A,T} keys referenced across all four triples, in
    first-seen order: one (X,T) and one (Z,T) key per seam -- same
    Candidate 3b rule as candidate_discipline_diagnostic.py, parameterised
    over the cover so it can be rerun on any repeated-support geometry."""
    keys: List[CarrierCoordinate] = []
    seen = set()
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = regions[xk], regions[yk], regions[zk]
        T = triple_support(X, Y, Z)
        for key in (carrier_key(X, T), carrier_key(Z, T)):
            if key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


def build_candidate_R(
    regions: Dict[str, FrozenSet[int]]
) -> Tuple[List[List[Fraction]], List[CarrierCoordinate], List[Tuple[str, str]]]:
    """R for Candidate 3b: mu_UV = mu_VW = 0, mu_U_VvW = rho_{X,T},
    mu_UvV_W = rho_{Z,T}, built via the shared infrastructure's build_R."""
    slots = all_slot_coordinates()
    carrier_coords = all_carrier_coordinates(regions)
    rule: Dict[Tuple[str, str], Dict[CarrierCoordinate, Fraction]] = {}
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = regions[xk], regions[yk], regions[zk]
        T = triple_support(X, Y, Z)
        rule[(seam, "U_VvW")] = {carrier_key(X, T): Fraction(1)}
        rule[(seam, "UvV_W")] = {carrier_key(Z, T): Fraction(1)}
    R = build_R(rule, carrier_coords, slots)
    return R, carrier_coords, slots


def induced_B(
    regions: Dict[str, FrozenSet[int]]
) -> Tuple[List[List[Fraction]], List[CarrierCoordinate], List[str]]:
    """B = D . R for Candidate 3b on the given cover, via the frozen
    infrastructure -- not a hand-derived matrix."""
    D, slots, seams = delta_matrix()
    R, carrier_coords, _ = build_candidate_R(regions)
    B = compose_B(D, R)
    return B, carrier_coords, seams


def residue_for(regions: Dict[str, FrozenSet[int]], rho: Dict[CarrierCoordinate, Fraction]) -> List[Fraction]:
    """Runs the REAL generator (compute_seam_residue, internally
    cross-checked against closed_form_delta) directly from a rho
    assignment -- an independent path from induced_B(), used to verify
    the abstract D/R composition actually matches the real code."""
    residues = {}
    for seam, (xk, yk, zk) in THETA.items():
        X, Y, Z = regions[xk], regions[yk], regions[zk]
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


def verify_B_matches_real_generator(regions: Dict[str, FrozenSet[int]]) -> bool:
    """Basis-probes the real generator (residue_for, one unit rho at a
    time) and checks it matches induced_B() column for column."""
    B, carrier_coords, seams = induced_B(regions)
    for col_idx, key in enumerate(carrier_coords):
        rho = {key: Fraction(1)}
        real_col = residue_for(regions, rho)
        abstract_col = [B[row][col_idx] for row in range(len(B))]
        if real_col != abstract_col:
            return False
    return True


def verify_reduction_against_real_code(
    regions: Dict[str, FrozenSet[int]], seam: str, trials: int = 8, seed: int = 20260711
) -> bool:
    """Spot-checks Delta_e = rho_{X,T} - rho_{Z,T} against
    compute_seam_residue directly, under random rational rho values."""
    rng = random.Random(seed)
    xk, yk, zk = THETA[seam]
    X, Y, Z = regions[xk], regions[yk], regions[zk]
    T = triple_support(X, Y, Z)
    kx, kz = carrier_key(X, T), carrier_key(Z, T)
    for _ in range(trials):
        rho = {
            kx: Fraction(rng.randint(-5, 5), rng.randint(1, 3)),
            kz: Fraction(rng.randint(-5, 5), rng.randint(1, 3)),
        }
        real_r = residue_for(regions, rho)[SEAMS.index(seam)]
        claimed_r = rho[kx] - rho[kz]
        if real_r != claimed_r:
            return False
    return True


def _rank_of(vectors: List[List[Fraction]]) -> int:
    if not vectors:
        return 0
    return len(vectors) - len(nullspace_over_Q(transpose(vectors)))


def diagnose(regions: Dict[str, FrozenSet[int]] = CANONICAL_REGIONS) -> dict:
    """Sharing check, rank(B), and the realisable-obstruction quotient
    relative to im(delta0) -- same computation pattern as
    lattice_ie_diagnostic.diagnose() and candidate_discipline_diagnostic.
    diagnose(), parameterised over the cover under test."""
    nondeg_ok, nondeg_problems = check_nondegenerate(regions)
    overlaps_ok, overlaps = check_triple_overlaps_singleton_and_equal(regions)

    B, carrier_coords, seams = induced_B(regions)
    B_columns = transpose(B)
    delta0_columns = [
        mat_vec(COARSE_D0, [Fraction(1) if i == j else Fraction(0) for i in range(4)])
        for j in range(4)
    ]

    rank_B = _rank_of(B_columns)
    rank_delta0 = _rank_of(delta0_columns)
    rank_union = _rank_of(B_columns + delta0_columns)
    dim_intersection = rank_B + rank_delta0 - rank_union
    dim_quotient_raw = rank_B - dim_intersection
    full_rank = rank_B == len(B)

    sharing_results = surviving_coordinate_sharing_check(B, carrier_coords, seams)
    summary = sharing_check_summary(sharing_results)

    return {
        "nondegenerate": nondeg_ok,
        "nondegenerate_problems": nondeg_problems,
        "triple_overlaps_singleton_and_equal": overlaps_ok,
        "triple_overlaps": overlaps,
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
        "B_matches_real_generator": verify_B_matches_real_generator(regions),
        "reduction_verified_e12": verify_reduction_against_real_code(regions, "e12"),
        "reduction_verified_e34": verify_reduction_against_real_code(regions, "e34"),
    }


def _build_enriched_cover(extra_private: int, extra_pairwise: int, seed: int) -> Dict[str, FrozenSet[int]]:
    """Builds a more richly-populated repeated-triple-support cover than
    CANONICAL_REGIONS, for richness_invariance_check() below. Same
    construction shape (global point + private points + pairwise-only
    points, each pairwise point confined to exactly its two regions so no
    triple overlap is ever contaminated), with more points per region."""
    rng = random.Random(seed)
    counter = [0]

    def fresh():
        counter[0] += 1
        return counter[0]

    t = 0
    regions = {f"U{i}": {t} for i in range(1, 5)}
    for i in range(1, 5):
        for _ in range(extra_private):
            regions[f"U{i}"].add(fresh())
    for a, b in PAIRS:
        for _ in range(extra_pairwise):
            pt = fresh()
            regions[a].add(pt)
            regions[b].add(pt)
    return {k: frozenset(v) for k, v in regions.items()}


def richness_invariance_check(trials: Tuple[Tuple[int, int, int], ...] = (
    (1, 1, 100), (2, 1, 101), (1, 2, 102), (2, 2, 103), (3, 2, 104), (2, 3, 105),
)) -> bool:
    """Reruns diagnose() on several more-enriched covers (up to |Ui|=12)
    and confirms the rank/quotient/verdict never change from
    CANONICAL_REGIONS -- the claim that this result depends only on
    theta-role incidence and the shared support point, not on cover
    richness, checked directly rather than argued by hand."""
    baseline = diagnose(CANONICAL_REGIONS)
    for extra_private, extra_pairwise, seed in trials:
        regions = _build_enriched_cover(extra_private, extra_pairwise, seed)
        result = diagnose(regions)
        if not result["nondegenerate"] or not result["triple_overlaps_singleton_and_equal"]:
            return False
        if (result["rank_B"], result["dim_intersection"], result["dim_quotient_raw"], result["verdict"], result["sharing_summary"]) != \
           (baseline["rank_B"], baseline["dim_intersection"], baseline["dim_quotient_raw"], baseline["verdict"], baseline["sharing_summary"]):
            return False
    return True


def print_report() -> None:
    result = diagnose()
    print("Repeated triple-support diagnostic: Candidate 3b on a repeated-support cover")
    print(f"  canonical cover non-degenerate: {result['nondegenerate']}")
    print(f"  triple overlaps singleton and all-equal: {result['triple_overlaps_singleton_and_equal']}  {result['triple_overlaps']}")
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
    print(f"  opposite-pair sharing forces global sharing (structural fact): {verify_opposite_pair_sharing_forces_global()}")
    print(f"  richness invariance (6 enriched covers up to |Ui|=12): {richness_invariance_check()}")
    print()
    print(f"  VERDICT: {result['verdict']}")


if __name__ == "__main__":
    print_report()
