#!/usr/bin/env python3
"""
r21_repair_or_separator.py

An untrusted, deliberately not-formally-verified Python generator for the
alternative `rocq/ExactRationalRepairOrSeparator.v` (R21) proves in Rocq:
for any rational system `D b = r`, either a repair `b` with `Db = r`, or a
separator `y` with `D^Ty = 0` and `y.r = 1`.

"Untrusted" is load-bearing, not a hedge: this module is a hand-written
mirror of R21's algorithm (Route C2 of `docs/design/
EXACT_RATIONAL_SEPARATION_SPEC.md` -- augmented elimination on `[D | r |
I_m]`), not an extraction of the Rocq function (this repository has never
used Rocq's Extraction mechanism -- see `rocq/PairwiseToGlobalAssembly.v`'s
own header for the same disclosure about its OCaml mirror). A bug here
would be a bug in this file only: `r21_certificate_checker.py` recomputes
`Db` or `D^Ty`/`y.r` itself from the emitted certificate and rejects
anything that does not check out, so this module's output is never trusted
on its own -- only what the independent checker accepts is.

Algorithm: perform the same column-by-column Gauss-Jordan elimination
`rational_linear_algebra.solve_over_Q` does on `[D | r]`, but with `I_m`
appended as extra tracked columns. Every row of the eliminated matrix is
some fixed linear combination of the *original* rows (row operations are
only swap / scale / subtract-a-multiple), and the `I_m` block of a given
row records exactly which combination produced it. If elimination ever
reduces a row to `[0 ... 0 | c | y]` with `c != 0`, the `D`-block being
all-zero means `y` annihilates every column of `D` (`D^Ty = 0`), and the
`r`-block being `c` means `y.r = c`; rescaling by `1/c` gives the
normalised separator (`y.r = 1`). If no such row appears, the system is
consistent and back-substitution over the pivot columns gives a repair.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional

RESULT_REPAIR = "repair"
RESULT_SEPARATOR = "separator"


@dataclass(frozen=True)
class RepairOrSeparatorResult:
    result: str
    repair: Optional[List[Fraction]] = None
    separator: Optional[List[Fraction]] = None


def repair_or_separate(D: List[List[Fraction]], r: List[Fraction]) -> RepairOrSeparatorResult:
    m = len(D)
    n = len(D[0]) if D else 0
    if len(r) != m:
        raise ValueError(f"D has {m} rows but r has length {len(r)}")
    if any(len(row) != n for row in D):
        raise ValueError("D is not rectangular")

    width = n + 1 + m
    aug = [
        list(D[i]) + [r[i]] + [Fraction(1) if k == i else Fraction(0) for k in range(m)]
        for i in range(m)
    ]

    pivot_row = 0
    pivot_cols: List[int] = []
    for col in range(n):
        pivot = next((rr for rr in range(pivot_row, m) if aug[rr][col] != 0), None)
        if pivot is None:
            continue
        aug[pivot_row], aug[pivot] = aug[pivot], aug[pivot_row]
        pivot_val = aug[pivot_row][col]
        aug[pivot_row] = [x / pivot_val for x in aug[pivot_row]]
        for rr in range(m):
            if rr != pivot_row and aug[rr][col] != 0:
                factor = aug[rr][col]
                aug[rr] = [aug[rr][k] - factor * aug[pivot_row][k] for k in range(width)]
        pivot_cols.append(col)
        pivot_row += 1
        if pivot_row == m:
            break

    for row in aug:
        if all(x == 0 for x in row[:n]) and row[n] != 0:
            c = row[n]
            y_raw = row[n + 1:]
            separator = [val / c for val in y_raw]
            return RepairOrSeparatorResult(result=RESULT_SEPARATOR, separator=separator)

    b = [Fraction(0)] * n
    for i, col in enumerate(pivot_cols):
        b[col] = aug[i][n]
    return RepairOrSeparatorResult(result=RESULT_REPAIR, repair=b)
