"""
Source-policy test for tracking_adapter_stonesoup_emitter.py -- step 10B
of the tracking-adapter implementation order. Statically scans the
emitter's own source (AST where precision matters, substring checks
where a simple textual absence is the actual claim) for the six
forbidden patterns this step's determinism requirement names explicitly.
Needs no Stone Soup installation at all -- this is a property of the
FILE, not of anything it does at runtime.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EMITTER_PATH = REPO_ROOT / "tracking_adapter_stonesoup_emitter.py"


def _source() -> str:
    return EMITTER_PATH.read_text()


def _tree() -> ast.Module:
    return ast.parse(_source(), filename=str(EMITTER_PATH))


def _code_without_docstring() -> str:
    """The module's own docstring explains, in prose, what this file
    must NOT do (clutter, YAML serialisation, ...) -- a naive full-text
    substring scan would trip on that explanation itself. Strips just
    the leading module docstring (identified via its own AST node, not a
    guessed line count) before doing textual "is this string absent"
    checks, the same fix test_tracking_adapter_verifier_independence.py
    already needed for an identical self-reference problem."""
    tree = _tree()
    docstring = ast.get_docstring(tree, clean=False)
    source = _source()
    if docstring is not None and docstring in source:
        return source.replace(docstring, "", 1)
    return source


def _call_names(tree: ast.Module):
    """Yields the dotted-ish name of every function/method call in the
    tree, e.g. "now" for both `datetime.now()` and `dt.now()`."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                yield node.func.attr, node
            elif isinstance(node.func, ast.Name):
                yield node.func.id, node


def test_emitter_file_exists():
    assert EMITTER_PATH.exists()


def test_rejects_datetime_now():
    tree = _tree()
    for name, node in _call_names(tree):
        assert name not in ("now", "utcnow"), (
            f"tracking_adapter_stonesoup_emitter.py calls {name}() at line {node.lineno} -- "
            f"forbidden, must use the one FIXED_TIMESTAMP constant instead"
        )


def test_uses_one_fixed_timestamp_constant():
    source = _source()
    assert "FIXED_TIMESTAMP = datetime(" in source
    assert "2026, 1, 1" in source


def test_rejects_unseeded_default_rng():
    tree = _tree()
    for name, node in _call_names(tree):
        if name != "default_rng":
            continue
        # Even a SEEDED default_rng() call is disallowed by this file's
        # own policy (module-level np.random.seed/random.seed plus
        # per-model `seed=` are the only sanctioned randomness
        # controls) -- so any default_rng() call at all fails this test.
        raise AssertionError(f"tracking_adapter_stonesoup_emitter.py calls default_rng() at line {node.lineno}")


def test_seeds_numpy_and_python_random_explicitly_at_module_scope():
    tree = _tree()
    seeded_numpy = False
    seeded_random = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "seed":
            if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "random":
                seeded_numpy = True
            elif isinstance(node.func.value, ast.Name) and node.func.value.id == "random":
                seeded_random = True
    assert seeded_numpy, "expected an explicit np.random.seed(...) call"
    assert seeded_random, "expected an explicit random.seed(...) call"


def test_every_lineargaussian_construction_has_an_explicit_seed():
    tree = _tree()
    calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "LinearGaussian":
            calls += 1
            kwarg_names = {kw.arg for kw in node.keywords}
            assert "seed" in kwarg_names, f"LinearGaussian(...) at line {node.lineno} has no explicit seed= kwarg"
    assert calls > 0, "expected at least one LinearGaussian(...) construction"


def test_every_measurement_model_function_call_disables_noise():
    tree = _tree()
    calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "function":
            calls += 1
            kwarg_names = {kw.arg: kw for kw in node.keywords}
            assert "noise" in kwarg_names, f".function(...) call at line {node.lineno} does not pass noise= explicitly"
            noise_kwarg = kwarg_names["noise"]
            assert isinstance(noise_kwarg.value, ast.Constant) and noise_kwarg.value.value is False, (
                f".function(...) call at line {node.lineno} does not set noise=False"
            )
    assert calls > 0, "expected at least one measurement model .function(...) call"


def test_rejects_undeclared_clutter():
    source = _code_without_docstring()
    assert "clutter" not in source.lower(), (
        "tracking_adapter_stonesoup_emitter.py references clutter -- step 10B's scope is explicitly "
        "no clutter of any kind; a clutter model would need its own declared, reviewed policy, not "
        "an incidental reference here"
    )


def test_rejects_uuid_based_or_otherwise_uncontrolled_ids():
    source = _source()
    assert "import uuid" not in source
    assert "uuid.uuid" not in source

    tree = _tree()
    # Every Track(...) construction must pass an explicit id= kwarg --
    # Stone Soup's own Track.__init__ defaults id to an auto-generated
    # UUID string if omitted, which would be an uncontrolled identifier.
    track_calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Track":
            track_calls += 1
            kwarg_names = {kw.arg for kw in node.keywords}
            assert "id" in kwarg_names, f"Track(...) at line {node.lineno} has no explicit id= kwarg"
    assert track_calls > 0, "expected at least one Track(...) construction"


def test_rejects_stonesoup_yaml_serialisation():
    source = _code_without_docstring()
    assert "yaml" not in source.lower()
    assert "serialise" not in source.lower()
    assert "serialize" not in source.lower()
    # Output must go through plain json, matching every other emitter in
    # this repository.
    assert "json.dump" in source
