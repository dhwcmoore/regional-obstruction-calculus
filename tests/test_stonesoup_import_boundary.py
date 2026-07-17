"""
Architectural import-boundary test for step 10 (Stone Soup integration,
docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md SS18-19).

Stone Soup is an OPTIONAL evidence producer -- it must never become a
dependency of the exact adapter or the R21 kernel. This is checked two
ways, neither of which requires Stone Soup to be installed at all:

  1. An AST scan of each named module's own source, proving no import
     statement (static OR dynamic, e.g. `importlib.import_module(...)`)
     references "stonesoup" anywhere -- immune to the reference being
     hidden behind a string concatenation or indirect alias, the same
     technique tracking_adapter_verifier.py's own independence test
     (test_tracking_adapter_verifier_independence.py) already uses for
     its analogous claim about tracking_adapter_generator.py.
  2. A runtime check that importing each module does not add
     "stonesoup" to sys.modules as a side effect -- meaningful whether
     or not Stone Soup happens to be installed in the environment this
     test runs in (if it is not installed, the check trivially holds;
     if it is, e.g. because both requirements.txt and requirements-
     stonesoup.txt are installed together, the check proves the core
     modules did not transitively pull it in anyway).
"""

import ast
import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# The exact adapter (tracking_adapter_generator.py included -- out of an
# abundance of caution beyond the four files this task named explicitly,
# since it is equally part of "the exact adapter verifier" this task's
# own introduction refers to) and every R21 module.
CORE_MODULES = [
    "tracking_adapter_format",
    "tracking_adapter_canon",
    "tracking_adapter_verifier",
    "tracking_adapter_certificate",
    "tracking_adapter_generator",
    "r21_certificate_format",
    "r21_certificate_emitter",
    "r21_certificate_checker",
    "r21_repair_or_separator",
    "rational_linear_algebra",
]

FORBIDDEN_SUBSTRING = "stonesoup"


def _module_path(name: str) -> Path:
    return REPO_ROOT / f"{name}.py"


def _imported_module_names(tree: ast.Module) -> set:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0].lower())
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0].lower())
    return names


def _dynamic_import_string_args(tree: ast.Module):
    dynamic_names = {"__import__", "import_module", "find_spec"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name in dynamic_names:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        yield arg.value


@pytest.mark.parametrize("module_name", CORE_MODULES)
def test_module_does_not_statically_import_stonesoup(module_name):
    path = _module_path(module_name)
    assert path.exists(), f"expected {path} to exist"
    tree = ast.parse(path.read_text(), filename=str(path))
    imported = _imported_module_names(tree)
    assert FORBIDDEN_SUBSTRING not in imported, (
        f"{module_name}.py imports {imported!r}, which includes stonesoup -- "
        f"this violates the step 10 boundary: Stone Soup must remain an "
        f"optional evidence producer, never a dependency of the exact "
        f"adapter or R21 kernel"
    )


@pytest.mark.parametrize("module_name", CORE_MODULES)
def test_module_does_not_dynamically_import_stonesoup(module_name):
    path = _module_path(module_name)
    tree = ast.parse(path.read_text(), filename=str(path))
    for arg_value in _dynamic_import_string_args(tree):
        assert FORBIDDEN_SUBSTRING not in arg_value.lower(), (
            f"{module_name}.py dynamically imports {arg_value!r}, which "
            f"references stonesoup"
        )


@pytest.mark.parametrize("module_name", CORE_MODULES)
def test_importing_module_does_not_pull_in_stonesoup(module_name):
    was_present_before = "stonesoup" in sys.modules
    importlib.import_module(module_name)
    if not was_present_before:
        assert "stonesoup" not in sys.modules, (
            f"importing {module_name} added 'stonesoup' to sys.modules -- "
            f"it has a transitive runtime dependency on Stone Soup, "
            f"violating the step 10 boundary"
        )


def test_requirements_txt_does_not_mention_stonesoup():
    """Stone Soup must be pinned ONLY in requirements-stonesoup.txt, never
    folded into the core requirements.txt that the exact adapter and R21
    kernel install from."""
    requirements = (REPO_ROOT / "requirements.txt").read_text().lower()
    assert "stonesoup" not in requirements


def test_stonesoup_requirements_file_exists_and_is_separate():
    path = REPO_ROOT / "requirements-stonesoup.txt"
    assert path.exists()
    assert path != REPO_ROOT / "requirements.txt"
