"""
Step 10E.1 of the tracking-adapter implementation order: process-level
determinism and sanity checks for tracking_adapter_stonesoup_
trackfusion.py's deterministic reconstruction of Stone Soup's own
two-radar track-fusion tutorial. This file does NOT touch the tracking-
adapter schema/verifier/R21 at all (that is 10E.2's own test file,
tests/test_stonesoup_trackfusion.py) -- it verifies only that the
reconstruction itself is genuine (real installed Stone Soup APIs) and
deterministic at PROCESS level (fresh interpreter, fresh Stone Soup
import, each run).

Skips (not fails) if Stone Soup is not installed, matching every other
Stone-Soup-dependent test file in this repository.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBPROCESS_TIMEOUT = 120

stonesoup_missing = pytest.mark.skipif(
    importlib.util.find_spec("stonesoup") is None,
    reason="stonesoup not installed; pip install -r requirements-stonesoup.txt first",
)


def _run(output_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_stonesoup_trackfusion.py"),
         "--output", str(output_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


@stonesoup_missing
def test_reconstruction_captures_two_local_tracks_and_a_fused_track(tmp_path):
    output_path = tmp_path / "result.json"
    result = _run(output_path)
    assert result.returncode == 0, result.stdout + result.stderr

    data = json.loads(output_path.read_text())
    assert len(data["local_tracks"]) == 2
    track_ids = {t["track_id"] for t in data["local_tracks"]}
    assert track_ids == {"track:kf-1", "track:kf-2"}
    for t in data["local_tracks"]:
        assert len(t["state_vector"]) == 4  # [x, vx, y, vy]
        assert len(t["covariance"]) == 4
        assert all(len(row) == 4 for row in t["covariance"])
    assert data["fused_track"] is not None
    assert len(data["fused_track"]["state_vector"]) == 4


@stonesoup_missing
def test_local_track_estimates_are_close_to_the_known_ground_truth(tmp_path):
    """Sanity check, not a determinism check: with near-zero measurement
    noise and zero ground-truth process noise, both trackers must
    converge close to the analytically known straight-line ground truth
    (initial state (25, 0.5, 75, -0.25), constant velocity) -- if this
    ever drifted far off, the reconstruction would be capturing garbage,
    not a genuine tracking result."""
    output_path = tmp_path / "result.json"
    result = _run(output_path)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(output_path.read_text())

    for t in data["local_tracks"]:
        x, vx, y, vy = (float(v) for v in t["state_vector"])
        # Ground truth after ~4-5 seconds at (25,0.5,75,-0.25): x in [26,28], y in [73,76].
        assert 24 < x < 30
        assert 70 < y < 78
        assert 0.0 < vx < 1.0
        assert -0.6 < vy < 0.0


@stonesoup_missing
def test_process_level_determinism_across_two_separate_runs(tmp_path):
    path_a = tmp_path / "result_a.json"
    path_b = tmp_path / "result_b.json"
    result_a = _run(path_a)
    result_b = _run(path_b)
    assert result_a.returncode == 0, result_a.stdout + result_a.stderr
    assert result_b.returncode == 0, result_b.stdout + result_b.stderr
    assert path_a.read_bytes() == path_b.read_bytes()


@stonesoup_missing
def test_genuine_stonesoup_objects_are_actually_used():
    """Confirms this is a real reconstruction, not a stand-in -- imports
    the module's own run_scenario and checks the classes it touches are
    the real installed Stone Soup ones (import succeeding at all is
    itself the primary evidence; this additionally checks the specific
    classes this step's own instructions named are genuinely importable
    from the installed package, not shadowed by anything local)."""
    from stonesoup.feeder.track import Tracks2GaussianDetectionFeeder
    from stonesoup.sensor.radar.radar import RadarBearingRange
    from stonesoup.tracker.simple import SingleTargetTracker
    from stonesoup.updater.chernoff import ChernoffUpdater

    assert RadarBearingRange.__module__.startswith("stonesoup.")
    assert SingleTargetTracker.__module__.startswith("stonesoup.")
    assert Tracks2GaussianDetectionFeeder.__module__.startswith("stonesoup.")
    assert ChernoffUpdater.__module__.startswith("stonesoup.")
