#!/usr/bin/env python3
"""
tracking_adapter_stonesoup_emitter.py

Step 10B of the tracking-adapter implementation order
(docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md SS18-19): an
OPTIONAL Stone Soup evidence-emission layer, clearly outside the core
adapter. None of tracking_adapter_format/canon/verifier/certificate/
generator.py import this module or Stone Soup at all -- proved
mechanically by tests/test_stonesoup_import_boundary.py, not merely by
this file living at the repository root.

Instantiates GENUINE Stone Soup objects -- `State`, `Detection`,
`Track`, `LinearGaussian` -- for four local tracks at one fixed
evaluation time, noise disabled, every source of randomness explicitly
seeded, then reduces them to a canonical `tracking-adapter/v1` snapshot,
the exact same schema every hand-authored fixture in `examples/
tracking_adapter/` already uses. This module PROPOSES a snapshot; it is
not the authority that certifies its own derivation -- the existing,
UNMODIFIED `tracking_adapter_verifier.py` remains that authority (design
doc SS5's emission-authority requirement), exercised unchanged via
`tracking_adapter_certificate.emit_certificate`.

SCOPE: two declared TRANSFORMATION POLICIES over the exact same Stone
Soup track evidence (step 10C) -- `"coherent"` (the REPAIRABLE case,
offsets `(0,1,3,2)` matching `examples/tracking_adapter/repairable_
snapshot.json` exactly) and `"canonical_obstruction"` (the OBSTRUCTED
case, edge-specific incoherent offsets matching `examples/tracking_
adapter/obstructed_snapshot.json`'s own construction, reproducing the
repository's canonical `r=(1,1,1,-2)`). `build_local_tracks()` -- the
genuine Stone Soup evidence itself -- is identical for both policies;
only `build_transformations_and_edges(policy)` differs. This is
deliberate: it isolates the structural claim precisely. Stone Soup
supplies the track evidence; the DECLARED TRANSFORMATION POLICY, not
Stone Soup, determines whether the resulting pairwise comparisons
assemble into a globally consistent correction or not. Neither `r`,
`b`, nor `y` is ever inserted as a literal anywhere in this file --
every one is derived from the transformation policy and the shared
track evidence, then independently reconstructed by the unmodified
verifier and certified by the unmodified R21 pipeline.

DETERMINISM POLICY, enforced by `tests/test_stonesoup_source_policy.py`'s
AST scan of this file's own source (not merely asserted in this
docstring):
  - one fixed UTC timestamp, never `datetime.now()`;
  - `numpy.random.seed(...)` and `random.seed(...)` called explicitly,
    at module scope, before any Stone Soup object is built;
  - every `LinearGaussian` constructed with its own explicit `seed=`;
  - noise disabled (`model.function(..., noise=False)`) at every
    measurement -- no `default_rng()` call anywhere, seeded or not;
  - no clutter of any kind;
  - explicit, hand-assigned platform/sensor/detection/tracker IDs, never
    an auto-generated or random identifier;
  - no Stone Soup YAML serialisation (`stonesoup.serialise`) anywhere --
    output is a plain dict, serialised with `json.dumps`, the same as
    every other emitter in this repository.

USAGE:
    python tracking_adapter_stonesoup_emitter.py --output snapshot.json
"""

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from typing import Dict, List

import numpy as np
from stonesoup.models.measurement.linear import LinearGaussian
from stonesoup.types.detection import Detection
from stonesoup.types.state import State
from stonesoup.types.track import Track

from tracking_adapter_verifier import compute_payload_digest

# --- fixed timestamp, never datetime.now() -----------------------------

FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
FIXED_TIMESTAMP_ISO = "2026-01-01T00:00:00Z"

# --- explicit seeds, everywhere ------------------------------------------

GLOBAL_SEED = 20260101
np.random.seed(GLOBAL_SEED)
random.seed(GLOBAL_SEED)

SENSOR_SEEDS = {"t1": 1001, "t2": 1002, "t3": 1003, "t4": 1004}

# --- fixed four-cycle graph, matching examples/tracking_adapter/*.json --

TRACKER_IDS = ["t1", "t2", "t3", "t4"]
EDGES = [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]

# Coherent per-track transformation offsets -- the REPAIRABLE case,
# reproducing examples/tracking_adapter/repairable_snapshot.json's own
# construction exactly, for cross-checking. Keyed by track_id ONLY: the
# same offset applies regardless of which edge references the track.
COHERENT_OFFSETS = {"t1": "0", "t2": "1", "t3": "3", "t4": "2"}

