# Presentation Invariance: What Is Already Proved, What Is Genuinely Open

**Status (2026-07-12): design only, nothing in this document is
implemented.** This document answers one question, asked before any
`Presentation` type, morphism record, or new Rocq file is written:

> When do two finite presentations describe the same regional system,
> and under what conditions do they determine the same obstruction
> information?

That question was proposed as the repository's next mathematical
level, with a specific five-theorem ladder (repairability preservation,
obstruction reflection, common-refinement verdict invariance,
obstruction-class invariance, functoriality) and a suggested new file,
`docs/design/PRESENTATION_INVARIANCE_SPEC.md` — this document.

**The single most important finding of this document is that most of
the proposed ladder already exists**, under different names, spread
across four files that were not written with this question in mind but
answer most of it anyway. The remaining gap is smaller, and more
precisely located, than the proposal's own framing suggests. Section 1
states exactly what exists. Section 6 states exactly what does not.
Readers in a hurry should read those two sections first.

## 0. A prior attempt at exactly this, and why it was abandoned

Before checking the current code, it is worth knowing that a fuller
version of this same idea was already tried once, and failed —
`CHANGELOG.md` records it plainly:

> "Moved the old, superseded universal-refinement scaffold
> (four-condition scheme with adjointness and H1-surjectivity, three
> placeholder checks, hardcoded legacy pairing values, non-compiling
> Rocq skeleton, and four now-inactive design docs) into
> `archive/deprecated_universal_refinement_scaffold/`... Nothing in the
> current checked result depends on it."

The archived scaffold had exactly the shape the current proposal
describes: a general morphism-of-presentations record, several bundled
conditions (cochain-map naturality, chain-map naturality, pairing
adjointness, H1-surjectivity), and an intended unified invariance
theorem. It did not compile, and three of its four conditions were
never more than placeholders. The paper's own name for the abandoned
theorem — "Universal admissible-refinement persistence" — was itself
renamed to "A1-A4 admissible-refinement persistence" specifically
because the old name "risked being misread as unrestricted refinement
invariance, which is explicitly not claimed" (`CHANGELOG.md`).

What replaced the scaffold is smaller and works: two independent,
fully machine-checked, exact-rational conditions, (N0) and (E0), each
proving one precise thing about one refinement map at a time, with
every non-claim stated in the same file as the proof. That discipline —
narrow, exact, compiling, honestly bounded — is why the repository has
21 non-`Admitted` Rocq files today instead of a fifth abandoned
scaffold. This document's own recommendation (§7) follows the same
discipline: the next step should be the smallest true statement that
closes a *named* gap, not a new general framework built ahead of any
concrete instance that needs it.

## 1. What already exists, mapped against the proposed ladder

The proposal names five theorems, A through E. This section states, for
each, exactly what already exists in the repository, quoting the
primary source rather than paraphrasing, since this claim is the load-
bearing one for everything that follows.

### 1.1 The commuting square already has a name: (N0)

The proposed morphism condition

```text
rho_1 . delta^0_P = delta^0_Q . rho_0
```

is not a new definition. It is `rocq/CochainNaturalityDescent.v`'s
condition **(N0)**, stated there as:

```coq
(N0)  forall b : C0, rho1_star (delta0 b) = coboundary' (rho0_star b)
```

using this repository's `rho0_star`/`rho1_star` in place of the
proposal's `rho_0`/`rho_1`. This is the collaborator's `rho_1 . delta^0
= delta^0 . rho_0` written the other way round — the same equation.

### 1.2 Theorem A (repairability preservation) is proved, but not named as its own theorem

`CochainNaturalityDescent.v`'s header states the forward direction in
prose:

> "pushing a coarse exactness witness `b` forward along the vertex-
> level pullback `rho0_star` always lands on a refined exactness
> witness for the transferred residue."

That is exactly proposed Theorem A: `r_P in im(delta^0_P) ==>
rho_1(r_P) in im(delta^0_Q)`, given (N0). The step is used inline,
as one line inside the proof of the file's actual top-level theorem
(`rewrite Heq. apply Hnat.`), but only the **contrapositive** is
extracted as its own named lemma:

