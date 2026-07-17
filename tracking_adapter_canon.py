#!/usr/bin/env python3
"""
tracking_adapter_canon.py

Step 2 of the tracking-adapter implementation order in
`docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md` SS10/SS16:
canonical decimal-string -> exact rational -> R21 `a/b`-string
conversion, with INDEPENDENT verification -- two separately-implemented
rounding routes that must agree, not one implementation trusted on its
own. This mirrors R21's own two-checker discipline
(`r21_certificate_checker.py`'s docstring: independence means never
importing the function under test), applied to the one new numeric
operation this adapter introduces that R21 itself has no opinion about:
R21's own parser (`r21_certificate_format.py`'s `_RATIONAL_RE`) accepts
only `-?digits` or `-?digits/digits` and rejects decimal notation
outright, so nothing on the R21 side ever performs this conversion or
could catch a bug in it.

The two routes:

  - `to_exact_rational` (the "generator" route): uses `decimal.Decimal`'s
    own rounding context (`ROUND_HALF_EVEN`) to round at the declared
    number of decimal places, then converts the rounded `Decimal` to a
    `Fraction` exactly (`Fraction(Decimal(...))` is exact -- `Decimal`
    is itself a base-10 rational internally, so this step introduces no
    floating-point error).
  - `to_exact_rational_independent` (the "verifier" route): parses the
    SAME canonical decimal string directly to an exact `Fraction` at
    full precision (no rounding at all), then performs round-half-to-
    even itself via plain integer/`Fraction` arithmetic -- floor
    division and remainder comparison against `Fraction(1, 2)` -- never
    calling `decimal.Decimal`'s rounding machinery at all.

Both must produce the same value for `convert_and_verify` to return
anything; disagreement raises, exactly as a mismatched R21 certificate
digest would.

Input format, per the design doc SS10's `quantisation_policy`: plain
decimal only, `-?digits(.digits)?`, no exponent notation, no `NaN`, no
infinity -- enforced by an explicit regex BEFORE any parsing is
attempted, not by relying on `Decimal`'s own (much more permissive)
parser to reject these after the fact (`Decimal("NaN")` and
`Decimal("1E5")` are both valid `Decimal` values that this module's
input format explicitly excludes).

Only `rounding_mode == "half_even"` is implemented at v1, matching the
design doc's own example policy (SS10) -- any other declared mode is
rejected outright rather than silently ignored.
"""

import decimal
import re
from fractions import Fraction

_DECIMAL_RE = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")

SUPPORTED_ROUNDING_MODES = frozenset({"half_even"})


def _validate_decimal_string(s: str) -> None:
    if not isinstance(s, str):
        raise ValueError(f"not a canonical decimal string: {s!r}")
    if not _DECIMAL_RE.match(s):
        raise ValueError(
            f"not a canonical plain-decimal string (no exponent, no NaN/Infinity, "
            f"digits with an optional single '.'): {s!r}"
        )


def _validate_policy(decimal_places: int, rounding_mode: str) -> None:
    if not isinstance(decimal_places, int) or isinstance(decimal_places, bool):
        raise ValueError(f"decimal_places must be an int, got {decimal_places!r}")
    if decimal_places < 0:
        raise ValueError(f"decimal_places must be >= 0, got {decimal_places}")
    if rounding_mode not in SUPPORTED_ROUNDING_MODES:
        raise ValueError(
            f"unsupported rounding_mode {rounding_mode!r}; supported: {sorted(SUPPORTED_ROUNDING_MODES)}"
        )


def to_exact_rational(dec_str: str, decimal_places: int, rounding_mode: str) -> Fraction:
    """The generator route: round via `decimal.Decimal`'s own rounding
    context, then convert the ALREADY-ROUNDED `Decimal` to a `Fraction`
    exactly."""
    _validate_decimal_string(dec_str)
    _validate_policy(decimal_places, rounding_mode)
    ctx = decimal.Context(rounding=decimal.ROUND_HALF_EVEN)
    d = decimal.Decimal(dec_str)
    quantum = decimal.Decimal(1).scaleb(-decimal_places)
    rounded = d.quantize(quantum, context=ctx)
    return Fraction(rounded)


def to_exact_rational_independent(dec_str: str, decimal_places: int, rounding_mode: str) -> Fraction:
    """The verifier route: full-precision exact `Fraction` from the raw
    string, then round-half-to-even via plain integer arithmetic --
    shares no rounding code with `to_exact_rational`. `decimal.Decimal`
    is used ONLY as a string-to-exact-value parser here (`Fraction(
    Decimal(s))` at full precision, no `quantize`/rounding context
    involved), which is a different operation from `to_exact_rational`'s
    use of `Decimal.quantize` to perform the rounding itself."""
    _validate_decimal_string(dec_str)
    _validate_policy(decimal_places, rounding_mode)
    exact = Fraction(decimal.Decimal(dec_str))
    scale = Fraction(10) ** decimal_places
    scaled = exact * scale
    floor_n = scaled.numerator // scaled.denominator
    remainder = scaled - floor_n
    half = Fraction(1, 2)
    if remainder < half:
        n = floor_n
    elif remainder > half:
        n = floor_n + 1
    else:
        n = floor_n if floor_n % 2 == 0 else floor_n + 1
    # scale = Fraction(10) ** decimal_places is always an integer (its own
    # denominator is 1, since decimal_places was validated >= 0 above), so
    # dividing n by scale's integer value is exact.
    return Fraction(n, scale.numerator)


def rational_to_r21_string(value: Fraction) -> str:
    """R21's own canonical `a/b` form is exactly `str(Fraction(...))`
    (`r21_certificate_format.py`'s `parse_rational` checks canonicality
    via this same `str(value)` comparison) -- no separate formatting
    logic is introduced here."""
    return str(value)


def convert_and_verify(dec_str: str, decimal_places: int, rounding_mode: str) -> str:
    """Runs BOTH independent routes and raises on any disagreement,
    returning the canonical R21 `a/b` string only if they agree
    exactly. This is the function any generator (step 3) or independent
    verifier (step 4) should call -- neither should call
    `to_exact_rational` alone and trust it."""
    generator_value = to_exact_rational(dec_str, decimal_places, rounding_mode)
    verifier_value = to_exact_rational_independent(dec_str, decimal_places, rounding_mode)
    if generator_value != verifier_value:
        raise ValueError(
            f"decimal conversion routes disagree for {dec_str!r} at "
            f"{decimal_places} places ({rounding_mode}): "
            f"generator route = {generator_value}, verifier route = {verifier_value}"
        )
    return rational_to_r21_string(generator_value)
