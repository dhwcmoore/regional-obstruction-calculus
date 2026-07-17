"""
Tests for tracking_adapter_format.py -- step 1 of the tracking-adapter
implementation order (docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER
_SPEC.md). Structural schema/domain-object validation only: closed
fields, required fields, duplicate identifiers, dangling references.
Does not test D/r derivation (step 3) or decimal conversion (step 2) --
those get their own modules and their own test files.
"""

import copy

import pytest

from tracking_adapter_format import (
    SNAPSHOT_SCHEMA,
    parse_comparison_edge,
    parse_detection,
    parse_snapshot_doc,
    parse_source,
    parse_track,
    parse_transformation,
)


def _valid_source(source_id="src-1"):
    return {
        "source_id": source_id,
        "sensor_modality": "radar",
        "platform_id": "platform-1",
        "source_data_digest": "sha256:" + "a" * 64,
        "source_timestamp_utc": "2026-01-01T00:00:00Z",
        "coordinate_frame": "frame-A",
        "measurement_model_id": "model-1",
    }


def _valid_detection(detection_id="det-1", source_id="src-1"):
    return {
        "detection_id": detection_id,
        "source_id": source_id,
        "timestamp_utc": "2026-01-01T00:00:00Z",
        "state_values": ["10.000000", "20.000000"],
        "coordinate_frame": "frame-A",
        "transformation_history": [],
        "source_record_digest": "sha256:" + "b" * 64,
    }


def _valid_track(track_id="trk-1", tracker_id="tracker-1", detection_ids=("det-1",)):
    return {
        "track_id": track_id,
        "tracker_id": tracker_id,
        "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
        "state_values": ["10.000000", "20.000000"],
        "state_space": "position-2d",
        "contributing_detection_ids": list(detection_ids),
        "ancestry": [],
        "transformation_record": "identity",
        "track_digest": "sha256:" + "c" * 64,
    }


def _valid_edge(edge_id="e12", source_track_id="trk-1", target_track_id="trk-2"):
    return {
        "edge_id": edge_id,
        "source_track_id": source_track_id,
        "target_track_id": target_track_id,
        "orientation": "source_to_target",
        "comparison_space_id": "cmp-1",
        "transformation_id": "xform-1",
        "discrepancy": "1.000000",
        "coreference_provenance": "operator-declared",
    }


def _valid_transformation(transformation_id, edge_id, track_id, offset="0"):
    return {
        "transformation_id": transformation_id,
        "edge_id": edge_id,
        "track_id": track_id,
        "kind": "additive_offset",
        "offset": offset,
    }


def _valid_snapshot():
    return {
        "schema_version": SNAPSHOT_SCHEMA,
        "scenario_id": "test-001",
        "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
        "state_space": {"dimension": 2},
        "quantisation_policy": {"position_decimal_places": 6},
        "correction_policy": {"kind": "additive-per-track"},
        "sources": [_valid_source("src-1"), _valid_source("src-2")],
        "detections": [
            _valid_detection("det-1", "src-1"),
            _valid_detection("det-2", "src-2"),
        ],
        "tracks": [
            _valid_track("trk-1", "tracker-1", ("det-1",)),
            _valid_track("trk-2", "tracker-2", ("det-2",)),
        ],
        "transformations": [
            _valid_transformation("xf-e12-1", "e12", "trk-1", "0"),
            _valid_transformation("xf-e12-2", "e12", "trk-2", "1"),
        ],
        "comparison_edges": [_valid_edge("e12", "trk-1", "trk-2")],
        "provenance": [],
        "derived_problem": {"D": [], "r": []},
        "payload_digest": "sha256:" + "d" * 64,
    }


# --- domain objects: closed + required keys ---------------------------

def test_valid_source_parses():
    parse_source(_valid_source())


def test_source_rejects_unknown_field():
    obj = _valid_source()
    obj["extra_field"] = "nope"
    with pytest.raises(ValueError, match="unrecognized field"):
        parse_source(obj)


def test_source_rejects_missing_field():
    obj = _valid_source()
    del obj["platform_id"]
    with pytest.raises(ValueError, match="missing required field"):
        parse_source(obj)


def test_valid_detection_parses():
    parse_detection(_valid_detection())


def test_detection_covariance_optional():
    obj = _valid_detection()
    d = parse_detection(obj)
    assert d.covariance is None


def test_detection_rejects_unknown_field():
    obj = _valid_detection()
    obj["bogus"] = 1
    with pytest.raises(ValueError, match="unrecognized field"):
        parse_detection(obj)


def test_valid_track_parses():
    parse_track(_valid_track())


def test_track_rejects_missing_field():
    obj = _valid_track()
    del obj["ancestry"]
    with pytest.raises(ValueError, match="missing required field"):
        parse_track(obj)


def test_valid_edge_parses():
    parse_comparison_edge(_valid_edge())


def test_edge_rejects_unknown_field():
    obj = _valid_edge()
    obj["bogus"] = 1
    with pytest.raises(ValueError, match="unrecognized field"):
        parse_comparison_edge(obj)


def test_valid_transformation_parses():
    parse_transformation(_valid_transformation("xf-1", "e12", "trk-1"))


