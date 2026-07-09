"""
Regression tests for refinement_witness_composition_boundary_search.py.
Uses smaller bounds than the module's own full exhaustive search (which
takes about a minute) to keep the suite fast, while still exercising the
real logic -- including the corrected E0 filtering (see module
docstring: an earlier version reported spurious E0 "counterexamples"
that were actually individual-step E0 failures, not composition
failures).
"""

from fractions import Fraction as F

from refinement_witness_composition_boundary_search import (
    build_witness_and_check, exhaustive_search, randomized_search,
)


def test_exhaustive_search_small_bounds_finds_no_counterexample():
    result = exhaustive_search(n1=2, values=(F(-1), F(1)), time_budget_s=60.0)
    assert result["exhaustive_completed"] is True
    assert result["composite_witnesses_tested"] > 0
    assert result["a4_failures"] == []
    assert result["e0_failures"] == []


def test_randomized_search_small_trials_finds_no_counterexample():
    result = randomized_search(trials=2000, seed=1)
    assert result["composite_witnesses_tested"] > 0
    assert result["a4_failures"] == []
    assert result["e0_failures"] == []


def test_step_with_individually_failing_E0_is_excluded_not_counted():
    """The corrected-mistake regression guard: construct a case where
    step 1 itself does not satisfy E0 (rho1_PQ maps everything to zero,
    so no coarse cycle can be a pushforward of anything nonzero unless
    the coarse cycle space is trivial) and confirm build_witness_and_check
    returns None rather than reporting a spurious composite failure."""
    delta_P = [[F(0)], [F(0)]]  # Z1(P) = all of Q^2 (delta_P is the zero map)
    rho1_PQ = [[F(0), F(0)], [F(0), F(0)]]  # zero pullback: cannot reflect any nonzero cycle
    rho1_QR = [[F(1), F(0)], [F(0), F(1)]]
    r = [F(1), F(0)]
    result = build_witness_and_check(delta_P, rho1_PQ, rho1_QR, r)
    assert result is None


def test_a_genuine_witness_is_found_and_reports_composite_fields():
    """Sanity check that build_witness_and_check does return a genuine
    result dict for at least one small, deliberately-chosen case."""
    delta_P = [[F(1)], [F(0)]]
    rho1_PQ = [[F(1), F(0)], [F(0), F(1)]]
    rho1_QR = [[F(1), F(0)], [F(0), F(1)]]
    r = [F(1), F(1)]
    result = build_witness_and_check(delta_P, rho1_PQ, rho1_QR, r)
    assert result is not None
    assert "composite_A4" in result and "composite_E0" in result