# Incoherent, edge-specific transformation offsets -- the OBSTRUCTED
# case, reproducing examples/tracking_adapter/obstructed_snapshot.json's
# own construction exactly. Keyed by (edge_id, track_id): the SAME track
# gets a DIFFERENT offset depending on which edge references it (e.g.
# t2 is 1 under e12 but 0 under e23) -- this incoherence, not Stone
# Soup's tracks themselves, is what makes the residue fail to be a
# coboundary of any single global assignment (design doc SS5).
INCOHERENT_OFFSETS = {
    ("e12", "t1"): "0", ("e12", "t2"): "1",
    ("e23", "t2"): "0", ("e23", "t3"): "1",
    ("e34", "t3"): "0", ("e34", "t4"): "1",
    ("e14", "t1"): "0", ("e14", "t4"): "-2",
}

TRANSFORMATION_POLICIES = ("coherent", "canonical_obstruction")

GROUND_TRUTH_VALUE = 100  # every track observes the same raw position, both policies

QUANTISATION_POLICY = {
    "position_decimal_places": 6,
    "transform_decimal_places": 6,
    "rounding_mode": "half_even",
}


def _exact_integer_decimal_string(value) -> str:
    """Converts a genuine Stone Soup numeric result (a numpy scalar) to a
    canonical decimal string, refusing to silently accept a non-integer
    floating-point artifact. This fixture's own construction (identity
    measurement model, noise disabled, integer inputs) guarantees every
    value handled here IS an exact integer -- this is a fail-closed
    check on that guarantee (exact terminating-decimal fixture values,
    per this step's own requirement), not a general float-to-decimal
    converter."""
    float_value = float(value)
    if float_value != int(float_value):
        raise ValueError(
            f"expected an exact integer from the noise-free measurement model, got {float_value!r}"
        )
    return str(int(float_value))


def _source_data_digest(tracker_id: str, seed: int, ground_truth_value: int) -> str:
    canonical = f"stonesoup-source:{tracker_id}:{seed}:{ground_truth_value}"
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_local_track(tracker_id: str) -> Dict:
    """Builds ONE local track using genuine Stone Soup objects -- a
    ground-truth `State`, a 1-dimensional `LinearGaussian` measurement
    model (noise disabled, its own explicit seed), a `Detection`
    produced by that model, and a `Track` wrapping the resulting
    state -- not a tracking-shaped dictionary assembled by hand."""
    seed = SENSOR_SEEDS[tracker_id]
    source_id = f"src-{tracker_id}"
    platform_id = f"platform-{tracker_id}"
    detection_id = f"det-{tracker_id}"
    track_id = f"trk-{tracker_id}"

    ground_truth = State(state_vector=[[GROUND_TRUTH_VALUE]], timestamp=FIXED_TIMESTAMP)

    model = LinearGaussian(ndim_state=1, mapping=[0], noise_covar=np.array([[0.0]]), seed=seed)
    measurement_vector = model.function(ground_truth, noise=False)

    detection = Detection(
        state_vector=measurement_vector,
        timestamp=FIXED_TIMESTAMP,
        measurement_model=model,
        metadata={"detection_id": detection_id, "source_id": source_id},
    )

    track_state = State(state_vector=detection.state_vector, timestamp=FIXED_TIMESTAMP)
    track = Track(states=[track_state], id=track_id)

    raw_value = _exact_integer_decimal_string(track.state_vector[0, 0])

    return {
        "source": {
            "source_id": source_id,
            "sensor_modality": "linear_gaussian",
            "platform_id": platform_id,
            "source_data_digest": _source_data_digest(tracker_id, seed, GROUND_TRUTH_VALUE),
            "source_timestamp_utc": FIXED_TIMESTAMP_ISO,
            "coordinate_frame": "frame-A",
            "measurement_model_id": f"linear-gaussian-seed-{seed}",
        },
        "detection": {
            "detection_id": detection.metadata["detection_id"],
            "source_id": detection.metadata["source_id"],
            "timestamp_utc": FIXED_TIMESTAMP_ISO,
            "state_values": [raw_value],
            "coordinate_frame": "frame-A",
            "transformation_history": [],
            "source_record_digest": _source_data_digest(tracker_id, seed, GROUND_TRUTH_VALUE),
        },
        "track": {
            "track_id": track.id,
            "tracker_id": f"tracker-{tracker_id}",
            "evaluation_timestamp_utc": FIXED_TIMESTAMP_ISO,
            "state_values": [raw_value],
            "state_space": "scalar",
            "contributing_detection_ids": [detection.metadata["detection_id"]],
            "ancestry": [f"platform:{platform_id}", f"source:{source_id}", f"detection:{detection_id}"],
            "transformation_record": "identity",
            "track_digest": _source_data_digest(tracker_id, seed, GROUND_TRUTH_VALUE),
        },
    }


