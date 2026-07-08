#!/usr/bin/env python3
"""
coupled_realisability_diagnostic.py

The first concrete test of the architectural correction specified in
docs/COUPLED_GENERATOR_SPEC.md: a genuinely coupled first-order associator
generator for the four-region cycle, built from one shared point universe
(no seam instantiates a private VennTriple), diagnosed by exact rational
basis probing exactly as realisability_diagnostic.py diagnosed the
independent generator.

The shared regional cover
--------------------------
One point universe P = {a, b, c, d, p1, p2, p3, p4}, with:

    U1 = {a, c, d, p1}      U2 = {a, b, d, p2}
    U3 = {a, b, c, p3}      U4 = {b, c, d, p4}

chosen so that each of the four cyclic-consecutive triples has a genuine
single-point overlap:

    U1 n U2 n U3 = {a}      U2 n U3 n U4 = {b}
    U3 n U4 n U1 = {c}      U4 n U1 n U2 = {d}

(checked computationally below, not assumed). This forces the "diagonal"
pairs U1 n U3 and U2 n U4 to be non-empty too ({a,c} and {b,d}
respectively) -- an unavoidable consequence of requiring all four cyclic
triple-overlaps to be genuine single points in one shared universe, not a
modelling choice. The associator formula for a single triple (X,Y,Z)
never references the far pair X n Z directly (see
regional_composition.associator_defect), so this forced diagonal
structure does not, by itself, introduce a "diagonal" correction
parameter.

theta (explicit, as required by the spec)
------------------------------------------
    theta(e12) = (U1, U2, U3)      theta(e23) = (U2, U3, U4)
    theta(e34) = (U3, U4, U1)      theta(e41) = (U4, U1, U2)

Design choice under test: adjacent-overlap sharing, outer slots zero
----------------------------------------------------------------------
For triple theta(e) = (X, Y, Z), the four SeamCorrectionData slots are
set as:

    mu_UV = the shared parameter for overlap X n Y
    mu_VW = the shared parameter for overlap Y n Z
    mu_U_VvW = 0   (outer slot, fixed -- not shared, not free)
    mu_UvV_W = 0   (outer slot, fixed -- not shared, not free)

This is one specific, falsifiable choice among the open questions
docs/COUPLED_GENERATOR_SPEC.md section 7 deliberately left open -- not a
claim that it is the right one. The result below shows it is not: see
"Result" below.

No seam instantiates its own VennTriple; every seam's triple is built
from the four shared region objects above, and mu_VW's diagnostic
run continues to cross-check the literal associator expansion against
regional_composition.closed_form_delta on every call (inside
associator_residue.compute_seam_residue), exactly as it does for the
independent generator.

Result
------
The induced matrix B (rows = seam residues r12,r23,r34,r41 in this
script's own cyclic e41 convention -- U4->U1, not the paper's e14 -- so
comparisons to the paper's displayed residue need an orientation flip on
the last coordinate, done explicitly in tests) from mu=(mu12,mu23,mu34,mu41)
is exactly the cyclic difference operator:

    r12 = -mu12 + mu23
    r23 = -mu23 + mu34
    r34 = -mu34 + mu41
    r41 =  mu12 - mu41

rank(B) = 3, a genuine rank drop from the independent generator's full
rank 4. But image(B) is exactly im(delta^0) of this same cyclic graph
(verified: every basis column of B lies in im(delta^0), and the ranks
match, so containment plus equal dimension gives equality) -- so the
realisable-obstruction quotient im(B) / (im(B) n im(delta^0)) is
zero-dimensional. Every residue this construction can produce is already
repairable. The rank drop is real; it is cohomologically empty.

Why: with the outer slots pinned to zero, each r_e reduces to exactly
mu_next - mu_prev around the cycle -- literally the discrete gradient of
the mu's read as a 0-cochain on the same graph. A discrete gradient is a
coboundary by construction. Adjacency-only mu, with outer slots zero,
produces gradients, not curvature. The outer correction slots are
load-bearing, not cosmetic; this diagnostic does not attempt to share
them (see docs/REALISABILITY_ROADMAP.md for what's still open).

USAGE:
    python coupled_realisability_diagnostic.py
"""

