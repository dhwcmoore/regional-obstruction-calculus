from fractions import Fraction as F

from finite_algebra import FiniteAlgebra, zero_vector


def _diagonal_algebra() -> FiniteAlgebra:
    """e_i * e_j = delta_ij e_i (like Q x Q): associative by construction."""
    return FiniteAlgebra(
        dim=2,
        basis_names=("e0", "e1"),
        structure_constants={
            (0, 0): (F(1), F(0)),
            (1, 1): (F(0), F(1)),
        },
    )


def _nonassociative_algebra() -> FiniteAlgebra:
    """e0*e0=e1, e0*e1=e0, e1*e0=e1, e1*e1=e0 -- deliberately not associative."""
    return FiniteAlgebra(
        dim=2,
        basis_names=("e0", "e1"),
        structure_constants={
            (0, 0): (F(0), F(1)),
            (0, 1): (F(1), F(0)),
            (1, 0): (F(0), F(1)),
            (1, 1): (F(1), F(0)),
        },
    )


def test_diagonal_algebra_is_associative_on_basis_triples():
    alg = _diagonal_algebra()
    e0, e1 = alg.basis_vector("e0"), alg.basis_vector("e1")
    for a in (e0, e1):
        for b in (e0, e1):
            for c in (e0, e1):
                assert alg.is_associative_on(a, b, c)


def test_diagonal_algebra_is_associative_on_generic_vectors():
    alg = _diagonal_algebra()
    a = (F(2), F(-3))
    b = (F(1, 2), F(5))
    c = (F(-1), F(7, 3))
    assert alg.associator(a, b, c) == zero_vector(2)


def test_nonassociative_algebra_has_nonzero_associator():
    alg = _nonassociative_algebra()
    e0 = alg.basis_vector("e0")
    defect = alg.associator(e0, e0, e0)
    assert defect != zero_vector(2)
    # e0*(e0*e0) - (e0*e0)*e0 = e0*e1 - e1*e0 = e0 - e1
    assert defect == (F(1), F(-1))
    assert not alg.is_associative_on(e0, e0, e0)


def test_multiply_matches_structure_constants_directly():
    alg = _nonassociative_algebra()
    e0, e1 = alg.basis_vector("e0"), alg.basis_vector("e1")
    assert alg.multiply(e0, e0) == (F(0), F(1))
    assert alg.multiply(e0, e1) == (F(1), F(0))
    assert alg.multiply(e1, e0) == (F(0), F(1))
    assert alg.multiply(e1, e1) == (F(1), F(0))


def test_multiply_is_bilinear():
    alg = _nonassociative_algebra()
    e0, e1 = alg.basis_vector("e0"), alg.basis_vector("e1")
    a = (F(3), F(-2))  # 3*e0 - 2*e1
    direct = alg.multiply(a, e0)
    expanded = tuple(
        F(3) * x - F(2) * y for x, y in zip(alg.multiply(e0, e0), alg.multiply(e1, e0))
    )
    assert direct == expanded
