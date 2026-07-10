# A Typed Diagnostic Calculus for the R11-R13 Fragment

**Status: design document, no Rocq proof yet.** This document turns
R11-R13's classification package into an explicit set of introduction,
elimination, and reduction rules — a small typed calculus, not a new
mathematical result. Every rule below either restates something already
proved (flagged inline) or organizes existing facts into a judgment
form R11-R13 never used (also flagged inline, in §8). Nothing here
should be read as a new theorem until it has its own Rocq proof; §11
gives the exact targets for `rocq/TypedDiagnosticCalculus.v`, not yet
attempted.

Scoped narrowly, matching every design doc before it in this line: this
calculus covers exactly the R11-R13 fragment (`Refuse` / `Scalar` /
`Structured` / `Unresolved`), nothing wider. See
`docs/theory/NO_NEUTRAL_SCALAR_FUSION.md` for the prose synthesis this
calculus formalizes the structure of, and `docs/design/
CONFLICT_DIAGNOSTIC_COMPLETENESS.md` for R13 itself, which this
document imports rather than re-derives.

## 1. Purpose

R13 answers "which of four shapes can a diagnostic be" — a
classification. It says nothing about *how* a diagnostic is built from
evidence, *what* can soundly be extracted from one once built, or *how*
an undecided case can be refined once evidence arrives. Those are
exactly the questions an introduction/elimination/reduction calculus is
for. The aim is not to prove anything R11-R13 didn't already prove — it
is to state the same content in a form that supports the two questions
a calculus is good at answering that a bare classification is not:

- **Elimination soundness**: if a diagnostic *claims* to let you
  recover a declaration, is that claim actually correct?
- **Safe refinement**: can an `Unresolved` diagnostic become a
  `Refuse`/`Scalar`/`Structured` one without ever silently becoming
  unsound in the process?

## 2. What R11-R13 already establish, in one place

(See `docs/theory/NO_NEUTRAL_SCALAR_FUSION.md` for the full account;
restated here only to the depth this calculus needs.)

- **R11**: no value `z : V` satisfies `z = x /\ z = y` when `x <> y`
  (`no_single_value_matches_both_declarations`,
  `rocq/ConflictResolutionTrilemma.v`).
- **R12**: an encoding `encode : V -> V -> C` with fixed projections
  `left_read, right_read : C -> V` recovering both declarations for
  every pair is injective on `V * V`
  (`nonlossy_encoding_injective`, `rocq/ConflictResolutionLowerBound.v`);
  pairing achieves this exactly (`structured_pair_is_nonlossy`).
- **R13**: `ConflictDiagnostic V C` is a closed four-constructor type
  (`RefuseDiagnostic`/`ScalarDiagnostic`/`StructuredDiagnostic`/
  `UnresolvedDiagnostic`, `rocq/ConflictDiagnosticCompleteness.v`),
  classified totally and exclusively into four `DiagnosticClass`
  buckets, with `ScalarDiagnostic` pinned to R11 and
  `StructuredDiagnostic` pinned to R12.

## 3. Syntax

Diagnostic terms, exactly R13's `ConflictDiagnostic V C`, given calculus
names:

```text
d ::= refuse
    | scalar z            z : V
    | structured c         c : C
    | unresolved
```

No new syntax beyond R13's own inductive type. The calculus adds
judgments *about* terms of this type, not new terms.

## 4. Judgments

Two judgment families. The first is trivial (R13 already gives it, for
free, as `d : ConflictDiagnostic V C`); the second is where the actual
content lives.

```text
d : Diagnostic
    -- well-formedness. Every term built from the four constructors is
    well-formed; this judgment carries no information beyond "d is a
    term of this type" (R13's classification, §6 of that document,
    already establishes this is total and exclusive).

SoundL(d, x)  /  SoundR(d, y)
    -- LEFT-SOUNDNESS / RIGHT-SOUNDNESS. "d, if you attempt to read a
    left/right declaration out of it, actually gives you back x / y."
    Defined per-constructor below (§6) -- for two of the four
    constructors it is never derivable at all, which is itself the
    content of two of this calculus's rules, not a gap in the
    definition.
```