from fractions import Fraction
from typing import Dict, List, Tuple

from regional_composition import VennTriple, SeamCorrectionData
from associator_residue import SeamAssociatorInstance, compile_residue
from rational_linear_algebra import nullspace_over_Q, transpose, in_span_over_Q, mat_vec

SEAM_ORDER = ("e12", "e23", "e34", "e41")
PARAM_ORDER = ("mu12", "mu23", "mu34", "mu41")

# --- The shared regional cover: one point universe, regions as subsets ---
_a, _b, _c, _d = 1, 2, 3, 4
_p1, _p2, _p3, _p4 = 11, 12, 13, 14

REGIONS: Dict[str, frozenset] = {
    "U1": frozenset({_a, _c, _d, _p1}),
    "U2": frozenset({_a, _b, _d, _p2}),
    "U3": frozenset({_a, _b, _c, _p3}),
    "U4": frozenset({_b, _c, _d, _p4}),
}

THETA: Dict[str, Tuple[str, str, str]] = {
    "e12": ("U1", "U2", "U3"),
    "e23": ("U2", "U3", "U4"),
    "e34": ("U3", "U4", "U1"),
    "e41": ("U4", "U1", "U2"),
}

_OVERLAP_PARAM = {
    ("U1", "U2"): "mu12", ("U2", "U1"): "mu12",
    ("U2", "U3"): "mu23", ("U3", "U2"): "mu23",
    ("U3", "U4"): "mu34", ("U4", "U3"): "mu34",
    ("U4", "U1"): "mu41", ("U1", "U4"): "mu41",
}


def check_shared_cover() -> None:
    """Verifies the claims in the module docstring computationally --
    every cyclic triple overlap is a genuine single point -- rather than
    assuming them. Raises AssertionError if the region construction above
    is ever edited into an inconsistent state."""
    for seam, (x, y, z) in THETA.items():
        overlap = REGIONS[x] & REGIONS[y] & REGIONS[z]
        assert len(overlap) == 1, f"theta({seam})={x,y,z}: triple overlap {overlap} is not a single point"


def _zero_mu() -> Dict[str, Fraction]:
    return {p: Fraction(0) for p in PARAM_ORDER}


def _seam_correction(seam: str, shared_mu: Dict[str, Fraction]) -> SeamCorrectionData:
    """Builds this seam's SeamCorrectionData from the SHARED mu dict alone.
    mu_UV/mu_VW are read off the shared adjacent-overlap parameters; the
    two outer slots are fixed at zero (the design choice under test --
    see module docstring)."""
    x, y, z = THETA[seam]
    return SeamCorrectionData(
        mu_VW=shared_mu[_OVERLAP_PARAM[(y, z)]],
        mu_UvV_W=Fraction(0),
        mu_U_VvW=Fraction(0),
        mu_UV=shared_mu[_OVERLAP_PARAM[(x, y)]],
    )


def _instances_for(shared_mu: Dict[str, Fraction]) -> List[SeamAssociatorInstance]:
    instances = []
    for seam in SEAM_ORDER:
        x, y, z = THETA[seam]
        triple = VennTriple(U=REGIONS[x], V=REGIONS[y], W=REGIONS[z])
        instances.append(SeamAssociatorInstance(seam=seam, mu=_seam_correction(seam, shared_mu), triple=triple))
    return instances


def residue_for(shared_mu: Dict[str, Fraction]) -> List[Fraction]:
    """Runs the real, literal-expansion-verified generator (compile_residue,
    cross-checked against closed_form_delta on every call inside
    compute_seam_residue) on the given shared parameters -- no hand
    derivation."""
    by_seam = compile_residue(_instances_for(shared_mu))
    return [by_seam[s] for s in SEAM_ORDER]


def coupled_columns() -> Tuple[List[List[Fraction]], List[str]]:
    """The 4 basis-probing columns of B, one per shared overlap parameter,
    each computed by actually running the generator on that parameter's
    unit vector."""
    columns = []
    for p in PARAM_ORDER:
        mu = _zero_mu()
        mu[p] = Fraction(1)
        columns.append(residue_for(mu))
    return columns, list(PARAM_ORDER)


