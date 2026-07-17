#!/usr/bin/env python3
"""
tracking_adapter_stonesoup_trackfusion_emitter.py

Step 10E.2 of the tracking-adapter implementation order
(docs/design/STONESOUP_TRACK_FUSION_EVALUATOR_SPEC.md): projects
`tracking_adapter_stonesoup_trackfusion.py`'s deterministic Stone Soup
track-fusion reconstruction (10E.1, `run_scenario()`) into a
`tracking-adapter/v1` snapshot, so the existing, UNMODIFIED tracking-
adapter verifier/certificate/R21 pipeline can operate on it exactly as
it already does on the hand-authored four-cycle fixtures.

GOVERNING QUESTION, restated verbatim from the design doc SS8:

    Given the local tracks produced by this deterministic Stone Soup
    track-fusion scenario, are the selected projected track comparisons
    simultaneously repairable under the declared correction and
    transformation policy?

TOPOLOGY, established by the design doc's own SS9 BEFORE any code was
written: two tracks, one declared comparison -- `D = (-1, 1)`,
`rank(D) = 1 = dim(C^1)`, so `D` is surjective and EVERY residue on this
topology is repairable, with or without the artificial perturbation
below. This module does not attempt, and cannot produce, an obstructed
verdict -- see SS9 for the full argument. The empirical content is the
actual residue and repair witness R21 returns on real Stone Soup output,
not whether one exists.

STATE PROJECTION (design doc SS3): only the x-position component
(state index 0 of the captured `[x, vx, y, vy]` state vector) enters
`LocalTrack.state_values` and therefore `(D, r)`. Velocity and
covariance are preserved as provenance ONLY, inside `Detection.
state_values` (all four components) and `Detection.covariance` (the
full 4x4 matrix) -- fields `tracking_adapter_generator.py`/
`tracking_adapter_verifier.py` never read at all, so tampering them
changes the snapshot's `payload_digest` (both fields live inside
`detections`, already covered by `compute_payload_digest`'s existing
whole-evidence hashing, design doc SS5) but never changes the
independently reconstructed `(D, r)`.

TRANSFORMATION SEMANTICS (design doc SS4): Stone Soup's own Unscented
Kalman filters already produce both local tracks in one common global
Cartesian frame -- there is no separate platform-to-global registration
left for the adapter to apply. The NATURAL policy therefore declares the
identity transformation (`offset = "0"`) for both tracks. The
ARTIFICIAL_PERTURBATION policy adds a clearly labelled, evaluator-
imposed nonzero offset to `track:kf-2` only, to exercise transformation
HANDLING (does the adapter correctly derive a different `r` and a
different repair witness from a different declared offset?) -- NOT an
attempt to manufacture an obstruction, since SS9 shows none is possible
on this topology for any offset.

PROVENANCE (design doc SS7): the two radar detection streams are
genuinely disjoint `source_record` ancestors (`radar1`/`radar2` each
generate their own, numerically distinct, detection at every timestep,
even though both observe one shared simulated target) -- so
`independence_policy` declares the one comparison independent, and
`check_independence` accepts it structurally. This says nothing about
the two tracks' STATISTICAL independence as estimators of one shared
physical target (design doc SS7's own explicit non-claim, restated in
this module's own docstring so it is never lost downstream): a
PROVENANCE ACCEPT verdict here means "no shared sensor-record ancestor",
not "statistically independent estimates".

The fused Stone Soup track (Chernoff/PHD fusion output) is captured by
`run_scenario()` but is DELIBERATELY EXCLUDED from this snapshot
entirely -- it is not a source, not a detection, not a track, and its
ancestry node (`fusion:chernoff-fused`, provenance only, see below) is
never a parent of `comparison:kf1-kf2`. `capture_fused_track_report`
below exposes it purely for side-by-side, non-authoritative reporting;
nothing in `tracking_adapter_generator.py`/`tracking_adapter_verifier.py`
ever reads it.

USAGE:
    python tracking_adapter_stonesoup_trackfusion_emitter.py \\
        --output snapshot.json --policy natural
"""

import argparse
import decimal
import hashlib
import json
from fractions import Fraction
from typing import Dict, List

from tracking_adapter_canon import to_exact_rational_independent
from tracking_adapter_stonesoup_trackfusion import (
    FIXED_TIMESTAMP_ISO,
    GLOBAL_SEED,
    RADAR1_SEED,
    RADAR2_SEED,
    run_scenario,
)
from tracking_adapter_verifier import compute_payload_digest

POLICIES = ("natural", "artificial_perturbation")

