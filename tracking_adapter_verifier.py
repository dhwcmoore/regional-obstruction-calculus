#!/usr/bin/env python3
"""
tracking_adapter_verifier.py

Step 4 of the tracking-adapter implementation order in
`docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md` SS12:
independently reconstructs `(D, r)` from a `tracking-adapter/v1`
snapshot's underlying evidence and rejects unless the reconstruction
succeeds, matches any claimed `derived_problem` exactly, and the
snapshot's own `payload_digest` is internally consistent.

INDEPENDENCE BOUNDARY -- stated precisely, not claimed absolute, per
this repository's own established discipline for that phrase (see
`r21_certificate_checker.py`'s own docstring for the identical pattern
between the R21 emitter and checker):

  Reused from `tracking_adapter_format.py` (SHARED -- schema constants
  and immutable domain-object types, not semantic logic): `SNAPSHOT_
  SCHEMA`, every `*_KEYS` frozenset, `SUPPORTED_TRANSFORMATION_KINDS`,
  and the `Source`/`Detection`/`LocalTrack`/`ComparisonEdge`/
  `Transformation`/`AdapterSnapshot` dataclasses themselves.

  Reused from `r21_certificate_format.py` (SHARED -- generic JSON
  hygiene and the published rational-string grammar, the same category
  R21's own emitter/checker already share): `strict_json_load`,
  `validate_closed_keys`, `parse_rational`, `canonical_input_digest`,
  `MAX_DIMENSION` (repurposed here as the ceiling on snapshot list
  lengths -- a resource limit, not a semantic constant).

  Reused from `tracking_adapter_canon.py` (SHARED, but ONLY the SECOND,
  independently-implemented rounding route): `to_exact_rational_
  independent`. Never `to_exact_rational` (the route
  `tracking_adapter_generator.py` uses) and never `convert_and_verify`
  (which couples both routes together in one call -- using that shared
  wrapper from both sides would reintroduce exactly the coupling this
  file exists to avoid).

  Written from scratch in THIS file, sharing no code with `tracking_
  adapter_generator.py` at all (mechanically enforced by
  `tests/test_tracking_adapter_verifier_independence.py`'s AST scan,
  not merely a docstring claim): closed/required-key checking per
  object, duplicate-identifier checking, dangling-reference checking,
  timestamp and dimension validation, transformation evaluation
  (`F(x) = x + offset`), per-edge residue reconstruction, `D`/`r`
  construction (including column/row ordering), canonical `roc-input/v1`
  reconstruction, the whole-snapshot payload-digest computation, and the
  final accept/reject decision.

  This is INDEPENDENT SEMANTIC RECOMPUTATION, not independent parsing or
  schema implementation from a blank page. The functions below
  necessarily have a similar SHAPE to `tracking_adapter_format.py`'s own
  parsing functions, because the schema rules themselves are shared and
  public (the `*_KEYS` frozensets) -- looking similar is expected and
  does not weaken independence. The load-bearing claim is architectural
  (no import of, or runtime dependence on, `tracking_adapter_generator.
  py`), not stylistic.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Dict, List, Optional

from r21_certificate_format import (
    MAX_DIMENSION,
    canonical_input_digest,
    parse_rational,
    strict_json_load,
    validate_closed_keys,
)
from tracking_adapter_canon import to_exact_rational_independent
from tracking_adapter_format import (
    COMPARISON_EDGE_KEYS,
    DETECTION_KEYS,
    DETECTION_REQUIRED_KEYS,
    SNAPSHOT_KEYS,
    SNAPSHOT_SCHEMA,
    SOURCE_KEYS,
    SUPPORTED_TRANSFORMATION_KINDS,
    TRACK_KEYS,
    TRANSFORMATION_KEYS,
    ComparisonEdge,
    Detection,
    LocalTrack,
    Source,
    Transformation,
)

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# Resource limit, independent of mathematical soundness (same rationale
# as r21_certificate_format.py's own MAX_* constants, reused directly
# here as the allowed shared "resource-limit constant" rather than
# inventing a parallel ceiling for the same purpose).
MAX_SNAPSHOT_LIST_LENGTH = MAX_DIMENSION


@dataclass
class VerificationResult:
    accepted: bool = True
    reasons: List[str] = field(default_factory=list)
    D: Optional[List[List[Fraction]]] = None
    r: Optional[List[Fraction]] = None
    track_order: Optional[List[str]] = None
    edge_order: Optional[List[str]] = None
    roc_input: Optional[dict] = None
    input_digest: Optional[str] = None

    def reject(self, msg: str) -> None:
        self.accepted = False
        self.reasons.append(msg)


def verify_snapshot_doc(doc: Any) -> VerificationResult:
    """Fail-closed: any unexpected exception during verification is
    caught here and converted into a rejection, never allowed to
    propagate as a crash a caller could mistake for "no verdict" rather
    than REJECT -- the same discipline `r21_certificate_checker.check_
    certificate` already documents and follows."""
    result = VerificationResult()
    try:
        _verify(doc, result)
    except Exception as e:
        result.reject(f"unexpected error during verification: {e}")
    return result


def verify_snapshot(path: str) -> VerificationResult:
    try:
        doc = strict_json_load(path)
    except Exception as e:
        result = VerificationResult()
        result.reject(f"malformed snapshot file: {e}")
        return result
    return verify_snapshot_doc(doc)


# ---------------------------------------------------------------------
# Independently-implemented per-object parsing. Each function's SHAPE
# mirrors tracking_adapter_format.py's own parser only because the
# *_KEYS frozensets are shared public schema constants -- see this
# module's own docstring for why that does not weaken independence.
# ---------------------------------------------------------------------

def _v_require_object(obj: Any, label: str) -> dict:
    if not isinstance(obj, dict):
        raise ValueError(f"{label} must be a JSON object, got {obj!r}")
    return obj


def _v_require_keys(obj: dict, required: frozenset, label: str) -> None:
    missing = required - set(obj.keys())
    if missing:
        raise ValueError(f"{label} missing required field(s): {sorted(missing)}")


def _verify_parse_source(obj: Any) -> Source:
    obj = _v_require_object(obj, "source")
    validate_closed_keys(obj, SOURCE_KEYS, "source")
    _v_require_keys(obj, SOURCE_KEYS, "source")
    return Source(**obj)


def _verify_parse_detection(obj: Any) -> Detection:
    obj = _v_require_object(obj, "detection")
    validate_closed_keys(obj, DETECTION_KEYS, "detection")
    _v_require_keys(obj, DETECTION_REQUIRED_KEYS, "detection")
    return Detection(**{**{"covariance": None}, **obj})


def _verify_parse_track(obj: Any) -> LocalTrack:
    obj = _v_require_object(obj, "track")
    validate_closed_keys(obj, TRACK_KEYS, "track")
    _v_require_keys(obj, TRACK_KEYS, "track")
    return LocalTrack(**obj)


def _verify_parse_edge(obj: Any) -> ComparisonEdge:
    obj = _v_require_object(obj, "comparison_edge")
    validate_closed_keys(obj, COMPARISON_EDGE_KEYS, "comparison_edge")
    _v_require_keys(obj, COMPARISON_EDGE_KEYS, "comparison_edge")
    return ComparisonEdge(**obj)


def _verify_parse_transformation(obj: Any) -> Transformation:
    obj = _v_require_object(obj, "transformation")
    validate_closed_keys(obj, TRANSFORMATION_KEYS, "transformation")
    _v_require_keys(obj, TRANSFORMATION_KEYS, "transformation")
    if obj["kind"] not in SUPPORTED_TRANSFORMATION_KINDS:
        raise ValueError(f"unsupported transformation kind {obj['kind']!r}")
    return Transformation(**obj)


def _verify_no_duplicate_ids(items: List[Any], id_attr: str, label: str, result: VerificationResult) -> None:
    seen = set()
    for item in items:
        value = getattr(item, id_attr)
        if value in seen:
            result.reject(f"duplicate {id_attr} in {label}: {value!r}")
        seen.add(value)


def _verify_references(
    sources: List[Source],
    detections: List[Detection],
    tracks: List[LocalTrack],
    edges: List[ComparisonEdge],
    transformations: List[Transformation],
    result: VerificationResult,
) -> None:
    source_ids = {s.source_id for s in sources}
    detection_ids = {d.detection_id for d in detections}
    track_ids = {t.track_id for t in tracks}
    edge_by_id = {e.edge_id: e for e in edges}

    for d in detections:
        if d.source_id not in source_ids:
            result.reject(f"detection {d.detection_id!r} references unknown source_id {d.source_id!r}")

    for t in tracks:
        for did in t.contributing_detection_ids:
            if did not in detection_ids:
                result.reject(f"track {t.track_id!r} references unknown detection_id {did!r}")

    for e in edges:
        if e.source_track_id not in track_ids:
            result.reject(f"comparison_edge {e.edge_id!r} references unknown source_track_id {e.source_track_id!r}")
        if e.target_track_id not in track_ids:
            result.reject(f"comparison_edge {e.edge_id!r} references unknown target_track_id {e.target_track_id!r}")
        if e.source_track_id == e.target_track_id:
            result.reject(f"comparison_edge {e.edge_id!r} compares a track to itself ({e.source_track_id!r})")

    for xf in transformations:
        edge = edge_by_id.get(xf.edge_id)
        if edge is None:
            result.reject(f"transformation {xf.transformation_id!r} references unknown edge_id {xf.edge_id!r}")
            continue
        if xf.track_id not in (edge.source_track_id, edge.target_track_id):
            result.reject(
                f"transformation {xf.transformation_id!r} declares track_id {xf.track_id!r}, "
                f"which is not an endpoint of edge {xf.edge_id!r}"
            )

    per_edge_track_count: Dict[Any, int] = {}
    for xf in transformations:
        key = (xf.edge_id, xf.track_id)
        per_edge_track_count[key] = per_edge_track_count.get(key, 0) + 1
    for e in edges:
        for track_id in (e.source_track_id, e.target_track_id):
            count = per_edge_track_count.get((e.edge_id, track_id), 0)
            if count == 0:
                result.reject(f"comparison_edge {e.edge_id!r} has no declared transformation for track {track_id!r}")
            elif count > 1:
                result.reject(
                    f"comparison_edge {e.edge_id!r} has {count} declared transformations for "
                    f"track {track_id!r}, expected exactly 1"
                )


def _verify_timestamps(sources: List[Source], detections: List[Detection], tracks: List[LocalTrack],
                        result: VerificationResult) -> None:
    for s in sources:
        if not _TIMESTAMP_RE.match(s.source_timestamp_utc):
            result.reject(f"source {s.source_id!r} has a malformed timestamp: {s.source_timestamp_utc!r}")
    for d in detections:
        if not _TIMESTAMP_RE.match(d.timestamp_utc):
            result.reject(f"detection {d.detection_id!r} has a malformed timestamp: {d.timestamp_utc!r}")
    for t in tracks:
        if not _TIMESTAMP_RE.match(t.evaluation_timestamp_utc):
            result.reject(f"track {t.track_id!r} has a malformed timestamp: {t.evaluation_timestamp_utc!r}")


def _verify_dimensions(tracks: List[LocalTrack], result: VerificationResult) -> None:
    for t in tracks:
        if len(t.state_values) != 1:
            result.reject(
                f"track {t.track_id!r} has {len(t.state_values)} state coordinate(s); "
                f"this verifier (v1) only supports exactly 1"
            )


def compute_payload_digest(doc: dict) -> str:
    """Canonical whole-evidence digest, binding `sources`, `detections`,
    `tracks`, `transformations`, and `comparison_edges` (everything
    `(D, r)` is reconstructed FROM) -- the same style as `r21_
    certificate_format.canonical_input_digest` (a fixed, deterministic
    serialisation of the canonical JSON values, not of the input
    document's own incidental formatting). Deliberately excludes
    `derived_problem` (the CLAIM being checked against this evidence,
    not part of the evidence itself) and `payload_digest` (which cannot
    include itself)."""
    canonical = json.dumps(
        {
            "sources": doc["sources"],
            "detections": doc["detections"],
            "tracks": doc["tracks"],
            "transformations": doc["transformations"],
            "comparison_edges": doc["comparison_edges"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _verify(doc: Any, result: VerificationResult) -> None:
    # 1-2: closed schema (duplicate-JSON-key rejection already happened
    # in strict_json_load at the file-reading boundary, for verify_
    # snapshot; here we validate the in-memory structure independently).
    if not isinstance(doc, dict):
        result.reject(f"snapshot is not a JSON object: {doc!r}")
        return
    extra = set(doc.keys()) - SNAPSHOT_KEYS
    if extra:
        result.reject(f"snapshot has unrecognized field(s): {sorted(extra)}")
        return
    missing = SNAPSHOT_KEYS - set(doc.keys())
    if missing:
        result.reject(f"snapshot missing required field(s): {sorted(missing)}")
        return
    if doc.get("schema_version") != SNAPSHOT_SCHEMA:
        result.reject(f"unrecognized schema_version: {doc.get('schema_version')!r}")
        return

    # 3: resource limits before any expensive reconstruction work.
    for key in ("sources", "detections", "tracks", "transformations", "comparison_edges"):
        if not isinstance(doc.get(key), list):
            result.reject(f"{key} must be a list")
            return
        if len(doc[key]) > MAX_SNAPSHOT_LIST_LENGTH:
            result.reject(f"{key} has {len(doc[key])} entries, exceeding MAX_SNAPSHOT_LIST_LENGTH={MAX_SNAPSHOT_LIST_LENGTH}")
            return

    # 4: identifiers and references, independently parsed and checked.
    try:
        sources = [_verify_parse_source(s) for s in doc["sources"]]
        detections = [_verify_parse_detection(d) for d in doc["detections"]]
        tracks = [_verify_parse_track(t) for t in doc["tracks"]]
        edges = [_verify_parse_edge(e) for e in doc["comparison_edges"]]
        transformations = [_verify_parse_transformation(t) for t in doc["transformations"]]
    except ValueError as e:
        result.reject(str(e))
        return

    _verify_no_duplicate_ids(sources, "source_id", "sources", result)
    _verify_no_duplicate_ids(detections, "detection_id", "detections", result)
    _verify_no_duplicate_ids(tracks, "track_id", "tracks", result)
    _verify_no_duplicate_ids(edges, "edge_id", "comparison_edges", result)
    _verify_no_duplicate_ids(transformations, "transformation_id", "transformations", result)
    if not result.accepted:
        return

    _verify_references(sources, detections, tracks, edges, transformations, result)
    if not result.accepted:
        return

    # 5: dimensions and timestamps. (Coordinate-space/units cross-
    # checking beyond dimension count is deferred -- not yet specified
    # precisely enough by the design doc to implement soundly here.)
    _verify_timestamps(sources, detections, tracks, result)
    _verify_dimensions(tracks, result)
    if not result.accepted:
        return

    quantisation_policy = doc["quantisation_policy"]
    for key in ("position_decimal_places", "transform_decimal_places", "rounding_mode"):
        if key not in quantisation_policy:
            result.reject(f"quantisation_policy missing required key {key!r}")
    if not result.accepted:
        return
    position_places = quantisation_policy["position_decimal_places"]
    transform_places = quantisation_policy["transform_decimal_places"]
    rounding_mode = quantisation_policy["rounding_mode"]

    # 6-10: independent decimal conversion, transformation evaluation,
    # residue derivation, and (D, r) construction.
    track_order = [t.track_id for t in tracks]
    col_index = {tid: i for i, tid in enumerate(track_order)}
    track_by_id = {t.track_id: t for t in tracks}
    xf_by_edge_track = {(x.edge_id, x.track_id): x for x in transformations}

    n = len(track_order)
    D: List[List[Fraction]] = []
    r: List[Fraction] = []
    edge_order: List[str] = []

    for edge in edges:
        edge_order.append(edge.edge_id)
        i_id, j_id = edge.source_track_id, edge.target_track_id
        i_track, j_track = track_by_id[i_id], track_by_id[j_id]
        xf_i = xf_by_edge_track[(edge.edge_id, i_id)]
        xf_j = xf_by_edge_track[(edge.edge_id, j_id)]

        try:
            state_i = to_exact_rational_independent(i_track.state_values[0], position_places, rounding_mode)
            state_j = to_exact_rational_independent(j_track.state_values[0], position_places, rounding_mode)
            offset_i = to_exact_rational_independent(xf_i.offset, transform_places, rounding_mode)
            offset_j = to_exact_rational_independent(xf_j.offset, transform_places, rounding_mode)
            declared_discrepancy = to_exact_rational_independent(edge.discrepancy, position_places, rounding_mode)
        except ValueError as e:
            result.reject(f"comparison_edge {edge.edge_id!r}: decimal conversion failed: {e}")
            return

        residue = (state_j + offset_j) - (state_i + offset_i)

        if residue != declared_discrepancy:
            result.reject(
                f"comparison_edge {edge.edge_id!r}: independently reconstructed residue {residue} "
                f"does not match the edge's own declared discrepancy {declared_discrepancy}"
            )
            return

        row = [Fraction(0)] * n
        row[col_index[i_id]] = Fraction(-1)
        row[col_index[j_id]] = Fraction(1)
        D.append(row)
        r.append(residue)

    result.D = D
    result.r = r
    result.track_order = track_order
    result.edge_order = edge_order

    # 11: compare against any claimed derived_problem -- untrusted, never
    # substituted for the independently reconstructed values above.
    claimed = doc["derived_problem"]
    claimed_D_raw = claimed.get("D")
    claimed_r_raw = claimed.get("r")
    if claimed_D_raw or claimed_r_raw:
        try:
            claimed_D = [[parse_rational(x) for x in row] for row in claimed_D_raw]
            claimed_r = [parse_rational(x) for x in claimed_r_raw]
        except (ValueError, TypeError) as e:
            result.reject(f"claimed derived_problem is malformed: {e}")
            return
        if claimed_D != D or claimed_r != r:
            result.reject("claimed derived_problem does not match the independently reconstructed (D, r)")
            return

    # 12: rebuild canonical roc-input/v1, independently.
    result.roc_input = {
        "schema": "roc-input/v1",
        "D": [[str(x) for x in row] for row in D],
        "r": [str(x) for x in r],
    }

    # 13: recompute and compare all relevant digests.
    result.input_digest = canonical_input_digest(D, r)
    expected_payload_digest = compute_payload_digest(doc)
    if doc.get("payload_digest") != expected_payload_digest:
        result.reject(
            f"payload_digest mismatch: snapshot declares {doc.get('payload_digest')!r}, "
            f"but its own evidence digests to {expected_payload_digest!r}"
        )
        return

    # 14: reaching here with result.accepted still True means every check
    # above passed -- ACCEPT.