`SoundL`/`SoundR` are relativized to a specific `x, y : V` because
R11/R12's own theorems are: `NonLossy` is a property of an encoding
*together with* the pair it is applied to, not a property of `C` alone.

## 5. Introduction rules

```text
STRUCTURED-INTRO
    encode : V -> V -> C
    left_read, right_read : C -> V
    forall x y, left_read (encode x y) = x
    forall x y, right_read (encode x y) = y
    ------------------------------------------------
    structured (encode x y) : Diagnostic

    Side conditions are literally R12's NonLossy(encode, left_read,
    right_read) hypothesis. Restates structured_diagnostic_nonlossy's
    own premises as an introduction rule's side conditions -- no new
    content.

SCALAR-INTRO
    resolve : V -> V -> V
    ------------------------------------------------
    scalar (resolve x y) : Diagnostic

    Unconditional -- ANY function V -> V -> V introduces a well-formed
    ScalarDiagnostic, including left_wins/right_wins/average/sum/erase
    and anything else. This is deliberate: the calculus does not forbid
    building a lossy diagnostic, it only refuses to let one CLAIM
    soundness it does not have (§6, SCALAR-CONFLICT-LOSS).

REFUSE-INTRO
    ------------------------------------------------
    refuse : Diagnostic

    Unconditional -- a system may always decline to produce a
    composite. Not the same claim as "declining is forced when x <> y";
    that stronger, proved fact is interface_disagreement_blocks_glue
    (rocq/CoupledParallelCompatibility.v) and concerns a specific glue
    construction, not this fragment's Diagnostic type directly (see
    §9's honesty note on this exact distinction).

UNRESOLVED-INTRO
    ------------------------------------------------
    unresolved : Diagnostic

    Unconditional -- the default/initial diagnostic before any
    computation happens. Matches ReportSource.UNRESOLVED's applied
    meaning: nothing has been computed yet.
```

## 6. Elimination rules

Two are ordinary positive rules (structured); two are **inadmissibility
rules** — statements that a rule of a certain shape does *not* exist,
which is exactly R11's content read as a fact about a calculus rather
than a fact about equality.

```text
STRUCTURED-LEFT-ELIM
    structured c : Diagnostic     c = encode x y
    ------------------------------------------------
    SoundL(structured c, x)

    Immediate from STRUCTURED-INTRO's own side condition
    (left_read (encode x y) = x) -- the elimination is sound by
    construction, restating structured_diagnostic_nonlossy.

STRUCTURED-RIGHT-ELIM
    symmetric, gives SoundR(structured c, y).

SCALAR-CONFLICT-LOSS   (inadmissibility)
    x <> y
    ------------------------------------------------
    there is no z : V such that SoundL(scalar z, x) AND SoundR(scalar z, y)
    both hold for the SAME z.

    This is no_single_value_matches_both_declarations (R11), restated:
    reading SoundL(scalar z, x) as "z = x" and SoundR(scalar z, y) as
    "z = y" (the only honest definition of soundness for a BARE V-typed
    value -- it has no structure to project two different things out
    of, so soundness can only mean literal equality), the claim
    "no z has both" is exactly R11's core theorem. A ScalarDiagnostic
    can be LEFT-sound (z = x, e.g. left_wins) or RIGHT-sound (z = y,
    e.g. right_wins) or NEITHER (e.g. average, erase, sum on most
    inputs) -- never both, once x <> y. Nothing prevents constructing
    scalar z via SCALAR-INTRO; what is inadmissible is CLAIMING both
    soundness judgments for the result.

REFUSE-NO-COMPOSITE   (inadmissibility)
    ------------------------------------------------
    there is no x, no y, and no elimination form producing SoundL(refuse, x)
    or SoundR(refuse, y) -- refuse has NO sound elimination of either kind,
    for any x or y whatsoever.

    Matches R13's own stated correspondence: RefuseDiagnostic is the
    shape of interface_conflict once a composite is refused entirely --
    there is no composite object for an elimination to project out of,
    full stop, not merely one that happens to be unsound.

UNRESOLVED-NO-CLAIM   (inadmissibility)
    ------------------------------------------------
    there is no x, no y, and no elimination form producing SoundL(unresolved, x)
    or SoundR(unresolved, y) either.

    Same SHAPE of rule as REFUSE-NO-COMPOSITE, but a genuinely different
    REASON, worth keeping distinct rather than collapsing the two into
    one "no elimination" rule: refuse's absence of soundness is a fact
    ABOUT THE CONFLICT (no composite CAN exist, once x <> y -- an
    impossibility). unresolved's absence of soundness is a fact about
    BOOKKEEPING (nothing has been COMPUTED yet -- an absence of
    information, not a proof that none could exist). Conflating these
    would repeat exactly the mistake transformation_diagnostics.py's
    own IllDefinedReport was built to prevent in the applied layer:
    interface_conflict and local_failure "mean structurally different
    things" despite both being failure-shaped.
```

