"""
Tests for the R21 (`rocq/ExactRationalRepairOrSeparator.v`) certificate
pipeline: `r21_certificate_emitter.py` runs the untrusted generator
(`r21_repair_or_separator.py`) and emits a `repair-or-separator/v1`
certificate; `r21_certificate_checker.py` independently verifies it,
without importing either the generator or the emitter (see that module's
docstring for exactly what "independent" means).

Six groups of tests, per the fail-closed discipline this checker is
supposed to enforce:

1. Valid certificates, for both outcomes (repair and separator), are
   accepted.
2. Malformed certificates (bad schema, bad rational syntax, wrong length,
   missing witness) are rejected.
3. Tampered certificates (one mutation per field that matters) are
   rejected -- the more important group, since a checker that only ever
   accepts is not doing any checking.
4. A certificate genuinely valid for one problem is rejected when
   presented against a *different* problem's `(D, r)` -- the binding the
   `input_digest` exists to enforce.
5. Determinism: repeated emission for the same input produces
   byte-identical certificates and a stable digest.
6. Hardening: a closed certificate/input schema, duplicate JSON keys, and
   resource limits on rational-string length and matrix/vector dimension
   are all enforced, and are rejections (fail-closed), not crashes.
"""

import json
import subprocess
import sys
from fractions import Fraction as F

import pytest

from r21_certificate_emitter import build_certificate, read_input as emitter_read_input
from r21_certificate_checker import check_certificate, check_files, read_input as checker_read_input
from r21_certificate_format import (
    MAX_DIMENSION,
    MAX_RATIONAL_CHARS,
    canonical_input_digest,
    CERTIFICATE_SCHEMA,
)

IDENTITY_D = [[F(1), F(0)], [F(0), F(1)]]
IDENTITY_R = [F(3), F(5)]

FOUR_CYCLE_D = [
    [F(-1), F(1), F(0), F(0)],
    [F(0), F(-1), F(1), F(0)],
    [F(0), F(0), F(-1), F(1)],
    [F(-1), F(0), F(0), F(1)],
]
FOUR_CYCLE_R = [F(1), F(1), F(1), F(-2)]


# --------------------------------------------------------------------------
# 1. Valid certificates are accepted.
# --------------------------------------------------------------------------

def test_repair_certificate_is_accepted():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    assert cert["result"] == "repair"
    assert cert["repair"] == ["3", "5"]
    result = check_certificate(IDENTITY_D, IDENTITY_R, cert)
    assert result.accepted, result.reasons


def test_separator_certificate_is_accepted():
    cert = build_certificate(FOUR_CYCLE_D, FOUR_CYCLE_R)
    assert cert["result"] == "separator"
    result = check_certificate(FOUR_CYCLE_D, FOUR_CYCLE_R, cert)
    assert result.accepted, result.reasons


def test_separator_recovers_paper_witness_normalised():
    """R21's own recorded fact (README, STATUS.md): the internal elimination
    finds z = (-1,-1,-1,1) with pairing -5; the public certificate is the
    normalised -1/5 z = (1/5,1/5,1/5,-1/5)."""
    cert = build_certificate(FOUR_CYCLE_D, FOUR_CYCLE_R)
    assert cert["separator"] == ["1/5", "1/5", "1/5", "-1/5"]


# --------------------------------------------------------------------------
# 2. Malformed certificates are rejected.
# --------------------------------------------------------------------------

def test_reject_wrong_schema():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    cert["schema"] = "something-else/v1"
    assert not check_certificate(IDENTITY_D, IDENTITY_R, cert).accepted


def test_reject_non_canonical_rational_in_repair():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    cert["repair"][0] = "1.5"
    result = check_certificate(IDENTITY_D, IDENTITY_R, cert)
    assert not result.accepted
    assert any("malformed repair witness" in r for r in result.reasons)


def test_reject_wrong_length_repair():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    cert["repair"] = ["3"]
    assert not check_certificate(IDENTITY_D, IDENTITY_R, cert).accepted


def test_reject_wrong_length_separator():
    cert = build_certificate(FOUR_CYCLE_D, FOUR_CYCLE_R)
    cert["separator"] = cert["separator"][:-1]
    assert not check_certificate(FOUR_CYCLE_D, FOUR_CYCLE_R, cert).accepted


def test_reject_missing_witness():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    del cert["repair"]
    assert not check_certificate(IDENTITY_D, IDENTITY_R, cert).accepted


def test_reject_unrecognized_result():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    cert["result"] = "maybe"
    assert not check_certificate(IDENTITY_D, IDENTITY_R, cert).accepted


# --------------------------------------------------------------------------
# 3. Tampered certificates are rejected.
# --------------------------------------------------------------------------

def test_reject_tampered_repair_value():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    cert["repair"][0] = "999"
    assert not check_certificate(IDENTITY_D, IDENTITY_R, cert).accepted


