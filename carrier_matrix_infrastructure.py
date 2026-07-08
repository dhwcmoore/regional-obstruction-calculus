#!/usr/bin/env python3
"""
carrier_matrix_infrastructure.py

Reusable machinery for testing coupled outer-slot disciplines, factored
out after the ordered inclusion-exclusion diagnostic (`3ad4bbd`,
docs/LATTICE_IE_DIAGNOSTIC.md) showed that "globally indexed" is not
enough: a candidate rule can be genuinely shared at the parameter level
and still collapse to seam-local independence if the associator formula
cancels exactly the shared terms. This module makes that check
executable and reusable, instead of re-deriving it by hand for every new
candidate.

This file defines infrastructure only. It does not test any candidate
outer-slot discipline -- see candidate_discipline_diagnostic.py (a
separate, later file) for that. The tests here
(tests/test_carrier_matrix_infrastructure.py) use toy matrices with known
answers, not real seam-residue data, so the infrastructure can be trusted
on its own terms before anything leans on it.

The matrix pipeline, frozen here
----------------------------------
    Carrier K --[R]--> Slots S --[D]--> Seam residues E

Carrier coordinates K
    Global ordered pairs of canonical supports:
        k = (A, B), A and B frozensets of points in the shared universe.
    Two coordinates are the same iff their frozensets are equal --
    canonical by construction, not by convention that has to be
    remembered at each call site.

Slot coordinates S
    One coordinate per (seam, slot) pair, slot in {UV, VW, U_VvW, UvV_W}
    -- the four real SeamCorrectionData fields. For four seams,
    dim(S) = 16.

Restriction matrix R : Q^K -> Q^S
    Encodes ONE candidate outer-slot discipline: for each slot, which
    carrier coordinates populate it and with what rational coefficient.
    This is where a specific rule (inclusion-exclusion, or anything else)
    gets encoded -- this module provides build_R() to construct it from a
    plain dict, not a hard-coded rule.

Delta matrix D : Q^S -> Q^E
    Fixed and verified, not a design choice: the four-term closed form

        Delta_e = mu_VW - mu_UvV_W + mu_U_VvW - mu_UV

    that regional_composition.closed_form_delta already cross-checks
    against literal associator expansion on every call elsewhere in this
    repository. delta_matrix() below encodes exactly those coefficients
    (UV -> -1, VW -> +1, U_VvW -> +1, UvV_W -> -1), and
    verify_delta_matches_closed_form() checks this encoding against the
    real regional_composition.closed_form_delta function directly, under
    random rational inputs -- not trusted from the coefficient table
    alone.

Induced generator B = D . R : Q^K -> Q^E
    The actual object to basis-probe and diagnose, for any candidate R.

Surviving-coordinate sharing check
    The `3ad4bbd` lesson made executable: for every carrier coordinate
    whose column in B is nonzero, that column's support (which seam rows
    are nonzero) must include at least two seams, or the coordinate is
    flagged as private residual freedom, not genuine sharing. This is a
    necessary, not sufficient, condition -- passing it does not by itself
    mean a candidate discipline is "useful"; rank and the im(delta^0)
    quotient still have to be computed separately (see
    candidate_discipline_diagnostic.py once it exists).

No quotient type anywhere in this module. The quotient (im(B) modulo
im(delta^0)) belongs only at the final obstruction-class computation, not
baked into the carrier representation -- keeping the raw incidence trail
auditable is the point.
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, FrozenSet, List, Tuple

SEAMS: Tuple[str, ...] = ("e12", "e23", "e34", "e14")
SLOT_NAMES: Tuple[str, ...] = ("UV", "VW", "U_VvW", "UvV_W")

CarrierCoordinate = Tuple[FrozenSet[int], FrozenSet[int]]
SlotCoordinate = Tuple[str, str]  # (seam, slot_name)

# The verified closed-form coefficients (regional_composition.closed_form_delta):
#     Delta = mu_VW - mu_UvV_W + mu_U_VvW - mu_UV
_SLOT_COEFFICIENT = {
    "UV": Fraction(-1),
    "VW": Fraction(1),
    "U_VvW": Fraction(1),
    "UvV_W": Fraction(-1),
}


def carrier_key(A: FrozenSet[int], B: FrozenSet[int]) -> CarrierCoordinate:
    """Canonical carrier coordinate: the same (A, B) always resolves to
    the same key, regardless of how the caller built the frozensets."""
    return (frozenset(A), frozenset(B))


@dataclass(frozen=True)
class SharedCarrierCoordinate:
    """
    A proof-carrying record for one carrier coordinate -- deliberately a
    plain validated dataclass, not a quotient type (see module docstring
    for why). Metadata fields are optional documentation, not consumed by
    the matrix machinery itself; they exist so a printed report can show
    *why* a coordinate exists, not just that it does.
    """
    key: CarrierCoordinate
    source_expressions: Tuple[str, ...] = field(default_factory=tuple)
    incident_seams: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        A, B = self.key
        if not isinstance(A, frozenset) or not isinstance(B, frozenset):
            raise TypeError("SharedCarrierCoordinate.key must be a pair of frozensets")


def all_slot_coordinates() -> List[SlotCoordinate]:
    return [(seam, slot) for seam in SEAMS for slot in SLOT_NAMES]


def delta_matrix() -> Tuple[List[List[Fraction]], List[SlotCoordinate], List[str]]:
    """
    D : Q^S -> Q^E, block-diagonal across seams (each seam's residue
    depends only on that seam's own four slots). Returns (D, slot_labels,
    seam_labels) with D as len(SEAMS) rows x len(slots) columns.
    """
    slots = all_slot_coordinates()
    D = []
    for target_seam in SEAMS:
        row = [
            _SLOT_COEFFICIENT[slot_name] if seam == target_seam else Fraction(0)
            for seam, slot_name in slots
        ]
        D.append(row)
    return D, slots, list(SEAMS)


def verify_delta_matches_closed_form(trials: int = 8, seed: int = 20260709) -> bool:
    """
    Checks delta_matrix()'s encoding against regional_composition.
    closed_form_delta directly, under random rational slot values, for
    one seam -- not trusted from the coefficient table alone. This ties
    the abstract D matrix back to the same closed form every other
    diagnostic in this repository cross-checks against literal
    associator expansion.
    """
    import random
    from regional_composition import SeamCorrectionData, closed_form_delta
    from rational_linear_algebra import mat_vec

    D, slots, seams = delta_matrix()
    rng = random.Random(seed)
    seam = "e12"
    seam_slot_indices = [i for i, (e, _) in enumerate(slots) if e == seam]
    row_idx = seams.index(seam)

    for _ in range(trials):
        values = {slots[i][1]: Fraction(rng.randint(-5, 5), rng.randint(1, 3)) for i in seam_slot_indices}
        s_vec = [Fraction(0)] * len(slots)
        for i in seam_slot_indices:
            s_vec[i] = values[slots[i][1]]
        d_result = mat_vec(D, s_vec)[row_idx]
        expected = closed_form_delta(SeamCorrectionData(
            mu_VW=values["VW"], mu_UvV_W=values["UvV_W"],
            mu_U_VvW=values["U_VvW"], mu_UV=values["UV"],
        ))
        if d_result != expected:
            return False
    return True


def build_R(
    slot_rule: Dict[SlotCoordinate, Dict[CarrierCoordinate, Fraction]],
    carrier_coords: List[CarrierCoordinate],
    slots: List[SlotCoordinate],
) -> List[List[Fraction]]:
    """
    R : Q^K -> Q^S, as a dense matrix (rows = slots, cols = carrier
    coordinates), built from a sparse rule: slot_rule[slot] is a dict
    mapping carrier coordinates to their rational coefficient in that
    slot's population formula. Coordinates absent from a slot's dict
    contribute 0 -- callers do not need to enumerate every (slot, key)
    pair, only the nonzero ones.
    """
    R = []
    for slot in slots:
        row_rule = slot_rule.get(slot, {})
        R.append([row_rule.get(k, Fraction(0)) for k in carrier_coords])
    return R


def compose_B(D: List[List[Fraction]], R: List[List[Fraction]]) -> List[List[Fraction]]:
    """B = D . R : Q^K -> Q^E, the actual induced generator for a
    candidate discipline. Plain matrix multiplication -- promoted here
    rather than reimplemented, from rational_linear_algebra.mat_mat."""
    from rational_linear_algebra import mat_mat
    return mat_mat(D, R)


def surviving_coordinate_sharing_check(
    B: List[List[Fraction]], carrier_coords: List[CarrierCoordinate], seams: List[str]
) -> Dict[CarrierCoordinate, dict]:
    """
    The `3ad4bbd` lesson made executable. For every carrier coordinate
    (column of B): if the column is entirely zero, it never reaches a
    residue at all. If nonzero in exactly one seam row, it is a
    *surviving private residual coordinate* -- globally indexed, but not
    actually shared once Delta has done its cancellation, exactly the
    inclusion-exclusion failure mode. If nonzero in two or more seam
    rows, it is genuinely shared.

    This is a necessary, not sufficient, condition for a candidate
    discipline to be structurally useful -- see module docstring.
    """
    results = {}
    for col_idx, k in enumerate(carrier_coords):
        col = [B[row][col_idx] for row in range(len(B))]
        nonzero_seams = [seams[r] for r in range(len(col)) if col[r] != 0]
        if not nonzero_seams:
            status = "zero_column"
        elif len(nonzero_seams) == 1:
            status = "private_residual"
        else:
            status = "genuinely_shared"
        results[k] = {"status": status, "nonzero_seams": nonzero_seams}
    return results


def sharing_check_summary(results: Dict[CarrierCoordinate, dict]) -> Dict[str, int]:
    """Counts of each status, for a quick pass/fail read without
    inspecting every coordinate by hand."""
    summary = {"zero_column": 0, "private_residual": 0, "genuinely_shared": 0}
    for r in results.values():
        summary[r["status"]] += 1
    return summary
