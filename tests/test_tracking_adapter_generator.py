"""
Tests for tracking_adapter_generator.py -- step 3 of the tracking-adapter
implementation order. Reproduces the design doc's own two feasibility-
spiked fixtures (repairable via a COHERENT per-track transformation
family, obstructed via an INCOHERENT edge-specific one reproducing the
repository's own canonical r=(1,1,1,-2)) using real AdapterSnapshot
objects and the real generator module -- not the untracked spike script
-- and, where the OCaml checker is built, runs the result through the
REAL R21 pipeline end to end, matching test_r21_cross_language_agreement
.py's own subprocess conventions.
"""

import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from tracking_adapter_format import parse_snapshot_doc
from tracking_adapter_generator import GeneratorError, generate_problem, to_roc_input

REPO_ROOT = Path(__file__).resolve().parent.parent
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


# --- fixture builders (mirroring tracking_adapter_format's own helpers) ---

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


def _base_snapshot(scenario_id):
    return {
        "schema_version": "tracking-adapter/v1",
        "scenario_id": scenario_id,
        "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
        "state_space": {"dimension": 1},
        "quantisation_policy": QUANTISATION_POLICY,
        "correction_policy": {"kind": "additive-per-track"},
        "sources": [_source("src-1")],
        "detections": [_detection("det-1", "src-1")],
        "provenance": [],
        "derived_problem": {"D": [], "r": []},
        "payload_digest": "sha256:" + "d" * 64,
    }


def _four_cycle_tracks_and_transforms(offsets):
    """`offsets` maps (edge_id, track_id) -> offset decimal string. All
    four tracks report the SAME raw state ('100'), so any nonzero
    discrepancy is purely a consequence of the per-edge transformation
    offsets, not of the raw states themselves -- exactly the
    design doc SS5/SS6 construction, not a naive difference of already-
    known global states."""
    tracks = [_track(f"t{i}", f"tracker-{i}", "100", ["det-1"]) for i in (1, 2, 3, 4)]
    edges_meta = [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]
    transformations = []
    for edge_id, i, j in edges_meta:
        transformations.append(_xf(f"xf-{edge_id}-{i}", edge_id, i, offsets[(edge_id, i)]))
        transformations.append(_xf(f"xf-{edge_id}-{j}", edge_id, j, offsets[(edge_id, j)]))
    return tracks, transformations, edges_meta


# --- 1. Repairable fixture: coherent per-track transformation family ---

def test_repairable_fixture_matches_Db():
    # b = (0,1,3,2) chosen first; a COHERENT per-track offset (same value
    # for a track regardless of which edge references it) reproduces r=Db.
    coherent = {"t1": "0", "t2": "1", "t3": "3", "t4": "2"}
    offsets = {}
    for edge_id, i, j in [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]:
        offsets[(edge_id, i)] = coherent[i]
        offsets[(edge_id, j)] = coherent[j]

    tracks, transformations, edges_meta = _four_cycle_tracks_and_transforms(offsets)
    discrepancies = {"e12": "1", "e23": "2", "e34": "-1", "e14": "2"}  # = Db for b=(0,1,3,2)
    edges = [_edge(eid, i, j, discrepancies[eid]) for eid, i, j in edges_meta]

    doc = _base_snapshot("repairable-001")
    doc.update(tracks=tracks, transformations=transformations, comparison_edges=edges)
    snapshot = parse_snapshot_doc(doc)
    problem = generate_problem(snapshot)

    assert problem.track_order == ["t1", "t2", "t3", "t4"]
    assert problem.edge_order == ["e12", "e23", "e34", "e14"]
    assert problem.r == [Fraction(1), Fraction(2), Fraction(-1), Fraction(2)]
    b = [Fraction(0), Fraction(1), Fraction(3), Fraction(2)]
    Db = [sum(problem.D[row][col] * b[col] for col in range(4)) for row in range(4)]
    assert Db == problem.r


# --- 2. Obstructed fixture: incoherent edge-specific transformation family ---

def test_obstructed_fixture_reproduces_canonical_residue():
    offsets = {
        ("e12", "t1"): "0", ("e12", "t2"): "1",
        ("e23", "t2"): "0", ("e23", "t3"): "1",
        ("e34", "t3"): "0", ("e34", "t4"): "1",
        ("e14", "t1"): "0", ("e14", "t4"): "-2",
    }
    tracks, transformations, edges_meta = _four_cycle_tracks_and_transforms(offsets)
    discrepancies = {"e12": "1", "e23": "1", "e34": "1", "e14": "-2"}
    edges = [_edge(eid, i, j, discrepancies[eid]) for eid, i, j in edges_meta]

    doc = _base_snapshot("obstructed-001")
    doc.update(tracks=tracks, transformations=transformations, comparison_edges=edges)
    snapshot = parse_snapshot_doc(doc)
    problem = generate_problem(snapshot)

    assert problem.r == [Fraction(1), Fraction(1), Fraction(1), Fraction(-2)]
    assert problem.D == [
        [Fraction(-1), Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(-1), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(-1), Fraction(1)],
        [Fraction(-1), Fraction(0), Fraction(0), Fraction(1)],
    ]


