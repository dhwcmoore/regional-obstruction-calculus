# No Neutral Scalar Fusion: Conflict Diagnostics and the Lower Bound for Non-Lossy Composition

**Status: synthesis note, not a new result.** Every claim below is
already proved (R11-R13, `RESULTS.md`) or already implemented
(`veribound-fce` `v0.8`-`v0.10`). This note adds no new theorem, no new
Rocq file, and no new probe — its only job is to state, in one place
and in one voice, what the three results jointly say, and to make the
single sentence that motivates all three legible without reading three
separate design documents first.

## 1. Interface conflict after coupled composition

Once two branches of a coupled parallel composition share a seam,
whether a glued composite can even be formed at all is a settled
question: agreement between the two branches' own declarations for the
shared seam is necessary and sufficient
(`interface_agreement_allows_glue`, `interface_disagreement_blocks_glue`,
`rocq/CoupledParallelCompatibility.v`, `coqchk`-clean). When the
declarations disagree, refusing to build a composite
(`interface_conflict`) is always available and always safe — the
system simply declines, and this refusal is itself proved, not merely
assumed.

But a system that wants to do more than decline — one that wants to
*produce* a value despite the disagreement, because some downstream
consumer expects one — needs something else: a resolver, or more
generally a diagnostic. This note is about what such a system can
honestly be, once it commits to producing something rather than
refusing.

## 2. Why scalar resolution is tempting

The obvious move is a scalar resolver: a function `resolve(x, y)` that
takes the two disagreeing declarations and returns one value of the
same type. This is tempting for good reasons, not naive ones — most
downstream consumers (a fusion pipeline's next stage, a policy
evaluator, a display layer) expect a single field of a known type, not
a pair or a record. `left_wins`, `right_wins`, `average`, `sum`, and
`erase` (`conflict_resolution_trilemma_probe.py`'s `NAMED_RESOLVERS`)
are all reasonable-looking answers to "just pick something." Each is a
few lines of code. None of them requires touching the consumer's
schema. The question this note's three results answer, in sequence, is
exactly what such a resolver gives up by being that convenient.

## 3. R11: scalar full fidelity is impossible

The minimal fact underneath everything else
(`no_single_value_matches_both_declarations`,
`rocq/ConflictResolutionTrilemma.v`):

```text
x != y  ->  ~ (z = x /\ z = y)
```

If two declarations genuinely disagree, no single value equals both.
Combined with two named properties — *left fidelity* (`resolve(x,y)=x`
always) and *right fidelity* (`resolve(x,y)=y` always) — this forces
`full_fidelity_forces_trivial_domain`: a resolver with both fidelities
collapses its entire value type to at most one element. The
operationally meaningful contrapositive,
`no_resolver_has_both_fidelities_on_nontrivial_domain`, is the theorem
that actually rules out "just satisfy both branches" for any scalar
resolver ever proposed for a real shared-seam interface: given any two
distinct values in the type — true of every real interface-value type
this project uses — no resolver can have both fidelities.

Checked against seven candidate resolver shapes
(`conflict_resolution_trilemma_probe.py`): none of `left_wins`,
`right_wins`, `average`, `sum`, `erase` has both fidelities; `refuse`
and `external_authority` are not even value-producing functions of
`(x, y)` alone. R11 also shows the impossibility is specifically about
*same-type* (lossy) resolution: a *structured* resolver whose codomain
is some other type carrying both declarations (`pair_resolver`, `V *
V`) always exists trivially — but a structured object's own embedded
scalar summary field, if it exposes one, is still fully subject to the
same impossibility (`structure_does_not_exempt_the_resolved_field`).
Widening the output type does not make a scalar decision, once made,
any less constrained.

## 4. R12: non-lossy diagnostics require product-level information

R11 shows a structured alternative exists; R12 asks how much structure
it actually needs. An encoding `encode : V -> V -> C` is **non-lossy**
when fixed projections `left_read, right_read : C -> V` recover both
original declarations, for every pair
(`NonLossy(encode, left_read, right_read)`,
`rocq/ConflictResolutionLowerBound.v`). The lower bound:

```text
nonlossy_encoding_injective :
    NonLossy(encode, left_read, right_read) ->
    encode(x1, y1) = encode(x2, y2) -> x1 = x2 /\ y1 = y2
```

Any non-lossy encoding must assign a genuinely distinct `C`-value to
every distinct ordered pair of declarations — it must be injective on
`V * V`. Pairing achieves this exactly, with no wasted structure
(`structured_pair_is_nonlossy`). For finite `V` with `|V| = n`, this
forces the encoding's codomain to have at least `n^2` elements
(`conflict_resolution_lower_bound_probe.py`, checked for `n = 1..6`):
no codomain confined to `V` itself (size `n`) can be non-lossy once
`n > 1`. A resolver whose *output* is structurally confined to `V`
(`left_wins`, `right_wins`, `erase` — not `average` or `sum`, whose
outputs are not confined to any finite test subset of `V`) can achieve
at best image size `n`, a factor of `n` short of the `n^2` pairs that
needed distinguishing.

R11 and R12 are the same impossibility seen from two directions: R11
says no value of the *original* type can be faithful; R12 says exactly
how much *larger* a type has to be before faithfulness becomes
possible.

## 5. R13: bounded completeness of the conflict-diagnostic fragment

R11 and R12 are both about individual encodings. Neither, on its own,
answers what a diagnostic system can honestly *be* — the exhaustive
list of shapes an honest response to a conflict can take.
`docs/design/CONFLICT_DIAGNOSTIC_COMPLETENESS.md` and
`rocq/ConflictDiagnosticCompleteness.v` close this gap with a small,
explicitly bounded fragment:

```coq
Inductive ConflictDiagnostic (V C : Type) : Type :=
  | RefuseDiagnostic
  | ScalarDiagnostic (z : V)
  | StructuredDiagnostic (c : C)
  | UnresolvedDiagnostic.
```

Classification into four classes (`no_composite` / `lossy_scalar` /
`nonlossy_structured` / `unresolved_case`) is proved total and
exclusive, and the four classes — along with the constructors
themselves — are proved pairwise distinct
(`conflict_diagnostic_classification_total`, `..._exclusive`,
`diagnostic_classes_pairwise_distinct`,
`no_diagnostic_is_both_refuse_and_scalar` and its two siblings). This
totality is, honestly, mostly a fact about Coq's closed inductive
types, not a discovery — see the design doc's §6 for the full
accounting. The genuine content is that `ScalarDiagnostic` is pinned to
R11 (`scalar_summary_not_fully_faithful_on_conflict`,
`no_hidden_neutral_scalar_case`: always lossy once `x <> y`) and
`StructuredDiagnostic` is pinned to R12
(`structured_diagnostic_nonlossy`, `nonlossy_diagnostic_injective`:
non-lossy exactly under the fixed-projection recovery condition).

**The sentence this licenses**:

> In the bounded conflict-diagnostic fragment, a system facing
> incompatible interface declarations has only four honest
> possibilities: refuse composition, emit a lossy scalar summary,
> preserve both declarations in a non-lossy structured diagnostic, or
> mark the case unresolved. There is no hidden neutral scalar
> resolution.

"Bounded" is load-bearing throughout — see §7.

## 6. Applied consequence: scalar summaries are audit claims, not neutral fusions

`veribound-fce` makes this concrete. `NonLossyConflictDiagnostic`
(`src/nonlossy_conflict_diagnostic.py`, `v0.8`) always stores
`left_declaration` and `right_declaration` as fields — it is, by
construction, always R13's `StructuredDiagnostic` shape, regardless of
whether an optional `scalar_summary` is attached. Its
`summary_is_lossy` property is true whenever a scalar summary is
present during an actual conflict, **even one that happens to equal one
of the two declarations exactly** — because the summary value alone
cannot be told apart, after the fact, from a case where both branches
actually agreed on that value.

This is the practical payoff of R11-R13 together: a scalar field
attached to a conflict record is not a neutral compression of the
disagreement. It is a claim about which side a resolver favoured (or
what combination it computed) — an audit fact about the resolver's own
behaviour, recoverable only if the two original declarations are
*also* kept alongside it. `examples/diagnostic_audit_demo.py` (`v0.9`)
demonstrates this on real repository data (Phase 5b's organic `e12p`
naming collision): a `left_wins` summary equal to the left declaration
exactly is still reported `summary_is_lossy = true`, because equality
with one branch is not evidence of agreement between both.
`src/conflict_diagnostic_classifier.py` (`v0.10`) is the executable
mirror of R13 itself: given a diagnostic-shaped input, it names which
of the four fragment classes it structurally is, reusing this
project's own vocabulary (`INTERFACE_CONFLICT`,
`ReportSource.UNRESOLVED`, `NonLossyConflictDiagnostic`'s own
constructor) rather than inventing new detection rules.

