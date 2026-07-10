# Reproducibility

Command-level reproduction of every checked result in this repository.
See `docs/theory/THEOREM_CONCORDANCE.md` for which result each command
exercises and exactly what it does and does not prove; this file is
deliberately just commands and expected output.

Python checks are the default reproducibility path. Rocq and OCaml
checks require external toolchains and are not assumed available in
every environment.

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

Expected: `181 passed`.

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

## Rocq (optional, requires `coqc`)

```sh
make check-rocq
```

which compiles all 18 `.v` files, in dependency order:

```sh
coqc rocq/AdmissibleRefinementPersistence.v
cd rocq
coqc AssociatorResidueRepair.v
coqc FourCycleObstruction.v
coqc RepeatedTripleSupportCandidate3b.v
coqc CandidateThreeBDistinctSupportClassification.v
coqc CochainNaturalityDescent.v
coqc CommonSubdivisionAgreement.v
coqc ExactnessReflection.v
coqc FirstOrderClassifierCertificate.v
coqc RefinementWitnessComposition.v
coqc RefinementWitnessVerdictComposition.v
coqc RefinementWitnessSequentialComposition.v
coqc RefinementWitnessParallelComposition.v
coqc CoupledParallelCompatibility.v
coqc ConflictResolutionTrilemma.v
coqc ConflictResolutionLowerBound.v
coqc ConflictDiagnosticCompleteness.v
coqc TypedDiagnosticCalculus.v
```

All 18 `.v` files contain no `Admitted`, `Axiom`, or `sorry` — grep them
yourself to check; nothing here depends on taking this file's word for
it. `coqchk` confirms zero axioms across the full 18-file dependency
closure. (Until the `v0.12-disjoint-parallel-classification` checkpoint,
four of these files -- `CochainNaturalityDescent.v`,
`CommonSubdivisionAgreement.v`, `ExactnessReflection.v`,
`FirstOrderClassifierCertificate.v` -- were valid and already claimed as
verified in `STATUS.md` §1, but not actually wired into the `check-rocq`
Makefile target; that gap is fixed as of this checkpoint.)

## OCaml parity (optional, requires `ocamlopt`)

```sh
make check-ocaml
```

which is:

```sh
cd ocaml
ocamlopt refinement_witnesses.ml refinement_checker.ml -o ../refinement_checker_ocaml
./refinement_checker_ocaml
```

Mirrors `refinement_checker.py`'s (A1)-(A4) computation independently, in
a self-contained OCaml exact-rational type over ordinary integers — not
(N0)/(E0), added to the Python side after this mirror was last updated.

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
