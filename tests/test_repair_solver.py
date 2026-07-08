from fractions import Fraction as F

from repair_solver import (
    attempt_repair,
    VERDICT_GLOBALLY_REPAIRABLE,
    VERDICT_NONTRIVIAL_OBSTRUCTION,
    VERDICT_INVALID_RESIDUE,
    VERDICT_DEGENERATE_INPUT,
)

FOUR_CYCLE_D0 = [
    [F(-1), F(1), F(0), F(0)],
    [F(0), F(-1), F(1), F(0)],
    [F(0), F(0), F(-1), F(1)],
    [F(-1), F(0), F(0), F(1)],
]
CYCLE = [F(-1), F(-1), F(-1), F(1)]


def test_nontrivial_obstruction_matches_paper_witness():
    residue = [F(1), F(1), F(1), F(-2)]
    result = attempt_repair(FOUR_CYCLE_D0, residue, CYCLE)
    assert result.verdict == VERDICT_NONTRIVIAL_OBSTRUCTION
    assert not result.repairable
    assert result.obstruction_pairing == F(-5)


def test_globally_repairable_when_residue_is_a_coboundary():
    b = [F(2), F(-1), F(3), F(0)]
    # delta^0 b = (b2-b1, b3-b2, b4-b3, b4-b1)
    residue = [b[1] - b[0], b[2] - b[1], b[3] - b[2], b[3] - b[0]]
    result = attempt_repair(FOUR_CYCLE_D0, residue, CYCLE)
    assert result.verdict == VERDICT_GLOBALLY_REPAIRABLE
    assert result.repairable
    assert result.correction is not None
    # correction genuinely reproduces the residue under delta^0
    reproduced = [
        result.correction[1] - result.correction[0],
        result.correction[2] - result.correction[1],
        result.correction[3] - result.correction[2],
        result.correction[3] - result.correction[0],
    ]
    assert reproduced == residue


def test_invalid_residue_when_not_closed():
    residue = [F(1), F(1), F(1), F(-2)]
    coboundary_1 = [[F(1), F(0), F(0), F(0)]]  # forces a nontrivial delta^1
    result = attempt_repair(FOUR_CYCLE_D0, residue, CYCLE, coboundary_1=coboundary_1)
    assert result.verdict == VERDICT_INVALID_RESIDUE


def test_degenerate_input_on_mismatched_lengths():
    result = attempt_repair(FOUR_CYCLE_D0, [F(1), F(1)], CYCLE)
    assert result.verdict == VERDICT_DEGENERATE_INPUT


def test_degenerate_input_on_empty_matrix():
    result = attempt_repair([], [], [])
    assert result.verdict == VERDICT_DEGENERATE_INPUT
