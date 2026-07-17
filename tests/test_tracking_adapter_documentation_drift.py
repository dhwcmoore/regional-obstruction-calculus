"""
Locks docs/TRACKING_ADAPTER_END_TO_END_DEMONSTRATION.md against silent
drift -- the same discipline test_r21_demonstration.py already applies
to docs/R21_END_TO_END_DEMONSTRATION.md. Re-runs the actual pipeline
(via run_tracking_adapter_pipeline.py's own functions, not a re-
implementation) and asserts the certificate contents, digests, witness
values, schema versions, and filenames the document quotes verbatim
still hold. If the adapter, the generator, either verifier, or R21
itself ever changes behaviour on these two tracked fixtures, this test
fails and the documentation claim is caught out of date rather than
silently wrong -- it does not re-verify the mathematics itself (that is
every other tracking-adapter test file's job), only that the DOCUMENT's
own quoted claims match what the pipeline actually produces.
"""

import re
from pathlib import Path

import pytest

from run_tracking_adapter_pipeline import run_scenario

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "TRACKING_ADAPTER_END_TO_END_DEMONSTRATION.md"

REPAIRABLE_EXPECTED = {
    "D": [["-1", "1", "0", "0"], ["0", "-1", "1", "0"], ["0", "0", "-1", "1"], ["-1", "0", "0", "1"]],
    "r": ["1", "2", "-1", "2"],
    "r21_result": "repair",
    "witness": ["-2", "-1", "1", "0"],
    "r21_input_digest": "sha256:b6d1eb992e0b98950549bfc82313889d82883d83bc62668837222aa781c64ac2",
}
OBSTRUCTED_EXPECTED = {
    "D": [["-1", "1", "0", "0"], ["0", "-1", "1", "0"], ["0", "0", "-1", "1"], ["-1", "0", "0", "1"]],
    "r": ["1", "1", "1", "-2"],
    "r21_result": "separator",
    "witness": ["1/5", "1/5", "1/5", "-1/5"],
    "r21_input_digest": "sha256:3db7d90d805d5e8f20708609a395c479951dc1e4ab18901c363f9269ad5bb240",
}


def _doc_text() -> str:
    return DOC_PATH.read_text()


def test_documentation_file_exists():
    assert DOC_PATH.exists()


def test_repairable_scenario_matches_documented_claims():
    summary = run_scenario("repairable", "repair")
    assert summary["D"] == REPAIRABLE_EXPECTED["D"]
    assert summary["r"] == REPAIRABLE_EXPECTED["r"]
    assert summary["r21_result"] == REPAIRABLE_EXPECTED["r21_result"]
    assert summary["witness"] == REPAIRABLE_EXPECTED["witness"]
    assert summary["r21_input_digest"] == REPAIRABLE_EXPECTED["r21_input_digest"]


def test_obstructed_scenario_matches_documented_claims():
    summary = run_scenario("obstructed", "separator")
    assert summary["D"] == OBSTRUCTED_EXPECTED["D"]
    assert summary["r"] == OBSTRUCTED_EXPECTED["r"]
    assert summary["r21_result"] == OBSTRUCTED_EXPECTED["r21_result"]
    assert summary["witness"] == OBSTRUCTED_EXPECTED["witness"]
    assert summary["r21_input_digest"] == OBSTRUCTED_EXPECTED["r21_input_digest"]


def test_obstructed_digest_matches_repository_own_four_cycle_demonstration():
    """The document claims this digest is identical to docs/R21_END_TO_
    END_DEMONSTRATION.md's own four-cycle example -- confirmed directly
    against that document's own text, not just asserted."""
    r21_doc = (REPO_ROOT / "docs" / "R21_END_TO_END_DEMONSTRATION.md").read_text()
    assert OBSTRUCTED_EXPECTED["r21_input_digest"] in r21_doc


@pytest.mark.parametrize("expected_value", [
    "tracking_adapter_verifier.py",
    "tracking_adapter_certificate.py",
    "r21_certificate_emitter.py",
    "r21_certificate_checker.py",
    "roc-verify-ocaml",
    "run_tracking_adapter_pipeline.py",
    "make check-tracking-adapter",
])
def test_doc_references_the_actual_command_names(expected_value):
    assert expected_value in _doc_text()


@pytest.mark.parametrize("expected_value", [
    "tracking-adapter/v1",
    "tracking-adapter-certificate/v1",
    "roc-input/v1",
    "repair-or-separator/v1",
])
def test_doc_references_the_actual_schema_versions(expected_value):
    assert expected_value in _doc_text()
    # Cross-check against the actual code constants, not just each
    # other -- the doc and the code could both be wrong in the same way
    # if only compared to each other.
    from tracking_adapter_certificate import CERTIFICATE_SCHEMA
    from tracking_adapter_format import SNAPSHOT_SCHEMA
    from r21_certificate_format import CERTIFICATE_SCHEMA as R21_CERTIFICATE_SCHEMA, INPUT_SCHEMA
    real_schemas = {SNAPSHOT_SCHEMA, CERTIFICATE_SCHEMA, INPUT_SCHEMA, R21_CERTIFICATE_SCHEMA}
    assert expected_value in real_schemas


def test_doc_references_the_tracked_fixture_filenames():
    for name in [
        "repairable_snapshot.json", "repairable_roc_input.json",
        "obstructed_snapshot.json", "obstructed_roc_input.json",
    ]:
        assert name in _doc_text()
        assert (REPO_ROOT / "examples" / "tracking_adapter" / name).exists()


def test_doc_witness_values_are_not_stale_literals():
    """Every witness quoted in the document must ALSO appear in the
    corresponding tracked R21 certificate file, not just be an
    independently-typed literal that happened to be correct once."""
    import json
    doc = _doc_text()
    repairable_cert = json.loads((REPO_ROOT / "examples" / "tracking_adapter" / "repairable_r21_certificate.json").read_text())
    obstructed_cert = json.loads((REPO_ROOT / "examples" / "tracking_adapter" / "obstructed_r21_certificate.json").read_text())
    assert repairable_cert["repair"] == REPAIRABLE_EXPECTED["witness"]
    assert obstructed_cert["separator"] == OBSTRUCTED_EXPECTED["witness"]
    for value in REPAIRABLE_EXPECTED["witness"] + OBSTRUCTED_EXPECTED["witness"]:
        assert value in doc


def test_doc_states_the_untrusted_coordinator_boundary():
    """The document must explicitly state the orchestrator is not
    another trusted verifier -- a load-bearing wording requirement, not
    just a filename/value check."""
    assert "untrusted coordinator" in _doc_text()
