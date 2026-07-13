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

**Correction record**: this document's first version defined
`Annihilator` and `Pullback` over *arbitrary* functions `carrier S ->
Q`, not linear functionals, and reported a "free, no-hypothesis" D1
easy direction on that basis. That theorem is true but is not D1 — it
transports predicate-annihilation, not cycle-space duality, and would
have been a misleading milestone if implemented under the D1 name. §2-3
below are corrected: the genuine D1 easy direction needs `f` linear,
confirmed by a second compiling check, not merely reasoned about. A
second, independent finding surfaced while fixing this: the natural
"linear functional into `Q`" formulation this repository's existing
`IsLinear S1 S2` record would suggest (instantiating `S2` at a `Q`-
valued `VSpace`) does not work at all — `QSpace : VSpace` is not
constructible from `Qplus`/`Qmult` under the current record's Leibniz
`=` laws (`Qplus_assoc`/`Qmult_assoc` in the standard library are
`Qeq`, not Leibniz, facts) — the same wrinkle that motivated
`AssociatorResidueRepair.v`'s `ceq` generalisation, resurfacing here.
Both corrections are checked, not merely argued for; see §2-3.

The governing question, unchanged from how it was posed:

> In finite-dimensional rational regional complexes with nondegenerate
> pairings, are coboundary preservation and reflection precisely dual
> to cycle-space landing and cycle-space coverage, and does this
> duality make obstruction certificates complete for non-exact
> quotient classes?

