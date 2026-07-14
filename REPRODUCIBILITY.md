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
```

`make check-all` reproduces every check below, in this order, stopping
at the first failure: `check-python`, `check-rocq`, `check-rocq-trust`,
`check-ocaml`, `check-assembly-parity`, `check-contribution-parity`
(the last of these was previously missing from this sentence, even
though the Makefile's own `check-all` target had always run it).

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
make check-rocq             # compiles all 25 .v files from a clean state, in dependency order (runs the inventory and scan checks first)
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
```

All 25 `.v` files contain no `Admitted`, `Axiom`, or `sorry` outside a
comment -- `make check-rocq-scan` checks this itself (comments stripped
first, so a doc comment that merely *mentions* the word `Axiom` is not
a false positive); grep them yourself to check independently, nothing
here depends on taking this file's word for it.

`make check-rocq-trust` then runs `coqchk`, Rocq's own independent,
from-scratch proof checker (a separate program from `coqc`), over the
complete 25-module dependency closure:

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
  PairwiseToGlobalAssembly AssociatorContributionCertificate
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
