# Cycle-Quotient Duality: Are Coboundary Preservation/Reflection Dual to Cycle Landing/Coverage?

**Status (2026-07-12): design only, nothing in this document is
committed as a repository proof.** This is the highest-risk piece of
new mathematics proposed anywhere in this research line so far — it is
the first document in the presentation-invariance programme to ask
whether genuinely new algebraic infrastructure (an annihilator
construction, a pullback-on-functionals operation, a nondegeneracy or
finite-dimensionality condition) needs to be built, rather than
assembling or reinterpreting infrastructure that already exists. That
is exactly the shape of question that produced the archived four-
condition scaffold (`PRESENTATION_INVARIANCE_SPEC.md` §0) — adjointness
and H1-surjectivity, checked only with floating point, never finished.
This document exists to scope precisely how much of the proposed D1-D5
ladder is actually free (needs nothing new), how much needs a small,
honest addition, and how much needs something this repository does not
yet have a design for — before any of it is written as tracked code.

The governing question, unchanged from how it was posed:

> In finite-dimensional rational regional complexes with nondegenerate
> pairings, are coboundary preservation and reflection precisely dual
> to cycle-space landing and cycle-space coverage, and does this
> duality make obstruction certificates complete for non-exact
> quotient classes?

The short answer, checked as far as a light feasibility prototype can
check it (§3): **partially, and the two halves split at exactly the
place finite-dimensionality actually starts to matter.** The easy
direction of D1 is a free, general fact, confirmed to compile with no
new hypothesis beyond what `PreservesCoboundaries` already needs. The
hard direction of D1, and D4 (certificate completeness) entirely, need
a condition — biorthogonality, or finite-dimensionality, or something
equivalent to either — that nothing in this repository currently
provides a Rocq-level notion of. That is not a minor gap; it is the
central open question this document's own governing question is
actually asking, restated precisely.

## 0. What already exists, checked directly, not assumed

`AdmissibleRefinementPersistence.v` (R1-R4's own abstract layer, which
`CommonSubdivisionAgreement.v` and every file built on it inherits)
formalises cycles as an **entirely opaque, unconnected** triple:

```coq
Variables C0' C1' Z1' : Type.
Variable coboundary' : C0' -> C1'.
Variable pairing' : Z1' -> C1' -> Q.
Variable cycle' : Z1' -> Prop.
```

`Z1'` is not a vector space (no `vadd`/`vscale`, no `VSpace` instance).
`pairing'` is not asserted linear in either argument. `cycle'` is a bare
predicate on `Z1'`, with no structural definition (e.g. as "the kernel
of some coboundary-like map") anywhere. There is **no transpose,
pullback-on-functionals, or annihilator operation defined in Rocq
anywhere in this repository** — `ExactnessReflection.v`'s own header
describes `rho_*` as "the pushforward on cycles (the transpose of
`rho1_star`)" entirely in prose; no such operation exists as a Rocq
term.

The Python side is fully concrete and already computes exactly the
dual picture this document proposes formalising, by name
(`refinement_checker.py`):

```python
Z1_coarse  = nullspace_over_Q(transpose(delta0_coarse))
Z1_refined = nullspace_over_Q(transpose(delta0_refined))
rho_push   = transpose(rho_star)            # rho_* : C'_1(refined) -> C_1(coarse)
pushed_cycles = [mat_vec(rho_push, z) for z in Z1_refined]
# E0 check: Z1_coarse subseteq span(pushed_cycles)
```