```coq
Lemma naturality_descent_nonexact :
  forall (C0 C1 C0' C1' : Type) (delta0 : C0 -> C1) (coboundary' : C0' -> C1')
         (rho0_star : C0 -> C0') (rho1_star : C1 -> C1') (r : C1),
    (forall b : C0, rho1_star (delta0 b) = coboundary' (rho0_star b)) ->  (* N0 *)
    ~ (exists b' : C0', rho1_star r = coboundary' b') ->
    ~ (exists b : C0, r = delta0 b).
```

Stating the forward direction as its own named lemma (call it
`naturality_descent_repairable`, the direct, non-contrapositive form)
would be a mechanical, few-line addition — the mathematics is already
done. **This is packaging work, not new mathematics.**

### 1.3 Theorem B (obstruction reflection) already exists, as (E0) — under a different, and not obviously equivalent, formulation

`rocq/ExactnessReflection.v`'s condition **(E0)**:

```coq
(E0)  (exists b' : C0', rho1_star r = delta0' b')
      -> exists b : C0, r = delta0 b
```

is precisely proposed Theorem B: refined-exactness of the transferred
residue implies coarse exactness of the original. But the proposal
phrases the required extra hypothesis as *"injectivity, usually, or a
left inverse"* on the induced quotient map. The file's own header
phrases the analogous condition differently — as a **surjectivity**
condition on the *pushforward* `rho_*` (the transpose of `rho1_star`,
acting on cycles rather than cochains):

```text
Z1(coarse) subseteq rho_*(Z1(refined))
```

i.e. every coarse cycle is the pushforward of some refined cycle. This
is checked by exact nullspace/subspace-membership computation
(`rational_linear_algebra.nullspace_over_Q`, `in_span_over_Q`), not
assumed.

**These two framings — injectivity of an induced map on the quotient
`C1/im(delta0)`, versus surjectivity of the pushforward on cycles — are
plausibly dual to each other by a standard linear-algebra argument (the
image of a coboundary map is the annihilator of the cycle space), but
no such equivalence is proved anywhere in this repository.** Treating
them as interchangeable without proof would be exactly the kind of
un-derived structural leap the associator-orientation scoping decision
(`AssociatorContributionCertificate.v`) was written to avoid making
silently. Section 4.3 below states this as an explicit open sub-
question rather than assuming it.

**Computed result, already on record**: (E0) holds for *all four*
declared witnesses, including the bridge witness — the one refinement
that breaks (N0). The paper's own remark on this (quoted in full in
§1.5) calls this "a genuine, if initially surprising, structural
fact," and it is the single clearest piece of evidence in the whole
repository that (N0) and (E0) are logically independent, not the same
condition read two ways.

### 1.4 Theorem C (common-refinement verdict invariance) has both halves proved separately, and the combining step is the one thing on record, by name, as not done

This is the most important finding in this document.

**Obstruction-present half** — `rocq/CommonSubdivisionAgreement.v`:

```coq
Theorem common_subdivision_certificate_agreement :
  forall ... (rho1_0star : C0_1 -> C0_12) (rho1_1star : C1_1 -> C1_12)
             (rho2_0star : C0_2 -> C0_12) (rho2_1star : C1_2 -> C1_12) ...
    (forall b, rho1_1star (delta1 b) = delta12 (rho1_0star b)) ->   (* N0, leg 1 *)
    (forall b, rho2_1star (delta2 b) = delta12 (rho2_0star b)) ->   (* N0, leg 2 *)
    cycle12 z12 -> (forall b, pairing12 z12 (delta12 b) == 0) ->
    rho1_1star r1 = rho2_1star r2 ->                                (* shared transferred residue *)
    ~ (pairing12 z12 (rho1_1star r1) == 0) ->
    ~ (exists b1, r1 = delta1 b1) /\ ~ (exists b2, r2 = delta2 b2).
```

Two coarse presentations `N1`, `N2`, sharing a common descent-safe
subdivision `N12` and a shared non-zero certificate there, are *both*
non-exact — neither presentation's obstruction is an artefact of that
presentation alone.

**Obstruction-absent half** — `rocq/ExactnessReflection.v`'s second
theorem, `common_subdivision_exactness_agreement`: the same triangle,
but where the shared transferred residue is instead *exact* in `N12`
under (E0), both `r1` and `r2` are exact in their own presentations.
This is literally the paper's own worked proof:

