"""
Tests for the proof-carrying first-order classifier: certificate_emitter.py
emits certificates for the associator_residue.py / repair_solver.py
pipeline, and first_order_certificate_checker.py independently verifies
them, without importing the classifier's own modules (see that module's
docstring for exactly what "independent" means).

Two groups of tests:

1. Valid certificates, for both verdict forms (obstruction and exact),
   are accepted.
2. Tampered certificates -- one mutation per certificate field that
   matters -- are rejected. This is the more important group: a checker
   that only ever accepts is not doing any checking.
"""

import copy
from fractions import Fraction as F

from associator_residue import (
    SeamAssociatorInstance,
    four_cycle_instances,
)
from regional_composition import SeamCorrectionData
from certificate_emitter import build_certificate
from first_order_certificate_checker import check_certificate

FOUR_CYCLE_D0 = [
    [F(-1), F(1), F(0), F(0)],
    [F(0), F(-1), F(1), F(0)],
    [F(0), F(0), F(-1), F(1)],
    [F(-1), F(0), F(0), F(1)],
]
CYCLE = [F(-1), F(-1), F(-1), F(1)]
SEAM_ORDER = ["e12", "e23", "e34", "e14"]


def obstruction_certificate() -> dict:
    return build_certificate(
        source="test:obstruction",
        coboundary_0=FOUR_CYCLE_D0,
        cycle=CYCLE,
        seam_order=SEAM_ORDER,
        instances=four_cycle_instances(),
    )


def _repairable_instances():
    # b = (0, 2, 1, 3); delta^0 b = (b1-b0, b2-b1, b3-b2, b3-b0) = (2, -1, 2, 3)
    targets = {"e12": F(2), "e23": F(-1), "e34": F(2), "e14": F(3)}
    return [
        SeamAssociatorInstance(
            seam=seam,
            mu=SeamCorrectionData(mu_VW=target, mu_UvV_W=F(0), mu_U_VvW=F(0), mu_UV=F(0)),
        )
        for seam, target in targets.items()
    ]


def repairable_certificate() -> dict:
    return build_certificate(
        source="test:repairable",
        coboundary_0=FOUR_CYCLE_D0,
        cycle=CYCLE,
        seam_order=SEAM_ORDER,
        instances=_repairable_instances(),
    )


# --------------------------------------------------------------------------
# Valid certificates are accepted.
# --------------------------------------------------------------------------

def test_obstruction_certificate_is_accepted():
    cert = obstruction_certificate()
    assert cert["verdict"] == "nontrivial_associator_obstruction"
    result = check_certificate(cert)
    assert result.accepted, result.reasons


def test_repairable_certificate_is_accepted():
    cert = repairable_certificate()
    assert cert["verdict"] == "globally_repairable"
    result = check_certificate(cert)
    assert result.accepted, result.reasons


def test_obstruction_certificate_records_closedness():
    cert = obstruction_certificate()
    assert cert["closed"] is True
    assert cert["delta1_r"] == []


# --------------------------------------------------------------------------
# Tampered certificates are rejected. Each test mutates exactly one field
# of an otherwise-valid certificate.
# --------------------------------------------------------------------------

def test_reject_tampered_residue_entry():
    cert = obstruction_certificate()
    cert["seam_residue"][0] = "99"
    assert not check_certificate(cert).accepted


def test_reject_tampered_cycle_coefficient():
    cert = obstruction_certificate()
    cert["cycle_vector"][1] = "5"
    assert not check_certificate(cert).accepted


def test_reject_tampered_correction_witness():
    cert = repairable_certificate()
    cert["correction"][0] = "999"
    assert not check_certificate(cert).accepted


def test_reject_tampered_coboundary_0_matrix():
    cert = obstruction_certificate()
    cert["coboundary_0_matrix"][0][0] = "7"
    assert not check_certificate(cert).accepted


def test_reject_tampered_mu_data():
    cert = obstruction_certificate()
    cert["mu_by_seam"]["e12"]["mu_VW"] = "42"
    assert not check_certificate(cert).accepted


def test_reject_declared_obstructed_when_actually_exact():
    cert = repairable_certificate()
    cert["verdict"] = "nontrivial_associator_obstruction"
    assert not check_certificate(cert).accepted


def test_reject_declared_exact_when_actually_obstructed():
    cert = obstruction_certificate()
    cert["verdict"] = "globally_repairable"
    assert not check_certificate(cert).accepted


def test_reject_malformed_rational():
    cert = obstruction_certificate()
    cert["seam_residue"][0] = "not-a-number"
    assert not check_certificate(cert).accepted


def test_reject_decimal_looking_input():
    cert = obstruction_certificate()
    cert["seam_residue"][0] = "1.5"
    result = check_certificate(cert)
    assert not result.accepted
    assert any("canonical exact-rational" in reason for reason in result.reasons)


def test_reject_tampered_coboundary_1_claim():
    cert = obstruction_certificate()
    # A genuinely non-closed residue must not be certifiable as closed.
    cert["coboundary_1_matrix"] = [["1", "0", "0", "0"]]
    cert["delta1_r"] = ["0"]
    cert["closed"] = True
    assert not check_certificate(cert).accepted


def test_reject_missing_pairing_on_obstruction_verdict():
    cert = obstruction_certificate()
    cert["pairing"] = None
    assert not check_certificate(cert).accepted


def test_untampered_deepcopy_is_still_accepted():
    """Sanity check that copy.deepcopy itself doesn't corrupt a certificate
    -- otherwise the tamper tests above would be testing the wrong thing."""
    cert = copy.deepcopy(obstruction_certificate())
    assert check_certificate(cert).accepted