This is the precise, standard linear-algebra fact `Z = im(delta0)^perp`
(nullspace of the transpose is the annihilator of the column space, for
finite matrices over a field) — but it is **never checked against a
Rocq-proved duality theorem**. The abstract Rocq layer and the concrete
Python computation currently relate to each other only by informal
correspondence (the same English words in both files' comments), not by
a shared proof. Closing that gap is the actual content of this
document's governing question, restated concretely: is there a Rocq
theorem that the Python computation above is an instance of, or is the
correspondence presently only asserted in prose?

## 1. The correction that must be preserved, exactly as specified

The proposal that produced this document itself supplies the one
correction most likely to be gotten wrong, and this document adopts it
without modification: **do not state that the repository's full (N0)
equation is equivalent to the first dual inclusion.** (N0), as it
appears everywhere in this repository, is witness-bearing:

```coq
rho1star (delta0 b) = delta0' (rho0star b)
```

It supplies a specific target primitive, `rho0star b`. The strictly
weaker, image-level condition —

```coq
Definition PreservesCoboundaries (f : carrier S1 -> carrier S1')
    (B : carrier S1 -> Prop) (B' : carrier S1' -> Prop) : Prop :=
  forall b : carrier S1, B b -> B' (f b).
```

— is what (N0) implies (`N0 -> PreservesCoboundaries`, a one-line
consequence, not proved as its own lemma anywhere yet) and what the
duality theorem below should actually be stated for. Conflating the
two would silently claim more than N0 supplies: N0 gives a *chosen*
witness for every coboundary; `PreservesCoboundaries` only gives that
*some* witness exists in `B'`, without saying which. `E0`, by contrast,
already *is* exactly the preimage-level condition it would need to be
dual to nothing more — `f^{-1}(B') subseteq B` is E0's own statement,
not a weakening of it.

## 2. What needs to be defined before D1 can even be stated

Two new, small, general-purpose definitions, checked to compile (§3),
neither requiring finite-dimensionality:

```coq
Definition Annihilator (S : VSpace) (B : carrier S -> Prop)
    (phi : carrier S -> Q) : Prop :=
  forall b : carrier S, B b -> phi b == 0.

Definition Pullback (S1 S1' : VSpace) (f : carrier S1 -> carrier S1')
    (phi : carrier S1' -> Q) : carrier S1 -> Q :=
  fun c => phi (f c).
```

`Annihilator S B` picks out the linear functionals on `S` that vanish
on `B` — the cycle space `Z`, *defined* this way rather than related to
an independently-declared opaque `Z1'`. `Pullback f phi` is `rho_*` /
the "transpose," made a first-class Rocq operation on functionals
rather than a matrix-transpose fact that only exists in Python. This is
a genuine departure from how `AdmissibleRefinementPersistence.v` and
everything built on it currently represent cycles — worth stating
plainly: **this is not a reinterpretation of the existing opaque
`Z1'`/`pairing'`/`cycle'` triple, it is a different, more committed
representation**, and a real implementation would need to decide
whether to replace that triple's use in this line of files or keep both
representations and prove them compatible. This document does not
decide that; it is exactly the kind of decision that should follow
proving D1-D2 hold for the new representation, not precede it.

## 3. D1, split at exactly the place finite-dimensionality starts to matter

**D1's easy direction** — `PreservesCoboundaries(f) implies
Pullback(f)(Z') subseteq Z` — is a free, general fact. Confirmed by an
actual compiling feasibility check before being written down here:

```coq
Theorem preservation_duality_easy_direction :
  PreservesCoboundaries f B B' ->
  forall phi : carrier S1' -> Q,
    Annihilator S1' B' phi -> Annihilator S1 B (Pullback S1 S1' f phi).
Proof.
  intros Hpres phi Hann b Hb.
  unfold Pullback. apply Hann. apply Hpres. exact Hb.
Qed.
```

No `VSpace`, no `CoboundaryQuotientLaws`, no linearity of `f`, no
finite-dimensionality — genuinely just unfolding definitions. This
confirms half of D1 (`PreservesCoboundaries(f) => f_*(Z') subseteq Z`)
is essentially free once `Annihilator`/`Pullback` exist.

**D1's hard direction** — the converse, `f_*(Z') subseteq Z implies
PreservesCoboundaries(f)` — is genuinely not free, and this document
does not claim otherwise. It would require `B'` to equal the
annihilator of its own annihilator (a biorthogonality property): a
subspace that is not the full annihilator of *something* can fail this
without further conditions. In finite dimensions over a field, every
subspace *is* the annihilator of its own annihilator (the standard
double-annihilator theorem) — but `VSpace` as it exists in this
repository (`RefinementWitnessVerdictComposition.v`,
`QuotientDescentReflection.v`) has **no notion of dimension, basis
cardinality, or finiteness anywhere in the record**. `InSpan` uses an
explicit `list (carrier S)` as a spanning set for its own, narrower
purpose (span-transport under a linear map), but nothing currently
represents "this `VSpace` is finite-dimensional" as a checkable Rocq
hypothesis.

**This is the actual content of the governing question**, restated
precisely: proving D1's hard direction (and D2, its mirror for E0/
reflection, and D4 entirely) needs a finite-dimensionality notion this
repository does not yet have a design for. That is a real prerequisite,
not a detail to fill in later — building it prematurely, before D1's
easy direction and a first genuine use case exist, would be close to
repeating the archived scaffold's mistake in a new guise.

