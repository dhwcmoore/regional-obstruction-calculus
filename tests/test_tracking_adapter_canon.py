"""
Tests for tracking_adapter_canon.py -- step 2 of the tracking-adapter
implementation order. Cross-checks the two independently-implemented
rounding routes against each other (not against a shared oracle), with
particular attention to exact half-way rounding ties, which is the only
case where an implementation bug in either route is likely to surface.
"""

from fractions import Fraction

import pytest

from tracking_adapter_canon import (
    convert_and_verify,
    to_exact_rational,
    to_exact_rational_independent,
)


@pytest.mark.parametrize(
    "dec_str,places,expected",
    [
        ("2", 6, Fraction(2)),
        ("0.333333", 6, Fraction(333333, 1000000)),
        ("-3.1415925", 6, Fraction(-392699, 125000)),  # exact tie: -3.141592 (even) vs -3.141593 (odd) -> even wins
        ("0", 6, Fraction(0)),
        ("-0", 6, Fraction(0)),
        ("1.0000005", 6, Fraction(1)),      # exact tie at the rounding boundary -> round to even (0)
        ("1.0000015", 6, Fraction(1000002, 1000000)),  # exact tie -> round to even (2)
        ("100", 0, Fraction(100)),
        ("100.4", 0, Fraction(100)),
        ("100.5", 0, Fraction(100)),   # tie -> even -> 100
        ("101.5", 0, Fraction(102)),   # tie -> even -> 102
    ],
)
def test_both_routes_agree_and_match_expected(dec_str, places, expected):
    a = to_exact_rational(dec_str, places, "half_even")
    b = to_exact_rational_independent(dec_str, places, "half_even")
    assert a == b == expected


def test_convert_and_verify_returns_r21_canonical_string():
    assert convert_and_verify("0.333333", 6, "half_even") == "333333/1000000"
    assert convert_and_verify("2", 6, "half_even") == "2"
    assert convert_and_verify("-3.1415925", 6, "half_even") == "-392699/125000"
    assert convert_and_verify("0", 6, "half_even") == "0"


def test_rejects_exponent_notation():
    with pytest.raises(ValueError, match="not a canonical plain-decimal string"):
        to_exact_rational("1E5", 6, "half_even")
    with pytest.raises(ValueError, match="not a canonical plain-decimal string"):
        to_exact_rational_independent("1E5", 6, "half_even")


def test_rejects_nan_and_infinity():
    for bad in ("NaN", "Infinity", "-Infinity", "nan", "inf"):
        with pytest.raises(ValueError, match="not a canonical plain-decimal string"):
            to_exact_rational(bad, 6, "half_even")


def test_rejects_non_string_input():
    with pytest.raises(ValueError, match="not a canonical decimal string"):
        to_exact_rational(1.5, 6, "half_even")  # a Python float, not a str


def test_rejects_negative_decimal_places():
    with pytest.raises(ValueError, match="decimal_places must be >= 0"):
        to_exact_rational("1.5", -1, "half_even")


def test_rejects_non_int_decimal_places():
    with pytest.raises(ValueError, match="decimal_places must be an int"):
        to_exact_rational("1.5", 6.0, "half_even")
    with pytest.raises(ValueError, match="decimal_places must be an int"):
        to_exact_rational("1.5", True, "half_even")  # bool is an int subclass -- must still be rejected


def test_rejects_unsupported_rounding_mode():
    with pytest.raises(ValueError, match="unsupported rounding_mode"):
        to_exact_rational("1.5", 6, "round_half_up")


def test_rejects_malformed_decimal_strings():
    for bad in ("1.2.3", "abc", "1,5", "--1", "1.", ".5", "1_000", ""):
        with pytest.raises(ValueError, match="not a canonical plain-decimal string"):
            to_exact_rational(bad, 6, "half_even")


def test_convert_and_verify_raises_on_route_disagreement(monkeypatch):
    """Deliberately break one route's output to confirm convert_and_verify
    actually cross-checks rather than trusting either route alone."""
    import tracking_adapter_canon as mod

    def broken_independent(dec_str, decimal_places, rounding_mode):
        return Fraction(999999)

    monkeypatch.setattr(mod, "to_exact_rational_independent", broken_independent)
    with pytest.raises(ValueError, match="disagree"):
        mod.convert_and_verify("0.333333", 6, "half_even")
