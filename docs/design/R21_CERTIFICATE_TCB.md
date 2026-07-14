# R21 Certificate Pipeline: What Is Proved, What Is Checked, and the Trusted Computing Base

**Status (2026-07-14): tracked and implemented, now with a second,
independent checker** — `r21_certificate_format.py`, `r21_repair_or_
separator.py`, `r21_certificate_emitter.py`, `r21_certificate_checker.py`
(Python), `ocaml/r21_verifier.ml` (OCaml, `roc-verify-ocaml`),
`tests/test_r21_certificates.py`, `tests/test_r21_cross_language_
agreement.py`, `tests/test_r21_canonical_vectors.py`,
`tests/r21_canonical_vectors.json`. This document records precisely what
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
        +-------------------------+
        v                         v
Python checker              OCaml checker
(r21_certificate_checker.py)  (ocaml/r21_verifier.ml, roc-verify-ocaml)
imports neither the           independently written: shares only the
generator nor the emitter     published spec, not the Python code,
        |                     with the Python checker
        v                         v
     ACCEPT/REJECT             ACCEPT/REJECT
        +-------------------------+
                    |
                    v
     both must agree (make check-all fails otherwise)
```

Both checkers are independent implementations of the same specification,
not one derived from the other: `ocaml/r21_verifier.ml`'s own header
states the independence boundary precisely — it shares with the Python
side only the published schema, the canonicalisation rule, the resource
limits, and the test fixtures, and contains no translated or generated
copy of `r21_certificate_checker.py` or `r21_certificate_format.py`.

## What each checker actually verifies

For a claimed repair `b`: `Db = r`, exactly, over an exact-rational type
(Python's `Fraction`; OCaml's `Zarith.Q`).

For a claimed separator `y`: `D^Ty` is the all-zero vector, exactly, AND
`y.r == 1`, exactly.

The Python checker computes this via `rational_linear_algebra.py`'s
`mat_vec`/`transpose`/`dot`/`is_zero` — the same already-audited
primitives every Python checker in this repository reuses
(`first_order_certificate_checker.py`, `refinement_checker.py`) rather
than each reimplementing matrix multiplication independently. The OCaml
checker computes the same four operations from scratch, over `Zarith.Q`
arrays, in `ocaml/r21_verifier.ml` itself — a second, independent
implementation, not a port. Neither checker calls a solver
(`solve_over_Q` or `r21_repair_or_separator.repair_or_separate`):
verifying a supplied witness is evaluation, not search, which is exactly
what keeps each checker's trusted surface smaller than the generator's.

## The four-layer picture

The second checker changes what kind of claim is available, and it is
worth stating precisely which kind, in four layers:

1. **Mathematical specification.** The Rocq R21 theorem
   (`rational_repair_or_separator`, `repair_and_separator_disjoint`) and
   the two certificate equations it licenses (`Db = r`; `D^Ty = 0 /\
   y.r = 1`). This layer is proved, `coqchk`-clean, zero project-added
   axioms.
2. **Independent runtime checkers.** `r21_certificate_checker.py`
   (Python) and `ocaml/r21_verifier.ml` (OCaml) each separately validate
   the same two equations, in different languages, over different
   exact-arithmetic types (`Fraction` vs. `Zarith.Q`), using different
   JSON parsers (`json` vs. `Yojson.Safe`) and different SHA-256
   implementations (`hashlib` vs. the `sha` opam/apt package). Both are
   tested, individually and against each other, on the same corpus
   (`tests/test_r21_cross_language_agreement.py`). **Nuance, since the
   Rocq-extracted generator (`docs/design/R21_EXTRACTION_TCB.md`) was
   added:** its OCaml adapter (`ocaml/r21_extracted_solve.ml`) shares
   `ocaml/r21_format.ml` with this OCaml checker — schema/canonicalisation
   code, not the arithmetic check itself (see that document's own "A
   nuance the independence claim needs stated precisely" section for the
   full account). The Python checker shares no code with any OCaml file
   in this pipeline, so it remains the one checker whose independence
   from either generator is unconditional.
3. **Shared specification surface.** What the two checkers deliberately
   have in common, and the only thing they are allowed to have in
   common: the `repair-or-separator/v1` and `roc-input/v1` schema
   versions, the canonicalisation rule for `input_digest`, the resource
   limits (`MAX_RATIONAL_CHARS`, `MAX_DIMENSION`), and the test
   fixtures/vectors both are checked against
   (`tests/r21_canonical_vectors.json` and the corpus in
   `test_r21_cross_language_agreement.py`). A bug in this shared surface
   — the specification itself, not either implementation — would not be
   caught by cross-language agreement, since both checkers would
   faithfully implement the same mistake. This is why `tests/test_r21_
   canonical_vectors.py`'s vectors were generated independently of
   `canonical_input_digest` (via a from-scratch `Fraction`/`hashlib`
   script, not through the function under test) rather than treating one
   checker's output as ground truth for the other.
4. **Still-untrusted components.** Both generators
   (`r21_repair_or_separator.py`, hand-written; `roc-solve-extracted`,
   Rocq-extracted -- see `docs/design/R21_EXTRACTION_TCB.md`), any future
   domain adapter, the operating system, both language runtimes and
   their compilers (`python3`, `ocamlopt`), the extraction mechanism and
   its ~40 individual `Extract Constant`/`Extract Inductive` realisations
   (itemised in `R21_EXTRACTION_TCB.md`), and the correspondence between
   the Rocq definition and either *checker* (neither checker is a Rocq
   extraction; only the generator now has an extracted alternative). See
   "The trusted computing base, stated precisely" below for the itemised
   version, and "What remains open" for what would
   shrink this list further.

**What cross-language agreement does and does not establish.** Two
independent implementations agreeing on every case in a substantial
corpus materially reduces the risk of an implementation-specific mistake
— a sign error, a transpose/row-vs-column confusion, an overly permissive
parser, a canonicalisation slip, a mishandled edge case — surviving
undetected, because such a mistake would have to be made identically in
both implementations to go unnoticed. It does **not** prove either
checker correct in any absolute sense, and it does not, by itself,
certify the specification layer (§3 above): both checkers could still
correctly implement the same mistaken written specification, and
agreement between them would not reveal that. The Rocq certificate
theorem (§1) is what supplies the mathematical reference; the fixed
canonicalisation vectors (§3) and the two independent code paths (§2)
reduce implementation and provenance risk relative to that reference —
they do not replace it.

## The trusted computing base, stated precisely

To trust a `roc-verify`/`roc-verify-ocaml` ACCEPT as meaning "this
`(D, r)` really has this repair / this separator," you must trust:

1. **Exact-rational arithmetic** — Python's `Fraction` (Python checker)
   or `Zarith.Q`, a GMP-backed rational type (OCaml checker). No floating
   point anywhere in either pipeline.
2. **Each checker's own matrix/vector primitives** —
   `rational_linear_algebra.py`'s `mat_vec`/`transpose`/`dot`/`is_zero`
   (Python, already shared and exercised elsewhere in this repository) or
   `ocaml/r21_verifier.ml`'s own from-scratch equivalents (OCaml, new
   code written for this checker specifically, exercised only by this
   file's own test suites so far).
3. **`r21_certificate_format.py`'s strict rational parser and canonical
   digest (Python), and `ocaml/r21_verifier.ml`'s independent
   reimplementation of the same rule (OCaml).** This item needs two
   separate claims, not one, because it sits in two different TCBs:
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
     TCB, though outside the mathematical-soundness TCB. `tests/test_r21_
     canonical_vectors.py` exists specifically to give this item
     independent, frozen ground truth rather than leaving it checked only
     against itself.
4. **The language runtimes, standard/third-party libraries, and
   compilers** — the Python interpreter and `hashlib`/`json` from its
   standard library; the OCaml runtime, `ocamlopt`, and the `zarith`/
   `yojson`/`sha` libraries (see REPRODUCIBILITY.md for exact pinned
   versions). None of these are audited by this repository; all are
   widely used, independently maintained dependencies.
5. **That the checker(s) were actually run, and their exit code(s)
   actually checked**, by whatever system reports the final user-facing
   verdict. This pipeline provides the fail-closed check(s); it does not
   yet wire itself into any application's reported-verdict path — see
   below.

Explicitly **not** in the trusted computing base: `r21_repair_or_
separator.py` (the generator), `r21_certificate_emitter.py`, and any
future replacement generator (extracted or otherwise) — none of their
correctness is a precondition for trusting an ACCEPT from either checker.

## Hardening: fail-closed mathematical checking is not DoS resistance

Getting the two certificate equations right is necessary but not
sufficient — a checker that safely rejects every unsound witness could
still be crashed, or made to spend unbounded time or memory, by an input
crafted before either equation is ever evaluated. `r21_certificate_
format.py`, the Python CLIs, and `ocaml/r21_verifier.ml` (independently,
using the same limits per the shared specification surface) all enforce,
and `tests/test_r21_certificates.py` (§5-6) and `tests/test_r21_cross_
language_agreement.py` (§3, the malformed/tampered/resource-limit corpus)
test:

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
- **Stage 3 (a tiny independent checker):** done, now with two
  independent checkers (Python, OCaml), a full cross-language agreement
  corpus (`tests/test_r21_cross_language_agreement.py`, 23 cases x 3
  assertions each), and frozen canonical-digest test vectors
  (`tests/test_r21_canonical_vectors.py`) that both are checked against
  independently of each other. `make check-all` fails if either checker
  rejects a case both should accept, accepts one both should reject, or
  the two disagree with each other.
- **Stage 4 (bind certificates to inputs):** done — `input_digest` over a
  canonical serialisation of `D` and `r`.
- **Stage 5 (an end-to-end command):** done at the CLI level —
  `r21_certificate_emitter.py input.json --certificate output.json`
  (`roc-solve`) and `r21_certificate_checker.py input.json output.json`
  (`roc-verify`), tested as two separate subprocesses in
  `tests/test_r21_certificates.py`.

## What remains open

- **Stage 2 (Rocq extraction): done.** `compute_repair_or_separator` is
  now extracted from Rocq (`rocq/ExtractR21.v`, `make extract-r21`) and
  wrapped by a thin adapter (`ocaml/r21_extracted_solve.ml`,
  `roc-solve-extracted`) — see `docs/design/R21_EXTRACTION_TCB.md` for
  the full account: exactly what was extracted, every extraction
  directive used (all from Coq's own official realisation files, none
  project-defined), the one representation adapter needed, and what
  extraction does and does not establish. Confirming the prediction made
  when this stage was still open: extraction does not by itself reduce
  the acceptance TCB the way the second checker did — both existing
  checkers still gate every certificate the extracted generator
  produces, exactly as they gate the hand-written one's.
- **A third, independently-implemented checker:** not built. Two exist
  (Python, OCaml); nothing here claims two is a stopping point in
  principle, only that it is the scope this phase covered.
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

You can now say: for the rational-matrix layer specifically, either a
hand-written or a **Rocq-extracted** generator (`roc-solve` /
`roc-solve-extracted`) plus a *pair* of independent, cross-language-
agreeing checkers (`roc-verify` in Python, `roc-verify-ocaml` in OCaml)
exists such that the *reported* ACCEPT/REJECT depends only on the
trusted computing base listed above — not on trusting either generator,
the elimination trace, or any internal solver state — and agreement
between two independently written implementations has been checked
against a corpus covering hand-authored fixtures, by-construction
certificates, tampering, resource limits, and a set of frozen
canonical-digest vectors neither implementation was allowed to generate
for the other. The extracted generator additionally lets you say that
its witnesses are produced by the actual function `compute_repair_or_
separator_correct` proves sound, translated by Rocq's own extraction —
see `docs/design/R21_EXTRACTION_TCB.md` for exactly what trusting that
translation requires.

You still cannot say that this proves either checker correct, or that it
validates the specification the two checkers share (§ "The four-layer
picture" above) — both could implement the same mistake identically, and
cross-language agreement alone would not reveal it; only the Rocq theorem
(layer 1) and the frozen, independently-generated test vectors (part of
layer 3) give that layer any check at all, and neither is a substitute
for a proof that the checkers implement the theorem.

You still cannot say that every result produced by a deployed application
is formally verified from original domain input to final reported
verdict — that needs Stage 6 (a verified domain adapter per application)
and the verdict-binding step described above, neither of which this
document claims to have done.