> "By Theorem [exactness-reflection-descent] applied to `rho_1^*`,
> `r_1 in im(delta_1^0)`. Since `rho_2^*r_2 = rho_1^*r_1 in
> im(delta_12^0)`, Theorem [exactness-reflection-descent] applied to
> `rho_2^*` gives `r_2 in im(delta_2^0)`." (`paper/
> associator_fields_ACS_revised.tex`, proof of the exactness-agreement
> theorem)

**Both halves already hold simultaneously for the three subdivision
witnesses** — this is exactly `verdict_safe` in `refinement_checker.py`
(`verdict_safe = bool(descent_safe and exactness_reflection)`, i.e.
(N0) and (E0) both hold). And the paper says, in its own words, in the
remark that is this document's single most direct predecessor:

> "For the three subdivision witnesses, both (N0) and (E0) hold
> (`verdict_safe` in the accompanying repository), so both branches'
> theorems are available for the same pair of maps; this paper does
> not, however, assemble that into a single combined verdict-
> equivalence theorem covering both directions at once, and no such
> combined theorem is claimed."
> (`paper/associator_fields_ACS_revised.tex`, Remark, "Result ladder,
> and what remains open")

That is proposed Theorem C, minus one `split` and two applications of
already-proved lemmas, sitting unassembled in a document written by
this project's own author, naming the exact gap this whole design
document was asked to identify. See §7 for the concrete milestone this
implies.

### 1.5 The paper's own remark is close to a first draft of this document

The full remark is worth reading directly rather than through this
summary — `paper/associator_fields_ACS_revised.tex`, the labeled
remark titled "Result ladder, and what remains open," immediately
after the exactness-reflection section. It states, in the author's own
words, nearly everything §1.1–§1.4 above independently re-derive from
the Rocq source: the two-branch structure, the shared-hypothesis case,
the explicit refusal to combine them, and — critically — the scope
boundary restated in §5 below:

> "Neither branch, individually or together, is full presentation
> invariance... even together they cover only descent-safe,
> subdivision-type refinements — nothing here handles topology-
> changing refinements such as the bridge witness... Reaching a genuine
> presentation-invariance theorem for topology-changing refinements
> still requires either (N0) itself for such refinements, or a
> different formulation of descent that avoids it."

This document does not supersede that remark. It is a formalization
plan for the one gap the remark names as closable within the current
scope (the combined iff for descent-safe refinements) and an honest
account of the gaps it names as *not* closable without new ideas
(topology-changing refinements).

### 1.6 Theorem D (obstruction-class invariance) does not exist

Every theorem above is stated at the level of individual residues (`r
in im(delta^0)` / `r notin im(delta^0)`), never as a statement about
the quotient `C1/im(delta^0)` or a correspondence `[r_P] <-> [r_Q]`
between quotient classes. This is genuinely new work, though it plausibly
follows quickly once Theorem C exists (§8.1).

### 1.7 Theorem E (functoriality) is the least developed of the five

`rocq/RefinementWitnessComposition.v`'s `N0_composes` proves that the
(N0) condition itself composes under literal function composition of
`rho0_star`/`rho1_star` — a necessary ingredient for functoriality, and
proved by two `rewrite`s using only associativity. But:

- No `Presentation` record type exists anywhere in Rocq or Python.
- No identity morphism, no category, no explicit functor is defined.
- The well-definedness lemma a functor would need — that (N0) implies
  `rho1_star` maps `im(delta^0)` into `im(delta'^0)`, hence descends to
  a map on the quotient — is not stated anywhere, though (like Theorem
  A) it follows in one line from (N0) alone.
- `rocq/RefinementWitnessSequentialComposition.v`'s own "what this does
  not do" section states explicitly: "does not prove composition for
  chains of arbitrary finite length" and "does not address sequential
  composition of heterogeneous transformation types."
- `rocq/RefinementWitnessParallelComposition.v` proves a machine-
  checked *counterexample* to the naive guess that (A4) composes under
  parallel (disjoint direct-sum) composition — worth remembering before
  assuming any composition property holds without checking it the same
  way.

Theorem E is real future work, not extraction-and-naming. Given §0's
lesson, it should be attempted only after a concrete second or third
instance of composed morphisms actually needs it — not built as
scaffolding in advance of a proof that needs it.

## 2. A terminological collision that must not be resolved silently

The proposal's morphism definition folds the commuting square into
"admissible": *"A morphism rho: P -> Q should induce maps rho_0, rho_1
such that the square commutes... this commuting square is the
algebraic heart of refinement soundness."*

This repository's existing vocabulary keeps two things separate that
this phrasing would merge:

- **"Admissible"** already means exactly (A1)-(A4) in
  `AdmissibleRefinementPersistence.v` — a condition entirely internal
  to the *refined* complex (closedness, cycle-hood, non-zero pairing),
  with **no commuting-square condition anywhere in that file**, by the
  file's own header, on purpose.
- **(N0)**, the commuting square, is a *separate*, additional
  condition, checked independently in `refinement_checker.py`
  (`descent_safe = admissible and N0`, i.e. `admissible` alone does not
  imply `descent_safe`).

All four declared witnesses (including the bridge) are `admissible` in
the existing (A1)-(A4) sense; only three of the four are
`descent_safe`. If "admissible refinement" in a new document silently
came to mean "(A1)-(A4) *and* (N0)," any statement using the word
"admissible" that carries over from existing files (`AdmissibleRefinementPersistence.v`'s
own theorem, in particular) would change meaning without changing its
own words. **This document reserves "admissible" for the existing
(A1)-(A4) sense throughout, and uses "descent-safe" (the repository's
own existing term) for "admissible and (N0)."** Any future formal file
should do the same, or introduce a visibly new term rather than
overload the old one.

## 3. What a "regional presentation" already is, versus what the proposal asks it to be

The proposal's `P = (V_P, E_P, C^0_P, C^1_P, delta^0_P, delta^1_P,
r_P)` is not a new object to invent from nothing — it is a restatement
of what `refinement_witnesses.py`'s `CoarseComplex` and each `Witness`
already carry, minus the record type. Checked directly against the
code:

- `V_P`, `E_P`: vertex and edge lists, already explicit fields
  (`refinement_witnesses.py`, `CoarseComplex`/`Witness`).
- `C^0_P`, `C^1_P`: represented implicitly as `Q^|V_P|` and `Q^|E_P|`
  via `rational_linear_algebra.py`'s matrix/vector types — never
  reified as their own named type.
- `delta^0_P`: `refinement_checker.py`'s `coboundary_0`, already
  generic over arbitrary vertex/edge lists (§1.7 of the investigation
  behind this document; not hard-coded to four regions).
- `delta^1_P`: exists for the base four-cycle case
  (`FourCycleObstruction.v`, `residue_classifier.py`'s cocycle check)
  but is not threaded through the refinement-witness machinery at all
  — `refinement_checker.py` never checks a `delta^1` condition on any
  refined complex.
- `r_P`: **the proposal's own open question — "you need to decide
  whether the residue is part of the presentation or produced by a
  generator" — is already answered, differently in different files.**
  `refinement_witnesses.py`'s `CoarseComplex.residue` is a stored
  field. `associator_residue.py`'s `compute_seam_residue` generates a
  residue from a `SeamAssociatorInstance`. **These are two different
  design choices already coexisting in the repository, not yet
  reconciled**, and this document does not attempt to reconcile them —
  doing so is exactly the kind of premature unification §0 warns
  against. Whichever new formal work proceeds from here should state,
  per file, which of the two it assumes, the same way
  `AssociatorContributionCertificate.v`'s own header states its
  registered-orientation assumption explicitly rather than leaving it
  implicit.

**Conclusion**: a `Presentation` record type, if built, should be built
as a thin, non-load-bearing bundling of fields that already exist
across `refinement_witnesses.py` and `refinement_checker.py` — not a
new mathematical object requiring its own justification. The Rocq side
should continue to use opaque `Type`s for `C0`/`C1` exactly as it does
now (§1.7's `AdmissibleRefinementPersistence.v` and
`CochainNaturalityDescent.v` are already fully general in this sense);
introducing a concrete `Presentation` record in Rocq before it is
needed by an actual new theorem would be exactly the scaffold-first
mistake §0 describes.

## 4. Definitions, stated precisely, cross-referenced to what exists

### 4.1 Regional presentation (informal, Python-facing)

A regional presentation is a tuple `(V, E, delta0, r)` where `V`, `E`
are finite sets, `delta0: Q^V -> Q^E` is linear (already
`refinement_checker.coboundary_0`), and `r in Q^E` is either stored or
generated (§3). `delta1` is omitted from this document's working
definition — no existing refinement-comparison theorem uses it, and
adding it now, before a theorem needs it, would repeat §0's mistake.
When a genuine `H^1` (rather than mere non-repairability) theorem is
needed later, `delta1` returns — see §8.4.

### 4.2 Admissible refinement morphism, and descent-safety (not "admissible refinement")

Reserving "admissible" as in §2, a **refinement morphism** `rho: P ->
Q` is a pair of linear maps `(rho0: Q^{V_P} -> Q^{V_Q}, rho1:
Q^{E_P} -> Q^{E_Q})`. It is:

- **admissible** (existing sense) when the *refined* residue
  `rho1(r_P)` satisfies (A1)-(A4) inside `Q` — a condition on `Q`
  alone, not on the pair `(P, Q)` jointly;
- **descent-safe** when additionally the commuting square (N0) holds:
  `rho1 . delta0_P = delta0_Q . rho0`;
- **reflecting** when additionally (E0) holds: refined exactness of
  `rho1(r_P)` in `Q` implies `r_P` was exact in `P`.

These three properties are independent axes, not a linear hierarchy —
the bridge witness is admissible and reflecting but not descent-safe,
which is exactly why it cannot be dropped from the theory as a
degenerate case.

### 4.3 Residue naturality: already true by construction, not a separate hypothesis to assume

The proposal lists `rho1(r_P) = r_Q` (or the weaker `equiv mod
im(delta0_Q)`) as a condition to impose. Checked against the code: in
every existing witness (`refinement_witnesses.py`), the refined
residue is *defined as* `rho1(r_P)` — there is no independently-
supplied `r_Q` that could disagree with it. "Residue naturality" is
therefore not an extra hypothesis in the current setup; it is true by
the way `Witness` objects are constructed. It becomes a genuine,
checkable hypothesis only once two *independently authored*
presentations `P` and `Q` (each with its own separately generated or
stored residue) are compared via a common refinement — which is
exactly the common-subdivision setting of §1.4, where
`rho1_1star r1 = rho2_1star r2` is stated as an explicit premise, not
assumed for free. Any new document or proof should keep this
distinction visible: naturality is definitional for a single coarse-
to-refined step, and a real premise for a two-presentation comparison.

### 4.4 The open sub-question from §1.3, stated as its own item

Does (E0) — `Z1(coarse) subseteq rho_*(Z1(refined))`, a surjectivity
statement about cycles — coincide with injectivity of the induced map
`C1_P/im(delta0_P) -> C1_Q/im(delta0_Q)` on quotients, as the original
proposal assumed? This is a finite-dimensional linear-algebra question
with a plausible affirmative answer (image/annihilator duality
suggests it), but it is unproven in this repository and should be
either proved or explicitly left open before any theorem statement
relies on treating the two framings as interchangeable.

## 5. The scope boundary, stated once, precisely

Every result in §1.2–§1.4 requires descent-safety — (N0) — for at
least the obstruction-present branch, and the bridge witness is a
real, machine-checked example of an admissible, reflecting refinement
that is *not* descent-safe. **Any theorem proved under this document's
plan therefore applies only to descent-safe (subdivision-type)
refinements, not to arbitrary admissible ones, and not to topology-
changing refinements such as bridge insertion.** This is not a
temporary gap to be closed later in this same effort — the paper's own
remark (quoted in full in §1.5) states that closing it requires either
extending (N0) to a different class of refinements, or "a different
formulation of descent that avoids it," and offers no candidate for
either. This document does not attempt one.

## 6. What this document does not claim

- That any new mathematics is required to state Theorem A or the
  well-definedness half of Theorem E — both are one-line consequences
  of (N0) that are simply not yet written as their own named lemmas.
- That Theorem B's (E0) and the proposal's "injectivity on the
  quotient" are the same condition — plausible, not proved (§1.3,
  §4.4).
- That Theorem C, once assembled, is full presentation invariance —
  it is verdict invariance restricted to descent-safe common
  refinements (§5), which is exactly what the paper's remark already
  calls "neither branch, individually or together... full presentation
  invariance."
- That Theorem D or E follow mechanically from Theorem C — Theorem D's
  quotient-level correspondence and Theorem E's functor are both
  genuinely unproven and should be attempted only after Theorem C is
  actually assembled and re-examined for what it does and does not
  hand you for free.
- That topology-changing refinements (bridge-type) are covered by
  anything in this plan. They are explicitly out of scope, per §5.
- That general finite covers (beyond the four-cycle and its four
  declared refinements) are addressed here. §3 confirms the Rocq side
  is already general enough to support this later; the Python side and
  every concrete instance are not, and building a general-cover
  instance is deferred, matching the collaborator's own proposed
  ordering (§8.5).
- That evidence-indexed soundness, nonlinear deformation, or any
  category-theoretic packaging beyond what Theorem C's proof literally
  requires are in scope for the milestone this document recommends
  (§7). These remain later steps, per §8.

## 7. The actual next milestone

Given §1.4, the correct first concrete step is smaller than "prove the
commuting-square preservation theorem and then isolate the exact
hypothesis for obstruction reflection" — both of those already exist,
named, proved, `coqchk`-clean, as (N0) and (E0). The real next
milestone is:

**Assemble the two existing halves into one Rocq theorem, restricted
to the case where both halves' hypotheses already hold together**
(the three subdivision witnesses, `verdict_safe`):

```coq
Theorem common_subdivision_verdict_invariance :
  forall ... (* the shared hypotheses of common_subdivision_certificate_agreement
                and common_subdivision_exactness_agreement, both legs
                descent-safe (N0) and reflecting (E0) *)
    rho1_1star r1 = rho2_1star r2 ->
    (exists b1, r1 = delta1 b1) <-> (exists b2, r2 = delta2 b2).
