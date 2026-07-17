#!/usr/bin/env python3
"""
tracking_adapter_format.py

Step 1 of the tracking-adapter implementation order in
`docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md`: the
domain-object model (SS2) and the closed `tracking-adapter/v1` snapshot
schema (SS11). This module is STRUCTURAL validation only -- it does not
derive `(D, r)` from evidence (step 3), perform the decimal-to-rational
conversion (step 2), or independently verify anything against a claimed
`derived_problem` (step 4). Parsing a snapshot with this module says
"this document is a well-formed `tracking-adapter/v1` snapshot with no
dangling references and no duplicate identifiers" -- nothing about
whether its `D`/`r` (if present) actually follow from its evidence.

Reuses `r21_certificate_format.py`'s `strict_json_load` (duplicate-JSON-
key rejection) and `validate_closed_keys` (closed-schema-field rejection)
rather than reimplementing them. This is the same deliberate, narrow
exception that module's own docstring describes for
`r21_certificate_emitter.py`/`r21_certificate_checker.py`: JSON hygiene
(duplicate keys, unknown fields, required fields, dangling ID
references) is not solver logic, and a bug in it can at most cause a
spurious REJECT of a well-formed snapshot, never a false ACCEPT of a
malformed one -- every function below is a positive, fail-closed
assertion that raises `ValueError` on any violation. The design doc's
own independence requirement (SS12: "the [D,r] verifier must NOT import
the same helper functions the adapter generator uses") is about the
SEMANTIC reconstruction of `D`/`r` from evidence (steps 3/4), not about
this structural layer -- exactly as R21's checker and emitter both
import `r21_certificate_format.py` without weakening their independence
from each other.

Schema (`tracking-adapter/v1`), per the design doc SS2/SS11:

    {
      "schema_version": "tracking-adapter/v1",
      "scenario_id": <str>,
      "evaluation_timestamp_utc": <str>,
      "state_space": {...},
      "quantisation_policy": {...},
      "correction_policy": {...},
      "sources": [<Source>, ...],
      "detections": [<Detection>, ...],
      "tracks": [<LocalTrack>, ...],
      "transformations": [{...}, ...],
      "comparison_edges": [<ComparisonEdge>, ...],
      "provenance": [...],
      "derived_problem": {"D": [...], "r": [...]},   -- UNTRUSTED, step 4 recomputes
      "payload_digest": <str>
    }

Every top-level and per-object field is REQUIRED at `v1` (even if an
empty list/dict) except `Detection.covariance`, which is optional
provenance the design doc (SS1) says does not yet enter any equation --
an adapter with no covariance information must still be able to state so
explicitly (`null`) rather than omit the field silently.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from r21_certificate_format import strict_json_load, validate_closed_keys

SNAPSHOT_SCHEMA = "tracking-adapter/v1"

SOURCE_KEYS = frozenset({
    "source_id", "sensor_modality", "platform_id", "source_data_digest",
    "source_timestamp_utc", "coordinate_frame", "measurement_model_id",
})

DETECTION_KEYS = frozenset({
    "detection_id", "source_id", "timestamp_utc", "state_values",
    "coordinate_frame", "transformation_history", "covariance",
    "source_record_digest",
})
DETECTION_REQUIRED_KEYS = DETECTION_KEYS - {"covariance"}

TRACK_KEYS = frozenset({
    "track_id", "tracker_id", "evaluation_timestamp_utc", "state_values",
    "state_space", "contributing_detection_ids", "ancestry",
    "transformation_record", "track_digest",
})

COMPARISON_EDGE_KEYS = frozenset({
    "edge_id", "source_track_id", "target_track_id", "orientation",
    "comparison_space_id", "transformation_id", "discrepancy",
    "coreference_provenance",
})

DERIVED_PROBLEM_KEYS = frozenset({"D", "r"})

SNAPSHOT_KEYS = frozenset({
    "schema_version", "scenario_id", "evaluation_timestamp_utc",
    "state_space", "quantisation_policy", "correction_policy",
    "sources", "detections", "tracks", "transformations",
    "comparison_edges", "provenance", "derived_problem", "payload_digest",
})


@dataclass(frozen=True)
class Source:
    source_id: str
    sensor_modality: str
    platform_id: str
    source_data_digest: str
    source_timestamp_utc: str
    coordinate_frame: str
    measurement_model_id: str


@dataclass(frozen=True)
class Detection:
    detection_id: str
    source_id: str
    timestamp_utc: str
    state_values: List[str]
    coordinate_frame: str
    transformation_history: List[str]
    source_record_digest: str
    covariance: Optional[List[List[str]]] = None


@dataclass(frozen=True)
class LocalTrack:
    track_id: str
    tracker_id: str
    evaluation_timestamp_utc: str
    state_values: List[str]
    state_space: str
    contributing_detection_ids: List[str]
    ancestry: List[str]
    transformation_record: str
    track_digest: str


@dataclass(frozen=True)
class ComparisonEdge:
    edge_id: str
    source_track_id: str
    target_track_id: str
    orientation: str
    comparison_space_id: str
    transformation_id: str
    discrepancy: str
    coreference_provenance: str


@dataclass(frozen=True)
class AdapterSnapshot:
    schema_version: str
    scenario_id: str
    evaluation_timestamp_utc: str
    state_space: Dict[str, Any]
    quantisation_policy: Dict[str, Any]
    correction_policy: Dict[str, Any]
    sources: List[Source]
    detections: List[Detection]
    tracks: List[LocalTrack]
    transformations: List[Dict[str, Any]]
    comparison_edges: List[ComparisonEdge]
    provenance: List[Any]
    derived_problem: Dict[str, Any]
    payload_digest: str


def _require_object(obj: Any, label: str) -> dict:
    if not isinstance(obj, dict):
        raise ValueError(f"{label} must be a JSON object, got {obj!r}")
    return obj


def _require_keys(obj: dict, required: frozenset, label: str) -> None:
    missing = required - set(obj.keys())
    if missing:
        raise ValueError(f"{label} missing required field(s): {sorted(missing)}")


def _check_no_duplicate_ids(items: List[Any], id_attr: str, label: str) -> None:
    seen = set()
    for item in items:
        value = getattr(item, id_attr)
        if value in seen:
            raise ValueError(f"duplicate {id_attr} in {label}: {value!r}")
        seen.add(value)


def parse_source(obj: Any) -> Source:
    obj = _require_object(obj, "source")
    validate_closed_keys(obj, SOURCE_KEYS, "source")
    _require_keys(obj, SOURCE_KEYS, "source")
    return Source(**obj)


def parse_detection(obj: Any) -> Detection:
    obj = _require_object(obj, "detection")
    validate_closed_keys(obj, DETECTION_KEYS, "detection")
    _require_keys(obj, DETECTION_REQUIRED_KEYS, "detection")
    return Detection(**{**{"covariance": None}, **obj})


def parse_track(obj: Any) -> LocalTrack:
    obj = _require_object(obj, "track")
    validate_closed_keys(obj, TRACK_KEYS, "track")
    _require_keys(obj, TRACK_KEYS, "track")
    return LocalTrack(**obj)


def parse_comparison_edge(obj: Any) -> ComparisonEdge:
    obj = _require_object(obj, "comparison_edge")
    validate_closed_keys(obj, COMPARISON_EDGE_KEYS, "comparison_edge")
    _require_keys(obj, COMPARISON_EDGE_KEYS, "comparison_edge")
    return ComparisonEdge(**obj)


def _validate_references(
    detections: List[Detection],
    tracks: List[LocalTrack],
    edges: List[ComparisonEdge],
    sources: List[Source],
) -> None:
    """Rejects dangling references -- design doc SS12 item 5 ("reject
    dangling references"), checked here since it is purely structural
    (does not require reconstructing any comparison or matrix
    coefficient), not deferred to the later independent verifier."""
    source_ids = {s.source_id for s in sources}
    detection_ids = {d.detection_id for d in detections}
    track_ids = {t.track_id for t in tracks}

    for d in detections:
        if d.source_id not in source_ids:
            raise ValueError(f"detection {d.detection_id!r} references unknown source_id {d.source_id!r}")

    for t in tracks:
        for did in t.contributing_detection_ids:
            if did not in detection_ids:
                raise ValueError(f"track {t.track_id!r} references unknown detection_id {did!r}")

    for e in edges:
        if e.source_track_id not in track_ids:
            raise ValueError(f"comparison_edge {e.edge_id!r} references unknown source_track_id {e.source_track_id!r}")
        if e.target_track_id not in track_ids:
            raise ValueError(f"comparison_edge {e.edge_id!r} references unknown target_track_id {e.target_track_id!r}")
        if e.source_track_id == e.target_track_id:
            raise ValueError(f"comparison_edge {e.edge_id!r} compares a track to itself ({e.source_track_id!r})")


def parse_snapshot_doc(doc: Any) -> AdapterSnapshot:
    """Parses an already-loaded JSON document (a `dict`), performing every
    structural check this module is responsible for. Split out from
    `parse_snapshot` so tests can exercise it directly on in-memory
    fixtures without writing a temp file for every case."""
    doc = _require_object(doc, "snapshot")
    validate_closed_keys(doc, SNAPSHOT_KEYS, "snapshot")
    _require_keys(doc, SNAPSHOT_KEYS, "snapshot")

    if doc["schema_version"] != SNAPSHOT_SCHEMA:
        raise ValueError(f"unrecognized schema_version: {doc['schema_version']!r}")

    derived_problem = _require_object(doc["derived_problem"], "derived_problem")
    validate_closed_keys(derived_problem, DERIVED_PROBLEM_KEYS, "derived_problem")
    _require_keys(derived_problem, DERIVED_PROBLEM_KEYS, "derived_problem")

    if not isinstance(doc["sources"], list):
        raise ValueError("sources must be a list")
    if not isinstance(doc["detections"], list):
        raise ValueError("detections must be a list")
    if not isinstance(doc["tracks"], list):
        raise ValueError("tracks must be a list")
    if not isinstance(doc["comparison_edges"], list):
        raise ValueError("comparison_edges must be a list")
    if not isinstance(doc["transformations"], list):
        raise ValueError("transformations must be a list")
    if not isinstance(doc["provenance"], list):
        raise ValueError("provenance must be a list")

    sources = [parse_source(s) for s in doc["sources"]]
    detections = [parse_detection(d) for d in doc["detections"]]
    tracks = [parse_track(t) for t in doc["tracks"]]
    edges = [parse_comparison_edge(e) for e in doc["comparison_edges"]]

    _check_no_duplicate_ids(sources, "source_id", "sources")
    _check_no_duplicate_ids(detections, "detection_id", "detections")
    _check_no_duplicate_ids(tracks, "track_id", "tracks")
    _check_no_duplicate_ids(edges, "edge_id", "comparison_edges")

    _validate_references(detections, tracks, edges, sources)

    return AdapterSnapshot(
        schema_version=doc["schema_version"],
        scenario_id=doc["scenario_id"],
        evaluation_timestamp_utc=doc["evaluation_timestamp_utc"],
        state_space=doc["state_space"],
        quantisation_policy=doc["quantisation_policy"],
        correction_policy=doc["correction_policy"],
        sources=sources,
        detections=detections,
        tracks=tracks,
        transformations=doc["transformations"],
        comparison_edges=edges,
        provenance=doc["provenance"],
        derived_problem=derived_problem,
        payload_digest=doc["payload_digest"],
    )


def parse_snapshot(path: str) -> AdapterSnapshot:
    doc = strict_json_load(path)
    return parse_snapshot_doc(doc)
