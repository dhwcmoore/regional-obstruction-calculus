# R21 Certificate Pipeline: What Is Proved, What Is Checked, and the Trusted Computing Base

**Status (2026-07-13): tracked and implemented** —
`r21_certificate_format.py`, `r21_repair_or_separator.py`,
`r21_certificate_emitter.py`, `r21_certificate_checker.py`,
`tests/test_r21_certificates.py`. This document records precisely what
this pipeline closes relative to R21 (`rocq/
ExactRationalRepairOrSeparator.v`) and what it deliberately still leaves
open, so neither gets overstated later.

## Why this exists

R21 proves, inside Rocq, that for any rational system `D b = r`:

```text
(exists b, D b = r)  \/  (exists y, D^T y = 0  /\  dot y r == 1)
```

and that the two outcomes are mutually exclusive
(`repair_and_separator_disjoint`). That is a complete result about the
*mathematics*. It says nothing about whether a Python or OCaml program
that claims to decide this alternative for a real input actually computes
what R21 proves exists — that gap is the second and third arrows of:

```text
domain input -> (D, r) -> verified solver -> serialised certificate ->
independent certificate verifier -> reported verdict
```

This pipeline closes the middle three arrows for the *rational-matrix*
layer specifically (not the domain-input layer — see "What remains open"
below).

## The architecture, and why it is verifier-centred, not solver-centred

The generator (`r21_repair_or_separator.py`) is **untrusted by
construction**. It is a hand-written mirror of R21's augmented-elimination
algorithm, not a Rocq extraction — this repository has never used Rocq's
`Extraction` mechanism (see `rocq/PairwiseToGlobalAssembly.v`'s header for
the same disclosure about its own OCaml mirror). If it has a bug, the
worst outcome is a certificate the checker then rejects; it can never
cause the checker to wrongly accept an unsound witness, because the
checker's soundness does not depend on the generator's correctness at
all — it only recomputes and checks the certified witness against the
caller-supplied `D`, `r`.

```text
canonical input (D, r)
        |
        v
possibly-untrusted generator (r21_repair_or_separator.py)
        |
        v
repair-or-separator/v1 certificate  (bound to (D,r) via input_digest)
        |
        v
independent checker (r21_certificate_checker.py) --- imports neither
        |                                            the generator nor
        v                                            the emitter
ACCEPT (verdict follows the certificate)  or  REJECT (no verdict)
```

## What the checker actually verifies

For a claimed repair `b`: `mat_vec(D, b) == r`, exactly, over `Fraction`.

For a claimed separator `y`: `mat_vec(transpose(D), y)` is the all-zero
vector, exactly, AND `dot(y, r) == 1`, exactly.

Both checks reuse `rational_linear_algebra.py`'s `mat_vec`/`transpose`/
`dot`/`is_zero` — the same already-audited primitives every checker in
this repository reuses (`first_order_certificate_checker.py`,
`refinement_checker.py`) rather than each reimplementing matrix
multiplication independently. The checker never calls `solve_over_Q` or
`r21_repair_or_separator.repair_or_separate`: verifying a supplied witness
is evaluation, not search, which is exactly what keeps the checker's
trusted surface smaller than the generator's.

## The trusted computing base, stated precisely

To trust a `roc-verify` ACCEPT as meaning "this `(D, r)` really has this
repair / this separator," you must trust:

1. **Python's `Fraction` arithmetic** — exact rational arithmetic, no
   floating point anywhere in this pipeline.
2. **`rational_linear_algebra.py`'s `mat_vec`, `transpose`, `dot`,
   `is_zero`** — four short, already-shared, already-exercised functions,
   not new code written for this pipeline.
3. **`r21_certificate_format.py`'s strict rational parser and canonical
   digest.** This item needs two separate claims, not one, because it sits
   in two different TCBs:
   - *Mathematical-soundness TCB:* a defect here cannot by itself bypass
     the independent mathematical checks. The digest gate and the `Db=r`
     / `D^Ty=0, y.r=1` gate are both independent preconditions for
     ACCEPT, so a digest bug can cause a false REJECT (on a genuinely
     matching problem) but not a false ACCEPT of a mathematically unsound
     witness.
   - *Provenance-binding TCB:* a defect here **can** weaken or invalidate
     the claim that a certificate is uniquely bound to the input it
     claims to certify. For example, if canonicalisation silently dropped
     a matrix entry, two distinct `(D, r)` could digest identically;
     emitter and checker would agree on that defective digest, and the
     checker would not notice the mismatch it exists to catch. The
     checker would still never accept a mathematically invalid repair or
     separator against whichever `(D, r)` it was actually called with —
     that check is untouched — but it could wrongly report that a
     certificate was specifically bound to the original encoded problem,
     when in fact it was bound to that problem *or a colliding one*. The
     digest implementation is therefore inside the provenance-binding
     TCB, though outside the mathematical-soundness TCB.