def test_reject_tampered_separator_value():
    cert = build_certificate(FOUR_CYCLE_D, FOUR_CYCLE_R)
    cert["separator"][0] = "999"
    assert not check_certificate(FOUR_CYCLE_D, FOUR_CYCLE_R, cert).accepted


def test_reject_declared_repair_when_actually_separator():
    """A tampered certificate that swaps outcome and witness wholesale:
    claims 'repair' but supplies the separator's numbers -- must not be
    accepted just because *some* witness-shaped list is present."""
    cert = build_certificate(FOUR_CYCLE_D, FOUR_CYCLE_R)
    cert["result"] = "repair"
    cert["repair"] = cert.pop("separator")
    assert not check_certificate(FOUR_CYCLE_D, FOUR_CYCLE_R, cert).accepted


def test_reject_tampered_digest():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    cert["input_digest"] = "sha256:" + "0" * 64
    assert not check_certificate(IDENTITY_D, IDENTITY_R, cert).accepted


# --------------------------------------------------------------------------
# 4. A certificate valid for one problem is rejected against another.
# --------------------------------------------------------------------------

def test_reject_certificate_for_wrong_problem():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    other_D = [[F(1), F(0)], [F(0), F(1)]]
    other_r = [F(7), F(9)]
    result = check_certificate(other_D, other_r, cert)
    assert not result.accepted
    assert any("does not certify this problem" in r for r in result.reasons)


def test_digests_differ_for_different_problems():
    d1 = canonical_input_digest(IDENTITY_D, IDENTITY_R)
    d2 = canonical_input_digest(IDENTITY_D, [F(7), F(9)])
    assert d1 != d2


# --------------------------------------------------------------------------
# End-to-end CLI: roc-solve then roc-verify as separate processes, the
# checker trusting nothing from the solver's own run.
# --------------------------------------------------------------------------

def test_cli_roundtrip_repair(tmp_path):
    input_path = tmp_path / "input.json"
    cert_path = tmp_path / "cert.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5"]}'
    )
    solve = subprocess.run(
        [sys.executable, "r21_certificate_emitter.py", str(input_path), "--certificate", str(cert_path)],
        capture_output=True, text=True,
    )
    assert solve.returncode == 0, solve.stderr
    verify = subprocess.run(
        [sys.executable, "r21_certificate_checker.py", str(input_path), str(cert_path)],
        capture_output=True, text=True,
    )
    assert verify.returncode == 0, verify.stdout + verify.stderr
    assert "ACCEPT" in verify.stdout


def test_cli_roundtrip_separator(tmp_path):
    input_path = tmp_path / "input.json"
    cert_path = tmp_path / "cert.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", '
        '"D": [["-1","1","0","0"],["0","-1","1","0"],["0","0","-1","1"],["-1","0","0","1"]], '
        '"r": ["1","1","1","-2"]}'
    )
    solve = subprocess.run(
        [sys.executable, "r21_certificate_emitter.py", str(input_path), "--certificate", str(cert_path)],
        capture_output=True, text=True,
    )
    assert solve.returncode == 0, solve.stderr
    verify = subprocess.run(
        [sys.executable, "r21_certificate_checker.py", str(input_path), str(cert_path)],
        capture_output=True, text=True,
    )
    assert verify.returncode == 0, verify.stdout + verify.stderr
    assert "ACCEPT" in verify.stdout


def test_cli_verify_rejects_wrong_input_file(tmp_path):
    input_path = tmp_path / "input.json"
    other_input_path = tmp_path / "other_input.json"
    cert_path = tmp_path / "cert.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5"]}'
    )
    other_input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["7","9"]}'
    )
    subprocess.run(
        [sys.executable, "r21_certificate_emitter.py", str(input_path), "--certificate", str(cert_path)],
        capture_output=True, text=True, check=True,
    )
    verify = subprocess.run(
        [sys.executable, "r21_certificate_checker.py", str(other_input_path), str(cert_path)],
        capture_output=True, text=True,
    )
    assert verify.returncode == 1
    assert "REJECT" in verify.stdout


# --------------------------------------------------------------------------
# 5. Determinism: repeated emission is byte-identical and digest-stable.
# --------------------------------------------------------------------------

def test_repeated_emission_is_byte_identical(tmp_path):
    input_path = tmp_path / "input.json"
    cert_a = tmp_path / "cert_a.json"
    cert_b = tmp_path / "cert_b.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", '
        '"D": [["-1","1","0","0"],["0","-1","1","0"],["0","0","-1","1"],["-1","0","0","1"]], '
        '"r": ["1","1","1","-2"]}'
    )
    for out in (cert_a, cert_b):
        subprocess.run(
            [sys.executable, "r21_certificate_emitter.py", str(input_path), "--certificate", str(out)],
            capture_output=True, text=True, check=True,
        )
    assert cert_a.read_bytes() == cert_b.read_bytes()


