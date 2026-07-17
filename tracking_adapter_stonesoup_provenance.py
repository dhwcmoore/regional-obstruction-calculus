#!/usr/bin/env python3
"""
tracking_adapter_stonesoup_provenance.py

Step 10D of the tracking-adapter implementation order: builds the three
provenance/data-incest fixtures over the SAME genuine Stone Soup track
evidence `tracking_adapter_stonesoup_emitter.py` already produces
(`build_local_tracks()`, the `"coherent"` transformation policy), each
one differing ONLY in the declared ancestry graph and independence
policy layered on top -- exactly the same "identical evidence, only the
declared structure differs" discipline step 10C already established for
the coherent/obstructed transformation-policy pair.

INSPIRATION, stated precisely so it is not overclaimed: this fixture is
inspired by Stone Soup's own data-incest architecture discussion (the
problem of a fusion node's output feeding back into a tracker that also,
through a different path, contributed to that same fusion output,
producing correlated -- not independent -- evidence). This module does
NOT claim to prove Stone Soup's own statistical fusion output
overconfident for any real scenario; it checks a narrower, purely
structural claim -- whether a DECLARED ancestry graph supports a
DECLARED independence claim between two compared tracks. See
`tracking_adapter_provenance.py`'s own docstring for the exact governing
distinction this rests on.

Framework identities are converted to stable, project-controlled string
IDs immediately (`detection.metadata["detection_id"]`, `track.id`, ...)
-- never Python object identity or a memory address, anywhere.

Three variants:

  - `build_disjoint_snapshot()`: every track's ancestry traces to its
    own distinct source_record -- PROVENANCE ACCEPT expected for every
    comparison.
  - `build_duplicated_path_snapshot()`: tracks t1 and t2 (compared by
    edge e12) BOTH trace back to one shared source_record, via two
    DIFFERENT paths (t1 via an extra `track_feeder` node, t2 directly)
    -- PROVENANCE REFUSE (UNDECLARED_SHARED_ANCESTRY) expected for e12.
  - `build_correlated_reuse_snapshot()`: the same duplicated ancestry as
    above, but with e12 explicitly declared in `declared_correlated_
    reuse` -- PROVENANCE ACCEPT expected, but e12 must NOT appear in
    `claimed_independent_edges` (it is accepted structurally, never
    relabelled independent).

All three share byte-identical `sources`/`detections`/`tracks` (the
underlying Stone Soup evidence) and byte-identical `(D, r)` once
computed -- only `provenance` (the ancestry graph) and
`independence_policy` differ, demonstrating this step's central result:
numerical coherence does not establish evidential independence.
"""

import argparse
import json

from tracking_adapter_stonesoup_emitter import (
    EDGES,
    TRACKER_IDS,
    build_local_tracks,
    build_transformations_and_edges,
)
from tracking_adapter_verifier import compute_payload_digest

POLICY_VERSION = "tracking-adapter-independence-policy/v1"


def _comparison_nodes():
    return [
        {
            "node_id": f"comparison:{edge_id}",
            "node_type": "declared_comparison",
            "parent_ids": [f"track:trk-{i}", f"track:trk-{j}"],
            "originating_source_id": "",
            "source_record_digest": "",
            "transformation_or_feeder_id": None,
        }
        for edge_id, i, j in EDGES
    ]


def _independence_policy(declared_correlated_reuse):
    return {
        "policy_version": POLICY_VERSION,
        "independent_comparisons": [edge_id for edge_id, _, _ in EDGES],
        "shared_ancestry_prohibited": True,
        "declared_correlated_reuse": declared_correlated_reuse,
    }


def _base_doc(local_tracks: dict) -> dict:
    sources = [local_tracks[tid]["source"] for tid in TRACKER_IDS]
    detections = [local_tracks[tid]["detection"] for tid in TRACKER_IDS]
    tracks = [local_tracks[tid]["track"] for tid in TRACKER_IDS]
    transformations, comparison_edges = build_transformations_and_edges("coherent", local_tracks)

    return {
        "schema_version": "tracking-adapter/v1",
        "evaluation_timestamp_utc": local_tracks["t1"]["track"]["evaluation_timestamp_utc"],
        "state_space": {"dimension": 1},
        "quantisation_policy": {
            "position_decimal_places": 6, "transform_decimal_places": 6, "rounding_mode": "half_even",
        },
        "correction_policy": {"kind": "additive-per-track", "transformation_policy": "coherent"},
        "sources": sources,
        "detections": detections,
        "tracks": tracks,
        "transformations": transformations,
        "comparison_edges": comparison_edges,
        "derived_problem": {"D": [], "r": []},
        "payload_digest": "PLACEHOLDER",
    }


def build_disjoint_snapshot() -> dict:
    local_tracks = build_local_tracks()
    doc = _base_doc(local_tracks)
    doc["scenario_id"] = "stonesoup-provenance-disjoint-001"

    ancestry_graph = []
    for tid in TRACKER_IDS:
        track_id = local_tracks[tid]["track"]["track_id"]
        detection_id = local_tracks[tid]["detection"]["detection_id"]
        source_id = local_tracks[tid]["source"]["source_id"]
        record_node_id = f"source_record:{tid}"
        ancestry_graph.append({
            "node_id": record_node_id, "node_type": "source_record", "parent_ids": [],
            "originating_source_id": source_id, "source_record_digest": record_node_id,
            "transformation_or_feeder_id": None,
        })
        ancestry_graph.append({
            "node_id": f"detection:{detection_id}", "node_type": "detection",
            "parent_ids": [record_node_id], "originating_source_id": source_id,
            "source_record_digest": record_node_id, "transformation_or_feeder_id": None,
        })
        ancestry_graph.append({
            "node_id": f"track:{track_id}", "node_type": "local_track",
            "parent_ids": [f"detection:{detection_id}"], "originating_source_id": source_id,
            "source_record_digest": record_node_id, "transformation_or_feeder_id": None,
        })
    ancestry_graph.extend(_comparison_nodes())

    doc["provenance"] = ancestry_graph
    doc["independence_policy"] = _independence_policy(declared_correlated_reuse=[])
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