# The one genuine use of the adapter's transformation slot in this
# scenario (design doc SS4): a clearly labelled, evaluator-imposed
# offset, never presented as a manufactured obstruction attempt (SS9).
ARTIFICIAL_PERTURBATION_OFFSET = "10"

EDGE_ID = "kf1-kf2"  # matches the design doc SS7's own worked example, "comparison:kf1-kf2"

PLATFORM_IDS = {"radar-1": "platform-radar-1", "radar-2": "platform-radar-2"}  # matches run_scenario()'s own literal FixedPlatform ids

QUANTISATION_POLICY = {
    "position_decimal_places": 6,
    "transform_decimal_places": 6,
    "rounding_mode": "half_even",
}

INDEPENDENCE_POLICY_VERSION = "tracking-adapter-independence-policy/v1"


def _to_plain_decimal(value) -> str:
    """Normalises ANY canonical representation of a real number (a plain
    decimal string, or one using exponent notation -- Python's own
    `repr(float(...))` uses exponent notation for very small magnitudes,
    e.g. measurement-noise-epsilon-scale covariance entries) into the
    plain `-?digits(.digits)?` form `tracking_adapter_canon.py`'s own
    `_DECIMAL_RE` expects, using `decimal.Decimal` purely as an exact
    parser/reformatter -- no rounding, no precision loss, since `Decimal`
    itself is a base-10 exact type."""
    return format(decimal.Decimal(str(value)), "f")


def _decimal_string_from_fraction(value: Fraction, places: int) -> str:
    """The exact inverse of `to_exact_rational_independent` at a fixed
    number of decimal places: renders a `Fraction` that is ALREADY an
    exact multiple of `10^-places` (as every residue derived from
    already-quantised state/offset values necessarily is) back to a
    canonical plain-decimal string, so a value this module computes
    matches -- exactly, not merely approximately -- what the independent
    verifier will itself recompute from the same evidence."""
    scale = Fraction(10) ** places
    scaled = value * scale
    if scaled.denominator != 1:
        raise ValueError(f"{value} is not an exact multiple of 10^-{places}; cannot render at {places} places")
    quantum = decimal.Decimal(scaled.numerator).scaleb(-places)
    return format(quantum, "f")


def _source_record_digest(radar_label: str) -> str:
    canonical = f"stonesoup-trackfusion-source-record:{radar_label}:{GLOBAL_SEED}:{RADAR1_SEED}:{RADAR2_SEED}"
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _track_digest(track_id: str, scenario_id: str) -> str:
    canonical = f"stonesoup-trackfusion-track:{track_id}:{scenario_id}:{GLOBAL_SEED}"
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _build_source(radar_label: str, seed: int) -> dict:
    return {
        "source_id": f"source:{radar_label}",
        "sensor_modality": "stonesoup-radarbearingrange-ukf-track",
        "platform_id": PLATFORM_IDS[radar_label],
        "source_data_digest": _source_record_digest(radar_label),
        "source_timestamp_utc": FIXED_TIMESTAMP_ISO,
        "coordinate_frame": "global-cartesian",
        "measurement_model_id": f"unscented-kalman-seed-{seed}",
    }


def _build_detection(radar_label: str, track_suffix: str, captured_track) -> dict:
    """The captured local track's FULL 4D state and 4x4 covariance,
    attached as a `Detection` -- provenance only (design doc SS5):
    neither `state_values` (all 4 components here) nor `covariance` is
    ever read by `tracking_adapter_generator.py`/`tracking_adapter_
    verifier.py`, which only ever look at `LocalTrack.state_values`
    (the x-projection alone, built separately below)."""
    x, vx, y, vy = (_to_plain_decimal(v) for v in captured_track.state_vector)
    covariance = [[_to_plain_decimal(v) for v in row] for row in captured_track.covariance]
    return {
        "detection_id": f"detection:{track_suffix}",
        "source_id": f"source:{radar_label}",
        "timestamp_utc": captured_track.timestamp_utc,
        "state_values": [x, vx, y, vy],
        "coordinate_frame": "global-cartesian",
        "transformation_history": [],
        "covariance": covariance,
        "source_record_digest": _source_record_digest(radar_label),
    }


def _build_local_track(captured_track, radar_label: str, detection_id: str, scenario_id: str,
                        transformation_record: str) -> dict:
    x_str = _to_plain_decimal(captured_track.state_vector[0])
    return {
        "track_id": captured_track.track_id,
        "tracker_id": captured_track.tracker_id,
        "evaluation_timestamp_utc": captured_track.timestamp_utc,
        "state_values": [x_str],
        "state_space": "scalar",
        "contributing_detection_ids": [detection_id],
        "ancestry": [
            f"platform:{PLATFORM_IDS[radar_label]}",
            f"source:{radar_label}",
            detection_id,
        ],
        "transformation_record": transformation_record,
        "track_digest": _track_digest(captured_track.track_id, scenario_id),
    }


