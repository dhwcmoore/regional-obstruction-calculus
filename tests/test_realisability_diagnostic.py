"""
Locks in the realisability diagnostic's negative result: the current
associator generator (associator_residue.py's four_cycle_instances-style
construction) is surjective onto all of C^1(N;Q). See
docs/REALISABILITY_ROADMAP.md for what this means and does not mean.

This is a regression guard, not a proof -- if a future change to the
generator (e.g. adding real cross-seam coupling) makes this test fail,
that is expected and good: it means the negative result no longer holds
and the roadmap doc should be revisited, not that this test is wrong.
"""

from fractions import Fraction as F

from realisability_diagnostic import diagnose, is_realisable, realisability_matrix


def test_current_generator_has_full_rank():
    result = diagnose()
    assert result["n_params"] == 16
    assert result["dim_C1"] == 4
    assert result["rank_A"] == 4
    assert result["dim_ker_A"] == 12
    assert result["full_rank"] is True


def test_paper_witness_residue_is_realisable():
    assert is_realisable([F(1), F(1), F(1), F(-2)]) is True


def test_zero_residue_is_realisable():
    assert is_realisable([F(0), F(0), F(0), F(0)]) is True


def test_arbitrary_residue_is_realisable():
    """Not one of the two residues this repo has ever declared -- picked
    with no relationship to the paper's example, to confirm the claim is
    about the whole space, not just familiar vectors."""
    assert is_realisable([F(3), F(-5), F(7), F(11)]) is True


def test_realisability_matrix_columns_match_seam_order():
    A, labels = realisability_matrix()
    assert len(A) == 4
    assert len(A[0]) == 16
    assert labels[0] == "e12.mu_VW"
    assert labels[-1] == "e14.mu_UV"
