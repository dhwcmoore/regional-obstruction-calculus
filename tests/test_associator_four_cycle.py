"""
The end-to-end coherence test for the associator-generation pipeline:

    associator data (associator_residue.four_cycle_instances)
        -> compiled residue (associator_residue.residue_vector)
        -> repair verdict (repair_solver.attempt_repair)
        -> agreement with residue_classifier.classify (the paper's own
           declared-residue classifier, examples/four_cycle.json)
        -> agreement with refinement_witnesses.COARSE.residue (the shared
           base residue the four refinement witnesses are built from)

This is the "bridge" the associator-generation layer exists to build: the
same (1,1,1,-2) vector that examples/four_cycle.json declares directly,
and that refinement_witnesses.py hardcodes as COARSE.residue for the
refinement-persistence witnesses, is shown here to also be *producible* by
literal associator-field computation over declared local correction data.
"""

import json
from fractions import Fraction as F

from associator_residue import four_cycle_instances, residue_vector, SEAM_ORDER
from repair_solver import attempt_repair, VERDICT_NONTRIVIAL_OBSTRUCTION
from residue_classifier import classify
from refinement_witnesses import COARSE

FOUR_CYCLE_D0 = [
    [F(-1), F(1), F(0), F(0)],
    [F(0), F(-1), F(1), F(0)],
    [F(0), F(0), F(-1), F(1)],
    [F(-1), F(0), F(0), F(1)],
]
CYCLE = [F(-1), F(-1), F(-1), F(1)]


def test_associator_generated_residue_matches_declared_witness():
    r = residue_vector(four_cycle_instances())
    assert r == [F(1), F(1), F(1), F(-2)]
    assert r == COARSE.residue


def test_associator_generated_residue_triggers_obstruction_verdict():
    r = residue_vector(four_cycle_instances())
    result = attempt_repair(FOUR_CYCLE_D0, r, CYCLE)
    assert result.verdict == VERDICT_NONTRIVIAL_OBSTRUCTION
    assert result.obstruction_pairing == F(-5)


def test_associator_generated_residue_agrees_with_declared_classifier():
    """
    Feed the associator-compiled residue through the exact same
    classify() used by residue_classifier.py on the paper's declared
    examples/four_cycle.json, and confirm it produces the identical
    verdict and certificate fields.
    """
    r = residue_vector(four_cycle_instances())

    with open("examples/four_cycle.json") as f:
        declared = json.load(f)
    assert declared["residue"] == [str(x) for x in r]

    data = {
        "name": "associator-generated four-cycle (test)",
        "complex": declared["complex"],
        "residue": [str(x) for x in r],
        "cycle_witness": declared["cycle_witness"],
    }
    cert = classify(data)
    assert cert["verdict"] == "nontrivial_H1_obstruction"
    assert cert["pairing"] == "-5"
    assert cert["is_cocycle"] is True
    assert cert["is_coboundary"] is False


def test_seam_order_matches_coarse_edge_order():
    assert SEAM_ORDER == tuple(e.name for e in COARSE.edges)
