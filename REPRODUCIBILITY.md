# Reproducibility

Command-level reproduction of every checked result in this repository.
See `docs/theory/THEOREM_CONCORDANCE.md` for which result each command
exercises and exactly what it does and does not prove; this file is
deliberately just commands and expected output.

Python checks are the default reproducibility path. Rocq and OCaml
checks require external toolchains and are not assumed available in
every environment; CI (`.github/workflows/`) runs all four -- Python,
Rocq, Rocq trust (`coqchk`), and OCaml -- against the exact versions
below on every push.

## Verified toolchain versions

```text
Python  3.12
pytest  9.1.1
Coq/Rocq 8.18.0    (coqc, coqchk)
OCaml   4.14.1     (ocamlopt)
zarith  1.13       (Ubuntu apt) / 1.14 (opam) -- for check-r21-ocaml
                    and check-r21-extraction only
yojson  2.1.2 (apt package version; its META ships no version field, so
                    `ocamlfind list` itself reports "n/a") / 3.0.0 (opam)
                    -- for check-r21-ocaml and check-r21-extraction only
sha     1.15.4     -- for check-r21-ocaml and check-r21-extraction only
```

`make check-all` reproduces every check below, in this order, stopping
at the first failure: `check-r21-ocaml`, `check-r21-extraction`,
`check-python` (which now includes the R21 cross-language agreement,
canonical-digest-vector, and extracted-generator suites), `check-rocq`,
`check-rocq-trust`, `check-ocaml`, `check-assembly-parity`,
`check-contribution-parity`.

## Pinned container

`Dockerfile` builds an image with exactly the versions above --
Coq/Rocq 8.18.0 and OCaml 4.14.1 from Ubuntu 24.04 LTS's own apt
archive (not opam), Python 3.12 -- and runs `make check-all` by
default:

```sh
docker build -t regional-obstruction-calculus .
docker run --rm regional-obstruction-calculus
```

