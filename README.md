# Regional Obstruction Calculus

Exact rational diagnostics for local-to-global coherence failure in finite regional systems.

This repository contains executable and proof-oriented artefacts for detecting when locally valid regional data fails to glue into a globally coherent object. It separates **detection**, **repair**, **refinement persistence**, and **realisability** as distinct, individually-checked questions, rather than treating "there is an obstruction" as one monolithic claim.

This repository grew out of the associator-fields paper and the `admissible-refinement-persistence` development. It is now the working repository for the broader regional obstruction calculus; see [Relation to the associator-fields paper](#relation-to-the-associator-fields-paper) below.

## What this repository does

Local compatibility does not guarantee global coherence. A finite regional system can satisfy local and pairwise boundary conditions while still carrying a non-removable global residue. This repository provides exact rational tools for:

- classifying whether a residue on a finite cover is a coherence obstruction or repairable;
- generating that residue from literal associator-field data instead of declaring it;
- checking whether an obstruction persists under refinement of the cover;
- emitting and independently checking proof-carrying certificates for classifier verdicts;
- diagnosing whether a given generator's associator residues are structurally forced or merely constructible (realisability).

Everything computational is exact-rational (Python `Fraction`, no floating point). Where a result is also formalised in Rocq, the proof scripts contain no `Admitted`, `Axiom`, or `sorry`.

## Interpretation, not formalism

The proved and computed content throughout this repository is entirely
at the level of finite cochains, δ⁰/δ¹, cocycles, and coboundaries — a
Čech-style obstruction calculus, not a higher category. It is useful to
read the surviving classes as failures of *higher coherence*: local
validity (object-level data on a single region) and pairwise
compatibility (seam-level agreement across an overlap) can both hold
while the data still fail to assemble into a globally warranted
structure. That reading motivates why the obstruction calculus matters;
it is not a formal claim proved anywhere in this repository. The
refinement-persistence results (item 10 onward) can likewise be read as
a finite, cochain-level form of coherence under change of presentation —
an obstruction that survives admissible refinement was not an artefact
of how the system happened to be described. See RESULTS.md and STATUS.md
for exactly what is proved versus interpreted.

## Central example

A four-region cyclic cover `U1-U2-U3-U4-U1`, coboundary map `delta^0`, and a residue `r = (1, 1, 1, -2)` on the induced 1-cochains. Pairing `r` against the cycle `z = (-1, -1, -1, 1)` gives `<z, r> = -5 != 0`, so `r` is not a coboundary: a genuine `H^1` obstruction, not a bookkeeping artefact. See [RESULTS.md](RESULTS.md) R1-R2 for how this residue is both declared and independently generated from associator data.

## Main results

See [RESULTS.md](RESULTS.md) for the full account. Headline items:

- **R1-R5**: the four-cycle obstruction is classified, generated from associator data, shown not repairable, shown to persist under refinement, and independently certificate-checked — all in exact rational arithmetic, with Rocq proofs for the repair-impossibility and refinement-persistence claims.
- **R6-R9**: a ladder of realisability diagnostics for what data a coupled associator generator must share to produce structurally-forced (rather than merely constructible) obstructions, ending in **R9**, the first positive linear/rational witness: a repeated-triple-support coupling with `rank(B)=2`, `dim(im(B) ∩ im δ⁰)=1`, `dim(quotient)=1` — neither too free nor collapsed — also formalised as a machine-checked Rocq theorem (`rocq/RepeatedTripleSupportCandidate3b.v`).
- **R10**: refinement-witness composition is theorem-grade for all three governing conditions — `N0_composes`, `A4_composes`, `E0_composes` (`rocq/RefinementWitnessComposition.v`, `rocq/RefinementWitnessVerdictComposition.v`) — reached only after a ~175,000-case search, with three different dependency profiles per condition, not a single "safe witnesses compose" fact.

## Repository map

See [PROJECT_MAP.md](PROJECT_MAP.md) for the full file-by-file map. Top level:

```
README.md            this file
PROJECT_MAP.md        where to start, by layer
STATUS.md             what is proved / computed / diagnostic / not claimed
RESULTS.md            the results, R1-R10
REPRODUCIBILITY.md    exact commands to reproduce every check
CHANGELOG.md
LICENSE
Makefile
requirements.txt
examples/             JSON witness data
tests/                pytest suite (124 tests)
rocq/                 Rocq proof scripts (no Admitted/Axiom/sorry)
ocaml/                OCaml parity mirror of the refinement checker
docs/                 theory, diagnostics, design, and archive notes
paper/                the associator-fields manuscript (see paper/README.md)
```

## Quick start

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make check-python
```

Expect `124 passed`. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the full command sequence, including the optional Rocq and OCaml checks.

## Verification status

| Layer | Artefact | Status |
|---|---|---|
| Exact rational classifier | `residue_classifier.py` | executable, tested |
| Associator-generated residue | `associator_residue.py`, `run_associator_obstruction.py` | executable, tested |
| Repair obstruction | `repair_solver.py` | executable, tested |
| Refinement witnesses | `refinement_checker.py` | executable, tested |
| First-order certificates | `certificate_emitter.py`, `first_order_certificate_checker.py` | executable, tested |
| Rocq abstract proofs | `rocq/*.v` | proof scripts, toolchain-dependent, no `Admitted`/`Axiom`/`sorry` |
| Realisability diagnostics (negative) | `realisability_diagnostic.py`, `coupled_realisability_diagnostic.py`, `lattice_ie_diagnostic.py`, `candidate_discipline_diagnostic.py` | executable, tested, negative/cover-inert results |
| Boolean proper-crossing witness | `boolean_crossing_diagnostic.py` | executable, tested, non-linear diagnostic witness |
| Repeated triple support | `repeated_triple_support_diagnostic.py`, `rocq/RepeatedTripleSupportCandidate3b.v` | executable + machine-checked, positive diagnostic witness |
| Full presentation invariance | none | not claimed |
| Full end-to-end verified implementation | none | not claimed |

## What is proved, what is computed, what is diagnostic

Three distinct kinds of evidence appear in this repository, and they are not interchangeable:

- **Proved** (Rocq, no `Admitted`/`Axiom`/`sorry`): abstract theorems and, where stated, their concrete instantiation over the paper's own numbers. See `rocq/*.v` and [STATUS.md](STATUS.md) §1.
- **Computed** (Python, exact rational): executable checks with a pytest regression suite. See [STATUS.md](STATUS.md) §2.
- **Diagnostic** (Python, exact rational, but not a theorem): witnesses and negative results in the realisability line — they establish that a specific candidate rule does or does not do something on a specific construction, not a general theorem about all such rules. See [STATUS.md](STATUS.md) §3.

[STATUS.md](STATUS.md) §4 states explicitly what is **not** claimed.

## Relation to the associator-fields paper

This repository originated as the companion code to *Associator Fields and Local-to-Global Failure in Finite Compositional Structures* (`paper/associator_fields_ACS_revised.tex`). The repository has since grown beyond that paper — in particular, the realisability diagnostics (R6-R9), the Candidate 3b classification, and refinement-witness composition (R10) are post-paper developments. A second manuscript, *A Finite Cohomological Obstruction Calculus for Regional Warrant* (`paper/finite_obstruction_calculus_for_regional_warrant.tex`), packages that later work into its own theorem ladder, with the Candidate 3b classification (§4) and refinement-witness composition (§5) as its actual new content. See `paper/README.md` for how the two manuscripts and the repository now relate.

The prior repository, `admissible-refinement-persistence`, is retained as historical/paper-companion material; this repository is the current, active one.

## Citation / contact

Duston Moore — Independent Researcher. See [CITATION.cff](CITATION.cff) if present, or the repository metadata on GitHub.
