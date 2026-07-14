# R21 Extraction: What Was Extracted, What It Changes, and the Extraction Trusted Computing Base

**Status (2026-07-14): tracked and implemented** —
`rocq/ExtractR21.v`, `ocaml/r21_extracted_solve.ml`,
`tests/test_r21_extracted_generator.py`. Companion to
`docs/design/R21_CERTIFICATE_TCB.md`, which this document does not
repeat: that file covers the certificate schema and the two independent
checkers; this one covers only the new extraction step and the adapter
around it.

## What was extracted, precisely

**The Rocq definition:** `compute_repair_or_separator`
(`rocq/ExactRationalRepairOrSeparator.v`):

```coq
Definition compute_repair_or_separator (m n : nat) (D : list (list Q)) (r : list Q)
  : RawRepairOrSeparator := ...
```

Not `certified_repair_or_separator`, `decide_repair_or_separator`,
`RepairOrSeparator`, or `RatVec`/`RatMatrix` — those are proof-carrying
wrappers (dependent record types whose constructors take propositions as
fields) and shape-safety types, not the computational content itself.
`compute_repair_or_separator` returns a plain `RawRepairOrSeparator`
(`RawRepair (b : list Q) | RawSeparator (y : list Q)`), with no proof
term attached.

**The theorem proving its returned witnesses sound:**

```coq
Theorem compute_repair_or_separator_correct : forall m n D r,
  MatrixShape m n D -> VectorShape m r ->
  match compute_repair_or_separator m n D r with
  | RawRepair b => VectorShape n b /\ VecEq (mat_vec D b) r
  | RawSeparator y => VectorShape m y /\
      VecEq (mat_vec (transpose D n) y) (repeat 0 n) /\ dot y r == 1
  end.
```

This is proved against the *original* `D`, `r` (not merely the
row-reduced matrix elimination operates on — see that file's own header
for why the repair branch needed its own `SolvesAug` solution-set
argument for this reason). `Print Assumptions compute_repair_or_
separator_correct` reports "Closed under the global context" — zero
project-added axioms, per `STATUS.md` §1.

## Why this changes anything, precisely

Before this phase, the deployed generator (`r21_repair_or_separator.py`)
was a hand-written mirror of the algorithm above — correct according to
its own test suite, but not derived from the proof in any mechanical
sense. Now, `ocaml/r21_extracted.ml` (regenerated fresh by `make
extract-r21`, see below) is *the actual extracted `compute_repair_or_
separator`* — the same function `compute_repair_or_separator_correct`
proves sound, translated to OCaml by Rocq's own extraction mechanism, not
reimplemented.

This does not change what "ACCEPT" means, and it does not remove either
checker from the acceptance path — see "Do not let extraction replace
verification" below.

## The bounded extraction spike that preceded this file

Before committing to any of this, an untracked spike (`rocq/
scratch_extract_r21.v` plus a throwaway driver, never committed)
extracted `compute_repair_or_separator` exactly as it stood, with no
redesign, and the resulting `.ml` was inspected by hand:

- Grepped for `failwith`, `Obj.magic`, `assert false`, and axiom stubs:
  none found.
- `Z`/`positive`/`nat` extracted to `Big_int_Z.big_int` — confirmed, by
  a direct OCaml type-check (`let z : Z.t = (b : Big_int_Z.big_int)`),
  to be *the same type* as Zarith's own `Z.t` (Zarith ships `Big_int_Z`
  as a same-type compatibility shim), not a wrapper needing runtime
  conversion.
- `Q` extracted as a plain, unreduced two-field record — the one
  representation adapter needed, exactly as anticipated before the spike
  was run.
- Compiled and linked against Zarith successfully; ran on the repository's
  own four-cycle data and reproduced R1's exact canonical witness
  `(1/5,1/5,1/5,-1/5)`; ran on a 30-digit-numerator case and was checked
  against Python's `Fraction` independently; every resulting certificate
  was accepted by both existing checkers.