def coupled_matrix() -> Tuple[List[List[Fraction]], List[str]]:
    columns, labels = coupled_columns()
    return transpose(columns), labels


def _cyclic_delta0() -> List[List[Fraction]]:
    """delta^0 for the SAME cyclic graph, in this script's own orientation
    (e12:U1->U2, e23:U2->U3, e34:U3->U4, e41:U4->U1, all 'forward') --
    not the paper's e14:U1->U4 convention. Used only to compare against
    im(B); see tests for the explicit orientation flip needed to compare
    against the paper's displayed residue."""
    vertices = ["U1", "U2", "U3", "U4"]
    edges = [("U1", "U2"), ("U2", "U3"), ("U3", "U4"), ("U4", "U1")]
    idx = {v: i for i, v in enumerate(vertices)}
    delta0 = []
    for src, tgt in edges:
        row = [Fraction(0)] * 4
        row[idx[src]] = Fraction(-1)
        row[idx[tgt]] = Fraction(1)
        delta0.append(row)
    return delta0


def _rank(vectors: List[List[Fraction]]) -> int:
    """Rank of a list of vectors (each the same length), by exact
    nullspace computation -- no floating-point SVD or determinant."""
    if not vectors:
        return 0
    mat = transpose(vectors)  # dim x n
    ker = nullspace_over_Q(mat)
    return len(vectors) - len(ker)


def diagnose() -> dict:
    """
    Computes rank(B), compares image(B) to im(delta^0) of the same
    cyclic graph, and computes the realisable-obstruction quotient
    dimension exactly:

        dim(im(B) n im(delta0)) = rank(B) + rank(delta0) - rank(B union delta0 columns)
        dim(quotient)            = rank(B) - dim(im(B) n im(delta0))

    This does not assume im(B) subseteq im(delta0); it computes the
    intersection dimension generally, so the same function is reusable
    for a future construction where that containment might fail.
    """
    check_shared_cover()
    B, labels = coupled_matrix()
    B_columns, _ = coupled_columns()
    delta0 = _cyclic_delta0()
    delta0_columns = transpose(delta0)  # delta0 is 4x4 (edges x vertices); columns = per-vertex images

    rank_B = _rank(B_columns)
    rank_delta0 = _rank(delta0_columns)
    rank_union = _rank(B_columns + delta0_columns)
    dim_intersection = rank_B + rank_delta0 - rank_union
    dim_quotient = rank_B - dim_intersection

    every_column_in_im_delta0 = all(in_span_over_Q(delta0_columns, col) for col in B_columns)

    return {
        "n_params": len(labels),
        "dim_C1": len(B),
        "rank_B": rank_B,
        "rank_delta0": rank_delta0,
        "dim_intersection": dim_intersection,
        "dim_quotient": dim_quotient,
        "image_B_subseteq_image_delta0": every_column_in_im_delta0,
        "image_B_equals_image_delta0": every_column_in_im_delta0 and rank_B == rank_delta0,
        "column_labels": labels,
    }


def print_report() -> None:
    result = diagnose()
    print("Coupled realisability diagnostic: shared adjacent-overlap mu, outer slots zero")
    print(f"  parameters: {result['n_params']} (mu12, mu23, mu34, mu41)")
    print(f"  dim C^1(N;Q): {result['dim_C1']}")
    print(f"  rank(B): {result['rank_B']}")
    print(f"  rank(delta^0) of the same graph: {result['rank_delta0']}")
    print(f"  image(B) subseteq image(delta^0)? {result['image_B_subseteq_image_delta0']}")
    print(f"  image(B) == image(delta^0)? {result['image_B_equals_image_delta0']}")
    print(f"  dim(realisable obstruction quotient): {result['dim_quotient']}")
    if result["dim_quotient"] == 0:
        print()
        print("  COHOMOLOGICAL COLLAPSE: the rank drop is real, but the entire image")
        print("  is already-repairable residues. This coupling produces gradients,")
        print("  not curvature. See docs/REALISABILITY_ROADMAP.md.")


if __name__ == "__main__":
    print_report()
