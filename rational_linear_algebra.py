#!/usr/bin/env python3
"""
rational_linear_algebra.py

Shared exact-rational linear algebra used by residue_classifier.py and
refinement_checker.py: matrix/vector products over Fraction, and an exact
Gauss-Jordan solver over Q. No floating point anywhere in this module.

Both callers previously had their own solver: residue_classifier.py used
`numpy.linalg.lstsq` on a `float` cast of the exact data, then rounded the
result back to a `Fraction` via `limit_denominator` and checked it against
the original system. That happened to work on the four-cycle example, but
it is not exact rational linear algebra -- an unrelated system could
produce a floating-point solution that is close enough to round to a
plausible-looking but wrong rational, or fail to round-trip at all.
`solve_over_Q` below replaces that path with the same exact elimination
`refinement_checker.py` already used for its solver cross-check.
"""

from fractions import Fraction
from typing import List, Optional, Tuple


def mat_vec(matrix: List[List[Fraction]], vec: List[Fraction]) -> List[Fraction]:
    return [sum((row[j] * vec[j] for j in range(len(vec))), Fraction(0)) for row in matrix]


def mat_mat(a: List[List[Fraction]], b: List[List[Fraction]]) -> List[List[Fraction]]:
    """a @ b for matrices given as lists of rows. a is m x n, b is n x p."""
    if not a or not b:
        return []
    n = len(b)
    p = len(b[0])
    return [
        [sum((a[i][k] * b[k][j] for k in range(n)), Fraction(0)) for j in range(p)]
        for i in range(len(a))
    ]


def transpose(matrix: List[List[Fraction]]) -> List[List[Fraction]]:
    if not matrix:
        return []
    return [[row[j] for row in matrix] for j in range(len(matrix[0]))]


def nullspace_over_Q(matrix: List[List[Fraction]]) -> List[List[Fraction]]:
    """
    Exact Gauss-Jordan elimination over Q. Returns a basis (list of column
    vectors, as plain lists) for {x : matrix @ x == 0}, by reducing to
    row-echelon form and reading one basis vector off each free column.
    """
    m = len(matrix)
    n = len(matrix[0]) if matrix else 0
    aug = [list(row) for row in matrix]

    pivot_row = 0
    pivot_cols: List[int] = []
    for col in range(n):
        pivot = next((r for r in range(pivot_row, m) if aug[r][col] != 0), None)
        if pivot is None:
            continue
        aug[pivot_row], aug[pivot] = aug[pivot], aug[pivot_row]
        pivot_val = aug[pivot_row][col]
        aug[pivot_row] = [x / pivot_val for x in aug[pivot_row]]
        for r in range(m):
            if r != pivot_row and aug[r][col] != 0:
                factor = aug[r][col]
                aug[r] = [aug[r][k] - factor * aug[pivot_row][k] for k in range(n)]
        pivot_cols.append(col)
        pivot_row += 1
        if pivot_row == m:
            break

    pivot_set = set(pivot_cols)
    free_cols = [c for c in range(n) if c not in pivot_set]

    basis = []
    for free_col in free_cols:
        vec = [Fraction(0)] * n
        vec[free_col] = Fraction(1)
        for i, col in enumerate(pivot_cols):
            vec[col] = -aug[i][free_col]
        basis.append(vec)
    return basis


def in_span_over_Q(basis: List[List[Fraction]], v: List[Fraction]) -> bool:
    """Whether v lies in the span of the given basis vectors, decided exactly
    by solving (basis as columns) @ c == v over Q."""
    if not basis:
        return is_zero(v)
    cols = transpose(basis)
    has_solution, _ = solve_over_Q(cols, v)
    return has_solution


def row_vec_mat(row: List[Fraction], matrix: List[List[Fraction]]) -> List[Fraction]:
    if not matrix:
        return []
    ncols = len(matrix[0])
    return [
        sum((row[i] * matrix[i][j] for i in range(len(row))), Fraction(0))
        for j in range(ncols)
    ]


def dot(u: List[Fraction], v: List[Fraction]) -> Fraction:
    return sum((a * b for a, b in zip(u, v)), Fraction(0))


def is_zero(v: List[Fraction]) -> bool:
    return all(x == 0 for x in v)


def solve_over_Q(
    matrix: List[List[Fraction]], rhs: List[Fraction]
) -> Tuple[bool, Optional[List[Fraction]]]:
    """
    Exact Gauss-Jordan elimination over Q. Determines whether
    `matrix @ b == rhs` has a solution.

    Returns (True, b) with a particular solution if the system is
    consistent, or (False, None) if it is provably inconsistent (some row
    reduces to 0 = nonzero).
    """
    m = len(matrix)
    n = len(matrix[0]) if matrix else 0
    aug = [list(matrix[i]) + [rhs[i]] for i in range(m)]

    pivot_row = 0
    pivot_cols: List[int] = []
    for col in range(n):
        pivot = next((r for r in range(pivot_row, m) if aug[r][col] != 0), None)
        if pivot is None:
            continue
        aug[pivot_row], aug[pivot] = aug[pivot], aug[pivot_row]
        pivot_val = aug[pivot_row][col]
        aug[pivot_row] = [x / pivot_val for x in aug[pivot_row]]
        for r in range(m):
            if r != pivot_row and aug[r][col] != 0:
                factor = aug[r][col]
                aug[r] = [aug[r][k] - factor * aug[pivot_row][k] for k in range(n + 1)]
        pivot_cols.append(col)
        pivot_row += 1
        if pivot_row == m:
            break

    for row in aug:
        if all(x == 0 for x in row[:n]) and row[n] != 0:
            return False, None

    solution = [Fraction(0)] * n
    for i, col in enumerate(pivot_cols):
        solution[col] = aug[i][n]
    return True, solution
