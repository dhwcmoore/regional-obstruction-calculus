"""
Regression tests for the refinement witnesses of the paper's "Admissible
refinement persistence" section.

Most of these tests check the actual hypotheses used by the paper's
theorem (A1)-(A4), not the earlier, superseded four-condition scheme
(cochain-map naturality / chain-map naturality / pairing adjointness / H1
surjectivity) that
archive/deprecated_universal_refinement_scaffold/refinement_classifier.py
and ocaml/refinement_algebra.ml implemented with hardcoded placeholders.

A separate, additional group of tests below checks (N0), one-directional
cochain-map naturality -- only one piece of that old scheme, honestly
recomputed in exact rational arithmetic, not revived wholesale -- and the
resulting `descent_safe` classification. See refinement_checker.py's
module docstring and rocq/CochainNaturalityDescent.v.

A third group checks (E0), exactness reflection -- another piece of that
old scheme (classically "H1-surjectivity"), also recomputed honestly in
exact rational arithmetic (nullspace + subspace-membership, not a
floating-point cycle lift). (E0) is logically independent of (N0): the
tests below lock in the perhaps-surprising fact that (E0) holds for ALL
FOUR witnesses, including insert_bridge, even though insert_bridge fails
(N0). See refinement_checker.py's module docstring and
rocq/ExactnessReflection.v.

Run with:
    pytest tests/test_refinement_witnesses.py
"""

import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from refinement_witnesses import ALL_WITNESSES, SUBDIVIDE_U1, SUBDIVIDE_U2, SUBDIVIDE_ALL, INSERT_BRIDGE
from refinement_checker import check_witness


@pytest.mark.parametrize("witness", ALL_WITNESSES, ids=lambda w: w.name)
def test_admissibility_conditions_hold(witness):
    cert = check_witness(witness)
    assert cert["A1_coarse_cocycle"] is True
    assert cert["A2_refined_cocycle"] is True
    assert cert["A3_declared_cycle"] is True
    assert cert["A4_nonzero_pairing"] is True
    assert cert["admissible"] is True


@pytest.mark.parametrize("witness", ALL_WITNESSES, ids=lambda w: w.name)
def test_pairing_is_nonzero(witness):
    cert = check_witness(witness)
    assert Fraction(cert["computed_pairing"]) != 0


@pytest.mark.parametrize("witness", ALL_WITNESSES, ids=lambda w: w.name)
def test_solver_cross_check_agrees_with_pairing(witness):
    """
    Independent confirmation of non-exactness: exact Gaussian elimination
    on delta'^0 b = rho^*r must agree with the A3/A4 cycle-pairing
    certificate, via two unrelated methods (same discipline as
    residue_classifier.py's two certificates for the base witness).
    """
    cert = check_witness(witness)
    assert cert["solver_cross_check_not_coboundary"] is True
    assert cert["pairing_and_solver_agree"] is True


def test_computed_pairings_are_honest_not_legacy_numerology():
    """
    Locks down the values actually produced by the constructions in
    refinement_witnesses.py. These differ from the paper's current table
    (-7/2, -4, -5/4, -5) for the three subdivision witnesses, because
    those table values were literal constants with no supporting
    construction (see README / docs/archive/OLD_IMPLEMENTATION_CHECKLIST.md history).
    The bridge witness recovers -5 exactly, since it doesn't touch the
    original four edges at all.
    """
    expected = {
        "subdivide_U1": Fraction(5),
        "subdivide_U2": Fraction(5),
        "subdivide_all": Fraction(5),
        "insert_bridge": Fraction(-5),
    }
    for witness in ALL_WITNESSES:
        cert = check_witness(witness)
        assert Fraction(cert["computed_pairing"]) == expected[witness.name]


def test_bridge_matches_legacy_table_value():
    cert = check_witness(INSERT_BRIDGE)
    assert cert["legacy_matches"] is True


