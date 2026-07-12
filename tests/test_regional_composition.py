import random
from fractions import Fraction as F

import pytest

from regional_composition import (
    VennTriple,
    SeamCorrectionData,
    associator_defect,
    closed_form_delta,
)


def test_zero_correction_gives_zero_defect():
    triple = VennTriple()
    mu = SeamCorrectionData(mu_VW=F(0), mu_UvV_W=F(0), mu_U_VvW=F(0), mu_UV=F(0))
    defect = associator_defect(triple, mu)
    assert defect.primary == ()
    assert defect.boundary == ()


def test_ex_venn_worked_values():
    """
    Reproduces the pattern of Example ex:interval / the Section-4.3 scalar
    worked example, transported to the ex:venn regional model: with all
    four seam constants set to 1 (mu_VW - mu_UvV_W + mu_U_VvW - mu_UV =
    1-1+1-1 = 0), the defect vanishes; dropping just mu_UvV_W to 0
    (1-0+1-1 = 1) produces a nonzero defect equal to exactly 1 on the
    triple overlap.
    """
    triple = VennTriple()

    all_reconciled = SeamCorrectionData(mu_VW=F(1), mu_UvV_W=F(1), mu_U_VvW=F(1), mu_UV=F(1))
    defect = associator_defect(triple, all_reconciled)
    assert defect.boundary == ()
    assert closed_form_delta(all_reconciled) == 0

    one_dropped = SeamCorrectionData(mu_VW=F(1), mu_UvV_W=F(0), mu_U_VvW=F(1), mu_UV=F(1))
    defect2 = associator_defect(triple, one_dropped)
    (point, value), = defect2.boundary
    assert point in triple.triple_overlap
    assert value == F(1)
    assert closed_form_delta(one_dropped) == F(1)


def test_associator_defect_is_supported_on_triple_overlap_only():
    """Computational check of Theorem thm:triple-localisation for this model."""
    triple = VennTriple()
    rng = random.Random(20260707)
    for _ in range(25):
        mu = SeamCorrectionData(
            mu_VW=F(rng.randint(-9, 9), rng.randint(1, 4)),
            mu_UvV_W=F(rng.randint(-9, 9), rng.randint(1, 4)),
            mu_U_VvW=F(rng.randint(-9, 9), rng.randint(1, 4)),
            mu_UV=F(rng.randint(-9, 9), rng.randint(1, 4)),
        )
        defect = associator_defect(triple, mu)
        assert defect.support() <= triple.triple_overlap
        # The paper's Example ex:venn: defect = Delta * 1_{UnVnW} * eps,
        # so the primary component must vanish identically.
        assert defect.primary == ()


def test_direct_expansion_matches_closed_form_property():
    """
    Property test: for many random rational seam-correction constants, the
    literal associator expansion (regional_composition.associator_defect)
    agrees exactly with the closed-form four-term formula of Proposition
    prop:four-term. This is the same "two independent methods must agree"
    discipline used throughout the rest of the repository
    (refinement_checker.py's solver/pairing cross-check).

    This is exactly the evidence rocq/AssociatorContributionCertificate.v's
    header (Decision 2) and docs/design/VERIFIED_CONTRIBUTION_CERTIFICATE.md
    cite when scoping that file to formalise closed_form_delta's arithmetic
    only, not associator_defect's full DualNumber/region expansion -- this
    200-case property test is the equivalence's only checked evidence
    anywhere in this project; it is Python-level implementation evidence,
    not a Rocq theorem, and Phase 3C does not attempt to promote it into
    one. Keep this test (and its accuracy) if this file is ever refactored
    -- later Rocq work may depend on citing it honestly.
    """
    triple = VennTriple()
    rng = random.Random(4242)
    for _ in range(200):
        mu = SeamCorrectionData(
            mu_VW=F(rng.randint(-20, 20), rng.randint(1, 6)),
            mu_UvV_W=F(rng.randint(-20, 20), rng.randint(1, 6)),
            mu_U_VvW=F(rng.randint(-20, 20), rng.randint(1, 6)),
            mu_UV=F(rng.randint(-20, 20), rng.randint(1, 6)),
        )
        defect = associator_defect(triple, mu)
        expected = closed_form_delta(mu)
        if expected == 0:
            assert defect.boundary == ()
        else:
            (point, value), = defect.boundary
            assert point in triple.triple_overlap
            assert value == expected
