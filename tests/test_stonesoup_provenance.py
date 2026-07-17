"""
Step 10D of the tracking-adapter implementation order: end-to-end,
Stone-Soup-driven provenance/data-incest tests, complementing tests/
test_tracking_adapter_provenance.py's fast, hand-built-graph coverage of
the same governing distinction.

Central result under test: identical deterministic Stone Soup track
evidence, identical (D, r), yet different admissibility outcomes solely
because the declared ancestry graph differs between the disjoint and
duplicated-path variants -- numerical coherence does not establish
evidential independence.

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
OCAML_CHECKER = REPO_ROOT / "roc-verify-ocaml"
SUBPROCESS_TIMEOUT = 60

stonesoup_missing = pytest.mark.skipif(
    importlib.util.find_spec("stonesoup") is None,
    reason="stonesoup not installed; pip install -r requirements-stonesoup.txt first",
)


def _run_emitter(variant: str, output_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_stonesoup_provenance.py"),
         "--output", str(output_path), "--variant", variant],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


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


@stonesoup_missing
def test_disjoint_variant_accepted_and_runs_full_r21_pipeline(tmp_path):
    snapshot_path = tmp_path / "disjoint_snapshot.json"
    cert_path = tmp_path / "disjoint_certificate.json"
    roc_input_path = tmp_path / "disjoint_roc_input.json"
    r21_cert_path = tmp_path / "disjoint_r21_certificate.json"

    assert _run_emitter("disjoint", snapshot_path).returncode == 0
    assert _run_verify(snapshot_path).returncode == 0  # PROVENANCE ACCEPT, structurally

    emit_result = _run_emit_cert(snapshot_path, cert_path)
    assert emit_result.returncode == 0, emit_result.stdout + emit_result.stderr
    assert "EMIT ACCEPT" in emit_result.stdout
    cert = json.loads(cert_path.read_text())

    roc_input_path.write_text(json.dumps(cert["roc_input"]))
    r21_result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(roc_input_path),
         "--certificate", str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert r21_result.returncode == 0, r21_result.stdout + r21_result.stderr
    r21_cert = json.loads(r21_cert_path.read_text())
    assert r21_cert["result"] == "repair"

    py_check = subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"), str(roc_input_path), str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert py_check.returncode == 0, py_check.stdout + py_check.stderr


@stonesoup_missing
def test_duplicated_variant_refused_before_certificate_or_r21(tmp_path, monkeypatch):
    snapshot_path = tmp_path / "duplicated_snapshot.json"
    cert_path = tmp_path / "duplicated_certificate.json"

    assert _run_emitter("duplicated", snapshot_path).returncode == 0
    assert _run_verify(snapshot_path).returncode == 0  # well-formed structurally -- SNAPSHOT is fine

    # PROVENANCE REFUSE: emit must fail, produce no certificate file, and
    # never reach R21 at all.
    emit_result = _run_emit_cert(snapshot_path, cert_path)
    assert emit_result.returncode == 1
    assert "EMIT REJECTED" in emit_result.stdout
    assert "UNDECLARED_SHARED_ANCESTRY" in emit_result.stdout
    assert not cert_path.exists()


@stonesoup_missing
def test_correlated_reuse_variant_accepted_but_not_relabelled_independent(tmp_path):
    from tracking_adapter_certificate import emit_certificate
    from tracking_adapter_provenance import check_independence
    from tracking_adapter_verifier import verify_snapshot_doc

    snapshot_path = tmp_path / "correlated_snapshot.json"
    assert _run_emitter("correlated_reuse", snapshot_path).returncode == 0
    doc = json.loads(snapshot_path.read_text())

    ver = verify_snapshot_doc(doc)
    assert ver.accepted, ver.reasons
    prov = check_independence(ver)
    assert prov.accepted
    assert prov.correlated_reuse_edges == ["e12"]
    assert "e12" not in prov.claimed_independent_edges

    cert = emit_certificate(doc)  # does not raise -- structurally accepted
    assert cert is not None


@stonesoup_missing
def test_process_level_determinism_for_each_variant(tmp_path):
    for variant in ("disjoint", "duplicated", "correlated_reuse"):
        path_a = tmp_path / f"{variant}_a.json"
        path_b = tmp_path / f"{variant}_b.json"
        assert _run_emitter(variant, path_a).returncode == 0
        assert _run_emitter(variant, path_b).returncode == 0
        assert path_a.read_bytes() == path_b.read_bytes()


@stonesoup_missing
def test_identical_D_r_different_admissibility_outcomes_stonesoup(tmp_path):
    """The central result: disjoint, duplicated, and correlated_reuse all
    share byte-identical Stone Soup evidence and byte-identical (D, r)
    (all use the SAME coherent transformation policy), yet receive
    different admissibility outcomes -- ACCEPT, REFUSE, ACCEPT-but-not-
    independent -- solely because the declared ancestry graph differs."""
    from tracking_adapter_certificate import CertificateError, emit_certificate
    from tracking_adapter_format import parse_snapshot_doc
    from tracking_adapter_generator import generate_problem

    docs = {}
    for variant in ("disjoint", "duplicated", "correlated_reuse"):
        path = tmp_path / f"{variant}.json"
        assert _run_emitter(variant, path).returncode == 0
        docs[variant] = json.loads(path.read_text())

    problems = {v: generate_problem(parse_snapshot_doc(d)) for v, d in docs.items()}
    assert problems["disjoint"].D == problems["duplicated"].D == problems["correlated_reuse"].D
    assert problems["disjoint"].r == problems["duplicated"].r == problems["correlated_reuse"].r

    assert docs["disjoint"]["sources"] == docs["duplicated"]["sources"] == docs["correlated_reuse"]["sources"]
    assert docs["disjoint"]["tracks"] == docs["duplicated"]["tracks"] == docs["correlated_reuse"]["tracks"]

    emit_certificate(docs["disjoint"])  # ACCEPT
    with pytest.raises(CertificateError, match="UNDECLARED_SHARED_ANCESTRY"):
        emit_certificate(docs["duplicated"])  # REFUSE
    emit_certificate(docs["correlated_reuse"])  # ACCEPT, but not independent (checked elsewhere)