```

The `->` (repairable implies repairable) direction follows immediately
from `common_subdivision_exactness_agreement`. The `<-` direction
follows by symmetry of the same argument, or by applying
`common_subdivision_certificate_agreement`'s contrapositive. Given
that both underlying theorems are already proved and `coqchk`-clean,
this is genuinely close to the "prove the weaker theorem first" step
the original proposal itself asked for — it is just smaller, and
already 90% built, rather than a fresh development. It should not be
scoped as "isolate a new hypothesis" (there is none left to isolate;
both hypotheses are already named, (N0) and (E0)) but as "combine two
finished proofs under their already-established shared hypothesis
set."

**This milestone should be proposed, scoped, and explicitly authorized
as its own next phase before any Rocq file is written** — consistent
with how every phase in this project's own history has been gated, and
because this document's own finding (§1) changes what "the next
phase" actually is relative to the original proposal.

## 8. Everything after the milestone, in the proposal's own order, unchanged except where §1–§7 revise it

1. Prove `common_subdivision_verdict_invariance` (§7) — the corrected,
   smaller version of the original "prove the weaker theorem first"
   step.
2. Resolve §4.4 (whether (E0)'s surjectivity framing and quotient-
   injectivity coincide) before stating any theorem in terms of
   quotient injectivity specifically.
3. Attempt Theorem D (obstruction-class invariance, `[r_P] <-> [r_Q]`)
   as a genuinely new quotient-level statement, checking first whether
   it follows from Theorem C's residue-level statement by a direct
   argument or needs its own proof.
4. Generalize `delta1`/cocycle-condition machinery (§4.1) into the
   refinement-comparison setting only once a concrete question needs
   to distinguish non-repairability from non-trivial `H^1` under
   refinement — not before.
5. Only then generalize from the four-cycle to arbitrary finite covers
   (§3, §6) — the Rocq side is already general; the Python side and
   every worked instance are not.
6. Attempt Theorem E (functoriality) only once a second or third
   genuinely independent instance of composed presentation morphisms
   exists to test it against — per §0 and §1.7, building the category-
   theoretic packaging ahead of a concrete need is the exact mistake
   the archived scaffold made.
7. Evidence-indexed soundness (extending `no_silent_soundness_gain`-
   style warrant-preservation from the typed diagnostic calculus into
   the obstruction-comparison setting) and nonlinear deformation theory
   both remain later, independent directions, exactly as the original
   proposal ordered them — nothing in this document changes that
   ordering, only what precedes it.
