"""
Locks `docs/R21_END_TO_END_DEMONSTRATION.md` against silent drift: re-runs
the exact two pipelines that document captures (a repairable identity
system, and R1's own four-cycle obstruction) through the real
`roc-solve-extracted` generator and both real verifiers, and asserts the
certificate contents, digests, and verdicts match what the document
records verbatim. If the extraction, the adapter, or either verifier ever
changes behaviour on these two inputs, this test fails and the
documentation claim is caught out of date rather than silently wrong.

Skips (not fails) if `roc-solve-extracted` and/or `roc-verify-ocaml` have
not been built -- `make check-all` builds both before running this suite
(see the Makefile's own comment on check-all's ordering).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTRACTED_BINARY = REPO_ROOT / "roc-solve-extracted"
OCAML_CHECKER = REPO_ROOT / "roc-verify-ocaml"

extraction_missing = pytest.mark.skipif(
    not os.access(EXTRACTED_BINARY, os.X_OK),
    reason="roc-solve-extracted not built; run `make check-r21-extraction` first",
)
ocaml_checker_missing = pytest.mark.skipif(
    not os.access(OCAML_CHECKER, os.X_OK),
    reason="roc-verify-ocaml not built; run `make check-r21-ocaml` first",
)

REPAIRABLE_INPUT = {"schema": "roc-input/v1", "D": [["1", "0"], ["0", "1"]], "r": ["3", "5"]}
REPAIRABLE_EXPECTED_DIGEST = "sha256:6ed797d190fcb066aece62d0a70065c8ea46f812b4e8e819cbdd8433a4f08b62"
REPAIRABLE_EXPECTED_WITNESS = ["3", "5"]

FOUR_CYCLE_INPUT = {
    "schema": "roc-input/v1",
    "D": [["-1", "1", "0", "0"], ["0", "-1", "1", "0"], ["0", "0", "-1", "1"], ["-1", "0", "0", "1"]],
    "r": ["1", "1", "1", "-2"],
}
FOUR_CYCLE_EXPECTED_DIGEST = "sha256:3db7d90d805d5e8f20708609a395c479951dc1e4ab18901c363f9269ad5bb240"
FOUR_CYCLE_EXPECTED_WITNESS = ["1/5", "1/5", "1/5", "-1/5"]


def run_extracted_solve(input_path, cert_path):
    result = subprocess.run(
        [str(EXTRACTED_BINARY), str(input_path), "--certificate", str(cert_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def run_python_checker(input_path, cert_path) -> int:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"), str(input_path), str(cert_path)],
        capture_output=True, text=True,
    )
    return result.returncode


def run_ocaml_checker(input_path, cert_path) -> int:
    result = subprocess.run([str(OCAML_CHECKER), str(input_path), str(cert_path)], capture_output=True, text=True)
    return result.returncode


@extraction_missing
def test_repairable_example_matches_documented_certificate(tmp_path):
    input_path = tmp_path / "input.json"
    cert_path = tmp_path / "cert.json"
    input_path.write_text(json.dumps(REPAIRABLE_INPUT))
    stdout = run_extracted_solve(input_path, cert_path)
    assert stdout.strip().startswith("REPAIR")

    cert = json.loads(cert_path.read_text())
    assert cert["input_digest"] == REPAIRABLE_EXPECTED_DIGEST
    assert cert["result"] == "repair"
    assert cert["repair"] == REPAIRABLE_EXPECTED_WITNESS

    assert run_python_checker(input_path, cert_path) == 0
    if os.access(OCAML_CHECKER, os.X_OK):
        assert run_ocaml_checker(input_path, cert_path) == 0


@extraction_missing
def test_four_cycle_example_matches_documented_certificate(tmp_path):
    """R1's own canonical witness, produced by the extracted computation,
    must still equal (1/5,1/5,1/5,-1/5) -- the value the demonstration
    document, README.md, and STATUS.md all independently record."""
    input_path = tmp_path / "input.json"
    cert_path = tmp_path / "cert.json"
    input_path.write_text(json.dumps(FOUR_CYCLE_INPUT))
    stdout = run_extracted_solve(input_path, cert_path)
    assert stdout.strip().startswith("SEPARATOR")

    cert = json.loads(cert_path.read_text())
    assert cert["input_digest"] == FOUR_CYCLE_EXPECTED_DIGEST
    assert cert["result"] == "separator"
    assert cert["separator"] == FOUR_CYCLE_EXPECTED_WITNESS

    assert run_python_checker(input_path, cert_path) == 0
    if os.access(OCAML_CHECKER, os.X_OK):
        assert run_ocaml_checker(input_path, cert_path) == 0


@ocaml_checker_missing
def test_digest_agreement_documented_in_demonstration(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(FOUR_CYCLE_INPUT))

    from r21_certificate_format import canonical_input_digest, parse_matrix, parse_vector

    python_digest = canonical_input_digest(parse_matrix(FOUR_CYCLE_INPUT["D"]), parse_vector(FOUR_CYCLE_INPUT["r"]))
    ocaml_result = subprocess.run(
        [str(OCAML_CHECKER), "--digest", str(input_path)], capture_output=True, text=True,
    )
    assert ocaml_result.returncode == 0
    ocaml_digest = ocaml_result.stdout.strip()

    assert python_digest == ocaml_digest == FOUR_CYCLE_EXPECTED_DIGEST
