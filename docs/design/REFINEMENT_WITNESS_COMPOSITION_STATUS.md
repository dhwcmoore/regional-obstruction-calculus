# Status: Refinement Witness Composition

**Status: mixed, and that is the actual result.** (N0)-composability is
now **proved** (`rocq/RefinementWitnessComposition.v`, `coqchk`-clean, no
`Admitted`/`Axiom`/`sorry`). (A4) and (E0) composability remain
**probed, not proved** — two concrete composed witnesses tested against
the real code, both positive, no counterexample found and none shown
impossible. No tag, no release milestone; one real theorem plus two open
questions, not a composition theory yet.

## The question

Given two refinement witnesses, $C \to Q$ and $Q \to R$, each
individually satisfying (A1)-(A4)/(N0)/(E0), does the **composite** map
$C \to R$ -- built by matrix-multiplying the two individually-verified
pullback maps, not re-derived from scratch -- itself satisfy those same
conditions? This is explicitly not assumed anywhere else in this
project (see the "Open directions" section of
`paper/finite_obstruction_calculus_for_regional_warrant.tex`), and it is
**not** the same claim as `rocq/CommonSubdivisionAgreement.v`, which
compares two witnesses sharing a common target, not one witness composed
with another.

## What is now known

### N0-composability: proved, not just probable

Machine-checked in `rocq/RefinementWitnessComposition.v`: given three
complexes' worth of vertex/edge cochain types and coboundary maps, and
two witnesses' worth of pullbacks each satisfying (N0), the theorem
`N0_composes` proves the composite pullbacks satisfy (N0) too. The proof
needs no linear algebra or matrix type at all — (N0) is an equality of
two composed *functions*, and the composite case is the same equality
one level up, closed by two `rewrite`s using associativity of function
composition. This is strictly more general than the matrix-level
argument below (which is the special case where every type involved is
`Q^n` and every map is `mat_vec` applied to a matrix): the theorem holds
for *any* pullback/coboundary maps between *any* types, linear or not.

### The matrix-level version of the same argument

If both individual steps satisfy (N0) -- $\delta'^0 \rho_0^{*} =
\rho_1^{*} \delta^0$ -- the composite provably satisfies (N0) too,
**by associativity of matrix multiplication alone**:

```text
delta''^0 . (rho0_QR . rho0_CQ)
    = (delta''^0 . rho0_QR) . rho0_CQ         [associativity]
    = (rho_QR . delta'^0) . rho0_CQ            [N0 at step 2]
    = rho_QR . (delta'^0 . rho0_CQ)            [associativity]
    = rho_QR . (rho_CQ . delta^0)              [N0 at step 1]
    = (rho_QR . rho_CQ) . delta^0              [associativity]
```

This needs no empirical support -- it is a one-line algebraic identity.
`refinement_witness_composition_probe.verify_n0_composability_is_
associativity()` checks the underlying associativity identity itself
against 20 random rational matrix triples, as a sanity check of
`mat_mat`'s own correctness, not as evidence for the argument (which
needs none). Machine-checked, abstractly, in
`rocq/RefinementWitnessComposition.v` (see above).

**Caveat, stated precisely:** this shows N0 composes *when both steps
individually satisfy it*. It does not show the converse (that a
composite failing N0 always traces to an individual step failing N0),
though the one case tested where a step fails N0 (bridge insertion, see
below) did propagate to the composite failing N0 too.

### A4 and E0 composability: tested, not proved

Two concrete composed witnesses were run through the real
`coboundary_0`/`pullback_matrix`/`vertex_pullback_matrix`/
`nullspace_over_Q`/`in_span_over_Q` machinery (`refinement_witness_
composition_probe.py`):

**Scenario 1 -- two genuine subdivisions.** Step 1: `SUBDIVIDE_U1`
(already verified elsewhere). Step 2: a second subdivision splitting the
already-refined complex's own `U2` vertex, constructed the same way
`SUBDIVIDE_U2` splits `COARSE`'s `U2`. Result:

```text
step1: admissible=True   descent_safe=True   E0=True
step2: admissible=True   descent_safe=True
composite: admissible=True  N0=True  descent_safe=True  E0=True  verdict_safe=True
```

The composite is fully verdict-safe here.

**Scenario 2 -- subdivision composed with bridge insertion.** Step 2 is
a bridge inserted inside the already-refined complex, analogous to
`INSERT_BRIDGE`'s construction -- the one operation that already fails
(N0) at a single step. Result:

```text
step2_N0: False  (expected -- mirrors INSERT_BRIDGE's own failure)
composite: admissible=True  N0=False  descent_safe=False  E0=True  verdict_safe=False
N0 failure propagated from step 2 to the composite: True
```

Admissibility (A1-A4) and E0 both still held at the composite level even
though N0 failed -- consistent with (N0) and (E0) being logically
independent at the single-witness level too (see `refinement_
checker.py`'s own module docstring).

**A caught mistake, worth recording.** The first draft of scenario 2
hand-copied `INSERT_BRIDGE`'s `declared_z_prime` vector into the
composed complex. The real code correctly rejected it: (A3) failed,
because the composed complex's edge structure is not `COARSE`'s, so that
vector is not actually a cycle there. Fixed by deriving a genuine cycle
from the composed complex's own coboundary map
(`nullspace_over_Q(transpose(delta0))`) instead of assuming a
plausible-looking vector would still work. This is exactly the
discipline the rest of this project insists on, caught here rather than
silently producing a wrong "witness."

## What is not known

- **A4 composability is untested beyond two positive examples.** Nothing
  in the algebra guarantees the composite pairing is nonzero just
  because both individual steps' pairings were nonzero -- the composite
  pairing is a different quantity (paired against the fully-composed
  pullback of the *original* coarse residue, not against either
  intermediate step's own residue). No counterexample has been found;
  none has been proved impossible. Two positive examples is a start, not
  a theorem.
- **E0 composability is likewise untested beyond two positive
  examples**, and E0's own definition (a subspace-inclusion condition on
  cycle spaces, not a simple matrix identity) gives no obvious
  associativity argument the way N0 has.
- No general theorem is stated or attempted here. This document
  deliberately stops at "probed."

## Reproducing this

```sh
python refinement_witness_composition_probe.py
coqc rocq/RefinementWitnessComposition.v
```

## Next steps

- **In progress**: reclassify (A4)/(E0) as a conjecture-or-counterexample
  search rather than a positive-example generator --
  `refinement_witness_a4_e0_counterexample_search.py`. The question is
  not "do A4 and E0 compose" but "under which additional hypotheses do
  they compose, and where do they fail without those hypotheses" --
  including whether A4 can pass while E0 fails (or vice versa) at the
  composite level, and whether both can fail while N0 still composes.
- If A4/E0 continue to survive adversarial construction attempts, that
  would be evidence (not proof) worth escalating to an actual proof
  attempt, at which point this document's status line should change
  again, and only then.
- ~~Write the N0-composability lemma into the Rocq chain~~ — done,
  `rocq/RefinementWitnessComposition.v`.