@pytest.mark.parametrize("witness", [SUBDIVIDE_U1, SUBDIVIDE_U2, SUBDIVIDE_ALL], ids=lambda w: w.name)
def test_subdivisions_do_not_match_legacy_table_value(witness):
    cert = check_witness(witness)
    assert cert["legacy_matches"] is False


@pytest.mark.parametrize(
    "witness", [SUBDIVIDE_U1, SUBDIVIDE_U2, SUBDIVIDE_ALL], ids=lambda w: w.name
)
def test_cochain_naturality_holds_for_subdivision_witnesses(witness):
    """
    (N0) delta'^0 rho_0^* = rho_1^* delta^0, checked in exact rational
    arithmetic against the declared `vertex_over` quotient map. All three
    subdivision witnesses satisfy it, so they are descent-safe: A1-A4
    plus (N0) is enough for rocq/CochainNaturalityDescent.v's
    `admissible_refinement_persistence_with_descent` to conclude
    non-exactness back in the *coarse* complex, not just the refined one.
    """
    cert = check_witness(witness)
    assert cert["N0_cochain_naturality_delta0"] is True
    assert cert["naturality_failures"] == []
    assert cert["descent_safe"] is True


def test_bridge_is_admissible_but_not_descent_safe():
    """
    insert_bridge remains a valid (A1)-(A4) persistence witness -- the
    obstruction genuinely persists into the refined complex -- but it is
    not descent-safe: its new edge b12 runs between two distinct coarse
    vertices rather than lying over a collapsed parent, so cochain-map
    naturality fails at exactly that row, and nothing here lets that
    failure be silently patched by changing what `over=None` means.
    """
    cert = check_witness(INSERT_BRIDGE)
    assert cert["admissible"] is True
    assert cert["N0_cochain_naturality_delta0"] is False
    assert cert["descent_safe"] is False
    failing_edges = {f["edge"] for f in cert["naturality_failures"]}
    assert failing_edges == {"b12"}


@pytest.mark.parametrize("witness", ALL_WITNESSES, ids=lambda w: w.name)
def test_exactness_reflection_holds_for_all_four_witnesses(witness):
    """
    (E0), Z1(coarse) subseteq rho_*(Z1(refined)), checked by exact
    rational nullspace computation and subspace-membership testing --
    not the deprecated scaffold's floating-point cycle lift. Unlike (N0),
    (E0) holds for ALL FOUR witnesses, including insert_bridge: in every
    case the already-declared refined cycle z' alone pushes forward to a
    non-zero rational multiple of the coarse cycle z, which already spans
    the (here one-dimensional) coarse cycle space. This is the surprising
    fact this test suite locks in -- (N0) and (E0) are independent
    conditions, and insert_bridge is the witness that separates them.
    """
    cert = check_witness(witness)
    assert cert["E0_exactness_reflection"] is True
    assert cert["reflection_failures"] == []


def test_verdict_safe_matches_descent_safe_for_a_different_reason_on_bridge():
    """
    verdict_safe = descent_safe and E0. Since E0 holds everywhere, this
    numerically tracks descent_safe exactly (true for the three
    subdivisions, false for the bridge) -- but for insert_bridge that
    False is entirely attributable to (N0) failing, not (E0); E0 itself
    is True there. This test pins that attribution down explicitly, so a
    future change that accidentally makes E0 fail for the bridge (or
    N0 pass) is caught, rather than silently changing verdict_safe's
    value for the wrong reason.
    """
    cert = check_witness(INSERT_BRIDGE)
    assert cert["N0_cochain_naturality_delta0"] is False
    assert cert["E0_exactness_reflection"] is True
    assert cert["verdict_safe"] is False

    for witness in (SUBDIVIDE_U1, SUBDIVIDE_U2, SUBDIVIDE_ALL):
        cert = check_witness(witness)
        assert cert["N0_cochain_naturality_delta0"] is True
        assert cert["E0_exactness_reflection"] is True
        assert cert["verdict_safe"] is True
