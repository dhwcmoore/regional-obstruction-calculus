"""
Tests for the tracked tracking-adapter example corpus
(examples/tracking_adapter/) -- step 6 of the tracking-adapter
implementation order.

Every artifact on disk is REGENERATED from the same builder functions
used elsewhere in this test suite and compared byte-for-byte (via
parsed JSON equality, which is stricter than string equality would be
useless for -- it catches meaning-changing drift while ignoring
incidental whitespace) against the tracked file. This is deliberate:
it proves the tracked examples are reproducible from the actual
production code, not hand-edited or stale, and it would catch
canonicalisation drift (e.g. a change to rational-string formatting or
digest serialisation) the moment it changed what these fixtures
produce.

Malformed/tampered cases are NOT stored as additional fixture files --
those are already covered exhaustively in test_tracking_adapter_
verifier.py and test_tracking_adapter_certificate.py, constructed
in-memory. This directory stays a small, legible demonstration corpus:
two scenarios, four files each, plus a README.
"""

import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from tracking_adapter_certificate import emit_certificate, verify_chain
from tracking_adapter_verifier import compute_payload_digest, verify_snapshot_doc

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "examples" / "tracking_adapter"
OCAML_BINARY = REPO_ROOT / "roc-verify-ocaml"
SUBPROCESS_TIMEOUT = 30

ocaml_missing = pytest.mark.skipif(
    not os.access(OCAML_BINARY, os.X_OK),
    reason="roc-verify-ocaml not built; run `make check-r21-ocaml` first",
)

QUANTISATION_POLICY = {
    "position_decimal_places": 6,
    "transform_decimal_places": 6,
    "rounding_mode": "half_even",
}


# --- builders (same shape as the generator/verifier/certificate test files) --

def _source(source_id):
    return {
        "source_id": source_id, "sensor_modality": "radar", "platform_id": "platform-1",
        "source_data_digest": "sha256:" + "a" * 64, "source_timestamp_utc": "2026-01-01T00:00:00Z",
        "coordinate_frame": "frame-A", "measurement_model_id": "model-1",
    }


def _detection(detection_id, source_id):
    return {
        "detection_id": detection_id, "source_id": source_id, "timestamp_utc": "2026-01-01T00:00:00Z",
        "state_values": ["0"], "coordinate_frame": "frame-A", "transformation_history": [],
        "source_record_digest": "sha256:" + "b" * 64,
    }


def _track(track_id, tracker_id, state_value, detection_ids):
    return {
        "track_id": track_id, "tracker_id": tracker_id, "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
        "state_values": [state_value], "state_space": "scalar",
        "contributing_detection_ids": list(detection_ids), "ancestry": [],
        "transformation_record": "identity", "track_digest": "sha256:" + "c" * 64,
    }


def _edge(edge_id, source_track_id, target_track_id, discrepancy):
    return {
        "edge_id": edge_id, "source_track_id": source_track_id, "target_track_id": target_track_id,
        "orientation": "source_to_target", "comparison_space_id": "cmp-1",
        "transformation_id": "family-1", "discrepancy": discrepancy,
        "coreference_provenance": "operator-declared",
    }


def _xf(transformation_id, edge_id, track_id, offset):
    return {
        "transformation_id": transformation_id, "edge_id": edge_id, "track_id": track_id,
        "kind": "additive_offset", "offset": offset,
    }


def _four_cycle(offsets, discrepancies):
    tracks = [_track(f"t{i}", f"tracker-{i}", "100", ["det-1"]) for i in (1, 2, 3, 4)]
    edges_meta = [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]
    transformations = []
    for edge_id, i, j in edges_meta:
        transformations.append(_xf(f"xf-{edge_id}-{i}", edge_id, i, offsets[(edge_id, i)]))
        transformations.append(_xf(f"xf-{edge_id}-{j}", edge_id, j, offsets[(edge_id, j)]))
    edges = [_edge(eid, i, j, discrepancies[eid]) for eid, i, j in edges_meta]
    return tracks, transformations, edges


def _make_doc(scenario_id, tracks, transformations, edges):
    doc = {
        "schema_version": "tracking-adapter/v1",
        "scenario_id": scenario_id,
        "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
        "state_space": {"dimension": 1},
        "quantisation_policy": QUANTISATION_POLICY,
        "correction_policy": {"kind": "additive-per-track"},
        "sources": [_source("src-1")],
        "detections": [_detection("det-1", "src-1")],
        "tracks": tracks,
        "transformations": transformations,
        "comparison_edges": edges,
        "provenance": [],
        "derived_problem": {"D": [], "r": []},
        "payload_digest": "PLACEHOLDER",
    }
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


def build_repairable_doc():
    """b = (0,1,3,2) chosen first (design doc SS13.1's required order);
    r derived from a COHERENT per-track transformation family, not
    copied from Db."""
    coherent = {"t1": "0", "t2": "1", "t3": "3", "t4": "2"}
    offsets = {}
    for edge_id, i, j in [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]:
        offsets[(edge_id, i)] = coherent[i]
        offsets[(edge_id, j)] = coherent[j]
    discrepancies = {"e12": "1", "e23": "2", "e34": "-1", "e14": "2"}
    tracks, transformations, edges = _four_cycle(offsets, discrepancies)
    return _make_doc("repairable-coherent-001", tracks, transformations, edges)