def _offsets_for(policy: str) -> Dict[str, str]:
    if policy == "natural":
        return {"track:kf-1": "0", "track:kf-2": "0"}
    if policy == "artificial_perturbation":
        return {"track:kf-1": "0", "track:kf-2": ARTIFICIAL_PERTURBATION_OFFSET}
    raise ValueError(f"unknown policy {policy!r}; expected one of {POLICIES}")


def _build_transformations_and_edge(policy: str, x1_str: str, x2_str: str):
    offsets = _offsets_for(policy)
    places = QUANTISATION_POLICY
    transformations = [
        {
            "transformation_id": f"xf-{policy}-kf1", "edge_id": EDGE_ID, "track_id": "track:kf-1",
            "kind": "additive_offset", "offset": offsets["track:kf-1"],
        },
        {
            "transformation_id": f"xf-{policy}-kf2", "edge_id": EDGE_ID, "track_id": "track:kf-2",
            "kind": "additive_offset", "offset": offsets["track:kf-2"],
        },
    ]

    # Recomputed here in EXACTLY the way the independent verifier will
    # recompute it (quantise state/offset individually via the same
    # canon.py route, then subtract) -- not a shortcut, so the declared
    # `discrepancy` below always matches the verifier's own independent
    # reconstruction exactly.
    state_1 = to_exact_rational_independent(x1_str, places["position_decimal_places"], places["rounding_mode"])
    state_2 = to_exact_rational_independent(x2_str, places["position_decimal_places"], places["rounding_mode"])
    offset_1 = to_exact_rational_independent(offsets["track:kf-1"], places["transform_decimal_places"], places["rounding_mode"])
    offset_2 = to_exact_rational_independent(offsets["track:kf-2"], places["transform_decimal_places"], places["rounding_mode"])
    residue = (state_2 + offset_2) - (state_1 + offset_1)
    discrepancy_str = _decimal_string_from_fraction(residue, places["position_decimal_places"])

    comparison_edge = {
        "edge_id": EDGE_ID,
        "source_track_id": "track:kf-1",
        "target_track_id": "track:kf-2",
        "orientation": "source_to_target",
        "comparison_space_id": "cmp-x-position",
        "transformation_id": f"family-{policy}",
        "discrepancy": discrepancy_str,
        "coreference_provenance": "stonesoup-trackfusion-declared",
    }
    return transformations, comparison_edge


def _build_provenance() -> List[dict]:
    """The full ancestry graph per design doc SS7's own table -- both
    radar `source_record`s are genuinely disjoint (confirmed in SS7 by
    tracing the fetched upstream source directly, not assumed), so the
    one declared comparison is PROVENANCE ACCEPT under `independence_
    policy` below. `feeder:chernoff-fusion-input` and `fusion:chernoff-
    fused` are included for a complete, honest ancestry graph (SS7's own
    table lists both) but neither is ever a parent of `comparison:kf1-
    kf2` -- the fused output never enters the structural verdict."""
    nodes = []
    for radar_label in ("radar-1", "radar-2"):
        digest = _source_record_digest(radar_label)
        nodes.append({
            "node_id": f"source_record:{radar_label}", "node_type": "source_record", "parent_ids": [],
            "originating_source_id": f"source:{radar_label}", "source_record_digest": digest,
            "transformation_or_feeder_id": None,
        })

    radar_by_track = {"track:kf-1": "radar-1", "track:kf-2": "radar-2"}
    for track_id, radar_label in radar_by_track.items():
        digest = _source_record_digest(radar_label)
        suffix = track_id.split(":")[1]
        nodes.append({
            "node_id": f"detection:{suffix}", "node_type": "detection",
            "parent_ids": [f"source_record:{radar_label}"],
            "originating_source_id": f"source:{radar_label}", "source_record_digest": digest,
            "transformation_or_feeder_id": None,
        })
        nodes.append({
            "node_id": track_id, "node_type": "local_track",
            "parent_ids": [f"detection:{suffix}"],
            "originating_source_id": f"source:{radar_label}", "source_record_digest": digest,
            "transformation_or_feeder_id": None,
        })

    nodes.append({
        "node_id": "feeder:chernoff-fusion-input", "node_type": "track_feeder",
        "parent_ids": ["track:kf-1", "track:kf-2"],
        "originating_source_id": "", "source_record_digest": "",
        "transformation_or_feeder_id": "tracks2gaussian-detection-feeder",
    })
    nodes.append({
        "node_id": "fusion:chernoff-fused", "node_type": "fusion_stage_track",
        "parent_ids": ["feeder:chernoff-fusion-input"],
        "originating_source_id": "", "source_record_digest": "",
        "transformation_or_feeder_id": "chernoff-phd-fusion",
    })
    nodes.append({
        "node_id": f"comparison:{EDGE_ID}", "node_type": "declared_comparison",
        "parent_ids": ["track:kf-1", "track:kf-2"],
        "originating_source_id": "", "source_record_digest": "",
        "transformation_or_feeder_id": None,
    })
    return nodes


