"""
Step 10F of the tracking-adapter implementation order: locks Example 3
("Stone Soup track fusion") of docs/TRACKING_ADAPTER_END_TO_END_
DEMONSTRATION.md against silent drift, the same discipline tests/
test_tracking_adapter_documentation_drift.py already applies to
Examples 1-2. Re-runs the real pipeline (tracking_adapter_stonesoup_
trackfusion_emitter.build_snapshot, the real R21 emitter, both real
checkers) and asserts the D/r/digest/witness/local-track-x values the
document quotes verbatim still hold.

Skips (not fails) if Stone Soup is not installed, matching every other
Stone-Soup-dependent test file in this repository.
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "TRACKING_ADAPTER_END_TO_END_DEMONSTRATION.md"
OCAML_CHECKER = REPO_ROOT / "roc-verify-ocaml"
SUBPROCESS_TIMEOUT = 60

stonesoup_missing = pytest.mark.skipif(
    importlib.util.find_spec("stonesoup") is None,
    reason="stonesoup not installed; pip install -r requirements-stonesoup.txt first",
)
ocaml_missing = pytest.mark.skipif(
    not os.access(OCAML_CHECKER, os.X_OK),
    reason="roc-verify-ocaml not built; run `make check-r21-ocaml` first",
)

NATURAL_EXPECTED = {
    "D": [["-1", "1"]],
    "r": ["-52909/1000000"],
    "r21_result": "repair",
    "witness": ["52909/1000000", "0"],
    "r21_input_digest": "sha256:e6d3b9545ee213f7f4fb32f7c03d108daa08bbfa469d4a19f61ea41b5e239cda",
}
PERTURBED_EXPECTED = {
    "D": [["-1", "1"]],
    "r": ["9947091/1000000"],
    "r21_result": "repair",
    "witness": ["-9947091/1000000", "0"],
    "r21_input_digest": "sha256:0a624b744a847da1fe45feacb12bde2a563aedbca7c9299872c0c13b3198db18",
}
CAPTURED_LOCAL_TRACK_X = {
    "track:kf-1": "26.98039176055807",
    "track:kf-2": "26.927482582803126",
}
CAPTURED_FUSED_TRACK_X = "26.521051413273668"


def _doc_text() -> str:
    return DOC_PATH.read_text()


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT)


def _pipeline(tmp_dir: Path, tag: str, policy: str) -> dict:
    snapshot_path = tmp_dir / f"{tag}_snapshot.json"
    cert_path = tmp_dir / f"{tag}_cert.json"
    roc_input_path = tmp_dir / f"{tag}_roc_input.json"
    r21_cert_path = tmp_dir / f"{tag}_r21_cert.json"

    result = _run([sys.executable, str(REPO_ROOT / "tracking_adapter_stonesoup_trackfusion_emitter.py"),
                   "--output", str(snapshot_path), "--policy", policy])
    assert result.returncode == 0, result.stdout + result.stderr

    result = _run([sys.executable, str(REPO_ROOT / "tracking_adapter_verifier.py"), str(snapshot_path)])
    assert result.returncode == 0, result.stdout + result.stderr

    result = _run([sys.executable, str(REPO_ROOT / "tracking_adapter_certificate.py"), "emit",
                    str(snapshot_path), "--output", str(cert_path)])
    assert result.returncode == 0, result.stdout + result.stderr
    cert = json.loads(cert_path.read_text())
    doc = json.loads(snapshot_path.read_text())

    roc_input_path.write_text(json.dumps(cert["roc_input"]))
    result = _run([sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(roc_input_path),
                    "--certificate", str(r21_cert_path)])
    assert result.returncode == 0, result.stdout + result.stderr
    r21_cert = json.loads(r21_cert_path.read_text())

    result = _run([sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"),
                    str(roc_input_path), str(r21_cert_path)])
    assert result.returncode == 0, result.stdout + result.stderr

    return {"doc": doc, "cert": cert, "r21_cert": r21_cert,
            "roc_input_path": roc_input_path, "r21_cert_path": r21_cert_path}


@pytest.fixture(scope="module")
def both_policies(tmp_path_factory):
    if importlib.util.find_spec("stonesoup") is None:
        pytest.skip("stonesoup not installed; pip install -r requirements-stonesoup.txt first")
    tmp_dir = tmp_path_factory.mktemp("doc-drift")
    natural = _pipeline(tmp_dir, "natural", "natural")
    perturbed = _pipeline(tmp_dir, "perturbed", "artificial_perturbation")
    return natural, perturbed


def test_documentation_file_exists():
    assert DOC_PATH.exists()


@stonesoup_missing
def test_natural_policy_matches_documented_claims(both_policies):
    natural, _ = both_policies
    assert natural["cert"]["D"] == NATURAL_EXPECTED["D"]
    assert natural["cert"]["r"] == NATURAL_EXPECTED["r"]
    assert natural["r21_cert"]["result"] == NATURAL_EXPECTED["r21_result"]
    assert natural["r21_cert"]["repair"] == NATURAL_EXPECTED["witness"]
    assert natural["r21_cert"]["input_digest"] == NATURAL_EXPECTED["r21_input_digest"]


@stonesoup_missing
def test_perturbed_policy_matches_documented_claims(both_policies):
    _, perturbed = both_policies
    assert perturbed["cert"]["D"] == PERTURBED_EXPECTED["D"]
    assert perturbed["cert"]["r"] == PERTURBED_EXPECTED["r"]
    assert perturbed["r21_cert"]["result"] == PERTURBED_EXPECTED["r21_result"]
    assert perturbed["r21_cert"]["repair"] == PERTURBED_EXPECTED["witness"]
    assert perturbed["r21_cert"]["input_digest"] == PERTURBED_EXPECTED["r21_input_digest"]


@stonesoup_missing
def test_captured_local_track_x_values_match_documented_claims(both_policies):
    natural, _ = both_policies
    for track in natural["doc"]["tracks"]:
        assert track["state_values"] == [CAPTURED_LOCAL_TRACK_X[track["track_id"]]]


@stonesoup_missing
def test_captured_fused_track_x_matches_documented_claim(both_policies):
    from tracking_adapter_stonesoup_trackfusion_emitter import capture_fused_track_report
    report = capture_fused_track_report("natural")
    assert report["stonesoup_fused_track_position_x"] == CAPTURED_FUSED_TRACK_X
    assert CAPTURED_FUSED_TRACK_X in _doc_text()


@stonesoup_missing
@ocaml_missing
def test_both_r21_checkers_accept_both_policies(both_policies):
    for run in both_policies:
        result = _run([str(OCAML_CHECKER), str(run["roc_input_path"]), str(run["r21_cert_path"])])
        assert result.returncode == 0, result.stdout + result.stderr


@stonesoup_missing
def test_complete_chains_verify(both_policies):
    from tracking_adapter_certificate import verify_chain
    for run in both_policies:
        chain = verify_chain(run["doc"], run["cert"], run["r21_cert"])
        assert chain.accepted, chain.reasons


@pytest.mark.parametrize("expected_value", [
    "tracking_adapter_stonesoup_trackfusion.py",
    "tracking_adapter_stonesoup_trackfusion_emitter.py",
    "STONESOUP_TRACK_FUSION_EVALUATOR_SPEC.md",
    "rational_linear_algebra.nullspace_over_Q",
])
def test_doc_references_the_actual_command_and_file_names(expected_value):
    assert expected_value in _doc_text()


def test_doc_states_the_topology_boundary():
    """Load-bearing wording, not just a value check -- the document must
    say plainly that this topology cannot demonstrate an obstruction."""
    text = _doc_text()
    assert "rank(D) = 1 = dim(C^1)" in text
    assert "cannot" in text and "obstruction" in text


def test_doc_states_the_provenance_vs_statistical_independence_distinction():
    assert "statistically independent" in _doc_text()


def test_doc_witness_values_are_present_verbatim():
    doc = _doc_text()
    for value in (NATURAL_EXPECTED["r21_input_digest"], PERTURBED_EXPECTED["r21_input_digest"]):
        assert value in doc
    for value in NATURAL_EXPECTED["witness"] + PERTURBED_EXPECTED["witness"]:
        assert value in doc