def build_duplicated_path_snapshot(declared_correlated_reuse=None) -> dict:
    """t1 and t2 (compared by e12) both trace back to one shared
    source_record, via two DIFFERENT paths: t2's detection reaches it
    directly; t1 reaches it through an EXTRA `track_feeder` node, in
    addition to t1's own honest, distinct detection record -- a track
    with two parents, one legitimate and one an undeclared reuse."""
    local_tracks = build_local_tracks()
    doc = _base_doc(local_tracks)
    doc["scenario_id"] = "stonesoup-provenance-duplicated-001"

    ancestry_graph = []
    shared_record_node_id = "source_record:shared"
    ancestry_graph.append({
        "node_id": shared_record_node_id, "node_type": "source_record", "parent_ids": [],
        "originating_source_id": local_tracks["t2"]["source"]["source_id"],
        "source_record_digest": shared_record_node_id, "transformation_or_feeder_id": None,
    })

    for tid in TRACKER_IDS:
        track_id = local_tracks[tid]["track"]["track_id"]
        detection_id = local_tracks[tid]["detection"]["detection_id"]
        source_id = local_tracks[tid]["source"]["source_id"]
        record_node_id = f"source_record:{tid}"

        if tid == "t2":
            # t2's detection traces DIRECTLY to the shared record.
            ancestry_graph.append({
                "node_id": f"detection:{detection_id}", "node_type": "detection",
                "parent_ids": [shared_record_node_id], "originating_source_id": source_id,
                "source_record_digest": shared_record_node_id, "transformation_or_feeder_id": None,
            })
            ancestry_graph.append({
                "node_id": f"track:{track_id}", "node_type": "local_track",
                "parent_ids": [f"detection:{detection_id}"], "originating_source_id": source_id,
                "source_record_digest": shared_record_node_id, "transformation_or_feeder_id": None,
            })
            continue

        # Every other track: its own distinct source_record, as in the
        # disjoint case.
        ancestry_graph.append({
            "node_id": record_node_id, "node_type": "source_record", "parent_ids": [],
            "originating_source_id": source_id, "source_record_digest": record_node_id,
            "transformation_or_feeder_id": None,
        })
        ancestry_graph.append({
            "node_id": f"detection:{detection_id}", "node_type": "detection",
            "parent_ids": [record_node_id], "originating_source_id": source_id,
            "source_record_digest": record_node_id, "transformation_or_feeder_id": None,
        })

        if tid == "t1":
            # t1 ALSO reaches the shared record, via an extra feeder node
            # -- an undeclared second path, in addition to its own
            # honest detection.
            feeder_node_id = "feeder:t1-secondary"
            ancestry_graph.append({
                "node_id": feeder_node_id, "node_type": "track_feeder",
                "parent_ids": [shared_record_node_id], "originating_source_id": source_id,
                "source_record_digest": shared_record_node_id,
                "transformation_or_feeder_id": "feeder-secondary-path",
            })
            ancestry_graph.append({
                "node_id": f"track:{track_id}", "node_type": "local_track",
                "parent_ids": [f"detection:{detection_id}", feeder_node_id],
                "originating_source_id": source_id, "source_record_digest": record_node_id,
                "transformation_or_feeder_id": None,
            })
        else:
            ancestry_graph.append({
                "node_id": f"track:{track_id}", "node_type": "local_track",
                "parent_ids": [f"detection:{detection_id}"], "originating_source_id": source_id,
                "source_record_digest": record_node_id, "transformation_or_feeder_id": None,
            })

    ancestry_graph.extend(_comparison_nodes())

    doc["provenance"] = ancestry_graph
    doc["independence_policy"] = _independence_policy(
        declared_correlated_reuse=list(declared_correlated_reuse or [])
    )
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


def build_correlated_reuse_snapshot() -> dict:
    """Same shared ancestry as build_duplicated_path_snapshot, but e12's
    reuse is explicitly declared permitted -- PROVENANCE ACCEPT, but e12
    must never appear in claimed_independent_edges."""
    doc = build_duplicated_path_snapshot(declared_correlated_reuse=["e12"])
    doc["scenario_id"] = "stonesoup-provenance-correlated-reuse-001"
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit a Stone Soup provenance/data-incest fixture.")
    parser.add_argument("--output", required=True, help="path to write the canonical snapshot JSON to")
    parser.add_argument(
        "--variant", choices=["disjoint", "duplicated", "correlated_reuse"], default="disjoint",
    )
    args = parser.parse_args()

    builder = {
        "disjoint": build_disjoint_snapshot,
        "duplicated": build_duplicated_path_snapshot,
        "correlated_reuse": build_correlated_reuse_snapshot,
    }[args.variant]
    snapshot = builder()
    with open(args.output, "w") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
    print(f"EMIT ACCEPT: wrote {args.output} (variant={args.variant})")


if __name__ == "__main__":
    main()
