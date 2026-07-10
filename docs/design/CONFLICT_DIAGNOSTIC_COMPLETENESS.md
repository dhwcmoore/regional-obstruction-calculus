# Bounded Completeness of the Conflict Diagnostic Fragment

**Status: design document for R13, no Rocq proof yet.** This document
defines the fragment R13 will formalise and states the completeness
claim precisely before any proof is attempted, following this project's
own standing discipline (design doc before probe before proof; see
`docs/design/CONFLICT_RESOLUTION_TRILEMMA.md`'s own history). It does
not choose a conflict-resolution rule, and it does not claim anything
about diagnostic systems beyond the specific, narrow fragment defined
in §3.

## 1. Purpose

R11 (`rocq/ConflictResolutionTrilemma.v`) proved that a single value
cannot preserve two disagreeing declarations. R12
(`rocq/ConflictResolutionLowerBound.v`) proved that a non-lossy
diagnostic must carry enough information to recover the ordered pair —
an encoding recoverable via fixed projections is injective on `V x V`.
Both are strong, separate facts. Neither, on its own, answers a
question a real diagnostic system actually needs answered: **once two
declarations disagree, what are the honest things a diagnostic can
even *be*?**

R13's purpose is to turn R11 and R12 into a **closed classification**:
within a small, explicitly bounded formal fragment, every diagnostic is
one of exactly four shapes — a refusal to form a composite, a lossy
scalar summary, a non-lossy structured diagnostic, or an explicitly
unresolved case — and nothing else typechecks as a diagnostic in this
fragment at all. The interesting content is not that a closed Coq
inductive type is exhaustive (that is automatic, see §6) — it is that
these four shapes are the *right* four to name, because R11 pins down
exactly what happens inside the second shape (always lossy on
conflict) and R12 pins down exactly what happens inside the third
(injective on `V x V`, achieved exactly by pairing). The completeness
claim is worth stating formally because it rules out a specific, easy
mistake: assuming there is a fifth, "neutral" way for a scalar output
to summarise a conflict without either losing information or being one
of the four named shapes. There is not.

## 2. What R11 and R12 already prove

**R11** (`docs/design/CONFLICT_RESOLUTION_TRILEMMA.md`, `rocq/
ConflictResolutionTrilemma.v`):

```text
no_single_value_matches_both_declarations :
    forall (V : Type) (x y z : V), x <> y -> ~ (z = x /\ z = y)
```

If two declarations genuinely disagree, no single value of the same
type equals both. A structured (non-lossy) alternative always exists,
trivially, by pairing (`pair_resolver_preserves_both_claims`) — but a
structured object's own embedded scalar summary field, if it has one,
is still fully subject to the same impossibility
(`structure_does_not_exempt_the_resolved_field`).

**R12** (`docs/design/CONFLICT_RESOLUTION_TRILEMMA.md` §9, `rocq/
ConflictResolutionLowerBound.v`):

```text
NonLossy(encode, left_read, right_read) :=
    forall x y, left_read(encode(x, y)) = x /\ right_read(encode(x, y)) = y

nonlossy_encoding_injective :
    NonLossy(encode, left_read, right_read) ->
    encode(x1, y1) = encode(x2, y2) -> x1 = x2 /\ y1 = y2
```

Any encoding recoverable via fixed projections must be injective on
`V x V`; for finite `V` with `|V| = n`, this forces the encoding's
codomain to have at least `n^2` elements, so no codomain confined to
`V` itself can be non-lossy once `n > 1`.

Neither result, individually, names a closed set of diagnostic
*shapes*. R11 is about resolver functions `V x V -> V`. R12 is about
recoverability of an already-chosen encoding. Neither says: "here is
the exhaustive list of honest things a diagnostic system can hand back
when asked about a conflict."

## 3. The bounded fragment

**"Bounded" is the load-bearing word in this document's title.** R13
does not prove completeness for all possible fusion systems, all
possible policy architectures, or all possible coupled composition. It
proves completeness for one small formal fragment, chosen to match
what this project has *actually* formalised and what `veribound-fce`
has *actually* built (`NonLossyConflictDiagnostic`,
`CompositionTrace`'s `interface_conflict`/`interface_consistent`
statuses, and `ReportSource.UNRESOLVED`). The fragment is exactly:

```text
Given a shared interface with two declared values x, y : V,
a diagnostic about that interface is one of:

  1. Refuse    -- decline to form a composite at all (no scalar
                   output, no structured output; matches
                   interface_conflict / interface_disagreement_
                   blocks_glue, already proved in
                   rocq/CoupledParallelCompatibility.v).
  2. Scalar    -- emit a single value z : V (matches a NAMED_RESOLVERS
                   -style strategy: left_wins, right_wins, average,
                   sum, erase).
  3. Structured -- emit a value c : C together with fixed projections
                   left_read, right_read : C -> V (matches
                   NonLossyConflictDiagnostic / R12's encode).
  4. Unresolved -- no diagnostic has been produced at all yet (matches
                   ReportSource.UNRESOLVED; a bookkeeping state, not a
                   value).
```

This is a *closed* fragment by construction: it is formalised as a
four-constructor Coq inductive type (§4), and nothing outside those
four constructors typechecks as a member of it. This is what makes
"bounded completeness" a precise, checkable claim rather than a slogan
— see §6 for exactly what work the Coq type system does here versus
what work the surrounding theorems do.

## 4. Diagnostic constructors

```coq
Inductive ConflictDiagnostic (V C : Type) : Type :=
  | RefuseDiagnostic
  | ScalarDiagnostic (z : V)
  | StructuredDiagnostic (c : C)
  | UnresolvedDiagnostic.
```

Four constructors, matching §3 exactly:

- `RefuseDiagnostic` carries no data — the shape of `interface_conflict`
  once a composite is refused entirely.
- `ScalarDiagnostic z` carries one `V`-typed value — the shape of every
  named resolver in `conflict_resolution_trilemma_probe.py`
  (`left_wins`, `right_wins`, `average`, `sum`, `erase`).
- `StructuredDiagnostic c` carries one `C`-typed value, together with
  (separately supplied) projection functions `left_read, right_read :
  C -> V` — the shape of `pair_resolver` / `NonLossyConflictDiagnostic`.
- `UnresolvedDiagnostic` carries no data — the shape of
  `ReportSource.UNRESOLVED`: nothing has been computed yet, not a claim
  about what the eventual diagnostic would say.

A companion classification type names the four buckets a diagnostic
falls into:

```coq
Inductive DiagnosticClass : Type :=
  | no_composite
  | lossy_scalar
  | nonlossy_structured
  | unresolved_case.
```

## 5. Lossy versus non-lossy diagnostics

`RefuseDiagnostic` and `UnresolvedDiagnostic` carry no `V`-typed
payload at all, so "lossy" does not apply to them the way it applies to
the other two shapes — they are not attempts at a faithful summary,
they are the absence of one (refusal) or the absence of a verdict yet
(unresolved). The interesting distinction is entirely between the
middle two:

- **`ScalarDiagnostic z` is always lossy when `x <> y`.** This is R11,
  restated in the fragment's own vocabulary
  (`scalar_summary_not_fully_faithful_on_conflict`,
  `no_hidden_neutral_scalar_case` in §8): no `V`-typed value `z` can
  equal both `x` and `y` once they disagree, regardless of which
  specific strategy produced `z`, and regardless of whether `z`
  happens to equal one of the two declarations exactly (matching
  `veribound-fce`'s own `NonLossyConflictDiagnostic.summary_is_lossy`
  semantics: a summary equal to one branch is still lossy *as a
  summary of both*, since the value alone cannot distinguish "one side
  won" from "both sides agreed").
- **`StructuredDiagnostic c` is non-lossy exactly when its fixed
  projections recover both declarations**, for every pair — R12's
  `NonLossy` predicate, restated in the fragment's vocabulary
  (`structured_diagnostic_nonlossy` in §8). Pairing (`C := V * V`,
  `left_read := fst`, `right_read := snd`) achieves this, and — by
  R12's injectivity bound — nothing smaller than an injective encoding
  on `V x V` can.

This is why the fragment's completeness claim has real content beyond
type-level exhaustiveness: the *scalar* class is uniformly, provably
lossy on conflict (a fact about R11), and the *structured* class's
non-lossiness is exactly characterised (a fact about R12) — the four
shapes are not merely four labels, two of them are pinned to specific,
already-proved semantic properties.

## 6. Completeness claim

**Thesis**, to be stated in `RESULTS.md` and the paper:

```text
For a conflicting shared-interface declaration, every well-formed
diagnostic in the current fragment is either non-compositional, lossy,
non-lossy by product-level recovery, or explicitly unresolved. A
scalar diagnostic cannot be both complete and faithful on nontrivial
domains.
```

**What "total" and "exclusive" actually mean here, stated honestly.**
`ConflictDiagnostic V C` is a closed, four-constructor Coq inductive
type. Coq's kernel enforces that any term of this type is built from
exactly one of the four constructors — this is not something this
project's proofs establish, it is what an inductive type *is*. The
`conflict_diagnostic_classification_total` and `..._exclusive` theorems
in §8 are consequences of this, nearly immediate to prove, in the same
spirit as R11's `pair_resolver_preserves_both_claims` and R12's
`structured_pair_is_nonlossy` — the value is in *naming* the fact
explicitly and testing it, not in its proof difficulty. **The actual
mathematical work of this phase is choosing these four constructors so
that they correspond to genuinely different, exhaustive real diagnostic
behaviours, and proving that the scalar and structured classes have the
specific lossiness/faithfulness properties R11 and R12 already
established.** That is what licenses the informal sentence "there is no
fifth neutral case": not that Coq's pattern matching is exhaustive (any
inductive type has that property, by definition, whether or not it
models anything real), but that the fragment was built to match what
this project's own proved results and applied vocabulary already
distinguish, and nothing in that vocabulary falls outside the four
names.

## 7. What is not claimed

- **This does not choose a resolver.** No strategy among
  `left_wins`/`right_wins`/`average`/`sum`/`erase`/`pair` is
  recommended, endorsed, or wired into any pipeline. R13 classifies
  *shapes* of diagnostic, not which shape (or which specific strategy
  within a shape) a real system should use.
- **This does not claim `docs/design/CONFLICT_RESOLUTION_TRILEMMA.md`
  §4's seven resolver shapes are exhaustive.** That document's own §10
  already states they are not a closed taxonomy of *strategies*. R13's
  completeness claim is at a different, coarser level — the four
  *structural classes* a diagnostic can belong to, not an exhaustive
  enumeration of every function that could populate the scalar or
  structured class. `external_authority` (§4 of the trilemma doc), for
  instance, is not even a pure function of `(x, y)` and so is out of
  scope for this fragment entirely, exactly as it was out of scope
  there.
- **This does not solve general coupled parallel composition.** The
  well-definedness gate (`interface_disagreement_blocks_glue` /
  `interface_agreement_allows_glue`,
  `rocq/CoupledParallelCompatibility.v`) and the aggregate-cancellation
  findings remain exactly as proved and exactly as limited as before —
  R13 is downstream of the *conflict* case specifically, not a new
  composition-preservation result.
- **This does not handle policy authority, downstream fusion,
  restriction, or failure composition.** Those remain proposed
  vocabulary in `docs/design/CERTIFICATE_COMPOSITION_SPEC.md`, not
  backed by any theorem in this document or its Rocq file.
- **This does not wire anything into `fce_check.py`.** No witness
  engine exists in this repository or in `veribound-fce`, and R13 does
  not build one.
- **This does not claim that all real-world diagnostic systems fit the
  fragment.** `ConflictDiagnostic V C`'s four constructors were chosen
  to match this project's own proved results and `veribound-fce`'s own
  applied vocabulary — a real system with, say, a partial-recovery
  diagnostic (recovering one declaration but not the other) or a
  probabilistic summary would need its own fragment, not this one. The
  claim is scoped to the fragment as defined in §3-§4, nothing wider.
- **This does not claim the four classes are disjoint in the sense that
  no real diagnostic could ever be redescribed as more than one
  shape.** It claims the four *constructors* of `ConflictDiagnostic V
  C` are pairwise distinct as Coq terms (§8,
  `no_diagnostic_is_both_refuse_and_scalar` and its two siblings) — a
  fact about this specific formalisation, not a claim that every
  conceivable real-world diagnostic implementation must literally be a
  term of this type to be classifiable at all.

## 8. Expected Rocq targets

All to be proved in `rocq/ConflictDiagnosticCompleteness.v`, importing
`rocq/ConflictResolutionTrilemma.v` and `rocq/
ConflictResolutionLowerBound.v` rather than duplicating their content:

```text
scalar_summary_not_fully_faithful_on_conflict :
    forall (V : Type) (x y z : V), x <> y -> ~ (z = x /\ z = y).
    R11's core fact, reused directly under this fragment's own name.

structured_diagnostic_nonlossy :
    forall (V C : Type) (encode : V -> V -> C) (left_read right_read : C -> V),
      (forall x y, left_read (encode x y) = x) ->
      (forall x y, right_read (encode x y) = y) ->
      forall x y, left_read (encode x y) = x /\ right_read (encode x y) = y.
    The R12 bridge, fixing the fragment's own vocabulary for it.

nonlossy_diagnostic_injective :
    the same statement as R12's nonlossy_encoding_injective, restated
    with the two separate recovery hypotheses this fragment's vocabulary
    uses, proved by direct appeal to R12's theorem.

pair_diagnostic_is_nonlossy, pair_encoding_injective :
    thin corollaries at C := V * V, reusing structured_pair_is_nonlossy
    and nonlossy_diagnostic_injective rather than reproving them.

conflict_diagnostic_classification_total :
    forall d : ConflictDiagnostic V C, exists cls, classify d = cls.

conflict_diagnostic_classification_exclusive :
    classify d = c1 -> classify d = c2 -> c1 = c2.

diagnostic_classes_pairwise_distinct :
    the four DiagnosticClass constructors are pairwise unequal.

no_diagnostic_is_both_refuse_and_scalar,
no_diagnostic_is_both_refuse_and_structured,
no_diagnostic_is_both_scalar_and_structured :
    the ConflictDiagnostic constructors themselves are pairwise
    distinct as Coq terms -- the content behind "the four classes are
    disjoint," kept deliberately minimal (three pairwise facts, not a
    combinatorial closure over all class pairs).

no_hidden_neutral_scalar_case :
    an alias for scalar_summary_not_fully_faithful_on_conflict, given
    this second name because it is the sentence meant to be quoted on
    its own -- the same fact, flagged explicitly as the fragment's
    headline finding rather than proved twice.
```

Deliberately not attempted: a general theorem about arbitrary `V -> V
-> V` functions being classified correctly by some inferred rule (the
classification here is by *constructor*, i.e. by which shape of
diagnostic was built in the first place — the fragment does not attempt
to look inside a `ScalarDiagnostic`'s specific strategy and derive
which of R11's six named properties it has; that remains
`conflict_resolution_trilemma_probe.py`'s job, computationally, not a
Rocq theorem this file adds).

## 9. Applied consequences for VeriBound-FCE

Only after R13 is proved. The applied object already exists
(`NonLossyConflictDiagnostic`, `veribound-fce` `v0.8`); the natural next
addition is a **classifier**, not a resolver — a function from an
existing diagnostic fixture to one of `NO_COMPOSITE` /
`LOSSY_SCALAR_SUMMARY` / `NONLOSSY_STRUCTURED` / `UNRESOLVED` /
`MALFORMED`, matching this fragment's four classes plus one purely
applied-layer addition (`MALFORMED`, for schema errors — a category
this abstract Rocq fragment has no need of, since a Coq term either
typechecks as a `ConflictDiagnostic V C` or does not exist at all). Not
started; not scoped further here. See `veribound-fce`'s own `STATUS.md`
once R13 lands.
