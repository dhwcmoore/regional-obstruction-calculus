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
# The only orientation this design's D (SS3: row = target-column minus
# source-column) is defined for -- "orientation" was previously a
# free-form required string never checked against any allowed value at
# all, a real gap caught only by asking "what happens if this says
# something else."
ALLOWED_EDGE_ORIENTATIONS = frozenset({"source_to_target"})

# `Transformation`, added when step 3 (the (D,r) generator) needed a
# properly typed object here instead of step 1's original placeholder
# `transformations: List[Dict[str, Any]]` -- the design doc's SS6
# construction needs, per edge, one declared transformation PER
# ENDPOINT TRACK (F_ij^(i) and F_ij^(j)), not one transformation per
# edge as a whole. `kind` is fixed to `"additive_offset"` at v1, the
# same affine family already checked end-to-end in this design's
# feasibility spike (SS20): `F(x) = x + offset`. A `Transformation`
# is looked up by its OWN `(edge_id, track_id)` pair, not by an edge's
# `transformation_id` field -- that field is a human/provenance label
# for which registration procedure was used, not a foreign key into
# this list, to avoid conflating "which named procedure" with "which
# specific per-endpoint parameter record".
TRANSFORMATION_KEYS = frozenset({
    "transformation_id", "edge_id", "track_id", "kind", "offset",
})
SUPPORTED_TRANSFORMATION_KINDS = frozenset({"additive_offset"})

# `AncestryNode` -- step 10D of the tracking-adapter implementation
# order (the Stone Soup data-incest / provenance-admissibility layer).
# Reuses the SNAPSHOT's own pre-existing `provenance` field (previously
# declared but never given real content -- an unvalidated `List[Any]`
# since step 1) to carry the ancestry graph, rather than adding a new
# top-level key for it: `provenance: []` (the value every prior fixture
# already has) now means "no ancestry graph declared", preserving every
# snapshot committed before this step unchanged. `independence_policy`
# IS a new, OPTIONAL top-level key (absent in every pre-10D snapshot,
# which is why it is allowed but not required, see SNAPSHOT_REQUIRED_
# KEYS below) -- it is a policy DECLARATION, not evidence, so folding it
# into `provenance` would conflate the two.
#
# GOVERNING DISTINCTION, stated once here since every function below
# depends on keeping it: R21 (steps 3-9) asks whether accepted pairwise
# declarations can be repaired coherently -- a MATHEMATICAL question
# about (D, r). This layer asks whether those declarations are
# ADMISSIBLE as independent evidence in the first place -- an
# EVIDENTIARY question about the ancestry graph, answered before (D, r)
# is ever computed, and answered independently of whether (D, r) turns
# out repairable or obstructed. Numerical coherence does not establish
# evidential independence, and a genuinely obstructed (D, r) says
# nothing about whether the evidence that produced it was admissible.
ALLOWED_ANCESTRY_NODE_TYPES = frozenset({
    "source_record", "detection", "local_track", "track_feeder",
    "fusion_stage_track", "declared_comparison",
})
ANCESTRY_NODE_KEYS = frozenset({
    "node_id", "node_type", "parent_ids", "originating_source_id",
    "source_record_digest", "transformation_or_feeder_id",
})
ANCESTRY_NODE_REQUIRED_KEYS = ANCESTRY_NODE_KEYS - {"transformation_or_feeder_id"}

INDEPENDENCE_POLICY_KEYS = frozenset({
    "policy_version", "independent_comparisons", "shared_ancestry_prohibited",
    "declared_correlated_reuse",
})

DERIVED_PROBLEM_KEYS = frozenset({"D", "r"})

SNAPSHOT_KEYS = frozenset({
    "schema_version", "scenario_id", "evaluation_timestamp_utc",
    "state_space", "quantisation_policy", "correction_policy",
    "sources", "detections", "tracks", "transformations",
    "comparison_edges", "provenance", "derived_problem", "payload_digest",
    "independence_policy",
})
# `independence_policy` is OPTIONAL -- every snapshot committed before
# step 10D lacks it, and provenance/independence checking (10D) is
# opt-in: absent entirely means "no independence claim is being made,
# skip that checking", not a validation failure.
SNAPSHOT_REQUIRED_KEYS = SNAPSHOT_KEYS - {"independence_policy"}


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
class Transformation:
    transformation_id: str
    edge_id: str
    track_id: str
    kind: str
    offset: str  # canonical decimal string, per SS10 -- exact conversion happens in tracking_adapter_canon.py