def build_local_tracks() -> Dict[str, Dict]:
    """The shared Stone Soup evidence -- IDENTICAL regardless of which
    transformation policy is later declared over it. Called once per
    policy in `build_snapshot`, but produces byte-identical sources/
    detections/tracks each time since every input (seeds, timestamp,
    ground truth value) is fixed."""
    return {tid: build_local_track(tid) for tid in TRACKER_IDS}


def _offset_for(policy: str, edge_id: str, track_id: str) -> str:
    if policy == "coherent":
        return COHERENT_OFFSETS[track_id]
    if policy == "canonical_obstruction":
        return INCOHERENT_OFFSETS[(edge_id, track_id)]
    raise ValueError(f"unknown transformation policy {policy!r}; expected one of {TRANSFORMATION_POLICIES}")


def build_transformations_and_edges(policy: str, local_tracks: Dict[str, Dict]):
    """The ONLY thing that differs between the two policies. Neither `r`
    nor any discrepancy is ever a literal here -- every value is
    computed from the shared track evidence plus this policy's own
    declared offsets, then independently reconstructed downstream by the
    unmodified verifier."""
    transformations = []
    for edge_id, i, j in EDGES:
        for track_id in (i, j):
            transformations.append({
                "transformation_id": f"xf-{policy}-{edge_id}-{track_id}",
                "edge_id": edge_id,
                "track_id": local_tracks[track_id]["track"]["track_id"],
                "kind": "additive_offset",
                "offset": _offset_for(policy, edge_id, track_id),
            })

    comparison_edges = []
    for edge_id, i, j in EDGES:
        ti = int(local_tracks[i]["track"]["state_values"][0])
        tj = int(local_tracks[j]["track"]["state_values"][0])
        oi = int(_offset_for(policy, edge_id, i))
        oj = int(_offset_for(policy, edge_id, j))
        discrepancy = (tj + oj) - (ti + oi)
        comparison_edges.append({
            "edge_id": edge_id,
            "source_track_id": local_tracks[i]["track"]["track_id"],
            "target_track_id": local_tracks[j]["track"]["track_id"],
            "orientation": "source_to_target",
            "comparison_space_id": "cmp-1",
            "transformation_id": f"family-{policy}",
            "discrepancy": str(discrepancy),
            "coreference_provenance": "stonesoup-emitter-declared",
        })

    return transformations, comparison_edges


def build_snapshot(policy: str = "coherent") -> dict:
    if policy not in TRANSFORMATION_POLICIES:
        raise ValueError(f"unknown transformation policy {policy!r}; expected one of {TRANSFORMATION_POLICIES}")

    local_tracks = build_local_tracks()
    sources = [local_tracks[tid]["source"] for tid in TRACKER_IDS]
    detections = [local_tracks[tid]["detection"] for tid in TRACKER_IDS]
    tracks = [local_tracks[tid]["track"] for tid in TRACKER_IDS]
    transformations, comparison_edges = build_transformations_and_edges(policy, local_tracks)

    scenario_id = {
        "coherent": "stonesoup-repairable-001",
        "canonical_obstruction": "stonesoup-obstructed-001",
    }[policy]

    doc = {
        "schema_version": "tracking-adapter/v1",
        "scenario_id": scenario_id,
        "evaluation_timestamp_utc": FIXED_TIMESTAMP_ISO,
        "state_space": {"dimension": 1},
        "quantisation_policy": QUANTISATION_POLICY,
        "correction_policy": {"kind": "additive-per-track", "transformation_policy": policy},
        "sources": sources,
        "detections": detections,
        "tracks": tracks,
        "transformations": transformations,
        "comparison_edges": comparison_edges,
        "provenance": [],
        "derived_problem": {"D": [], "r": []},
        "payload_digest": "PLACEHOLDER",
    }
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit a deterministic Stone Soup tracking-adapter/v1 snapshot.")
    parser.add_argument("--output", required=True, help="path to write the canonical snapshot JSON to")
    parser.add_argument(
        "--policy", choices=TRANSFORMATION_POLICIES, default="coherent",
        help="declared transformation policy over the shared Stone Soup track evidence (default: coherent)",
    )
    args = parser.parse_args()

    snapshot = build_snapshot(args.policy)
    with open(args.output, "w") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
    print(f"EMIT ACCEPT: wrote {args.output} (policy={args.policy})")


if __name__ == "__main__":
    main()