def test_transformation_rejects_unsupported_kind():
    obj = _valid_transformation("xf-1", "e12", "trk-1")
    obj["kind"] = "projective"
    with pytest.raises(ValueError, match="unsupported transformation kind"):
        parse_transformation(obj)


def test_transformation_rejects_unknown_field():
    obj = _valid_transformation("xf-1", "e12", "trk-1")
    obj["bogus"] = 1
    with pytest.raises(ValueError, match="unrecognized field"):
        parse_transformation(obj)


# --- transformation cross-referencing within a full snapshot -----------

def test_snapshot_rejects_transformation_dangling_edge_reference():
    doc = _valid_snapshot()
    doc["transformations"][0] = _valid_transformation("xf-bad", "e-does-not-exist", "trk-1")
    with pytest.raises(ValueError, match="references unknown edge_id"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_transformation_track_not_an_edge_endpoint():
    doc = _valid_snapshot()
    doc["tracks"].append(_valid_track("trk-3", "tracker-3", ("det-1",)))
    doc["transformations"][0] = _valid_transformation("xf-bad", "e12", "trk-3")
    with pytest.raises(ValueError, match="not an endpoint of edge"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_edge_missing_a_transformation():
    doc = _valid_snapshot()
    doc["transformations"].pop()  # remove trk-2's transformation for e12
    with pytest.raises(ValueError, match="has no declared transformation"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_edge_with_duplicate_transformation_for_same_track():
    doc = _valid_snapshot()
    doc["transformations"].append(_valid_transformation("xf-e12-1-dup", "e12", "trk-1", "5"))
    with pytest.raises(ValueError, match="expected exactly 1"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_duplicate_transformation_id():
    doc = _valid_snapshot()
    doc["transformations"][1] = dict(doc["transformations"][1], transformation_id="xf-e12-1")
    with pytest.raises(ValueError, match="duplicate transformation_id"):
        parse_snapshot_doc(doc)


# --- full snapshot ------------------------------------------------------

def test_valid_snapshot_parses():
    snap = parse_snapshot_doc(_valid_snapshot())
    assert snap.schema_version == SNAPSHOT_SCHEMA
    assert len(snap.sources) == 2
    assert len(snap.detections) == 2
    assert len(snap.tracks) == 2
    assert len(snap.comparison_edges) == 1


def test_snapshot_rejects_unknown_top_level_field():
    doc = _valid_snapshot()
    doc["mystery"] = 1
    with pytest.raises(ValueError, match="unrecognized field"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_missing_top_level_field():
    doc = _valid_snapshot()
    del doc["provenance"]
    with pytest.raises(ValueError, match="missing required field"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_wrong_schema_version():
    doc = _valid_snapshot()
    doc["schema_version"] = "tracking-adapter/v0"
    with pytest.raises(ValueError, match="unrecognized schema_version"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_derived_problem_unknown_field():
    doc = _valid_snapshot()
    doc["derived_problem"]["extra"] = 1
    with pytest.raises(ValueError, match="unrecognized field"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_duplicate_source_id():
    doc = _valid_snapshot()
    doc["sources"].append(_valid_source("src-1"))  # duplicate of an existing id
    with pytest.raises(ValueError, match="duplicate source_id"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_duplicate_track_id():
    doc = _valid_snapshot()
    doc["tracks"].append(_valid_track("trk-1", "tracker-3", ("det-1",)))
    with pytest.raises(ValueError, match="duplicate track_id"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_duplicate_edge_id():
    doc = _valid_snapshot()
    doc["comparison_edges"].append(_valid_edge("e12", "trk-2", "trk-1"))
    with pytest.raises(ValueError, match="duplicate edge_id"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_detection_dangling_source_reference():
    doc = _valid_snapshot()
    doc["detections"][0] = _valid_detection("det-1", "src-does-not-exist")
    with pytest.raises(ValueError, match="unknown source_id"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_track_dangling_detection_reference():
    doc = _valid_snapshot()
    doc["tracks"][0] = _valid_track("trk-1", "tracker-1", ("det-does-not-exist",))
    with pytest.raises(ValueError, match="unknown detection_id"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_edge_dangling_track_reference():
    doc = _valid_snapshot()
    doc["comparison_edges"][0] = _valid_edge("e12", "trk-1", "trk-does-not-exist")
    with pytest.raises(ValueError, match="unknown target_track_id"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_edge_comparing_track_to_itself():
    doc = _valid_snapshot()
    doc["comparison_edges"][0] = _valid_edge("e12", "trk-1", "trk-1")
    with pytest.raises(ValueError, match="compares a track to itself"):
        parse_snapshot_doc(doc)


def test_snapshot_rejects_non_dict_snapshot():
    with pytest.raises(ValueError, match="must be a JSON object"):
        parse_snapshot_doc(["not", "a", "dict"])


def test_snapshot_rejects_non_list_sources():
    doc = _valid_snapshot()
    doc["sources"] = {"not": "a list"}
    with pytest.raises(ValueError, match="sources must be a list"):
        parse_snapshot_doc(doc)


def test_deep_copy_independence_of_fixture_helpers():
    """Sanity check on the test helpers themselves: mutating one snapshot
    dict must not affect another, since several tests above mutate the
    dict returned by _valid_snapshot() in place."""
    a = _valid_snapshot()
    b = _valid_snapshot()
    a["sources"].append(_valid_source("src-3"))
    assert len(b["sources"]) == 2
