"""
Source-policy test for tracking_adapter_stonesoup_trackfusion.py --
step 10E.1. Statically scans the reconstruction's own source for the
determinism properties docs/design/STONESOUP_TRACK_FUSION_EVALUATOR_
SPEC.md's SS6 audit requires, the same discipline test_stonesoup_
source_policy.py already applies to the simpler four-cycle emitter.
Needs no Stone Soup installation to run -- this is a property of the
FILE, not of anything it does at runtime.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "tracking_adapter_stonesoup_trackfusion.py"


def _source() -> str:
    return MODULE_PATH.read_text()


def _tree() -> ast.Module:
    return ast.parse(_source(), filename=str(MODULE_PATH))


def _code_without_docstring() -> str:
    tree = _tree()
    docstring = ast.get_docstring(tree, clean=False)
    source = _source()
    if docstring is not None and docstring in source:
        return source.replace(docstring, "", 1)
    return source


def _call_names(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                yield node.func.attr, node
            elif isinstance(node.func, ast.Name):
                yield node.func.id, node


def test_module_exists():
    assert MODULE_PATH.exists()


def test_rejects_datetime_now():
    for name, node in _call_names(_tree()):
        assert name not in ("now", "utcnow"), (
            f"calls {name}() at line {node.lineno} -- forbidden, must use FIXED_TIMESTAMP"
        )


def test_uses_one_fixed_timestamp_constant():
    source = _source()
    assert "FIXED_TIMESTAMP = datetime(" in source
    assert "2026, 1, 1" in source


def test_seeds_both_numpy_rng_systems_explicitly():
    """The design doc's own audit finding: np.random.seed(...) alone does
    NOT seed np.random.default_rng() -- two separate RNG systems. This
    file must seed both explicitly, not repeat the upstream gap."""
    tree = _tree()
    seeded_legacy = False
    seeded_modern = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "seed":
            if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "random":
                seeded_legacy = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "default_rng":
            if node.args or node.keywords:
                seeded_modern = True
    assert seeded_legacy, "expected an explicit np.random.seed(...) call"
    assert seeded_modern, "expected an explicit, SEEDED np.random.default_rng(SEED) call"


def test_every_radar_construction_has_an_explicit_seed():
    tree = _tree()
    calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "RadarBearingRange":
            calls += 1
            kwarg_names = {kw.arg for kw in node.keywords}
            assert "seed" in kwarg_names, f"RadarBearingRange(...) at line {node.lineno} has no explicit seed="
    assert calls == 2, f"expected exactly 2 RadarBearingRange constructions, found {calls}"


def test_every_radar_has_clutter_disabled():
    tree = _tree()
    calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "RadarBearingRange":
            calls += 1
            kwargs = {kw.arg: kw.value for kw in node.keywords}
            assert "clutter_model" in kwargs, f"RadarBearingRange(...) at line {node.lineno} has no explicit clutter_model="
            value = kwargs["clutter_model"]
            assert isinstance(value, ast.Constant) and value.value is None, (
                f"RadarBearingRange(...) at line {node.lineno} does not set clutter_model=None"
            )
    assert calls == 2


def test_no_particle_filter_branch():
    source = _code_without_docstring()
    for forbidden in ("ParticlePredictor", "ParticleUpdater", "ESSResampler", "GaussianParticleInitiator"):
        assert forbidden not in source, f"{forbidden} found -- the particle-filter branch must not be present in 10E.1"


def test_no_plotting_or_metrics_imports():
    source = _code_without_docstring()
    for forbidden in ("Plotterly", "MetricPlotter", "SIAPMetrics", "MultiManager", "TrackToTruth", "matplotlib", "plotly"):
        assert forbidden not in source, f"{forbidden} found -- no plotting/metrics code belongs in the reconstruction"


def test_every_platform_construction_has_an_explicit_id():
    tree = _tree()
    calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "FixedPlatform":
            calls += 1
            kwarg_names = {kw.arg for kw in node.keywords}
            assert "id" in kwarg_names, f"FixedPlatform(...) at line {node.lineno} has no explicit id="
    assert calls == 2
