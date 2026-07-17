"""
Process-level determinism tests for tracking_adapter_stonesoup_emitter.py
-- step 10B of the tracking-adapter implementation order. Determinism is
required at PROCESS level, not merely within one Python process: the
emitter is run twice as separate `subprocess` invocations (a fresh
Python interpreter, fresh numpy import, fresh Stone Soup import each
time), and every downstream artifact -- canonical snapshot bytes,
payload digest, reconstructed (D, r), adapter certificate, R21
certificate -- is compared byte-for-byte between the two runs.

Skips (not fails) if Stone Soup is not installed -- this file is itself
one of the "Stone-Soup-dependent test files" `make check-stonesoup-
adapter` runs only when `stonesoup` actually imports (see that target's
own comment in the Makefile).
"""

import importlib.util
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
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


def _run_emitter(output_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_stonesoup_emitter.py"), "--output", str(output_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _run_verify(snapshot_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_verifier.py"), str(snapshot_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_emit_cert(snapshot_path: Path, cert_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_certificate.py"), "emit",
         str(snapshot_path), "--output", str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_r21_emitter(roc_input_path: Path, r21_cert_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(roc_input_path),
         "--certificate", str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_python_checker(roc_input_path: Path, r21_cert_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"), str(roc_input_path), str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_ocaml_checker(roc_input_path: Path, r21_cert_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(OCAML_CHECKER), str(roc_input_path), str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _full_pipeline(tmp_dir: Path, tag: str) -> dict:
    """Runs the emitter and the complete existing chain, all as real
    subprocesses, exactly as run_tracking_adapter_pipeline.py does for
    the hand-authored fixtures -- returns everything needed to compare
    two independent runs."""
    snapshot_path = tmp_dir / f"{tag}_snapshot.json"
    cert_path = tmp_dir / f"{tag}_certificate.json"
    roc_input_path = tmp_dir / f"{tag}_roc_input.json"
    r21_cert_path = tmp_dir / f"{tag}_r21_certificate.json"

    _run_emitter(snapshot_path)
    snapshot_bytes = snapshot_path.read_bytes()
    snapshot = json.loads(snapshot_bytes)

    verify_result = _run_verify(snapshot_path)
    assert verify_result.returncode == 0, verify_result.stdout + verify_result.stderr

    emit_result = _run_emit_cert(snapshot_path, cert_path)
    assert emit_result.returncode == 0, emit_result.stdout + emit_result.stderr
    cert = json.loads(cert_path.read_text())

    roc_input_path.write_text(json.dumps(cert["roc_input"]))
    r21_result = _run_r21_emitter(roc_input_path, r21_cert_path)
    assert r21_result.returncode == 0, r21_result.stdout + r21_result.stderr
    r21_cert = json.loads(r21_cert_path.read_text())

    py_check = _run_python_checker(roc_input_path, r21_cert_path)
    assert py_check.returncode == 0, py_check.stdout + py_check.stderr

    return {
        "snapshot_bytes": snapshot_bytes,
        "snapshot": snapshot,
        "cert": cert,
        "r21_cert": r21_cert,
        "roc_input_path": roc_input_path,
        "r21_cert_path": r21_cert_path,
    }


@stonesoup_missing
def test_snapshot_is_repairable_with_expected_witness(tmp_path):
    run = _full_pipeline(tmp_path, "single")
    assert run["r21_cert"]["result"] == "repair"
    # R21's own witness for this D/r, matching examples/tracking_adapter/
    # repairable_r21_certificate.json exactly -- this Stone-Soup-derived
    # fixture reproduces an already-independently-verified value, not a
    # new unchecked one.
    assert run["r21_cert"]["repair"] == ["-2", "-1", "1", "0"]
    assert run["cert"]["r"] == ["1", "2", "-1", "2"]


@stonesoup_missing
def test_process_level_determinism_across_two_separate_runs(tmp_path):
    """The two runs below share NOTHING at the Python-process level --
    each is a fresh interpreter, fresh numpy import, fresh Stone Soup
    import. Determinism here means determinism that survives that, not
    merely "the same object reused twice in one process"."""
    run_a = _full_pipeline(tmp_path, "run_a")
    run_b = _full_pipeline(tmp_path, "run_b")

    # 1-2. Canonical snapshot bytes and payload digest.
    assert run_a["snapshot_bytes"] == run_b["snapshot_bytes"]
    assert run_a["snapshot"]["payload_digest"] == run_b["snapshot"]["payload_digest"]

    # 3. Reconstructed (D, r) -- via the certificate, which the
    # independent verifier's own reconstruction populates.
    assert run_a["cert"]["D"] == run_b["cert"]["D"]
    assert run_a["cert"]["r"] == run_b["cert"]["r"]

    # 4. Adapter certificates.
    assert run_a["cert"] == run_b["cert"]

    # 5. R21 certificates.
    assert run_a["r21_cert"] == run_b["r21_cert"]


@stonesoup_missing
def test_full_chain_verification_accepts(tmp_path):
    from tracking_adapter_certificate import verify_chain

    run = _full_pipeline(tmp_path, "chain")
    snapshot_path = tmp_path / "chain_snapshot.json"
    with open(snapshot_path) as f:
        doc = json.load(f)
    chain = verify_chain(doc, run["cert"], run["r21_cert"])
    assert chain.accepted, chain.reasons


@stonesoup_missing
@ocaml_missing
def test_both_r21_checkers_accept(tmp_path):
    run = _full_pipeline(tmp_path, "both")
    ml_check = _run_ocaml_checker(run["roc_input_path"], run["r21_cert_path"])
    assert ml_check.returncode == 0, ml_check.stdout + ml_check.stderr