def _build_independence_policy() -> dict:
    return {
        "policy_version": INDEPENDENCE_POLICY_VERSION,
        "independent_comparisons": [EDGE_ID],
        "shared_ancestry_prohibited": True,
        "declared_correlated_reuse": [],
    }


def build_snapshot(policy: str) -> dict:
    if policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}; expected one of {POLICIES}")

    scenario = run_scenario()
    captured_kf1, captured_kf2 = scenario.local_tracks
    scenario_id = f"stonesoup-trackfusion-{policy}-001"

    source_radar1 = _build_source("radar-1", RADAR1_SEED)
    source_radar2 = _build_source("radar-2", RADAR2_SEED)

    detection_kf1 = _build_detection("radar-1", "kf-1", captured_kf1)
    detection_kf2 = _build_detection("radar-2", "kf-2", captured_kf2)

    # track:kf-1's own declared offset is always "0" (identity) under
    # both policies -- only track:kf-2 carries the artificial
    # perturbation, see _offsets_for.
    track_kf1 = _build_local_track(
        captured_kf1, "radar-1", detection_kf1["detection_id"], scenario_id, "identity",
    )
    kf2_record = "identity" if policy == "natural" else "artificial-perturbation-evaluator-imposed"
    track_kf2 = _build_local_track(
        captured_kf2, "radar-2", detection_kf2["detection_id"], scenario_id, kf2_record,
    )

    transformations, comparison_edge = _build_transformations_and_edge(
        policy, track_kf1["state_values"][0], track_kf2["state_values"][0],
    )

    doc = {
        "schema_version": "tracking-adapter/v1",
        "scenario_id": scenario_id,
        "evaluation_timestamp_utc": captured_kf1.timestamp_utc,
        "state_space": {
            "dimension": 1,
            "stone_soup_state_index": 0,
            "stone_soup_state_dimension": 4,
        },
        "quantisation_policy": QUANTISATION_POLICY,
        "correction_policy": {"kind": "additive-per-track", "transformation_policy": policy},
        "sources": [source_radar1, source_radar2],
        "detections": [detection_kf1, detection_kf2],
        "tracks": [track_kf1, track_kf2],
        "transformations": transformations,
        "comparison_edges": [comparison_edge],
        "provenance": _build_provenance(),
        "independence_policy": _build_independence_policy(),
        "derived_problem": {"D": [], "r": []},
        "payload_digest": "PLACEHOLDER",
    }
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


def capture_fused_track_report(policy: str) -> dict:
    """Stone Soup's OWN fused-track output, for side-by-side reporting
    ONLY (design doc SS2/SS9) -- deliberately NOT part of `build_snapshot`
    at all, so there is no schema field to tamper: the fused output
    structurally cannot affect `(D, r)`, since nothing about it is ever
    present in the document `tracking_adapter_verifier.py` reconstructs
    from."""
    scenario = run_scenario()
    fused = scenario.fused_track
    return {
        "policy": policy,
        "stonesoup_fused_track_position_x": fused.state_vector[0] if fused is not None else None,
        "note": (
            "Reported for comparison only. Stone Soup's own fused-track output is never "
            "read by tracking_adapter_generator.py or tracking_adapter_verifier.py, and is "
            "not part of the tracking-adapter/v1 snapshot at all -- it cannot affect (D, r) "
            "or the repair-or-separator verdict. This is a STRUCTURAL result (does a "
            "declared comparison of local tracks repair coherently?), not a STATISTICAL one "
            "(is Stone Soup's fusion estimate itself accurate or well-calibrated?); the two "
            "are not the same claim."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit a tracking-adapter/v1 snapshot from a deterministic Stone Soup track-fusion scenario."
    )
    parser.add_argument("--output", required=True, help="path to write the canonical snapshot JSON to")
    parser.add_argument("--policy", choices=POLICIES, default="natural")
    args = parser.parse_args()

    snapshot = build_snapshot(args.policy)
    with open(args.output, "w") as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
    print(f"EMIT ACCEPT: wrote {args.output} (policy={args.policy})")


if __name__ == "__main__":
    main()
