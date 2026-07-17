"""
Tests for tracking_adapter_verifier.py -- step 4 of the tracking-adapter
implementation order. Covers: acceptance of both production-generated
and independently handwritten valid snapshots, reconstruction of both
the coherent (repairable) and incoherent (obstructed) fixtures, and
rejection of every tamper class the design doc's SS14 names (state,
transformation, orientation, ancestry, D, r, rational conversion,
digest), plus duplicate-key/unknown-field/reordering behaviour.

Architectural independence (no import of tracking_adapter_generator.py,
and no behavioural dependence on it even if monkeypatched) is tested
separately, in test_tracking_adapter_verifier_independence.py.
"""

import copy
import json

import pytest

from tracking_adapter_generator import generate_problem, to_roc_input
from tracking_adapter_format import parse_snapshot_doc
from tracking_adapter_verifier import compute_payload_digest, verify_snapshot_doc

QUANTISATION_POLICY = {
    "position_decimal_places": 6,
    "transform_decimal_places": 6,
    "rounding_mode": "half_even",
}


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


def _coherent_fixture_doc():
    coherent = {"t1": "0", "t2": "1", "t3": "3", "t4": "2"}
    offsets = {}
    for edge_id, i, j in [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]:
        offsets[(edge_id, i)] = coherent[i]
        offsets[(edge_id, j)] = coherent[j]
    discrepancies = {"e12": "1", "e23": "2", "e34": "-1", "e14": "2"}
    tracks, transformations, edges = _four_cycle(offsets, discrepancies)
    return _make_doc("coherent-001", tracks, transformations, edges)


def _obstructed_fixture_doc():
    offsets = {
        ("e12", "t1"): "0", ("e12", "t2"): "1",
        ("e23", "t2"): "0", ("e23", "t3"): "1",
        ("e34", "t3"): "0", ("e34", "t4"): "1",
        ("e14", "t1"): "0", ("e14", "t4"): "-2",
    }
    discrepancies = {"e12": "1", "e23": "1", "e34": "1", "e14": "-2"}
    tracks, transformations, edges = _four_cycle(offsets, discrepancies)
    return _make_doc("obstructed-001", tracks, transformations, edges)


def _make_doc(scenario_id, tracks, transformations, edges, derived_problem=None):
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
        "derived_problem": derived_problem if derived_problem is not None else {"D": [], "r": []},
        "payload_digest": "PLACEHOLDER",
    }
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


# --- 1. Acceptance: independently handwritten valid snapshots -----------

def test_accepts_handwritten_obstructed_snapshot_with_no_claimed_derived_problem():
    doc = _obstructed_fixture_doc()
    result = verify_snapshot_doc(doc)
    assert result.accepted, result.reasons
    assert result.r == [1, 1, 1, -2]
    assert result.track_order == ["t1", "t2", "t3", "t4"]
    assert result.edge_order == ["e12", "e23", "e34", "e14"]


def test_accepts_handwritten_coherent_snapshot():
    doc = _coherent_fixture_doc()
    result = verify_snapshot_doc(doc)
    assert result.accepted, result.reasons
    assert result.r == [1, 2, -1, 2]


# --- 2. Acceptance: production-code-generated derived_problem ----------

def test_accepts_production_generated_derived_problem_matching_evidence():
    doc = _obstructed_fixture_doc()
    snapshot = parse_snapshot_doc(doc)
    problem = generate_problem(snapshot)
    roc_input = to_roc_input(problem)
    doc["derived_problem"] = {"D": roc_input["D"], "r": roc_input["r"]}
    doc["payload_digest"] = compute_payload_digest(doc)  # payload digest excludes derived_problem, but rebuild anyway for clarity

    result = verify_snapshot_doc(doc)
    assert result.accepted, result.reasons
    assert result.r == [1, 1, 1, -2]


def test_rejects_production_generated_derived_problem_that_was_then_tampered():
    doc = _obstructed_fixture_doc()
    snapshot = parse_snapshot_doc(doc)
    problem = generate_problem(snapshot)
    roc_input = to_roc_input(problem)
    tampered_r = list(roc_input["r"])
    tampered_r[-1] = "999"  # tamper with the LAST claimed r component
    doc["derived_problem"] = {"D": roc_input["D"], "r": tampered_r}

    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("does not match the independently reconstructed" in msg for msg in result.reasons)


# --- 3. Tamper: track state value ---------------------------------------

def test_rejects_tampered_track_state_value_via_residue_mismatch():
    """Tampering a track's state, without adjusting anything downstream,
    is caught by residue-consistency BEFORE the digest check is even
    reached (the reconstruction loop returns early on mismatch) -- this
    test documents that ordering; the digest-only detection case (a
    tamper that residue-checking cannot see at all) is tested separately
    below via a field that plays no role in any (D, r) computation."""
    doc = _obstructed_fixture_doc()
    for t in doc["tracks"]:
        if t["track_id"] == "t2":
            t["state_values"] = ["999"]
    doc["payload_digest"] = compute_payload_digest(doc)
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("does not match the edge's own declared discrepancy" in msg for msg in result.reasons)