The short answer, corrected and re-checked: **partially, and the
boundary is sharper than first stated.** R17-R20 required algebraic
preservation and reflection but no representation of the dual space at
all. Cycle-quotient duality requires the repository to represent linear
functionals, subspaces, and a separation principle for the first
time — none of which is free, including D1's own easy direction, which
needs `f` linear (a real, if modest, hypothesis, not the "no hypothesis
at all" this document first claimed). D1's hard direction, D2's mirror,
and D4 (certificate completeness) entirely need a **separation
property** (§5) — stated more economically than "finite-
dimensionality," though finite-dimensionality is one way to obtain it —
that nothing in this repository currently provides a Rocq-level notion
of. That is not a minor gap; it is the central open question this
document's own governing question is actually asking, restated
precisely, and it is where §5's three-way fork begins.

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

## 2. What needs to be defined before D1 can even be stated, corrected

**What the first version got wrong**: it defined `Annihilator` over
arbitrary functions `carrier S -> Q`, with nothing requiring additivity
or scalar-compatibility, despite calling them "linear functionals" in
prose. That is why the first "easy direction" compiled with no `VSpace`,
no linearity, and no algebraic assumptions at all — it was proving a
true but different, weaker fact (§3).

**Why the obvious fix doesn't typecheck**: the natural repair is to
require `phi` to be linear via this repository's existing `IsLinear S1
S2` record, instantiating `S2` at a `Q`-valued `VSpace`. That needs
`QSpace : VSpace` to exist. It does not, checked directly:

```coq
Definition QSpace : VSpace.
Proof.
  refine (mkVSpace Q 0 Qplus Qmult _ _ _ _ _).
  - intros a b c. apply Qplus_assoc.   (* FAILS *)
  ...
```

fails with `Unable to unify ... = ...` because `Qplus_assoc` (and
`Qmult_assoc`) in the standard library are stated for `Qeq` (`==`), not
Leibniz `=` — the exact mismatch `AssociatorResidueRepair.v` already
generalised away from once (Leibniz `=` on `Q`-valued vectors is too
strict; `1#2` and `2#4` are `Qeq`-equal but not `=`-equal). `VSpace`'s
own laws (`vadd_assoc`, etc.) are stated with bare Leibniz `=`
throughout, so no VSpace instance whose carrier is `Q` under its native
operations can satisfy them without first forcing every operation
through a canonicalising normal form (`Qred`) — a real complication,
not attempted here.

**The fix that avoids the problem entirely**: do not reuse the generic
`IsLinear S1 S2` record for functionals into `Q` at all. Define
linearity of a `Q`-valued functional as its own bespoke predicate,
using `Qeq` directly where the codomain is involved (exactly the
discipline `AdmissibleRefinementPersistence.v`'s own `pairing'` already
uses `==` for):

```coq
Definition IsLinearFunctional (S : VSpace) (phi : carrier S -> Q) : Prop :=
  phi (vzero S) == 0 /\
  (forall a b : carrier S, phi (vadd S a b) == phi a + phi b) /\
  (forall (c : Q) (a : carrier S), phi (vscale S c a) == c * phi a).

Definition Annihilator (S : VSpace) (B : carrier S -> Prop)
    (phi : carrier S -> Q) : Prop :=
  forall b : carrier S, B b -> phi b == 0.

Definition Pullback (S1 S1' : VSpace) (f : carrier S1 -> carrier S1')
    (phi : carrier S1' -> Q) : carrier S1 -> Q :=
  fun c => phi (f c).
```

`Annihilator` here is unchanged in its own statement from the first
version — the correction is that D1 must range only over `phi`
satisfying `IsLinearFunctional`, not every `phi`, and this needed a
`QSpace`-free formulation of what "linear" even means for a `Q`-valued
map before it could be stated at all. `Pullback f phi` is `rho_*` / the
"transpose," still a first-class Rocq operation rather than a matrix-
transpose fact that only exists in Python — that part of the original
design was sound. This is still not a reinterpretation of the existing
opaque `Z1'`/`pairing'`/`cycle'` triple, and a real implementation would
still need to decide whether to replace or reconcile the two
representations — deferred, as before.

## 3. D1, corrected: the easy direction needs `f` linear after all

**The corrected easy direction**, confirmed by an actual compiling
check (a second one, after the first version's flawed check):

```coq
Theorem pullback_preserves_linearity :
  IsLinear S1 S1' f ->
  forall phi : carrier S1' -> Q,
    IsLinearFunctional S1' phi -> IsLinearFunctional S1 (Pullback S1 S1' f phi).

Theorem preservation_duality_easy_direction_corrected :
  PreservesCoboundaries f B B' ->
  IsLinear S1 S1' f ->
  forall phi : carrier S1' -> Q,
    IsLinearFunctional S1' phi ->
    Annihilator S1' B' phi ->
    IsLinearFunctional S1 (Pullback S1 S1' f phi)
    /\ Annihilator S1 B (Pullback S1 S1' f phi).
```

Both proved by unfolding definitions and the components of `IsLinear`/
`IsLinearFunctional` — no finite-dimensionality, no `CoboundaryQuotient
Laws`, no basis or subspace machinery — but genuinely, and unlike the
first version's claim, **`f` linear is a real, load-bearing hypothesis
here**, needed for `pullback_preserves_linearity` specifically:
`Pullback f phi` is a linear functional on `S1` only because `f` itself
distributes over `S1`'s own `vadd`/`vscale`. Without it, `phi ∘ f`
inherits no algebraic structure at all.

**What the first version's theorem actually was**, kept and renamed
rather than deleted, because it is a true statement and the distinction
between it and D1 is worth keeping visible rather than erasing:

```coq
Theorem annihilation_transport_alone_needs_no_linearity :
  PreservesCoboundaries f B B' ->
  forall phi : carrier S1' -> Q,
    Annihilator S1' B' phi -> Annihilator S1 B (Pullback S1 S1' f phi).
```

This is **predicate annihilation transport**, not linear-dual
annihilator transport — it says an arbitrary function vanishing on `B'`
pulls back to an arbitrary function vanishing on `B`, true for any `f`
whatsoever, with no algebraic content beyond `PreservesCoboundaries`
itself. It should never be cited as D1, and any future tracked file
implementing this line of work should keep the two names and the two
theorems separate, exactly as this section now does.

**D1's hard direction** — the converse, `f_*(Z') subseteq Z implies
PreservesCoboundaries(f)`, now additionally requiring `Z`/`Z'` to be
built from genuine linear functionals rather than arbitrary ones — is
still not free, and needs more than the easy direction's correction
supplies. It would require `B'` to equal the annihilator of its own
annihilator among linear functionals specifically (a biorthogonality
property restricted to the linear dual) — see §5 for the separation
property this reduces to, and for why `VSpace` as it currently exists
has no notion of dimension, basis cardinality, or finiteness that would
supply it.

## 4. D2-D5, scoped against §3's corrected finding

- **D2 (reflection duality, `f^{-1}(B') subseteq B iff Z subseteq
  f_*(Z')`)**: the direction `Z subseteq f_*(Z') implies f^{-1}(B')
  subseteq B` is E0's own *definition*, already proved sufficient for
  everything R18-R19 needed (`QuotientDescentReflection.v`) without
  ever invoking cycles at all. The genuinely new content D2 would add
  is the *other* direction — `f^{-1}(B') subseteq B implies Z subseteq
  f_*(Z')` — which, symmetrically to D1's hard direction, needs `B`
  (not `B'` this time) to equal the annihilator of its own annihilator
  among linear functionals. Same prerequisite as D1's hard direction,
  applied to the other side.
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
  is exactly the separation property §5 states directly — not a
  Hahn-Banach-shaped statement in the abstract, but the concrete
  hypothesis `SeparatesOutside B` below. **D4 needs the same missing
  prerequisite as D1's hard direction, not a different or smaller
  one** — it is not, despite reading as more self-contained (no
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

## 5. The separation property, stated once, and the three-way fork it opens

The missing prerequisite for D1's hard direction, D2's mirror, and D4 in
full can be stated more economically than "finite-dimensionality or
double-annihilator equality" (the first version's phrasing, correct but
imprecise). The actual load-bearing principle is a **separation
property**:

```coq
Definition SeparatesOutside (S : VSpace) (B : carrier S -> Prop) : Prop :=
  forall x : carrier S,
    ~ B x ->
    exists phi : carrier S -> Q,
      IsLinearFunctional S phi /\ Annihilator S B phi /\ ~ (phi x == 0).
```

Given `SeparatesOutside B`, D4's forward direction is immediate: `r
notin B` supplies exactly `phi` with `phi|_B = 0` and `phi(r) <> 0`,
which is `r`'s own separating cycle-functional. The same principle
supplies the double-annihilator step D1's and D2's hard directions need.
One principle, three places it closes a gap — worth isolating by name
for exactly that reason, rather than restating "finite-dimensionality"
three times as if it were a different fact each time.

**Three ways to obtain `SeparatesOutside`, with real, different costs**:

- **Route A — assume it.** Prove D1-D4 conditionally on `SeparatesOutside
  B` as an explicit hypothesis, supplied by the caller rather than
  derived. Smallest possible formal development; identifies the exact
  missing ingredient without claiming to derive it. The cost is that
  certificate completeness becomes conditional — the repository would
  still separately owe a proof that its own concrete finite rational
  complexes actually satisfy `SeparatesOutside`, or the whole D4 line
  remains hypothetical for every real use.
- **Route B — derive it from basis-bearing finite-dimensional
  infrastructure.** Define a finite basis, coordinate representation,
  linear independence, spanning, and dual-basis machinery general enough
  to prove `SeparatesOutside` as a theorem for any finite-dimensional
  `VSpace`. This is the general result the original governing question
  actually asked for. It is also the highest-risk route by a wide
  margin, and resembles, in shape if not in every detail, exactly the
  kind of general infrastructure-before-use-case expansion that produced
  the archived four-condition scaffold — general dual-space machinery,
  built ahead of a single theorem that needs all of it, is a real
  precedent for stalling out unfinished.
- **Route C — construct it concretely for `Q^n`.** Build a genuine
  finite-vector or matrix representation matching what
  `rational_linear_algebra.py` already computes, and construct the
  separating functional by exact Gauss-Jordan elimination, mirroring
  `nullspace_over_Q` directly. This is the route that would actually
  connect the abstract Rocq layer to the concrete Python computation
  §0 found has no shared proof today — arguably the most valuable
  outcome of this whole line of work — but it is a real finite-matrix
  Rocq development, not a small extension of `VSpace`/`CoboundaryQuotient
  Laws`, and should not be underestimated as such.

This document does not choose among the three. That choice is exactly
the next foundational fork, not a detail to settle inside this
document — it determines the shape of a real chunk of future work, not
a naming or packaging decision the way R18b/R19b's own small choices
were.

## 6. What this document does not claim

- That `IsLinearFunctional`/`Annihilator`/`Pullback` (§2) have been
  added to any tracked Rocq file, or that they are the final
  representation to adopt — only that the corrected D1 easy direction
  compiles from them with `f` linear as a genuine, checked hypothesis.
- That D1's hard direction, D2's hard direction, D3, D4, or D5 have been
  proved, prototyped, or even fully stated in a compiling Rocq file.
  Only D1's corrected easy direction, and the separate, weaker
  predicate-annihilation-transport fact, have been checked (§3).
- That `SeparatesOutside` (§5) has been proved for anything — not for an
  abstract finite-dimensional `VSpace` (Route B), not for concrete `Q^n`
  (Route C). It is stated as the named target the next phase should
  either assume, derive, or construct — not claimed to hold.
- That Route A, B, or C has been chosen. §5 states the three options and
  their real, different costs; choosing among them is exactly the next
  decision this document defers.
- That the opaque `Z1'`/`pairing'`/`cycle'` representation
  `AdmissibleRefinementPersistence.v` and everything built on it uses
  should be replaced by the `Annihilator`-based representation this
  document proposes. Whether the two representations need to be
  reconciled, and how, is deferred.
- That any of this connects to the concrete four-cycle,
  `refinement_checker.py`'s actual `nullspace_over_Q`/`transpose`
  computation, or `veribound-fce` — Route C, if chosen, is what would
  eventually make that connection real, not this document.
- That this is the next authorized phase. Per every prior phase in this
  research line, starting any tracked implementation from this
  document — even D1's corrected easy direction alone — needs its own
  explicit go-ahead.