4. **The Python interpreter and `hashlib.sha256`/`json` from the standard
   library** — not audited by this repository, standard for any Python
   tool.
5. **That `roc-verify` was actually run, and its exit code actually
   checked**, by whatever system reports the final user-facing verdict.
   This pipeline provides the fail-closed check; it does not yet wire
   itself into any application's reported-verdict path — see below.

Explicitly **not** in the trusted computing base: `r21_repair_or_
separator.py` (the generator), `r21_certificate_emitter.py`, and any
future replacement generator (extracted or otherwise) — none of their
correctness is a precondition for trusting an ACCEPT.

## Hardening: fail-closed mathematical checking is not DoS resistance

Getting the two certificate equations right is necessary but not
sufficient — a checker that safely rejects every unsound witness could
still be crashed, or made to spend unbounded time or memory, by an input
crafted before either equation is ever evaluated. `r21_certificate_
format.py` and both CLIs now additionally enforce, and
`tests/test_r21_certificates.py` (§5-6) test:

- **A closed schema.** Both the `roc-input/v1` file and the
  `repair-or-separator/v1` certificate reject any field beyond the
  declared set (`validate_closed_keys`) — an extra field cannot silently
  ride along unchecked.
- **No duplicate JSON keys.** `strict_json_load` uses an
  `object_pairs_hook` that raises on a repeated key at any level, instead
  of `json`'s default last-value-wins behaviour, which would let two
  readers of the same raw bytes (e.g. a human auditing the file and this
  checker) disagree about what the certificate actually says.
- **Resource limits.** `MAX_RATIONAL_CHARS` (100,000) bounds a single
  rational literal's length; `MAX_DIMENSION` (10,000) bounds matrix/vector
  row and column counts. Both are generous relative to this repository's
  own examples and are resource limits, not soundness checks — see the
  digest discussion above for the same category distinction.
- **Shape validation at input time.** `parse_matrix` rejects a ragged `D`
  (rows of differing length); `validate_problem_shape` rejects an `r`
  whose length does not match `D`'s row count. Both close a gap where
  `rational_linear_algebra.dot`'s use of `zip` would otherwise silently
  truncate to the shorter of two mismatched-length vectors instead of
  raising, which could make a length mismatch fail silently rather than
  loudly.
- **A top-level `try`/`except` in `check_certificate`.** Even with the
  above, verification is fail-closed against any *other* unexpected
  exception: it is caught and converted to a rejection, never allowed to
  propagate as a crash a caller could mistake for "no verdict yet" rather
  than "REJECT."

None of this touches the mathematical-soundness TCB (§ above) — these are
independent, additional gates a certificate must also pass.

## What this closes, relative to the six-stage roadmap

- **Stage 1 (freeze the certificate contract):** done —
  `repair-or-separator/v1`, digest-bound.
- **Stage 3 (a tiny independent checker):** done for the Python side.
  Only one independent checker exists so far (Python); a second,
  cross-language checker (e.g. OCaml) and a cross-language agreement
  test are not yet built.
- **Stage 4 (bind certificates to inputs):** done — `input_digest` over a
  canonical serialisation of `D` and `r`.
- **Stage 5 (an end-to-end command):** done at the CLI level —
  `r21_certificate_emitter.py input.json --certificate output.json`
  (`roc-solve`) and `r21_certificate_checker.py input.json output.json`
  (`roc-verify`), tested as two separate subprocesses in
  `tests/test_r21_certificates.py`.

## What remains open

- **Stage 2 (Rocq extraction):** not attempted. The generator is still a
  hand-written mirror, not an extraction of `compute_repair_or_separator`.
  Per the explicit instruction that motivated this document, extraction
  is deferred until this interface and checker were complete — they now
  are, so extraction is the next candidate phase, not a claim made here.
- **A second, independently-implemented checker and cross-language
  agreement tests:** not built. Only one checker exists.
- **Domain adapters (Stage 6):** entirely out of scope here. Nothing in
  this pipeline says anything about whether a real sensor-fusion,
  GIS, financial, or configuration problem was correctly compiled into
  `(D, r)` in the first place. That remains a separate, per-domain
  verification task.
- **Binding to a real application's reported verdict (Stage 6's
  fail-closed discipline, applied here):** `roc-verify`'s exit code is
  authoritative for this pipeline in isolation, but no application in
  this repository yet calls it and gates its own user-facing output on
  the result. Wiring that up, so that "certificate verification failed"
  can never coexist with an application still reporting a verdict, is
  future work, not something this document claims is done.

## The honest current claim, updated

You can now say: for the rational-matrix layer specifically, a `roc-solve`
/ `roc-verify` pair exists such that the *reported* ACCEPT/REJECT depends
only on the trusted computing base listed above, not on trusting the
generator, the elimination trace, or any internal solver state. You still
cannot say that every result produced by a deployed application is
formally verified from original domain input to final reported verdict —
that needs Stage 6 (a verified domain adapter per application) and the
verdict-binding step just described, neither of which this document
claims to have done.