## 7. Reduction: refining an unresolved diagnostic

The one rule in this calculus with no direct R11-R13 antecedent — see
§9.

```text
UNRESOLVED-REFINE-BY-EVIDENCE
    d : Diagnostic     d is refuse, (scalar _), or (structured _)   [not unresolved]
    ------------------------------------------------
    unresolved --> d

    An Unresolved diagnostic may be REPLACED by any other well-formed
    diagnostic for the same conflict, once that diagnostic is actually
    produced. This is the calculus's only reduction rule -- it gives
    "unresolved" a genuine operational reading (a state that changes as
    evidence arrives) rather than treating it as a fourth, permanent
    peer of refuse/scalar/structured. Reduction never targets
    unresolved itself (no d = unresolved case) and never applies to
    refuse/scalar/structured as a SOURCE (they do not further reduce --
    they are the calculus's normal forms).
```

## 8. Safety properties (the metatheorems this calculus should satisfy)

Not yet proved — this is what §11's Rocq file needs to establish for
the design to count as a genuine calculus rather than a naming
exercise.

```text
ELIMINATION SOUNDNESS
    Every SoundL/SoundR judgment derivable via STRUCTURED-LEFT-ELIM /
    STRUCTURED-RIGHT-ELIM is semantically correct (trivial given §6's
    rules are stated as direct consequences of R12's own hypotheses --
    the content is that NO OTHER rule of this calculus can derive a
    SoundL/SoundR judgment for scalar/refuse/unresolved, which is
    exactly SCALAR-CONFLICT-LOSS / REFUSE-NO-COMPOSITE /
    UNRESOLVED-NO-CLAIM's job).

PRESERVATION UNDER REDUCTION
    If unresolved : Diagnostic (for a given x, y) and
    unresolved --> d, then d : Diagnostic for that SAME x, y --
    refinement never changes which conflict is being diagnosed.
    Near-definitional given UNRESOLVED-REFINE-BY-EVIDENCE's own
    side condition, worth stating and proving explicitly anyway
    (matching this whole project's standing practice for
    near-definitional facts -- R11's pair_resolver_preserves_both_claims,
    R13's classification_total).

NO SILENT SOUNDNESS GAIN UNDER REDUCTION
    Reduction cannot manufacture a SoundL/SoundR judgment that would
    not otherwise be derivable for the target d directly -- i.e.
    refining unresolved --> scalar z under conflict is STILL subject
    to SCALAR-CONFLICT-LOSS; "it used to be unresolved" is not a
    loophole. This is the property that actually justifies calling
    UNRESOLVED-REFINE-BY-EVIDENCE "safe" in the aim stated in §1 --
    without it, refinement could be used to smuggle an unsound claim
    in under cover of "no longer unresolved."
```

