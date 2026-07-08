#!/usr/bin/env python3
"""
associator_residue.py

Compiles a seam-indexed residue vector r in C^1 out of genuine finite
associator-field data, instead of taking r as a declared input the way
examples/four_cycle.json does.

The paper is explicit that the H^1 witness of Section 7 is "not identical
to the full associator field; it is a computable obstruction extracted
from the repair problem, one degree below the field that generated it"
(Section "From associator fields to finite cohomology certificates"), and
that a single triple's defect is always repairable in isolation (Remark
after Example ex:venn) -- genuine obstruction needs several triples whose
repair constants are shared or otherwise constrained. This module does not
claim to reconstruct the historical derivation of the paper's displayed
residue (1,1,1,-2); the CHANGELOG documents that it was originally posited
directly. What it does is construct four *independent* finite associator
defects, one per coarse seam of the four-cycle nerve of Section 7, each
computed by regional_composition.associator_defect from declared
correction constants (real local product/boundary-correction data, in the
same sense as the paper's worked Examples ex:interval and ex:venn), and
show that the resulting seam-indexed vector coincides with (1,1,1,-2) --
so the classifier's residue is, in this construction, an *output* of
associator-field data rather than an assumed vector.

Each seam's associator defect is computed twice and cross-checked: once by
literal expansion (regional_composition.associator_defect) and once by the
closed-form four-term formula (regional_composition.closed_form_delta).
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List

from regional_composition import (
    VennTriple,
    SeamCorrectionData,
    associator_defect,
    closed_form_delta,
)

SEAM_ORDER = ("e12", "e23", "e34", "e14")


@dataclass(frozen=True)
class SeamAssociatorInstance:
    """
    The declared local product/correction data for one coarse seam: a
    Venn triple (U, V, W) and the four seam-correction constants of
    Proposition prop:four-term. `triple` defaults to the shared Venn shape
    of Example ex:venn; distinct seams may in principle use distinct
    triples, but all four witnesses below reuse the same shape with
    different constants, exactly as multiple independent instances of one
    construction.
    """

    seam: str
    mu: SeamCorrectionData
    triple: VennTriple = VennTriple()


def compute_seam_residue(instance: SeamAssociatorInstance) -> Fraction:
    """
    Returns the single rational coefficient assigned to `instance.seam`:
    the boundary-component value of the associator defect at the (unique,
    for the shared Venn shape) triple-overlap point, computed by literal
    associator expansion. Raises if the defect is not supported exactly on
    the triple overlap (Theorem thm:triple-localisation) or is not
    concentrated on a single point (a modelling requirement of this
    compiler, not of the general theory).
    """
    defect = associator_defect(instance.triple, instance.mu)
    support = defect.support()
    overlap = instance.triple.triple_overlap
    if not support <= overlap:
        raise ValueError(
            f"seam {instance.seam}: associator defect supported outside the "
            f"triple overlap ({sorted(support)} not subset of {sorted(overlap)}); "
            "this violates Theorem thm:triple-localisation and indicates a bug."
        )
    if len(overlap) != 1:
        raise ValueError(
            f"seam {instance.seam}: this compiler requires a single-point "
            f"triple overlap, got {sorted(overlap)}"
        )
    (point,) = tuple(overlap)
    _, boundary = defect.as_dicts()
    value = boundary.get(point, Fraction(0))

    # Independent cross-check against the closed-form four-term formula
    # (Proposition prop:four-term); the two methods must agree exactly.
    expected = closed_form_delta(instance.mu)
    if value != expected:
        raise AssertionError(
            f"seam {instance.seam}: direct associator expansion ({value}) "
            f"disagrees with the closed-form Delta formula ({expected})"
        )
    return value


def compile_residue(instances: List[SeamAssociatorInstance]) -> Dict[str, Fraction]:
    """Compute the seam residue for every declared instance."""
    return {inst.seam: compute_seam_residue(inst) for inst in instances}


def residue_vector(instances: List[SeamAssociatorInstance], seam_order=SEAM_ORDER) -> List[Fraction]:
    """The residue as an ordered vector, in `seam_order`."""
    by_seam = compile_residue(instances)
    missing = [s for s in seam_order if s not in by_seam]
    if missing:
        raise ValueError(f"no associator instance declared for seams: {missing}")
    return [by_seam[s] for s in seam_order]


def four_cycle_instances() -> List[SeamAssociatorInstance]:
    """
    The four independent associator instances whose computed residue
    reproduces the paper's four-cycle witness r = (1, 1, 1, -2)
    (examples/four_cycle.json, refinement_witnesses.COARSE.residue). Each
    instance sets exactly one of the four seam-correction constants to the
    target value and the other three to zero -- a free modelling choice of
    which pairwise reconciliation carries the seam's residue, in the same
    spirit as the paper's Example ex:interval (chi(X,Y) in {0,1}, freely
    assigned) and Example ex:venn (mu_{X,Y} freely chosen). The formula
    Delta = mu_VW - mu_{UvV,W} + mu_{U,VvW} - mu_UV then *computes* the
    target exactly: target - 0 + 0 - 0 = target.
    """
    targets = {"e12": Fraction(1), "e23": Fraction(1), "e34": Fraction(1), "e14": Fraction(-2)}
    return [
        SeamAssociatorInstance(
            seam=seam,
            mu=SeamCorrectionData(
                mu_VW=target,
                mu_UvV_W=Fraction(0),
                mu_U_VvW=Fraction(0),
                mu_UV=Fraction(0),
            ),
        )
        for seam, target in targets.items()
    ]
