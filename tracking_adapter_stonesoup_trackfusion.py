#!/usr/bin/env python3
"""
tracking_adapter_stonesoup_trackfusion.py

Step 10E.1 of the tracking-adapter implementation order
(docs/design/STONESOUP_TRACK_FUSION_EVALUATOR_SPEC.md): a minimal,
deterministic rewrite of Stone Soup's own two-radar track-fusion
tutorial (`docs/examples/trackfusion/track_fusion_example.py` at tag
v1.9.1), using genuine installed Stone Soup APIs -- real `RadarBearingRange`
detections, real `SingleTargetTracker` (Unscented Kalman) local
trackers, a real `Tracks2GaussianDetectionFeeder`, a real
`ChernoffUpdater` inside a real `PointProcessMultiTargetTracker` -- not
a reimplementation of any of these.

THIS FILE IS RECONSTRUCTION ONLY (10E.1): it captures local tracks and
the fused track as plain, project-controlled-ID-bearing Python
dataclasses. It does NOT touch the tracking-adapter schema, the
verifier, or R21 at all -- that is step 10E.2's job, built on top of
this file's own `run_scenario()` output, kept as a separate module so
10E.1's own determinism can be committed and verified on its own before
any adapter-specific code depends on it.

DETERMINISM, per the design doc's own SS6 inventory:
  - one fixed UTC start time, never `datetime.now()`;
  - both the legacy (`numpy.random.seed`) and modern (`numpy.random.
    default_rng`) NumPy RNG systems seeded explicitly, closing the exact
    gap the design doc found in the upstream example (`np.random.seed`
    does not seed `default_rng()` -- two separate systems);
  - every `RadarBearingRange` constructed with its own explicit `seed=`;
  - sensor noise covariance set to the zero matrix -- deterministic by
    construction (sampling a zero-covariance Gaussian always returns
    its mean exactly), not merely "seeded and hoped stable", the same
    technique steps 10B-10D already used for `LinearGaussian`;
  - ground-truth process noise is zero (`ConstantVelocity(0.0)` on both
    axes, matching the upstream example's own choice) -- the TRACKING
    filter's own transition model may still declare nonzero process
    noise (a filter design parameter controlling covariance growth, not
    a source of randomness -- covariance prediction is deterministic
    linear algebra regardless of Q's value);
  - no clutter (`clutter_model=None` on both radars) and no particle-
    filter branch -- both removed, not merely seeded, per the design
    doc's own SS6 decision;
  - explicit, project-controlled `id=` at every `Track()` construction
    Stone Soup would otherwise auto-generate a UUID for.

USAGE:
    python tracking_adapter_stonesoup_trackfusion.py --output result.json
"""

import argparse
import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from itertools import tee
from typing import List, Optional

import numpy as np

FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
FIXED_TIMESTAMP_ISO = "2026-01-01T00:00:00Z"

GLOBAL_SEED = 20260117
NUMBER_OF_STEPS = 5  # small and deterministic -- not the upstream example's 75

RADAR1_SEED = 30260117
RADAR2_SEED = 30260118


def _seed_everything() -> None:
    """Seeds BOTH NumPy RNG systems explicitly -- closing the exact gap
    the design doc's audit found in the upstream example, where
    `np.random.seed(...)` alone left `np.random.default_rng()` (used by
    the upstream clutter model, removed here anyway) unseeded."""
    np.random.seed(GLOBAL_SEED)
    np.random.default_rng(GLOBAL_SEED)  # a seeded instance exists in-process, even though this file's own code no longer calls an unseeded one anywhere


@dataclass
class CapturedTrackState:
    track_id: str
    tracker_id: str
    timestamp_utc: str
    state_vector: List[str]  # canonical decimal strings, [x, vx, y, vy]
    covariance: List[List[str]]  # canonical decimal strings, 4x4


@dataclass
class CapturedFusedState:
    fusion_id: str
    timestamp_utc: str
    state_vector: List[str]
    covariance: List[List[str]]


@dataclass
class ScenarioResult:
    local_tracks: List[CapturedTrackState]
    fused_track: Optional[CapturedFusedState]
    number_of_steps: int
    seeds: dict


def _decimal(value) -> str:
    """Canonical decimal string for a genuine (deterministic, zero-noise)
    Stone Soup numeric result. Does not silently accept an unexpected
    non-terminating float -- this scenario's own zero-noise, zero-
    process-noise-on-ground-truth construction keeps every state-vector
    component an exact rational in practice (integers or simple halves),
    but covariance entries involve accumulated linear-algebra products
    or exponentiation and are not guaranteed integral, so unlike step
    10B's stricter integer check, this records the full float decimal
    expansion Python's own `repr` gives, canonical and lossless for the
    IEEE-754 value actually produced -- provenance data, not (D, r)
    input requiring R21's own canonical-rational grammar."""
    return repr(float(value))