def test_digest_is_stable_across_repeated_computation():
    digests = {canonical_input_digest(FOUR_CYCLE_D, FOUR_CYCLE_R) for _ in range(20)}
    assert len(digests) == 1


def test_reject_after_mutating_one_matrix_coefficient(tmp_path):
    """A certificate valid for the original problem must be rejected once
    a single D coefficient in the *input file* changes -- the digest binds
    to every entry, not merely to shape."""
    input_path = tmp_path / "input.json"
    mutated_path = tmp_path / "mutated.json"
    cert_path = tmp_path / "cert.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5"]}'
    )
    mutated_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","7"]], "r": ["3","5"]}'
    )
    subprocess.run(
        [sys.executable, "r21_certificate_emitter.py", str(input_path), "--certificate", str(cert_path)],
        capture_output=True, text=True, check=True,
    )
    result = check_files(str(mutated_path), str(cert_path))
    assert not result.accepted


def test_reject_after_mutating_one_residue_coefficient(tmp_path):
    input_path = tmp_path / "input.json"
    mutated_path = tmp_path / "mutated.json"
    cert_path = tmp_path / "cert.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5"]}'
    )
    mutated_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","9"]}'
    )
    subprocess.run(
        [sys.executable, "r21_certificate_emitter.py", str(input_path), "--certificate", str(cert_path)],
        capture_output=True, text=True, check=True,
    )
    result = check_files(str(mutated_path), str(cert_path))
    assert not result.accepted


# --------------------------------------------------------------------------
# 6. Hardening: closed schema, duplicate keys, resource limits.
# --------------------------------------------------------------------------

def test_reject_certificate_with_unknown_field():
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    cert["extra_field"] = "not part of the schema"
    result = check_certificate(IDENTITY_D, IDENTITY_R, cert)
    assert not result.accepted
    assert any("unrecognized field" in reason for reason in result.reasons)


def test_reject_input_file_with_unknown_field(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5"], "extra": 1}'
    )
    with pytest.raises(ValueError, match="unrecognized field"):
        checker_read_input(str(input_path))


def test_reject_duplicate_key_in_certificate_file(tmp_path):
    input_path = tmp_path / "input.json"
    cert_path = tmp_path / "cert.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5"]}'
    )
    # Hand-crafted certificate JSON with "result" declared twice, disagreeing --
    # json.loads alone would silently keep the last one; this must be rejected
    # instead, since the two occurrences are contradictory raw input.
    cert_path.write_text(
        '{"schema": "repair-or-separator/v1", '
        '"input_digest": "' + canonical_input_digest(IDENTITY_D, IDENTITY_R) + '", '
        '"result": "repair", "repair": ["3","5"], "result": "separator"}'
    )
    result = check_files(str(input_path), str(cert_path))
    assert not result.accepted
    assert any("malformed certificate file" in reason for reason in result.reasons)


def test_reject_duplicate_key_in_input_file(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], '
        '"r": ["3","5"], "r": ["7","9"]}'
    )
    with pytest.raises(ValueError, match="duplicate JSON key"):
        checker_read_input(str(input_path))


def test_reject_oversized_rational_string():
    huge = "1" * (MAX_RATIONAL_CHARS + 1)
    cert = build_certificate(IDENTITY_D, IDENTITY_R)
    cert["repair"][0] = huge
    result = check_certificate(IDENTITY_D, IDENTITY_R, cert)
    assert not result.accepted


def test_reject_oversized_dimension(tmp_path):
    input_path = tmp_path / "input.json"
    oversized_r = ",".join(f'"{i}"' for i in range(MAX_DIMENSION + 1))
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [], "r": [' + oversized_r + "]}"
    )
    with pytest.raises(ValueError, match="MAX_DIMENSION"):
        checker_read_input(str(input_path))


def test_reject_ragged_matrix(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1","2"]], "r": ["3","5"]}'
    )
    with pytest.raises(ValueError, match="rectangular"):
        checker_read_input(str(input_path))


def test_reject_mismatched_residue_length(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5","7"]}'
    )
    with pytest.raises(ValueError):
        checker_read_input(str(input_path))


def test_emitter_read_input_enforces_the_same_hardening(tmp_path):
    """The closed-schema/dimension/rectangularity checks are shared
    (`r21_certificate_format.py`), so the emitter's own input reading is
    just as strict as the checker's -- a malformed input file cannot even
    reach the untrusted generator."""
    input_path = tmp_path / "input.json"
    input_path.write_text(
        '{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5"], "extra": 1}'
    )
    with pytest.raises(ValueError, match="unrecognized field"):
        emitter_read_input(str(input_path))