@dataclass(frozen=True)
class AncestryNode:
    node_id: str
    node_type: str
    parent_ids: List[str]
    originating_source_id: str
    source_record_digest: str
    transformation_or_feeder_id: Optional[str] = None


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
    transformations: List[Transformation]
    comparison_edges: List[ComparisonEdge]
    provenance: List[AncestryNode]
    derived_problem: Dict[str, Any]
    payload_digest: str
    independence_policy: Optional[Dict[str, Any]] = None


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
    # Dataclass field type annotations are hints, not runtime-enforced --
    # `LocalTrack(**obj)` below would happily accept a string where
    # `List[str]` is declared, so these list-typed fields need an
    # explicit isinstance check, caught only by actually trying a
    # wrong-typed value rather than trusting the annotation.
    if not isinstance(obj["state_values"], list):
        raise ValueError(f"track {obj.get('track_id')!r} state_values must be a list, got {obj['state_values']!r}")
    if not isinstance(obj["ancestry"], list):
        raise ValueError(f"track {obj.get('track_id')!r} ancestry must be a list, got {obj['ancestry']!r}")
    if not isinstance(obj["contributing_detection_ids"], list) or len(obj["contributing_detection_ids"]) == 0:
        raise ValueError(
            f"track {obj.get('track_id')!r} must have at least one contributing_detection_id "
            f"(a track with no ancestry at all is not derived from any evidence)"
        )
    return LocalTrack(**obj)


def parse_transformation(obj: Any) -> Transformation:
    obj = _require_object(obj, "transformation")
    validate_closed_keys(obj, TRANSFORMATION_KEYS, "transformation")
    _require_keys(obj, TRANSFORMATION_KEYS, "transformation")
    if obj["kind"] not in SUPPORTED_TRANSFORMATION_KINDS:
        raise ValueError(
            f"unsupported transformation kind {obj['kind']!r}; "
            f"supported: {sorted(SUPPORTED_TRANSFORMATION_KINDS)}"
        )
    return Transformation(**obj)


def parse_comparison_edge(obj: Any) -> ComparisonEdge:
    obj = _require_object(obj, "comparison_edge")
    validate_closed_keys(obj, COMPARISON_EDGE_KEYS, "comparison_edge")
    _require_keys(obj, COMPARISON_EDGE_KEYS, "comparison_edge")
    if obj["orientation"] not in ALLOWED_EDGE_ORIENTATIONS:
        raise ValueError(
            f"comparison_edge {obj.get('edge_id')!r} has unsupported orientation {obj['orientation']!r}; "
            f"supported: {sorted(ALLOWED_EDGE_ORIENTATIONS)}"
        )
    return ComparisonEdge(**obj)


def parse_ancestry_node(obj: Any) -> AncestryNode:
    obj = _require_object(obj, "ancestry node")
    validate_closed_keys(obj, ANCESTRY_NODE_KEYS, "ancestry node")
    _require_keys(obj, ANCESTRY_NODE_REQUIRED_KEYS, "ancestry node")
    if obj["node_type"] not in ALLOWED_ANCESTRY_NODE_TYPES:
        raise ValueError(
            f"ancestry node {obj.get('node_id')!r} has unsupported node_type {obj['node_type']!r}; "
            f"supported: {sorted(ALLOWED_ANCESTRY_NODE_TYPES)}"
        )
    if not isinstance(obj["parent_ids"], list):
        raise ValueError(f"ancestry node {obj.get('node_id')!r} parent_ids must be a list")
    return AncestryNode(**{**{"transformation_or_feeder_id": None}, **obj})


def _validate_ancestry_graph(nodes: List[AncestryNode]) -> None:
    """Structural checks only -- duplicate node IDs, dangling parent
    references, and cycles. Does NOT compute closures for independence
    checking (that is tracking_adapter_provenance.py's job, a separate
    concern per this step's own governing distinction) -- a malformed
    graph is a SNAPSHOT REJECT regardless of what any independence
    policy says, exactly as a malformed comparison_edges list already
    is regardless of what (D, r) would have been."""
    seen_ids = set()
    for node in nodes:
        if node.node_id in seen_ids:
            raise ValueError(f"duplicate ancestry node_id: {node.node_id!r}")
        seen_ids.add(node.node_id)

    by_id = {node.node_id: node for node in nodes}
    for node in nodes:
        for parent_id in node.parent_ids:
            if parent_id not in by_id:
                raise ValueError(f"ancestry node {node.node_id!r} references unknown parent_id {parent_id!r}")

    # Cycle detection: plain DFS with a recursion-stack set, over the
    # (small, finite) ancestry graph.
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node.node_id: WHITE for node in nodes}

    def visit(node_id: str, path: List[str]) -> None:
        color[node_id] = GRAY
        for parent_id in by_id[node_id].parent_ids:
            if color[parent_id] == GRAY:
                cycle = " -> ".join(path + [parent_id])
                raise ValueError(f"ancestry graph contains a cycle: {cycle}")
            if color[parent_id] == WHITE:
                visit(parent_id, path + [parent_id])
        color[node_id] = BLACK

    for node in nodes:
        if color[node.node_id] == WHITE:
            visit(node.node_id, [node.node_id])