# --- 4. Tamper: transformation offset ------------------------------------

def test_rejects_tampered_transformation_offset():
    doc = _obstructed_fixture_doc()
    for xf in doc["transformations"]:
        if xf["transformation_id"] == "xf-e12-t2":
            xf["offset"] = "999"
    doc["payload_digest"] = compute_payload_digest(doc)
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("does not match the edge's own declared discrepancy" in msg for msg in result.reasons)


# --- 5. Tamper: edge orientation (reversed, residue not correspondingly flipped) ---

def test_rejects_edge_reversed_orientation_with_unchanged_residue():
    doc = _obstructed_fixture_doc()
    for e in doc["comparison_edges"]:
        if e["edge_id"] == "e12":
            # Reverse orientation but leave `discrepancy` (still "1") and
            # both endpoints' transformations untouched -- an edge whose
            # role assignment flipped without a correspondingly flipped
            # sign on its declared value is internally inconsistent
            # evidence, not a legitimate re-presentation.
            e["source_track_id"], e["target_track_id"] = e["target_track_id"], e["source_track_id"]
    doc["payload_digest"] = compute_payload_digest(doc)
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("does not match the edge's own declared discrepancy" in msg for msg in result.reasons)


# --- 6. Tamper: ancestry / dangling references ---------------------------

def test_rejects_dangling_detection_ancestry():
    doc = _obstructed_fixture_doc()
    for t in doc["tracks"]:
        if t["track_id"] == "t1":
            t["contributing_detection_ids"] = ["det-does-not-exist"]
    doc["payload_digest"] = compute_payload_digest(doc)
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("unknown detection_id" in msg for msg in result.reasons)


# --- 7. Tamper: rational conversion (malformed decimal) ------------------

def test_rejects_malformed_decimal_in_track_state():
    doc = _obstructed_fixture_doc()
    for t in doc["tracks"]:
        if t["track_id"] == "t1":
            t["state_values"] = ["1E5"]  # exponent notation, explicitly rejected
    doc["payload_digest"] = compute_payload_digest(doc)
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("decimal conversion failed" in msg for msg in result.reasons)


# --- 8. Tamper: payload digest -------------------------------------------

def test_rejects_tamper_to_a_field_outside_any_D_r_computation_via_digest_only():
    """`Source.sensor_modality` plays no role in any residue, D entry, or
    r entry -- residue-consistency checking cannot see this tamper at
    all. The payload digest is the ONLY thing that catches it, which is
    exactly why step 4's own sequence puts a digest check at the end
    rather than treating residue-matching as sufficient on its own."""
    doc = _obstructed_fixture_doc()
    doc["sources"][0]["sensor_modality"] = "tampered-modality"
    # payload_digest intentionally NOT recomputed.
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("payload_digest mismatch" in msg for msg in result.reasons)


def test_rejects_tampered_payload_digest_alone():
    doc = _obstructed_fixture_doc()
    doc["payload_digest"] = "sha256:" + "0" * 64
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("payload_digest mismatch" in msg for msg in result.reasons)


# --- 9. Duplicate keys / unknown fields -----------------------------------

def test_rejects_unknown_top_level_field():
    doc = _obstructed_fixture_doc()
    doc["mystery"] = 1
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("unrecognized field" in msg for msg in result.reasons)


def test_rejects_duplicate_json_key_from_file(tmp_path):
    raw = (
        '{"schema_version": "tracking-adapter/v1", "schema_version": "tracking-adapter/v1"}'
    )
    path = tmp_path / "dup.json"
    path.write_text(raw)
    from tracking_adapter_verifier import verify_snapshot
    result = verify_snapshot(str(path))
    assert not result.accepted
    assert any("duplicate" in msg.lower() for msg in result.reasons)


# --- 10. Reordering: legitimately changes the concrete presentation -----

def test_reordering_tracks_changes_column_order_and_digest_but_not_math_content():
    doc = _obstructed_fixture_doc()
    original = verify_snapshot_doc(doc)
    assert original.accepted

    reordered = copy.deepcopy(doc)
    reordered["tracks"] = list(reversed(reordered["tracks"]))
    reordered["payload_digest"] = compute_payload_digest(reordered)
    result = verify_snapshot_doc(reordered)

    assert result.accepted, result.reasons
    # Column order legitimately changed (track_order is part of what D
    # means, per this design -- reordering is NOT expected to produce an
    # identical D, only an equally valid re-presentation of it).
    assert result.track_order == list(reversed(original.track_order))
    assert original.input_digest != result.input_digest
    # But the underlying residues, keyed by edge, are unchanged.
    assert dict(zip(result.edge_order, result.r)) == dict(zip(original.edge_order, original.r))