Only after this spike confirmed a clean result was the tracked pipeline
below built. The tracked `rocq/ExtractR21.v` produces byte-identical
output to the spike (confirmed directly, `diff`, no differences).

## Every extraction directive, itemised

`rocq/ExtractR21.v` adds **zero project-defined** `Extract Constant` or
`Extract Inductive` directives of its own. It uses exactly three of
Coq 8.18.0's own official, upstream-shipped realisation files:

**`ExtrOcamlBasic.v`** — standard, unremarkable mappings used by nearly
every Coq extraction: `bool`→`bool`, `option`→`option`, `unit`→`unit`,
`list`→`list`, `prod`→`( * )`, `sumbool`/`sumor`→`bool`/`option`
(erasing the proof component of a decidability result, a standard,
safe simplification), `andb`/`orb`→`(&&)`/`(||)`.

**`ExtrOcamlZBigInt.v`** — maps `positive`, `Z`, `N` to
`Big_int_Z.big_int` (i.e., Zarith's real `Z.t`, per the type-check
above), and replaces roughly thirty individual `Z`/`Pos`/`N` operations
(`Z.add`, `Z.mul`, `Z.compare`, `Z.div_eucl`, `Z.shiftl`, `Pos.compare`,
`N.div`, etc.) with direct calls to the corresponding `Big_int_Z`
function, instead of Coq's own inductively-defined (binary-representation,
markedly slower) implementations. The file's own comment discloses this
is a deliberate efficiency trade: "trying to obtain efficient certified
programs by extracting Z into big_int isn't necessarily a good idea" —
i.e., correctness of the *specification* (`Z.add` really does add) is
not separately re-proved for the replacement; it is trusted as a
correct, widely-used realisation.

**`ExtrOcamlNatBigInt.v`** — the same treatment for `nat`: maps it to
`Big_int_Z.big_int` and replaces `plus`, `mult`, `pred`, `minus`,
`Nat.compare`, `Compare_dec.leb`, `Nat.div2`, `Euclid.eucl_dev`, etc.
with direct `Big_int_Z` calls.

None of these three files were written for this repository, modified by
it, or contain any repository-specific logic — they are Coq's own
standard extraction library, shipped with every Coq 8.18.0 install and
used across the Coq ecosystem for exactly this purpose (efficient
extraction of `nat`/`Z`/`positive` to an arbitrary-precision OCaml type).
Trusting the extraction therefore means trusting these ~40 individual
realisations to correctly implement the Coq operations they replace — a
strictly smaller, and far more scrutinised, trust surface than trusting
a project-specific extraction mapping would be.

`Q` itself (`Qmake { Qnum : Z ; Qden : positive }`) has no realisation in
any of the three files above, and none is added — it extracts via Coq's
default record-extraction rule, as a plain two-field OCaml record. This
is deliberate: leaving it unmapped is what makes the one remaining
adapter step (below) necessary and visible, rather than hiding a fourth
custom directive inside this file.

## The representation adapter

`ocaml/r21_extracted_solve.ml` converts between the extracted, unreduced
`R21_extracted.q = { qnum : Big_int_Z.big_int ; qden : Big_int_Z.big_int }`
and Zarith's `Q.t` (always kept reduced to lowest terms, denominator
positive):

```ocaml
let q_of_zarith (x : Q.t) : R21_extracted.q = { qnum = Q.num x; qden = Q.den x }
let zarith_of_q (x : R21_extracted.q) : Q.t = Q.make x.qnum x.qden
```

Two calls, no arithmetic reimplemented. `nat` (dimensions) converts via
`Big_int_Z.big_int_of_int`, safe because this pipeline's own
`MAX_DIMENSION` (10,000) is far inside native `int` range. This adapter
also handles the module-naming collision extraction produces: `ocaml/
r21_extracted.ml` defines its own local `module Z` (the small subset
`ExtrOcamlZBigInt` gives realisations for) which would shadow Zarith's
real `Z` if the file were `open`ed — `r21_extracted_solve.ml` avoids this
by never opening `R21_extracted`, only referencing it qualified.

