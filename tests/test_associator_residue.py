from fractions import Fraction as F

import pytest

from associator_residue import (
    SeamAssociatorInstance,
    compute_seam_residue,
    residue_vector,
    four_cycle_instances,
    SEAM_ORDER,
)
from regional_composition import SeamCorrectionData, VennTriple


def test_four_cycle_instances_reproduce_paper_residue():
    r = residue_vector(four_cycle_instances())
    assert r == [F(1), F(1), F(1), F(-2)]


def test_seam_order_matches_default():
    assert SEAM_ORDER == ("e12", "e23", "e34", "e14")


def test_missing_seam_instance_raises():
    incomplete = four_cycle_instances()[:3]
    with pytest.raises(ValueError):
        residue_vector(incomplete)


def test_compute_seam_residue_single_instance():
    inst = SeamAssociatorInstance(
        seam="e12",
        mu=SeamCorrectionData(mu_VW=F(3), mu_UvV_W=F(0), mu_U_VvW=F(0), mu_UV=F(0)),
    )
    assert compute_seam_residue(inst) == F(3)


def test_multi_point_overlap_is_rejected():
    # A triple overlap with more than one point is outside this compiler's
    # single-point modelling assumption and must fail loudly, not silently
    # pick one point.
    triple = VennTriple(
        U=frozenset({1, 2, 3}),
        V=frozenset({2, 3, 4}),
        W=frozenset({2, 3, 5}),
    )
    inst = SeamAssociatorInstance(
        seam="e12",
        mu=SeamCorrectionData(mu_VW=F(1), mu_UvV_W=F(0), mu_U_VvW=F(0), mu_UV=F(0)),
        triple=triple,
    )
    with pytest.raises(ValueError):
        compute_seam_residue(inst)
