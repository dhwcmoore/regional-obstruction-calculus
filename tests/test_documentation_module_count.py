"""
A documentation-drift test, added after a real drift was found: the
Rocq module count had silently diverged across README.md, STATUS.md,
PROJECT_MAP.md, and REPRODUCIBILITY.md (27 in one, 28 in another, and
R22's seven modules were never counted anywhere) because
`check-rocq-inventory` (Makefile) checks `rocq/*.v` against
`ROCQ_MODULES` -- a real, mechanical check -- but nothing checked that
the PROSE describing that count, in the top-level docs, ever agreed
with it. This file is that check, not a substitute for
`check-rocq-inventory`: it re-derives the true count directly from
`rocq/*.v` and the Makefile, then asserts the docs quote the same
number, and that both R22 and R24 are actually mentioned somewhere in
the results/status account (the same drift that dropped the module
count also dropped R22 out of every doc but the Makefile and rocq/
themselves, for a full session).
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROCQ_DIR = REPO_ROOT / "rocq"
MAKEFILE = REPO_ROOT / "Makefile"


def _read(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8")


def _rocq_module_count() -> int:
    return len(list(ROCQ_DIR.glob("*.v")))


def _declared_rocq_modules() -> list[str]:
    makefile_text = MAKEFILE.read_text(encoding="utf-8")
    match = re.search(r"ROCQ_MODULES\s*:=\s*(.*?)\n\n", makefile_text, re.DOTALL)
    assert match, "Makefile's ROCQ_MODULES assignment not found in the expected form"
    modules = match.group(1).replace("\\\n", " ").split()
    return modules


def test_rocq_module_count_matches_makefile_declaration():
    actual = _rocq_module_count()
    declared = _declared_rocq_modules()
    assert len(declared) == actual, (
        f"rocq/*.v has {actual} files but Makefile's ROCQ_MODULES declares "
        f"{len(declared)} -- run `make check-rocq-inventory` for the file-by-file diff"
    )
    assert sorted(declared) == sorted(m.stem for m in ROCQ_DIR.glob("*.v"))


def test_readme_states_current_module_count():
    # README.md is pure current-state prose (unlike CHANGELOG.md, which
    # legitimately quotes old counts under dated historical headings) --
    # so every module-count-shaped mention must agree with the true count,
    # not merely have the true count appear somewhere alongside a stale
    # one. The negative lookbehind excludes false matches from R-number
    # table cells ("R10 Rocq modules", "R11-R16 Rocq modules").
    actual = _rocq_module_count()
    text = _read("README.md")
    counts = {int(n) for n in re.findall(r"(?<![\w-])(\d+)\s+(?:active |Rocq )?[Mm]odules?", text)}
    assert counts == {actual}, (
        f"README.md's module-count mentions are {sorted(counts)}, expected only {{{actual}}} -- "
        f"likely stale prose left over from before the count changed"
    )


def test_status_states_current_module_count():
    actual = _rocq_module_count()
    text = _read("STATUS.md")
    counts = {int(n) for n in re.findall(r"(\d+)-file dependency closure", text)}
    assert counts == {actual}, (
        f"STATUS.md's module-count mentions are {sorted(counts)}, expected only {{{actual}}} -- "
        f"likely stale prose left over from before the count changed"
    )


def test_project_map_states_current_module_count():
    actual = _rocq_module_count()
    text = _read("PROJECT_MAP.md")
    counts = {int(n) for n in re.findall(r"All (\d+) active modules", text)}
    assert counts == {actual}, (
        f"PROJECT_MAP.md's module-count mentions are {sorted(counts)}, expected only {{{actual}}} -- "
        f"likely stale prose left over from before the count changed"
    )


def test_reproducibility_states_current_module_count():
    actual = _rocq_module_count()
    text = _read("REPRODUCIBILITY.md")
    counts = {int(n) for n in re.findall(r"(\d+)-module dependency closure", text)}
    assert counts == {actual}, (
        f"REPRODUCIBILITY.md's module-count mentions are {sorted(counts)}, expected only {{{actual}}} -- "
        f"likely stale prose left over from before the count changed"
    )


def test_r22_and_r24_both_documented_in_results_and_status():
    results = _read("RESULTS.md")
    status = _read("STATUS.md")
    for label, text, doc in (
        ("R22", results, "RESULTS.md"),
        ("R24", results, "RESULTS.md"),
    ):
        assert re.search(rf"\b{label}\b", text), f"{label} is not mentioned in {doc}"
    # STATUS.md doesn't use the bare "R22"/"R24" labels in the same way as
    # RESULTS.md's numbered headings -- check for the theorem names instead,
    # which is what actually matters (the drift this test guards against
    # was R22 being entirely absent from STATUS.md, not a label mismatch).
    assert "cycle-quotient duality" in status.lower(), (
        "STATUS.md does not document R22 (cycle-quotient duality)"
    )
    assert "certificate transport" in status.lower(), (
        "STATUS.md does not document R24 (certificate transport)"
    )