def _validate_references(
    detections: List[Detection],
    tracks: List[LocalTrack],
    edges: List[ComparisonEdge],
    sources: List[Source],
    transformations: List[Transformation],
) -> None:
    """Rejects dangling references -- design doc SS12 item 5 ("reject
    dangling references"), checked here since it is purely structural
    (does not require reconstructing any comparison or matrix
    coefficient), not deferred to the later independent verifier."""
    source_ids = {s.source_id for s in sources}
    detection_ids = {d.detection_id for d in detections}
    track_ids = {t.track_id for t in tracks}
    edge_by_id = {e.edge_id: e for e in edges}

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

    for xf in transformations:
        edge = edge_by_id.get(xf.edge_id)
        if edge is None:
            raise ValueError(f"transformation {xf.transformation_id!r} references unknown edge_id {xf.edge_id!r}")
        if xf.track_id not in (edge.source_track_id, edge.target_track_id):
            raise ValueError(
                f"transformation {xf.transformation_id!r} declares track_id {xf.track_id!r}, "
                f"which is not an endpoint of edge {xf.edge_id!r} "
                f"({edge.source_track_id!r} -> {edge.target_track_id!r})"
            )

    # Every edge needs EXACTLY one transformation per endpoint (SS6: F_ij^(i)
    # and F_ij^(j), both declared) -- neither zero (no registration claim at
    # all) nor more than one (an ambiguous, conflicting claim for the same
    # endpoint under the same edge) is well-formed.
    per_edge_track_count: Dict[Any, int] = {}
    for xf in transformations:
        key = (xf.edge_id, xf.track_id)
        per_edge_track_count[key] = per_edge_track_count.get(key, 0) + 1
    for e in edges:
        for track_id in (e.source_track_id, e.target_track_id):
            count = per_edge_track_count.get((e.edge_id, track_id), 0)
            if count == 0:
                raise ValueError(f"comparison_edge {e.edge_id!r} has no declared transformation for track {track_id!r}")
            if count > 1:
                raise ValueError(
                    f"comparison_edge {e.edge_id!r} has {count} declared transformations for "
                    f"track {track_id!r}, expected exactly 1"
                )


def parse_snapshot_doc(doc: Any) -> AdapterSnapshot:
    """Parses an already-loaded JSON document (a `dict`), performing every
    structural check this module is responsible for. Split out from
    `parse_snapshot` so tests can exercise it directly on in-memory
    fixtures without writing a temp file for every case."""
    doc = _require_object(doc, "snapshot")
    validate_closed_keys(doc, SNAPSHOT_KEYS, "snapshot")
    _require_keys(doc, SNAPSHOT_REQUIRED_KEYS, "snapshot")

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
    transformations = [parse_transformation(t) for t in doc["transformations"]]
    # `provenance` is optionally an ancestry graph (10D) -- `[]` (every
    # pre-10D snapshot's own value) means "no graph declared".
    ancestry_nodes = [parse_ancestry_node(n) for n in doc["provenance"]]

    _check_no_duplicate_ids(sources, "source_id", "sources")
    _check_no_duplicate_ids(detections, "detection_id", "detections")
    _check_no_duplicate_ids(tracks, "track_id", "tracks")
    _check_no_duplicate_ids(edges, "edge_id", "comparison_edges")
    _check_no_duplicate_ids(transformations, "transformation_id", "transformations")
    _check_no_duplicate_ids(ancestry_nodes, "node_id", "provenance (ancestry graph)")

    _validate_references(detections, tracks, edges, sources, transformations)
    _validate_ancestry_graph(ancestry_nodes)

    independence_policy = doc.get("independence_policy")
    if independence_policy is not None:
        independence_policy = _require_object(independence_policy, "independence_policy")
        validate_closed_keys(independence_policy, INDEPENDENCE_POLICY_KEYS, "independence_policy")
        _require_keys(independence_policy, INDEPENDENCE_POLICY_KEYS, "independence_policy")
        if not isinstance(independence_policy["independent_comparisons"], list):
            raise ValueError("independence_policy.independent_comparisons must be a list")
        if not isinstance(independence_policy["declared_correlated_reuse"], list):
            raise ValueError("independence_policy.declared_correlated_reuse must be a list")
        if not isinstance(independence_policy["shared_ancestry_prohibited"], bool):
            raise ValueError("independence_policy.shared_ancestry_prohibited must be a bool")

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
        transformations=transformations,
        comparison_edges=edges,
        provenance=ancestry_nodes,
        derived_problem=derived_problem,
        payload_digest=doc["payload_digest"],
        independence_policy=independence_policy,
    )


def parse_snapshot(path: str) -> AdapterSnapshot:
    doc = strict_json_load(path)
    return parse_snapshot_doc(doc)
