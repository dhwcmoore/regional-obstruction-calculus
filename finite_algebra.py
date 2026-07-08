#!/usr/bin/env python3
"""
finite_algebra.py

A small, general-purpose finite-dimensional algebra over Fraction, given by
structure constants. This is the bottom layer of the associator-generation
pipeline described in the paper's Section 4 (First-order repair calculus):
a not-necessarily-associative bilinear product on a finite-dimensional
Q-vector space, plus the literal associator

    associator(a, b, c) = a * (b * c) - (a * b) * c

(the right-minus-left convention used throughout the paper, Definition
"Associator defect"). No shortcut formula is used here: both parenthesised
products are computed by the same `multiply` method and then subtracted.

This module knows nothing about regions, seams, or boundary corrections --
that structure is layered on top in regional_composition.py. It exists so
that "the associator is computed, not assumed" is true starting from the
lowest level: a bilinear multiplication table.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Tuple

Vector = Tuple[Fraction, ...]


def zero_vector(dim: int) -> Vector:
    return tuple(Fraction(0) for _ in range(dim))


def add(u: Vector, v: Vector) -> Vector:
    return tuple(a + b for a, b in zip(u, v))


def sub(u: Vector, v: Vector) -> Vector:
    return tuple(a - b for a, b in zip(u, v))


def scale(c: Fraction, v: Vector) -> Vector:
    return tuple(c * x for x in v)


@dataclass(frozen=True)
class FiniteAlgebra:
    """
    A finite-dimensional not-necessarily-associative Q-algebra given by
    structure constants: e_i * e_j = structure_constants[(i, j)], a vector
    in the same basis, defaulting to the zero vector when a pair is absent.
    """

    dim: int
    basis_names: Tuple[str, ...]
    structure_constants: Dict[Tuple[int, int], Vector]

    def __post_init__(self) -> None:
        if len(self.basis_names) != self.dim:
            raise ValueError("basis_names must have length dim")
        for (i, j), prod in self.structure_constants.items():
            if not (0 <= i < self.dim and 0 <= j < self.dim):
                raise ValueError(f"structure constant index ({i},{j}) out of range")
            if len(prod) != self.dim:
                raise ValueError(f"structure constant ({i},{j}) has wrong dimension")

    def multiply(self, a: Vector, b: Vector) -> Vector:
        """Bilinear extension of the structure constants to arbitrary vectors."""
        result = list(zero_vector(self.dim))
        for i in range(self.dim):
            if a[i] == 0:
                continue
            for j in range(self.dim):
                if b[j] == 0:
                    continue
                coeff = a[i] * b[j]
                prod = self.structure_constants.get((i, j))
                if prod is None:
                    continue
                for k in range(self.dim):
                    if prod[k] != 0:
                        result[k] += coeff * prod[k]
        return tuple(result)

    def associator(self, a: Vector, b: Vector, c: Vector) -> Vector:
        """
        Right-minus-left associator, matching the paper's Definition
        "Associator defect": a*(b*c) - (a*b)*c. Computed by literally
        forming both parenthesised products with `multiply`, not by any
        closed-form shortcut.
        """
        left = self.multiply(self.multiply(a, b), c)
        right = self.multiply(a, self.multiply(b, c))
        return sub(right, left)

    def is_associative_on(self, a: Vector, b: Vector, c: Vector) -> bool:
        return all(x == 0 for x in self.associator(a, b, c))

    def basis_vector(self, name: str) -> Vector:
        i = self.basis_names.index(name)
        v = [Fraction(0)] * self.dim
        v[i] = Fraction(1)
        return tuple(v)