## Whether the generated OCaml is committed or regenerated

**Not committed.** `ocaml/r21_extracted.ml`/`.mli` are `.gitignore`d and
regenerated fresh by `make extract-r21` every time — the same discipline
this repository already applies to `.vo`/`.cmi`/`.cmx`: a build product
standing in for its own regeneration is never checked in. `make
check-r21-extraction` (which `make check-all` runs) always regenerates
before compiling the adapter, so a stale extracted file can never be
silently used.

## Compiler and library versions required

Same toolchain `docs/design/R21_CERTIFICATE_TCB.md`/`REPRODUCIBILITY.md`
already document for `roc-verify-ocaml` (Coq/Rocq 8.18.0, OCaml 4.14.1,
`zarith`/`yojson`/`sha` via apt or opam) — extraction adds no new
external dependency beyond what was already required to build the
second checker, since `ExtrOcamlZBigInt`/`ExtrOcamlNatBigInt` are part of
the Coq distribution itself, not a separate package.

## Do not let extraction replace verification

The pipeline remains:

```text
Rocq-proved computational function (compute_repair_or_separator)
        | extraction (rocq/ExtractR21.v, make extract-r21)
        v
extracted OCaml generator (ocaml/r21_extracted.ml, never committed)
        | thin adapter (ocaml/r21_extracted_solve.ml, roc-solve-extracted)
        v
repair-or-separator/v1 certificate
        +-------------------------+
        v                         v
Python checker              OCaml checker
        +-------------------------+
                    |
                    v
     both must independently ACCEPT (make check-all fails otherwise)
```

Both existing checkers still gate every certificate the extracted
generator produces, exactly as they gate the hand-written generator's
output. Extraction improves confidence in *generation* — that a valid
certificate is produced whenever the theorem says one exists, and that
the runtime generator corresponds to the proved algorithm — it does not
make either checker redundant, and it does not shrink the
mathematical-soundness TCB documented in `R21_CERTIFICATE_TCB.md` at all
(that TCB was already independent of the generator's correctness).

## The handwritten generator is retained, not replaced

`r21_repair_or_separator.py` is unchanged and still shipped. It now
serves as:

- a reference implementation, independent of Rocq's extraction pipeline;
- the differential-testing partner the extraction test suite's parity
  checks (`tests/test_r21_extracted_generator.py`) compare against, for
  determinate systems;
- an independent source of test cases;
- a diagnostic fallback if the Rocq/OCaml/opam-or-apt toolchain is
  unavailable (`r21_certificate_emitter.py`, `roc-solve`, needs only
  Python).

The extracted generator (`roc-solve-extracted`) is the new
*proof-derived* generator; the Python one is no longer the only
generator, but nothing here deletes or deprecates it.

## What this still does not establish

- **That the extraction mechanism itself is correct** — i.e., that
  Rocq's extraction algorithm faithfully preserves the computational
  content of Gallina terms in general. That is Rocq's own claim about
  its extraction feature, not something this repository re-proves or
  could re-prove.
- **That `ExtrOcamlZBigInt`/`ExtrOcamlNatBigInt`'s ~40 individual
  realisations are correct** — they are trusted, not verified, per the
  "efficient but uncertified" disclaimer in their own source (quoted
  above). This is a materially smaller trust surface than a
  project-specific mapping would be, but it is still a trust surface.
- **That the OCaml compiler, the `zarith`/`yojson`/`sha` libraries, and
  the operating system are correct** — same items already listed in
  `R21_CERTIFICATE_TCB.md`'s trusted computing base, unchanged by this
  phase.
- **Domain adapters, or binding to any application's reported verdict**
  — entirely out of scope here, exactly as `R21_CERTIFICATE_TCB.md`
  already states for the hand-written generator.