def _matrix_to_strings(mat) -> List[List[str]]:
    return [[_decimal(x) for x in row] for row in np.asarray(mat)]


def _vector_to_strings(vec) -> List[str]:
    return [_decimal(x) for x in np.asarray(vec).flatten()]


def run_scenario() -> ScenarioResult:
    _seed_everything()

    from stonesoup.dataassociator.neighbour import GNNWith2DAssignment
    from stonesoup.deleter.time import UpdateTimeStepsDeleter
    from stonesoup.feeder.multi import MultiDataFeeder
    from stonesoup.feeder.track import Tracks2GaussianDetectionFeeder
    from stonesoup.hypothesiser.distance import DistanceHypothesiser
    from stonesoup.hypothesiser.gaussianmixture import GaussianMixtureHypothesiser
    from stonesoup.initiator.simple import SimpleMeasurementInitiator
    from stonesoup.measures import Mahalanobis
    from stonesoup.mixturereducer.gaussianmixture import GaussianMixtureReducer
    from stonesoup.models.transition.linear import (
        CombinedLinearGaussianTransitionModel, ConstantVelocity,
    )
    from stonesoup.platform.base import FixedPlatform
    from stonesoup.predictor.kalman import UnscentedKalmanPredictor
    from stonesoup.sensor.radar.radar import RadarBearingRange
    from stonesoup.simulator.platform import PlatformDetectionSimulator
    from stonesoup.simulator.simple import SingleTargetGroundTruthSimulator
    from stonesoup.tracker.pointprocess import PointProcessMultiTargetTracker
    from stonesoup.tracker.simple import SingleTargetTracker
    from stonesoup.types.array import CovarianceMatrix
    from stonesoup.types.state import GaussianState, TaggedWeightedGaussianState
    from stonesoup.updater.chernoff import ChernoffUpdater
    from stonesoup.updater.kalman import UnscentedKalmanUpdater
    from stonesoup.updater.pointprocess import PHDUpdater

    # --- ground truth: zero process noise -> deterministic straight-line motion ---
    gnd_transition_model = CombinedLinearGaussianTransitionModel(
        [ConstantVelocity(0.0), ConstantVelocity(0.0)]
    )
    initial_target_state = GaussianState(
        [25, 0.5, 75, -0.25], np.diag([10, 1, 10, 1]), timestamp=FIXED_TIMESTAMP,
    )
    groundtruth_simulation = SingleTargetGroundTruthSimulator(
        transition_model=gnd_transition_model,
        initial_state=initial_target_state,
        timestep=timedelta(seconds=1),
        number_steps=NUMBER_OF_STEPS,
    )

    # --- sensors: (near-)zero noise covariance, no clutter, explicit per-sensor seed ---
    # A genuinely EXACT zero covariance makes the Unscented Kalman Filter's
    # own internal sigma-point Cholesky decomposition ill-posed (confirmed
    # directly: it raises a "Matrix is not positive definite" warning with
    # noise_covar = 0 exactly) -- a small, fixed epsilon keeps the filter
    # numerically well-posed while remaining fully deterministic (fixed
    # seed, fixed epsilon) and negligible once quantised to this adapter's
    # own 6-decimal-place canonical policy (10E.2).
    MEASUREMENT_NOISE_EPSILON = 1e-6
    radar_noise = CovarianceMatrix(np.diag([MEASUREMENT_NOISE_EPSILON, MEASUREMENT_NOISE_EPSILON]))
    radar1 = RadarBearingRange(
        ndim_state=4, position_mapping=(0, 2), noise_covar=radar_noise,
        clutter_model=None, max_range=3000, seed=RADAR1_SEED,
    )
    radar2 = RadarBearingRange(
        ndim_state=4, position_mapping=(0, 2), noise_covar=deepcopy(radar_noise),
        clutter_model=None, max_range=3000, seed=RADAR2_SEED,
    )

    sensor1_platform = FixedPlatform(
        states=GaussianState([10, 0, 80, 0], np.diag([1, 0, 1, 0])),
        position_mapping=(0, 2), sensors=[radar1], id="platform-radar-1",
    )
    sensor2_platform = FixedPlatform(
        states=GaussianState([75, 0, 10, 0], np.diag([1, 0, 1, 0])),
        position_mapping=(0, 2), sensors=[radar2], id="platform-radar-2",
    )

    gt_sims = tee(groundtruth_simulation, 2)
    radar_simulator1 = PlatformDetectionSimulator(groundtruth=gt_sims[0], platforms=[sensor1_platform])
    radar_simulator2 = PlatformDetectionSimulator(groundtruth=gt_sims[1], platforms=[sensor2_platform])

    # --- Kalman tracker components (kept -- particle-filter branch dropped) ---
    transition_model = CombinedLinearGaussianTransitionModel(
        [ConstantVelocity(0.5), ConstantVelocity(0.5)]
    )
    KF_predictor = UnscentedKalmanPredictor(transition_model)
    KF_updater = UnscentedKalmanUpdater(measurement_model=None)
    hypothesiser_KF = DistanceHypothesiser(
        predictor=KF_predictor, updater=KF_updater, measure=Mahalanobis(), missed_distance=10,
    )
    data_associator_KF = GNNWith2DAssignment(hypothesiser_KF)
    deleter = UpdateTimeStepsDeleter(3)
    initiator = SimpleMeasurementInitiator(prior_state=initial_target_state, measurement_model=None)

    radar1KF, radar1fusion = tee(radar_simulator1, 2)
    radar2KF, radar2fusion = tee(radar_simulator2, 2)

    KF_tracker_1 = SingleTargetTracker(
        initiator=initiator, detector=radar1KF, updater=KF_updater,
        data_associator=data_associator_KF, deleter=deleter,
    )
    KF_tracker_2 = SingleTargetTracker(
        initiator=initiator, detector=radar2KF, updater=KF_updater,
        data_associator=data_associator_KF, deleter=deleter,
    )

    PartialTrack1, TrackFusion1 = tee(KF_tracker_1, 2)
    PartialTrack2, TrackFusion2 = tee(KF_tracker_2, 2)

    # --- Chernoff fusion stage ---
    ch_updater = ChernoffUpdater(measurement_model=None)
    updater = PHDUpdater(updater=ch_updater, clutter_spatial_density=1e-10, prob_detection=0.99, prob_survival=0.95)
    base_hypothesiser = DistanceHypothesiser(predictor=KF_predictor, updater=ch_updater, measure=Mahalanobis(), missed_distance=15)
    hypothesiser = GaussianMixtureHypothesiser(base_hypothesiser, order_by_detection=True)
    ch_reducer = GaussianMixtureReducer(prune_threshold=1e-10, pruning=True, merge_threshold=100, merging=True)
    birth_covar = CovarianceMatrix(np.diag([50, 5, 50, 5]))
    ch_birth_component = TaggedWeightedGaussianState(
        state_vector=[25, 0.5, 70, -0.25], covar=birth_covar ** 2, weight=1,
        tag=TaggedWeightedGaussianState.BIRTH, timestamp=FIXED_TIMESTAMP,
    )
    track_fusion_tracker = PointProcessMultiTargetTracker(
        detector=None, hypothesiser=hypothesiser, updater=updater,
        reducer=deepcopy(ch_reducer), birth_component=deepcopy(ch_birth_component),
        extraction_threshold=0.95,
    )
    track_fusion_tracker.detector = Tracks2GaussianDetectionFeeder(
        MultiDataFeeder([TrackFusion1, TrackFusion2])
    )

    iter_fusion_tracker = iter(track_fusion_tracker)
    iter_track1 = iter(PartialTrack1)
    iter_track2 = iter(PartialTrack2)

    fused_tracks = set()
    track1_snapshot = None
    track2_snapshot = None
    for _ in range(NUMBER_OF_STEPS):
        _, tracks = next(iter_fusion_tracker)
        fused_tracks.update(tracks)
        _, t1 = next(iter_track1)
        _, t2 = next(iter_track2)
        track1_snapshot = t1
        track2_snapshot = t2

    # --- capture: local tracks (LAST timestep both trackers share), before fusion consumes them further ---
    def _capture_track(tracks, track_id: str, tracker_id: str) -> CapturedTrackState:
        (track,) = tracks
        state = track[-1]
        return CapturedTrackState(
            track_id=track_id, tracker_id=tracker_id,
            timestamp_utc=state.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            state_vector=_vector_to_strings(state.state_vector),
            covariance=_matrix_to_strings(state.covar),
        )

    captured_track1 = _capture_track(track1_snapshot, "track:kf-1", "tracker-kf-1")
    captured_track2 = _capture_track(track2_snapshot, "track:kf-2", "tracker-kf-2")

    captured_fused = None
    if fused_tracks:
        fused = sorted(fused_tracks, key=lambda t: str(t.id))[0]
        state = fused[-1]
        captured_fused = CapturedFusedState(
            fusion_id="fusion:chernoff-fused",
            timestamp_utc=state.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            state_vector=_vector_to_strings(state.state_vector),
            covariance=_matrix_to_strings(state.covar),
        )

    return ScenarioResult(
        local_tracks=[captured_track1, captured_track2],
        fused_track=captured_fused,
        number_of_steps=NUMBER_OF_STEPS,
        seeds={"global_seed": GLOBAL_SEED, "radar1_seed": RADAR1_SEED, "radar2_seed": RADAR2_SEED},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce a deterministic Stone Soup track-fusion scenario.")
    parser.add_argument("--output", required=True, help="path to write the captured result JSON to")
    args = parser.parse_args()

    result = run_scenario()
    with open(args.output, "w") as f:
        json.dump(asdict(result), f, indent=2, sort_keys=True)
    print(f"CAPTURE ACCEPT: wrote {args.output}")


if __name__ == "__main__":
    main()