## 4. D2-D5, scoped against §3's finding

- **D2 (reflection duality, `f^{-1}(B') subseteq B iff Z subseteq
  f_*(Z')`)**: the direction `Z subseteq f_*(Z') implies f^{-1}(B')
  subseteq B` is E0's own *definition*, already proved sufficient for
  everything R18-R19 needed (`QuotientDescentReflection.v`) without
  ever invoking cycles at all. The genuinely new content D2 would add
  is the *other* direction — `f^{-1}(B') subseteq B implies Z subseteq
  f_*(Z')` — which, symmetrically to D1's hard direction, needs `B`
  (not `B'` this time) to equal the annihilator of its own annihilator.
  Same prerequisite as §3, applied to the other side.
- **D3 (`f_*(Z') = Z`, faithful refinement duality)**: a direct
  conjunction of D1 and D2's hard directions once both exist. Adds no
  new mechanism beyond them, exactly the way `N0_E0_give_faithful_
  quotient_descent` (R19b) is a conjunction of `quotient_descent` and
  `E0_iff_reflects_CobEquiv`'s already-proved halves, not new
  machinery.
- **D4 (certificate completeness, `r notin B iff exists z in Z, <z,r>
  <> 0`)**: the reverse implication (`exists z, <z,r> <> 0 => r notin
  B`) is exactly `AdmissibleRefinementPersistence.v`'s own
  `nonzero_cycle_pairing_implies_nonexact`, already proved, no new work
  needed. The forward implication (`r notin B => exists z, <z,r> <> 0`)
  is the actual separation theorem — a Hahn-Banach-shaped statement
  that, over a *finite-dimensional* vector space, reduces to exactly
  the double-annihilator fact §3 identifies as missing. **D4 needs the
  same missing prerequisite as D1's hard direction, not a different or
  smaller one** — it is not, despite reading as more self-contained (no
  refinement map, one complex only), an easier place to start.
- **D5 (verdict-certificate equivalence)**: combines D4 with R17, so it
  inherits D4's own prerequisite entirely. Also worth flagging
  precisely, per the original proposal's own careful phrasing: D5 would
  give a witness "constructively or classically... depending on the
  finite-dimensional development chosen" — a finite-dimensional
  existence proof over `Q` can very plausibly be made fully
  constructive (compute a basis, compute the complement, exhibit the
  separating functional by Gauss-Jordan elimination, exactly what
  `rational_linear_algebra.py` already does), but nothing in this
  document should be read as promising that in advance of actually
  attempting it.

## 5. What this document does not claim

- That `Annihilator`/`Pullback` (§2) have been added to any tracked
  Rocq file, or that they are the right final representation to adopt
  — only that they compile and that D1's easy direction is provable
  from them with no further hypothesis.
- That D1's hard direction, D2's hard direction, D3, D4, or D5 have
  been proved, prototyped, or even fully stated in a compiling Rocq
  file. Only D1's easy direction has been checked (§3).
- That a finite-dimensionality (or biorthogonality) notion for `VSpace`
  has been designed. This document identifies exactly where it is
  needed and why, not what it should look like — that is real,
  separate design work, likely substantial given `InSpan`'s own
  restriction to finite spanning lists is the closest existing
  precedent and was built for a narrower purpose.
- That the opaque `Z1'`/`pairing'`/`cycle'` representation
  `AdmissibleRefinementPersistence.v` and everything built on it uses
  should be replaced by the `Annihilator`-based representation this
  document proposes. Whether the two representations need to be
  reconciled, and how, is deferred.
- That any of this connects to the concrete four-cycle,
  `refinement_checker.py`'s actual `nullspace_over_Q`/`transpose`
  computation, or `veribound-fce`.
- That this is the next authorized phase. Per every prior phase in this
  research line, starting any tracked implementation from this document
  — even D1's easy direction alone — needs its own explicit go-ahead.