## 9. What is genuinely new here versus what R11-R13 already say

Honesty check, done before any Rocq work, matching this project's
standing discipline of separating restatement from new content:

- **STRUCTURED-INTRO/-LEFT-ELIM/-RIGHT-ELIM** are R12 restated as
  inference rules. No new content.
- **SCALAR-CONFLICT-LOSS** is R11 restated as an inadmissibility rule.
  No new content, but a new READING: R11 has never before been phrased
  as "no elimination rule of this shape is derivable" — that framing
  is new, the underlying fact is not.
- **REFUSE-NO-COMPOSITE** restates R13's own stated correspondence
  between `RefuseDiagnostic` and `interface_conflict`
  (`docs/design/CONFLICT_DIAGNOSTIC_COMPLETENESS.md` §4). It does
  **not** restate `interface_disagreement_blocks_glue`
  (`rocq/CoupledParallelCompatibility.v`) directly — that theorem is
  about a specific `Key -> option Value` glue construction, a
  different (related, but not identical) object from this fragment's
  `ConflictDiagnostic V C`. Conflating the two would overclaim; this
  document does not attempt to derive REFUSE-NO-COMPOSITE from
  `CoupledParallelCompatibility.v`'s theorems, only to note the
  correspondence R13 itself already draws.
- **UNRESOLVED-NO-CLAIM** is new in the sense that R11-R13 never stated
  an elimination-inadmissibility fact for `UnresolvedDiagnostic` at
  all — it follows immediately from the constructor carrying no data
  (an even more trivial fact than R13's own "nearly definitional"
  totality theorems), but it has not been written down as its own
  named fact before this document.
- **UNRESOLVED-REFINE-BY-EVIDENCE and §8's three safety properties are
  the only genuinely new structure in this document.** R11-R13 are all
  *static* classification facts — none of them describe change over
  time, and none needed to, since none of them modeled a system that
  starts undecided and becomes decided. The reduction relation and its
  safety properties are this calculus's actual contribution: not a new
  theorem about `V`, `C`, or conflicting declarations, but a new
  *shape* of claim (an operational one) that R11-R13's vocabulary
  turns out to support cleanly. This is exactly the kind of addition
  that needs its own Rocq proof before being trusted (§11) — nothing
  above should be treated as established until then.

## 10. What is not claimed

- **This is not a general theory of typed calculi, nor a claim that
  every conceivable diagnostic system fits this shape.** It is scoped,
  like R13, to the closed four-constructor fragment already
  formalized.
- **This does not choose a resolver.** SCALAR-INTRO admits every
  `V -> V -> V` function unconditionally; SCALAR-CONFLICT-LOSS
  constrains what can be CLAIMED about the result, not which function
  is used to produce it.
- **This does not prove REFUSE-NO-COMPOSITE from
  `CoupledParallelCompatibility.v`'s glue theorems.** See §9 — the two
  are related by R13's own stated correspondence, not by a derivation
  this document performs.
- **This does not model time, concurrency, or multiple rounds of
  refinement beyond the single `unresolved --> d` step.** Whether
  `d` itself could later be replaced again (e.g. a `Scalar` diagnostic
  superseded by a `Structured` one once more information arrives) is
  not modeled — `UNRESOLVED-REFINE-BY-EVIDENCE` is a one-shot
  transition out of `unresolved` specifically, not a general revision
  calculus.
- **This does not commit `veribound-fce` to implementing an actual
  reduction/state-machine object.** `NonLossyConflictDiagnostic` and
  `conflict_diagnostic_classifier.py` remain exactly what they are —
  static schema and classifier, not a stateful diagnostic-refinement
  engine. Whether this calculus's reduction rule ever gets an applied
  counterpart is a separate, later, unstarted question.
- **Nothing in this document is proved.** It is a design document. See
  §11 for what would need to hold in Rocq before any claim here is
  trusted the way R11-R13 are.