```text
regional-obstruction-calculus R13
        |
        v
veribound-fce DiagnosticClass classifier
```

## 7. Limits and non-claims

- **No resolver is chosen, recommended, or endorsed**, anywhere in
  either repository. R11-R13 classify what any resolver or diagnostic
  can honestly be; none of `left_wins`/`right_wins`/`average`/`sum`/
  `erase`/pairing is selected as the "right" answer for a real system.
- **"Bounded" means bounded.** R13's completeness is for the specific,
  narrow, four-constructor fragment defined in
  `docs/design/CONFLICT_DIAGNOSTIC_COMPLETENESS.md` §3-4 — chosen to
  match this project's own proved results and `veribound-fce`'s own
  applied vocabulary, not a claim about every possible fusion, policy,
  or coupled-composition system. A real system with a partial-recovery
  diagnostic, or a probabilistic summary, would need its own fragment.
- **This does not contradict R11's own disclaimer** that its seven
  named resolver *shapes* are not an exhaustive taxonomy
  (`docs/design/CONFLICT_RESOLUTION_TRILEMMA.md` §10). R13 classifies
  structural *diagnostic shapes* (four of them, closed by the Coq
  type), a coarser, different axis from an exhaustive enumeration of
  every function that could populate the scalar or structured class.
- **No real-world policy authority is formalised.** `external_authority`
  (a resolver taking a third input not derivable from `(x, y)`) is
  explicitly outside every fragment in this line of work — not a
  property-level failure but a category-level exclusion, since it is
  not a pure function of the two declarations at all.
- **No general coupled-parallel preservation theorem exists.** The
  well-definedness gate (`rocq/CoupledParallelCompatibility.v`) and the
  aggregate-cancellation findings are unaffected by, and independent
  of, this note's synthesis — R11-R13 are downstream of the *conflict*
  case specifically, not a new composition-preservation result.
- **No witness engine, and nothing wired into `fce_check.py`.** Every
  applied object referenced in §6 is a schema or a classifier, exercised
  only by its own tests and demo fixtures — none of them computes
  anything from a real, live transformation.
- **This note proves nothing new.** It is exposition: every theorem
  cited above already exists, `coqchk`-clean, in the files named. If
  this note and a cited file ever disagree, the file is authoritative
  (matching `docs/theory/THEOREM_CONCORDANCE.md`'s own stated policy).