def build_obstructed_doc():
    """r derived from an INCOHERENT edge-specific transformation family,
    reproducing the repository's own canonical r=(1,1,1,-2) bit-exactly,
    not inserted as a literal (design doc SS6/SS13.2)."""
    offsets = {
        ("e12", "t1"): "0", ("e12", "t2"): "1",
        ("e23", "t2"): "0", ("e23", "t3"): "1",
        ("e34", "t3"): "0", ("e34", "t4"): "1",
        ("e14", "t1"): "0", ("e14", "t4"): "-2",
    }
    discrepancies = {"e12": "1", "e23": "1", "e34": "1", "e14": "-2"}
    tracks, transformations, edges = _four_cycle(offsets, discrepancies)
    return _make_doc("obstructed-incoherent-001", tracks, transformations, edges)


def _run_r21_emitter(roc_input: dict, tmp_path) -> dict:
    input_path = tmp_path / "roc_input.json"
    cert_path = tmp_path / "r21_cert.json"
    input_path.write_text(json.dumps(roc_input))
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(input_path),
         "--certificate", str(cert_path)],
        check=True, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    return json.loads(cert_path.read_text())


def _load(name: str):
    return json.loads((FIXTURE_DIR / name).read_text())


def _run_python_checker(input_path, cert_path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"), str(input_path), str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_ocaml_checker(input_path, cert_path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(OCAML_BINARY), str(input_path), str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _check_scenario(scenario: str, build_doc, expected_r21_result: str, tmp_path):
    doc = build_doc()

    # 1. Snapshot verification succeeds.
    ver = verify_snapshot_doc(doc)
    assert ver.accepted, ver.reasons

    # Regenerated snapshot matches the tracked one exactly.
    tracked_snapshot = _load(f"{scenario}_snapshot.json")
    assert doc == tracked_snapshot

    # 2. Regenerated adapter certificate exactly matches the tracked one.
    cert = emit_certificate(doc)
    tracked_cert = _load(f"{scenario}_adapter_certificate.json")
    assert cert == tracked_cert

    # 3. Regenerated R21 input exactly matches the tracked one.
    tracked_roc_input = _load(f"{scenario}_roc_input.json")
    assert cert["roc_input"] == tracked_roc_input

    # 4. Regenerated R21 certificate exactly matches the tracked one.
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)
    tracked_r21_cert = _load(f"{scenario}_r21_certificate.json")
    assert r21_cert == tracked_r21_cert
    assert r21_cert["result"] == expected_r21_result

    # 5. Full-chain verification succeeds.
    chain = verify_chain(doc, cert, r21_cert)
    assert chain.accepted, chain.reasons

    # 6. Python and OCaml R21 checkers both accept the TRACKED files
    # directly (not the regenerated in-memory ones), proving the
    # committed artifacts themselves, not just this test run's fresh
    # output, pass both independent checkers.
    input_path = FIXTURE_DIR / f"{scenario}_roc_input.json"
    cert_path = FIXTURE_DIR / f"{scenario}_r21_certificate.json"
    py_result = _run_python_checker(input_path, cert_path)
    assert py_result.returncode == 0, py_result.stdout + py_result.stderr

    return doc, cert, r21_cert


def test_repairable_fixture_reproduces_and_verifies(tmp_path):
    doc, cert, r21_cert = _check_scenario("repairable", build_repairable_doc, "repair", tmp_path)
    # 7. The repairable case carries the expected b -- NOT the (0,1,3,2)
    # used to construct the fixture's r, but R21's own actual
    # deterministic witness. The four-cycle's incidence matrix D has a
    # 1-dimensional kernel spanned by the all-ones vector (shifting every
    # track's correction by the same constant changes no pairwise
    # discrepancy), so (0,1,3,2) and R21's (-2,-1,1,0) are both valid
    # repairs for the same r, differing by exactly 2*(1,1,1,1). This is
    # a real gauge freedom of the comparison-graph formulation, not a
    # discrepancy to paper over -- the tracked certificate records
    # whatever R21's own solver actually, deterministically produces.
    assert r21_cert["repair"] == ["-2", "-1", "1", "0"]


def test_obstructed_fixture_reproduces_and_verifies(tmp_path):
    doc, cert, r21_cert = _check_scenario("obstructed", build_obstructed_doc, "separator", tmp_path)
    # 8. The obstructed case reproduces r=(1,1,1,-2), y=(1/5,1/5,1/5,-1/5).
    assert cert["r"] == ["1", "1", "1", "-2"]
    y = [Fraction(s) for s in r21_cert["separator"]]
    assert y == [Fraction(1, 5), Fraction(1, 5), Fraction(1, 5), Fraction(-1, 5)]


@ocaml_missing
def test_repairable_fixture_ocaml_checker_accepts():
    input_path = FIXTURE_DIR / "repairable_roc_input.json"
    cert_path = FIXTURE_DIR / "repairable_r21_certificate.json"
    result = _run_ocaml_checker(input_path, cert_path)
    assert result.returncode == 0, result.stdout + result.stderr


@ocaml_missing
def test_obstructed_fixture_ocaml_checker_accepts():
    input_path = FIXTURE_DIR / "obstructed_roc_input.json"
    cert_path = FIXTURE_DIR / "obstructed_r21_certificate.json"
    result = _run_ocaml_checker(input_path, cert_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_fixture_directory_is_a_small_legible_corpus():
    """Documents the intended shape of this directory: two scenarios,
    four tracked JSON files each, plus a README -- malformed/tampered
    cases belong in the existing in-memory test suites, not as
    additional files here."""
    files = sorted(p.name for p in FIXTURE_DIR.iterdir())
    expected = sorted([
        "README.md",
        "repairable_snapshot.json", "repairable_adapter_certificate.json",
        "repairable_roc_input.json", "repairable_r21_certificate.json",
        "obstructed_snapshot.json", "obstructed_adapter_certificate.json",
        "obstructed_roc_input.json", "obstructed_r21_certificate.json",
    ])
    assert files == expected
