"""
Property-based regression tests for the four-cycle obstruction classifier.

These tests do not prove the cohomology theorem. They verify, over 1000
bounded rational residues (plus forced positive/negative controls), that
the exact rational solver agrees with the cycle-pairing certificate on the
four-cycle witness of examples/four_cycle.json:

    r ∈ im(δ⁰)  <=>  <z, r> = 0

equivalently

    <z, r> != 0  <=>  r represents a non-trivial H¹ obstruction.

This is a regression and reproducibility check on one finite complex, not
a substitute for the proof (Proposition prop:nonremovable / Theorem
thm:classifier-soundness in the paper).
"""

import os
import random
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rational_linear_algebra import dot, solve_over_Q
from refinement_witnesses import COARSE
from refinement_checker import coboundary_0

Z = COARSE.cycle
DELTA0 = coboundary_0(COARSE.vertices, COARSE.edges)


def random_fraction(rng: random.Random, numerator_bound: int = 20, denominator_bound: int = 12) -> Fraction:
    numerator = rng.randint(-numerator_bound, numerator_bound)
    denominator = rng.randint(1, denominator_bound)
    return Fraction(numerator, denominator)


def test_1000_random_residues_solver_agrees_with_cycle_pairing():
    rng = random.Random(20260706)

    for _ in range(1000):
        r = [random_fraction(rng) for _ in range(4)]

        pairing = dot(Z, r)
        solver_has_solution, _ = solve_over_Q(DELTA0, r)

        assert solver_has_solution == (pairing == 0)


def test_forced_exact_residues_are_removable():
    rng = random.Random(20260706 + 1)

    for _ in range(250):
        a = random_fraction(rng)
        b = random_fraction(rng)
        c = random_fraction(rng)
        d = a + b + c

        r = [a, b, c, d]

        pairing = dot(Z, r)
        solver_has_solution, solution = solve_over_Q(DELTA0, r)

        assert pairing == 0
        assert solver_has_solution is True
        assert solution is not None


def test_forced_obstruction_residues_are_not_removable():
    rng = random.Random(20260706 + 2)

    for _ in range(250):
        a = random_fraction(rng)
        b = random_fraction(rng)
        c = random_fraction(rng)

        epsilon = Fraction(0)
        while epsilon == 0:
            epsilon = random_fraction(rng)

        d = a + b + c + epsilon

        r = [a, b, c, d]

        pairing = dot(Z, r)
        solver_has_solution, solution = solve_over_Q(DELTA0, r)

        assert pairing != 0
        assert solver_has_solution is False
        assert solution is None


def test_original_paper_residue_is_the_expected_obstruction():
    r = [Fraction(1), Fraction(1), Fraction(1), Fraction(-2)]

    pairing = dot(Z, r)
    solver_has_solution, _ = solve_over_Q(DELTA0, r)

    assert pairing == Fraction(-5)
    assert solver_has_solution is False