## 11. Expected Rocq targets

For `rocq/TypedDiagnosticCalculus.v`, not yet attempted. Importing
`ConflictResolutionTrilemma.v`, `ConflictResolutionLowerBound.v`, and
`ConflictDiagnosticCompleteness.v` directly, per this project's own
established discipline of reusing rather than duplicating.

```text
sound_left, sound_right :
    Definitions of SoundL(d, x) / SoundR(d, y) as Props over
    ConflictDiagnostic V C, by cases on d's constructor -- structured
    cases defined via the encode/left_read/right_read used to build it;
    scalar cases defined as literal equality (z = x / z = y); refuse
    and unresolved cases defined as False (unconditionally
    unsatisfiable, formalizing §6's two inadmissibility rules directly
    in the definition rather than as a separate non-existence theorem).

structured_elim_sound_left, structured_elim_sound_right :
    direct restatements of structured_diagnostic_nonlossy's two halves
    under sound_left/sound_right's vocabulary.

scalar_conflict_loss :
    forall (V : Type) (x y z : V), x <> y ->
      ~ (sound_left (ScalarDiagnostic z) x /\ sound_right (ScalarDiagnostic z) y).
    Direct application of no_single_value_matches_both_declarations
    once sound_left/sound_right are unfolded to their scalar-case
    definitions (literal equality) -- expected to be a one-line proof,
    like every other near-definitional theorem in this fragment.

refuse_no_sound_elimination, unresolved_no_sound_elimination :
    forall x, ~ sound_left RefuseDiagnostic x  (and the three siblings:
    right/refuse, left/unresolved, right/unresolved). Immediate once
    sound_left/sound_right's refuse/unresolved cases are defined as
    False.

Inductive Reduces (V C : Type) : ConflictDiagnostic V C -> ConflictDiagnostic V C -> Prop :=
  | refine_by_evidence : forall d : ConflictDiagnostic V C,
      d <> UnresolvedDiagnostic -> Reduces UnresolvedDiagnostic d.
    Formalizes UNRESOLVED-REFINE-BY-EVIDENCE directly as a one-constructor
    inductive relation -- deliberately minimal, matching §10's "one-shot
    transition" scope.

reduction_preserves_no_new_soundness :
    forall (V C : Type) (d : ConflictDiagnostic V C) (x : V),
      Reduces UnresolvedDiagnostic d ->
      sound_left d x -> sound_left d x.
    (Stated this way -- the conclusion is literally the second
    hypothesis -- because "no silent soundness gain" for THIS
    calculus's single reduction rule reduces to: reduction targets are
    exactly the ordinary diagnostics already governed by §6's rules, so
    there is no separate soundness fact to prove beyond the target's
    own already-proved soundness rules. If this ends up TOO trivial to
    be worth a named theorem once attempted, that itself is a finding
    worth recording honestly in RESULTS.md rather than papering over --
    matching the same posture §6 of docs/design/
    CONFLICT_DIAGNOSTIC_COMPLETENESS.md already took toward
    "total"/"exclusive.")
```

Deliberately not attempted: a general progress theorem ("every
`unresolved` diagnostic eventually reduces") — nothing in this fragment
models *when* evidence arrives, only that *if* it does, refinement is
safe. Also not attempted: soundness/completeness of `SCALAR-INTRO`
against any specific resolver's desiderata (`conflict_resolution_
trilemma_probe.py`'s classification table already does this, at the
Python level, for named strategies — restating it as a Rocq theorem per
strategy is not this document's job).

## 12. Applied consequences

None yet, and none proposed here. If this calculus's design doc and
Rocq file both land cleanly, the natural next applied question would be
whether `conflict_diagnostic_classifier.py` (`veribound-fce`, `v0.10`)
should gain a notion of "this fixture is `UNRESOLVED` and here is the
evidence that would refine it" — but that is a future, separate,
unstarted decision, not scoped by this document.