The image fails its own build loudly if the apt archive ever serves a
different `coqc`/`ocamlopt` version than the ones pinned here -- see
the Dockerfile's own version-check step. This is the recommended path
for an evaluator who wants to reproduce the Rocq/`coqchk`/OCaml stages
without installing or configuring a toolchain by hand; the commands
below remain the direct, no-container path.

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make check-python
```

`make check-python` runs the core computed results in order, then the
full pytest suite:

```sh
python residue_classifier.py examples/four_cycle.json
python refinement_checker.py
python run_associator_obstruction.py examples/four_cycle_associator.json
python -m pytest -q
```

Expected: `212 passed`.

## Individual checks

```sh
python residue_classifier.py examples/four_cycle.json
python refinement_checker.py
python run_associator_obstruction.py examples/four_cycle_associator.json --json out.json
python first_order_certificate_checker.py out.json
python -m pytest -q
```

## Realisability diagnostics (optional; also covered by pytest)

```sh
python realisability_diagnostic.py
python coupled_realisability_diagnostic.py
python boolean_crossing_diagnostic.py
python lattice_ie_diagnostic.py
python candidate_discipline_diagnostic.py
python repeated_triple_support_diagnostic.py
```

Each prints its own rank/quotient/verdict numbers; see
`docs/diagnostics/REALISABILITY_DIAGNOSTICS.md` and RESULTS.md R6-R9 for
what each result means.

## Rocq (optional, requires `coqc`, `coqchk`)

Three separate, composable targets -- each independently runnable, each
one a real check rather than a formality:

```sh
make check-rocq-inventory   # rocq/*.v matches the Makefile's declared build chain exactly, in both directions
make check-rocq-scan        # fast preliminary text scan for Admitted/Axiom/Parameter outside comments -- not a substitute for the next two
make check-rocq             # compiles all 28 .v files from a clean state, in dependency order (runs the inventory and scan checks first)
make check-rocq-trust       # runs coqchk over the complete declared module list (runs check-rocq first)
```

`check-rocq` removes any stale `.vo`/`.vok`/`.vos`/`.glob` files before
compiling, so a failure can never be masked by a leftover artefact from
an earlier run. In dependency order:

```sh
cd rocq
coqc AdmissibleRefinementPersistence.v
coqc AssociatorResidueRepair.v
coqc FourCycleObstruction.v
coqc RepeatedTripleSupportCandidate3b.v
coqc CandidateThreeBDistinctSupportClassification.v
coqc CochainNaturalityDescent.v
coqc CommonSubdivisionAgreement.v
coqc ExactnessReflection.v
coqc CommonSubdivisionVerdictInvariance.v
coqc FirstOrderClassifierCertificate.v
coqc RefinementWitnessComposition.v
coqc RefinementWitnessVerdictComposition.v
coqc QuotientDescentReflection.v
coqc QuotientVerdictClosure.v
coqc RefinementWitnessSequentialComposition.v
coqc RefinementWitnessParallelComposition.v
coqc CoupledParallelCompatibility.v
coqc ConflictResolutionTrilemma.v
coqc ConflictResolutionLowerBound.v
coqc ConflictDiagnosticCompleteness.v
coqc TypedDiagnosticCalculus.v
coqc PairwiseDiagnosticCertificate.v
coqc GlobalCoherenceCertificate.v
coqc PairwiseToGlobalAssembly.v
coqc AssociatorContributionCertificate.v
coqc ExactRationalRepairOrSeparator.v
coqc ExtractR21.v
```

All 28 `.v` files contain no `Admitted`, `Axiom`, or `sorry` outside a
comment -- `make check-rocq-scan` checks this itself (comments stripped
first, so a doc comment that merely *mentions* the word `Axiom` is not
a false positive); grep them yourself to check independently, nothing
here depends on taking this file's word for it. (`ExtractR21.v` has no
theorem of its own -- it is the extraction entry point, see
`docs/design/R21_EXTRACTION_TCB.md` -- so this claim is vacuous for that
one file specifically, not a proof-content claim about it.)

`make check-rocq-trust` then runs `coqchk`, Rocq's own independent,
from-scratch proof checker (a separate program from `coqc`), over the
complete 28-module dependency closure:

```sh
cd rocq && coqchk -Q . "" \
  AdmissibleRefinementPersistence AssociatorResidueRepair FourCycleObstruction \
  RepeatedTripleSupportCandidate3b CandidateThreeBDistinctSupportClassification \
  CochainNaturalityDescent CommonSubdivisionAgreement ExactnessReflection \
  CommonSubdivisionVerdictInvariance \
  FirstOrderClassifierCertificate RefinementWitnessComposition \
  RefinementWitnessVerdictComposition QuotientDescentReflection \
  QuotientVerdictClosure \
  RefinementWitnessSequentialComposition \
  RefinementWitnessParallelComposition CoupledParallelCompatibility \
  ConflictResolutionTrilemma ConflictResolutionLowerBound ConflictDiagnosticCompleteness \
  TypedDiagnosticCalculus PairwiseDiagnosticCertificate GlobalCoherenceCertificate \
  PairwiseToGlobalAssembly AssociatorContributionCertificate \
  ExactRationalRepairOrSeparator ExtractR21
