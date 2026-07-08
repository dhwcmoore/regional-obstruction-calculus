#!/usr/bin/env python3
"""
repair_solver.py

Obstruction-language wrapper around the exact rational solver in
rational_linear_algebra.py, framed in the associator-field vocabulary of
Section "Detection, repair, and obstruction": given a seam residue r
(closed, since delta^1 = 0 on the four-cycle nerve), can it be absorbed by
admissible boundary corrections b, i.e. is r = delta^0 b?

This does not reimplement the linear algebra -- it reuses
rational_linear_algebra.solve_over_Q and .dot exactly as
residue_classifier.py and refinement_checker.py do, so all three pipelines
(declared-residue classifier, refinement witnesses, associator-generated
residue) run on the same audited exact-rational core.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional

from rational_linear_algebra import dot, is_zero, mat_vec, solve_over_Q

VERDICT_GLOBALLY_REPAIRABLE = "globally_repairable"
VERDICT_NONTRIVIAL_OBSTRUCTION = "nontrivial_associator_obstruction"
VERDICT_INVALID_RESIDUE = "invalid_residue"
VERDICT_DEGENERATE_INPUT = "degenerate_input"


@dataclass(frozen=True)
class RepairResult:
    repairable: bool
    correction: Optional[List[Fraction]]
    obstruction_pairing: Optional[Fraction]
    verdict: str


def attempt_repair(
    coboundary_0: List[List[Fraction]],
    residue: List[Fraction],
    cycle: List[Fraction],
    coboundary_1: Optional[List[List[Fraction]]] = None,
) -> RepairResult:
    """
    Attempt to repair (absorb) `residue` by admissible boundary corrections,
    i.e. solve delta^0 b = residue over Q, and independently certify
    non-removability, when it holds, by the cycle pairing <cycle, residue>
    (Lemma lem:cycle-pairing). `coboundary_1` defaults to the empty map
    (C^2 = 0, as in the four-cycle nerve of Section 7); when supplied, a
    residue that is not closed (delta^1 r != 0) is reported as
    `invalid_residue`, since Theorem thm:classifier-soundness only classifies
    closed residues.
    """
    if not coboundary_0 or not coboundary_0[0]:
        return RepairResult(False, None, None, VERDICT_DEGENERATE_INPUT)
    n_edges = len(coboundary_0)
    if len(residue) != n_edges or len(cycle) != n_edges:
        return RepairResult(False, None, None, VERDICT_DEGENERATE_INPUT)

    if coboundary_1:
        d1r = mat_vec(coboundary_1, residue)
        if not is_zero(d1r):
            return RepairResult(False, None, None, VERDICT_INVALID_RESIDUE)

    repairable, b = solve_over_Q(coboundary_0, residue)
    pairing = dot(cycle, residue)

    if repairable:
        return RepairResult(True, b, pairing, VERDICT_GLOBALLY_REPAIRABLE)
    return RepairResult(False, None, pairing, VERDICT_NONTRIVIAL_OBSTRUCTION)