def _obstructed_doc():
    offsets = {
        ("e12", "t1"): "0", ("e12", "t2"): "1",
        ("e23", "t2"): "0", ("e23", "t3"): "1",
        ("e34", "t3"): "0", ("e34", "t4"): "1",
        ("e14", "t1"): "0", ("e14", "t4"): "-2",
    }
    tracks, transformations, edges_meta = _four_cycle_tracks_and_transforms(offsets)
    discrepancies = {"e12": "1", "e23": "1", "e34": "1", "e14": "-2"}
    edges = [_edge(eid, i, j, discrepancies[eid]) for eid, i, j in edges_meta]
    doc = _base_snapshot("obstructed-001")
    doc.update(tracks=tracks, transformations=transformations, comparison_edges=edges)
    return doc


# --- 3. Self-consistency check ------------------------------------------

def test_rejects_edge_whose_declared_discrepancy_disagrees_with_evidence():
    doc = _obstructed_doc()
    # Tamper with e12's declared discrepancy so it no longer matches
    # what the track state + transformations actually compute (1).
    for edge in doc["comparison_edges"]:
        if edge["edge_id"] == "e12":
            edge["discrepancy"] = "999"
    snapshot = parse_snapshot_doc(doc)
    with pytest.raises(GeneratorError, match="does not match the edge's own declared discrepancy"):
        generate_problem(snapshot)


# --- 4. Scope restrictions -----------------------------------------------

def test_rejects_multi_dimensional_track():
    doc = _obstructed_doc()
    doc["tracks"][0] = dict(doc["tracks"][0], state_values=["100", "200"])
    snapshot = parse_snapshot_doc(doc)
    with pytest.raises(GeneratorError, match="only supports exactly 1"):
        generate_problem(snapshot)


def test_rejects_missing_quantisation_policy_key():
    doc = _obstructed_doc()
    doc["quantisation_policy"] = {"transform_decimal_places": 6, "rounding_mode": "half_even"}
    snapshot = parse_snapshot_doc(doc)
    with pytest.raises(GeneratorError, match="position_decimal_places"):
        generate_problem(snapshot)


# --- 5. End-to-end through the REAL R21 pipeline -------------------------

def run_python_checker(input_path, cert_path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"), str(input_path), str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def run_ocaml_checker(input_path, cert_path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(OCAML_BINARY), str(input_path), str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def run_emitter(input_path, cert_path) -> None:
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(input_path),
         "--certificate", str(cert_path)],
        check=True, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


@ocaml_missing
def test_obstructed_fixture_end_to_end_through_real_r21(tmp_path):
    doc = _obstructed_doc()
    snapshot = parse_snapshot_doc(doc)
    problem = generate_problem(snapshot)
    roc_input = to_roc_input(problem)

    input_path = tmp_path / "input.json"
    cert_path = tmp_path / "certificate.json"
    input_path.write_text(json.dumps(roc_input))

    run_emitter(input_path, cert_path)
    cert = json.loads(cert_path.read_text())
    assert cert["result"] == "separator"
    y = [Fraction(s) for s in cert["separator"]]
    assert y == [Fraction(1, 5), Fraction(1, 5), Fraction(1, 5), Fraction(-1, 5)]

    py_result = run_python_checker(input_path, cert_path)
    assert py_result.returncode == 0, py_result.stdout + py_result.stderr

    ml_result = run_ocaml_checker(input_path, cert_path)
    assert ml_result.returncode == 0, ml_result.stdout + ml_result.stderr


@ocaml_missing
def test_repairable_fixture_end_to_end_through_real_r21(tmp_path):
    coherent = {"t1": "0", "t2": "1", "t3": "3", "t4": "2"}
    offsets = {}
    for edge_id, i, j in [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]:
        offsets[(edge_id, i)] = coherent[i]
        offsets[(edge_id, j)] = coherent[j]
    tracks, transformations, edges_meta = _four_cycle_tracks_and_transforms(offsets)
    discrepancies = {"e12": "1", "e23": "2", "e34": "-1", "e14": "2"}
    edges = [_edge(eid, i, j, discrepancies[eid]) for eid, i, j in edges_meta]
    doc = _base_snapshot("repairable-001")
    doc.update(tracks=tracks, transformations=transformations, comparison_edges=edges)

    snapshot = parse_snapshot_doc(doc)
    problem = generate_problem(snapshot)
    roc_input = to_roc_input(problem)

    input_path = tmp_path / "input.json"
    cert_path = tmp_path / "certificate.json"
    input_path.write_text(json.dumps(roc_input))

    run_emitter(input_path, cert_path)
    cert = json.loads(cert_path.read_text())
    assert cert["result"] == "repair"

    py_result = run_python_checker(input_path, cert_path)
    assert py_result.returncode == 0, py_result.stdout + py_result.stderr

    ml_result = run_ocaml_checker(input_path, cert_path)
    assert ml_result.returncode == 0, ml_result.stdout + ml_result.stderr