```

Expected: `Modules were successfully checked`, with no `Axioms:` section
in the output. This is the check that actually backs the "zero axioms"
claim -- stated precisely: **the project has introduced no unproved
assumption (no `Admitted` proof, no extra `Axiom` or `Parameter`) into
the theorem chain, beyond Rocq's own kernel and standard library.**
This is not a claim that Rocq's own logical foundation is itself free
of foundational assumptions -- every proof assistant has some, by
design; that question is out of scope here and always will be. (Until
the `v0.12-disjoint-parallel-classification` checkpoint, four of these
files -- `CochainNaturalityDescent.v`, `CommonSubdivisionAgreement.v`,
`ExactnessReflection.v`, `FirstOrderClassifierCertificate.v` -- were
valid and already claimed as verified in `STATUS.md` §1, but not
actually wired into the `check-rocq` Makefile target; that gap is fixed
as of this checkpoint.)

## OCaml parity (optional, requires `ocamlopt`)

```sh
make check-ocaml
```

removes any stale `.cmi`/`.cmx`/`.o`/executable files first, then:

```sh
cd ocaml
ocamlopt refinement_witnesses.ml refinement_checker.ml -o ../refinement_checker_ocaml
./refinement_checker_ocaml
```

Mirrors `refinement_checker.py`'s (A1)-(A4) computation independently, in
a self-contained OCaml exact-rational type over ordinary integers — not
(N0)/(E0), added to the Python side after this mirror was last updated.
`refinement_checker.ml`'s own `run_self_check` compares every computed
pairing against a fixed set of expected values (`5, 5, 5, -5`) and the
program itself exits `1` on any mismatch -- `make check-ocaml` fails
whenever that self-check fails, not only when the build itself fails.

## Assembly parity (optional, requires `ocamlopt`)

```sh
make check-assembly-parity
```

Compiles and runs `ocaml/assembly_checker.ml` -- an independent OCaml
mirror of `PairwiseToGlobalAssembly.v`'s Gallina specification and
`veribound-fce`'s `src/pairwise_to_global_assembly.py`. Not Rocq
extraction (this repository has never used that mechanism); see the
file's own header for why the established hand-written-mirror pattern
above is used instead. Nine cases are hardcoded, each independently
verified against a real run of `veribound-fce`'s
`assemble_global_evidence()` at commit `f3d4b12` before being written
into this file -- covering a complete four-cycle assembly, refusal on
Incompatible evidence, and every `AssemblyUnresolved` reason. The
program's own self-check asserts its independently computed outcome
matches each of those nine already-verified values exactly and exits
`1` on any mismatch.

## R21 second checker (OCaml, optional, requires `ocamlfind` + zarith/yojson/sha)

```sh
make check-r21-ocaml
```

Compiles `roc-verify-ocaml` from `ocaml/r21_verifier.ml` -- the second,
independently written checker for R21's `repair-or-separator/v1`
certificates (see `docs/design/R21_CERTIFICATE_TCB.md`). Unlike every
other OCaml file in this repository, it needs three libraries beyond the
standard library: `zarith` (exact-rational arithmetic over GMP, so an
untrusted numerator or denominator cannot silently overflow a machine
int), `yojson` (JSON parsing), and `sha` (SHA-256, for the `input_digest`
binding). Two ways to get them, either is fine:

**Apt (matches this repository's Docker image, no opam):**

```sh
sudo apt-get install ocaml-findlib libzarith-ocaml-dev libyojson-ocaml-dev libsha-ocaml-dev
make check-r21-ocaml
```

**Opam (no root required):**

```sh
opam init --bare -a --disable-sandboxing -y   # only if opam has never been initialised
opam switch create default --packages="ocaml-system" -y
eval $(opam env)
opam install zarith yojson sha -y
make check-r21-ocaml
```

`check-r21-ocaml`'s recipe runs `eval $(opam env 2>/dev/null)` before
invoking `ocamlfind`, so either path works unmodified: with the apt path,
opam is absent and that `eval` is a silent no-op, falling through to the
system `ocamlfind` (which already sees the apt-installed packages, since
they land under `/usr/lib/ocaml`, already on its default search path);
with the opam path, the switch's own `ocamlfind` and library paths are
picked up instead.

Once built, `roc-verify-ocaml` has the same contract as `roc-verify`
(`r21_certificate_checker.py`):

```sh
python r21_certificate_emitter.py input.json --certificate cert.json   # roc-solve (either checker)
./roc-verify-ocaml input.json cert.json                                # ACCEPT/REJECT, exit 0/1
./roc-verify-ocaml --digest input.json                                 # print only "sha256:<hex>"
```

`make check-all` runs `check-r21-ocaml` before `check-python`
specifically so that `tests/test_r21_cross_language_agreement.py` and
`tests/test_r21_canonical_vectors.py` (in the pytest run `check-python`
triggers) find the binary already built and actually exercise it rather
than skipping -- a plain `make check-python` or `pytest` without this
toolchain still passes, just skipping that coverage (see those two
files' own module docstrings).

## R21 Rocq extraction (optional, requires `coqc` + the same zarith/yojson/sha as above)

```sh
make extract-r21          # regenerates ocaml/r21_extracted.ml/.mli (never committed)
make check-r21-extraction # + compiles roc-solve-extracted
```

Extracts `compute_repair_or_separator` -- the function `compute_repair_
or_separator_correct` proves sound against the original `D`, `r` -- from
`rocq/ExactRationalRepairOrSeparator.v`, via `rocq/ExtractR21.v`, using
only Coq's own official extraction realisation files (no project-defined
`Extract Constant`/`Extract Inductive` directives). `ocaml/r21_extracted_
solve.ml` is the thin adapter around it (`roc-solve-extracted`),
converting Coq's unreduced `Qmake` representation to `Zarith.Q` via one
`Q.make` call. See `docs/design/R21_EXTRACTION_TCB.md` for the full
account: exactly what was extracted, every extraction directive used,
and what trusting this pipeline does and does not require.

`ocaml/r21_extracted.ml`/`.mli` are **not committed** -- `make extract-
r21` regenerates them fresh every time, the same discipline this
repository already applies to `.vo`/`.cmi`/`.cmx`. Needs the same
`zarith`/`yojson`/`sha` packages as `check-r21-ocaml` (apt or opam, see
above) -- no additional external dependency, since the extraction
realisation files (`ExtrOcamlZBigInt`/`ExtrOcamlNatBigInt`) are part of
the Coq distribution itself.

Once built, `roc-solve-extracted` has the same contract as `roc-solve`:

```sh
./roc-solve-extracted input.json --certificate cert.json   # roc-solve, Rocq-extracted generator
./roc-verify-ocaml input.json cert.json                     # still gated by both checkers
python r21_certificate_checker.py input.json cert.json      # -- extraction does not bypass either
```

`make check-all` runs `check-r21-extraction` right after
`check-r21-ocaml` and before `check-python`, so `tests/test_r21_
extracted_generator.py` (48 tests: repairable/separator/four-cycle/
boundary/rectangular/row-swap/rational-pivot/negative/large-number/
random cases) finds `roc-solve-extracted` already built and exercises it
rather than skipping.

## Expected truth table (`refinement_checker.py`)

```text
subdivide_U1      A1-A4 true, N0 true,  E0 true, verdict_safe true
subdivide_U2      A1-A4 true, N0 true,  E0 true, verdict_safe true
subdivide_all     A1-A4 true, N0 true,  E0 true, verdict_safe true
insert_bridge     A1-A4 true, N0 false, E0 true, verdict_safe false
```

`insert_bridge` is the load-bearing row: it is admissible (a genuine
A1-A4 persistence witness) and satisfies (E0) exactness reflection, but
fails (N0) cochain-map naturality — the witness that shows (N0) and (E0)
are independent conditions, not two views of the same fact. See
`docs/theory/THEOREM_CONCORDANCE.md` and the paper's Remark 10.8.

## Expected result (`repeated_triple_support_diagnostic.py`)

```text
rank(B) = 2
rank(delta0) = 3
dim(im(B) ∩ im(delta0)) = 1
dim(quotient) = 1
verdict = genuinely_partial_nontrivial_quotient
```

The first positive linear/rational realisability witness; see RESULTS.md
R9 and `docs/diagnostics/REPEATED_TRIPLE_SUPPORT_DIAGNOSTIC.md`. It does
not prove Candidate 3b is unique, universal, or final.
