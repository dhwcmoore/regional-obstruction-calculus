"""
Architectural independence tests for tracking_adapter_verifier.py.

These do not test WHAT the verifier decides (see test_tracking_adapter_
verifier.py for that) -- they test that its accept/reject decision does
not, and structurally cannot, depend on tracking_adapter_generator.py at
all: no import at parse time (an AST scan, not a grep -- immune to the
import being hidden behind a string or an indirect alias), and no
behavioural dependence at runtime even if the generator module is
monkeypatched to return nonsense.
"""

import ast
import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFIER_SOURCE = REPO_ROOT / "tracking_adapter_verifier.py"


def _imported_module_names(tree: ast.Module) -> set:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def test_verifier_source_does_not_import_generator_module():
    tree = ast.parse(VERIFIER_SOURCE.read_text(), filename=str(VERIFIER_SOURCE))
    imported = _imported_module_names(tree)
    assert "tracking_adapter_generator" not in imported, (
        f"tracking_adapter_verifier.py imports {imported!r}, which includes "
        f"tracking_adapter_generator -- this violates the independence "
        f"boundary the design doc (SS12) and step 4's own docstring require"
    )


def test_verifier_has_no_dynamic_import_of_generator():
    """Belt-and-braces check, in addition to the static-import AST scan:
    looks for a dynamic import route (`importlib.import_module(...)`,
    `__import__(...)`, `importlib.util.find_spec(...)`) whose argument
    names the generator module or its key entry point -- a form of
    obfuscated dependency a plain `ast.Import`/`ast.ImportFrom` scan
    would not catch. Deliberately does NOT do a blanket substring search
    over the whole file: this module's own docstring names `tracking_
    adapter_generator.py` for documentation (explaining what is NOT
    shared), which is expected and is not a dependency."""
    tree = ast.parse(VERIFIER_SOURCE.read_text(), filename=str(VERIFIER_SOURCE))
    forbidden = {"tracking_adapter_generator", "generate_problem"}
    dynamic_import_names = {"__import__", "import_module", "find_spec"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name in dynamic_import_names:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        assert not any(f in arg.value for f in forbidden), (
                            f"dynamic import call {func_name!r} references the generator "
                            f"module via string argument {arg.value!r}"
                        )


def test_monkeypatching_generator_does_not_affect_verification(monkeypatch):
    """Even if tracking_adapter_generator.py is imported ELSEWHERE in the
    process and then broken, the verifier's own result must not change --
    proving the independence is not just "no import statement" but "no
    runtime dependence via any indirect channel" (a shared global, a
    monkeypatched function looked up dynamically, etc.)."""
    import tracking_adapter_generator as gen
    from tests.test_tracking_adapter_verifier import _obstructed_fixture_doc
    from tracking_adapter_verifier import verify_snapshot_doc

    doc = _obstructed_fixture_doc()
    baseline = verify_snapshot_doc(doc)
    assert baseline.accepted
    assert baseline.r == [1, 1, 1, -2]

    def broken_generate_problem(snapshot):
        raise RuntimeError("generator deliberately broken by this test")

    monkeypatch.setattr(gen, "generate_problem", broken_generate_problem)
    monkeypatch.setattr(gen, "to_roc_input", lambda problem: {"schema": "roc-input/v1", "D": [], "r": []})

    after = verify_snapshot_doc(doc)
    assert after.accepted == baseline.accepted
    assert after.r == baseline.r
    assert after.D == baseline.D


def test_generator_and_verifier_reach_same_result_via_different_internal_paths():
    """Confirms the two modules AGREE (they should, since they implement
    the same design), while test_verifier_source_does_not_import_
    generator_module confirms they do so via genuinely separate code --
    agreement alone would not prove independence, and independence alone
    would not prove correctness; both are needed and are therefore two
    separate tests, not one."""
    from tests.test_tracking_adapter_verifier import _obstructed_fixture_doc
    from tracking_adapter_format import parse_snapshot_doc
    from tracking_adapter_generator import generate_problem
    from tracking_adapter_verifier import verify_snapshot_doc

    doc = _obstructed_fixture_doc()

    snapshot = parse_snapshot_doc(doc)
    generator_problem = generate_problem(snapshot)

    verifier_result = verify_snapshot_doc(doc)
    assert verifier_result.accepted

    assert generator_problem.D == verifier_result.D
    assert generator_problem.r == verifier_result.r
    assert generator_problem.track_order == verifier_result.track_order
    assert generator_problem.edge_order == verifier_result.edge_order
