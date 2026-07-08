"""
Locks in the "cohomological collapse" result for the first concrete
coupled generator test (docs/COUPLED_GENERATOR_SPEC.md's architecture,
adjacent-overlap sharing with outer correction slots fixed to zero): the
induced map has rank 3 (a real drop from the independent generator's
full rank 4), but its image is exactly im(delta^0) of the same cyclic
graph, so the realisable-obstruction quotient is trivial.

This is a regression guard on a specific, falsified design choice, not a
proof that coupling is hopeless -- see
coupled_realisability_diagnostic.py's module docstring and
docs/REALISABILITY_ROADMAP.md for what remains open (the outer
correction slots). If a future change to this specific construction
makes these assertions fail, check whether that's because the outer
slots are no longer zero -- that would be expected, and good.
"""

from fractions import Fraction as F

from coupled_realisability_diagnostic import (
    diagnose,
    coupled_matrix,
    residue_for,
    check_shared_cover,
    THETA,
    REGIONS,
)
from rational_linear_algebra import in_span_over_Q, transpose


def test_shared_cover_has_genuine_single_point_triple_overlaps():
    check_shared_cover()  # raises AssertionError internally if not


def test_forced_diagonal_overlaps_are_nonempty():
    """Documents the forced topology explicitly: requiring all four
    cyclic triple overlaps to be single points, in one shared universe,
    unavoidably makes the 'diagonal' pairs U1 n U3 and U2 n U4 nonempty
    too -- not a modelling choice, a consequence of the other four."""
    assert len(REGIONS["U1"] & REGIONS["U3"]) > 0
    assert len(REGIONS["U2"] & REGIONS["U4"]) > 0


def test_rank_drops_but_image_collapses_to_im_delta0():
    result = diagnose()
    assert result["n_params"] == 4
    assert result["dim_C1"] == 4
    assert result["rank_B"] == 3
    assert result["rank_delta0"] == 3
    assert result["image_B_subseteq_image_delta0"] is True
    assert result["image_B_equals_image_delta0"] is True
    assert result["dim_quotient"] == 0


def test_matrix_is_exactly_the_cyclic_difference_operator():
    B, labels = coupled_matrix()
    assert labels == ["mu12", "mu23", "mu34", "mu41"]
    expected = [
        [F(-1), F(1), F(0), F(0)],
        [F(0), F(-1), F(1), F(0)],
        [F(0), F(0), F(-1), F(1)],
        [F(1), F(0), F(0), F(-1)],
    ]
    assert B == expected


def test_every_row_sums_to_zero():
    """The structural signature of a coboundary/gradient: r12+r23+r34+r41
    is identically zero for every choice of mu."""
    for mu in [
        {"mu12": F(3), "mu23": F(-5), "mu34": F(7), "mu41": F(11)},
        {"mu12": F(0), "mu23": F(0), "mu34": F(0), "mu41": F(1)},
    ]:
        r = residue_for(mu)
        assert sum(r) == 0


def test_papers_displayed_residue_is_not_producible_by_this_construction():
    """The paper's r=(1,1,1,-2), in the (e12,e23,e34,e14) convention, sums
    to 1, not 0 -- and this construction's image is exactly the sum-zero
    hyperplane (im(delta0)), so no orientation convention can rescue it:
    a residue that fails 'sum to zero' cannot lie in this image regardless
    of sign flips on individual coordinates from e14 vs e41 relabelling.
    This is checked directly here, not just inferred from the sum."""
    B, _ = coupled_matrix()
    B_columns = transpose(B)
    paper_r_e14_convention = [F(1), F(1), F(1), F(-2)]
    # Re-expressed in this script's (e12,e23,e34,e41) convention: e41 is
    # the reverse of e14, so its coordinate sign flips.
    my_convention_r = paper_r_e14_convention[:3] + [-paper_r_e14_convention[3]]
    assert sum(my_convention_r) != 0
    assert not in_span_over_Q(B_columns, my_convention_r)
