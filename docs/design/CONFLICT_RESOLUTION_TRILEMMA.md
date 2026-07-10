# The Conflict-Resolution Trilemma

**Status: problem framing and impossibility theorem, no resolver
chosen.** This document does not propose, endorse, or implement a
conflict-resolution rule for `interface_conflict` — the shared-seam
compatibility gate (`rocq/CoupledParallelCompatibility.v`, Phases
5b-5e) deliberately left that question unaddressed, and this document
does not answer it either. What it does instead: shows that *any*
resolver — however it is eventually chosen — must sacrifice something,
and proves the minimal core of why, before any specific resolver is
built.

## 1. Purpose

Once two branches disagree on a shared interface (`interface_conflict`:
`x ≠ y` for the shared value each branch declares), a system that
refuses to build a composite (the gate this project has already proved,
`interface_disagreement_blocks_glue`) is always available and always
safe — it simply declines. But a system that instead wants to *produce*
a composite value despite the disagreement needs a resolver: a function
`resolve(x, y)` that turns two disagreeing declarations into one.

This document's purpose: show that once such a resolver is required to
actually commit to *some* value when `x ≠ y`, it cannot simultaneously
have every property a naive reader might expect it to have. This is not
a design defect to fix — it is a structural fact about disagreement
itself, independent of which specific resolver is eventually chosen.
The applied sentence this document exists to justify:

> A conflict-resolution rule is not a preservation theorem. It is an
> authority rule.

## 2. Minimal resolver desiderata

Let `V` be the type of declared values at a shared seam (in the
concrete refinement-witness setting, `V` might be a rational number, an
`Edge`'s structural data, or a coarse-parent label — the desiderata
below are stated abstractly, over any `V`, exactly as
`CoupledParallelCompatibility.v`'s own `Key`/`Value` model was kept
abstract). A **resolver** is a function `resolve : V -> V -> V`
(deliberately total here — see §5 for why refusal is treated as an
*alternative to having a resolver at all*, not as one more property a
resolver can satisfy).

Six properties, named exactly as directed:

```text
Agreement:      x = y  ->  resolve(x, y) = x
                 (when the branches already agree, the resolver must
                 recover that shared value -- the trivial case must be
                 handled correctly.)

Left fidelity:  forall x y, resolve(x, y) = x
                 (the resolver always honours the left branch's
                 declaration, regardless of what the right branch said.)

Right fidelity: forall x y, resolve(x, y) = y
                 (symmetric to the above, for the right branch.)

Symmetry:       forall x y, resolve(x, y) = resolve(y, x)
                 (which branch is called "left" and which is "right" is
                 bookkeeping, not meaning -- the resolver should not
                 depend on it.)

Idempotence:    forall x, resolve(x, x) = x

Refusal:        the resolver may instead decline to produce any value at
                 all, rather than being forced to satisfy any of the
                 above -- see §5.
```

**An honest observation, checked before anything else was built on top
of these six names**: *Idempotence*, as stated, is exactly the special
case of *Agreement* where the input pair is `(x, x)` — `x = x` always
holds, so Agreement's hypothesis is trivially satisfied on the diagonal,
and its conclusion `resolve(x, x) = x` is the literal statement of
Idempotence. **Every resolver satisfying Agreement automatically
satisfies Idempotence; Idempotence is not an independent axis.** Kept
as its own named property below (matching the six names given) because
it is a useful, separately-checkable fact about any *specific* resolver
under test — but the classification in §4 will not treat it as
something a resolver could satisfy independently of Agreement, since
that is not possible.

## 3. The core impossibility theorem

The minimal fact underneath everything else, stated first because
everything else is a consequence or elaboration of it:

```text
x ≠ y  ->  ¬ (z = x ∧ z = y)
```

In words: if the two branches genuinely disagree, no single value can
equal both of their declarations at once. This is not a theorem about
refinement witnesses, coupled parallel composition, or any of this
project's specific machinery — it is a fact about equality itself,
true for any type `V`. Its significance is entirely in what it forces
once combined with the desiderata above:

**No resolver can have both full Left fidelity and full Right fidelity,
unless `V` has at most one element.** If `resolve(x, y) = x` for all
`x, y` (Left fidelity) and `resolve(x, y) = y` for all `x, y` (Right
fidelity), then for any `x` and `y`, `x = resolve(x, y) = y` — every
pair of elements of `V` is equal, i.e. `V` is trivial. Contrapositively:
for any genuinely nontrivial `V` (any type with two distinct
elements — every real interface-value type in this project has this
property), **a resolver cannot have both fidelities.** Committing to
honour the left branch's declaration, universally, forecloses ever
honouring the right branch's declaration on a disagreement, and vice
versa.

This is proved formally, not just argued in prose, in
`rocq/ConflictResolutionTrilemma.v` (§7).

## 4. Classifying candidate resolvers

Given that no resolver can have both fidelities, what can a resolver
actually have? This section names seven candidate resolver *shapes*
(none endorsed — this is a classification, not a recommendation) and
states, for each, which of §2's desiderata it satisfies and which it
must sacrifice. Checked computationally in
`conflict_resolution_trilemma_probe.py` (§6), not merely asserted here.

```text
refuse              -- declines to produce a value at all when x != y.
                        Satisfies: Agreement, Idempotence (vacuously/trivially,
                        since it never needs to answer on a genuine conflict).
                        Sacrifices: totality itself -- this is the "opt out"
                        move, not a value-producing resolver at all.

left_wins           -- resolve(x, y) := x, always.
                        Satisfies: Agreement, Idempotence, Left fidelity.
                        Sacrifices: Right fidelity (whenever x != y), Symmetry.

right_wins          -- resolve(x, y) := y, always.
                        Satisfies: Agreement, Idempotence, Right fidelity.
                        Sacrifices: Left fidelity (whenever x != y), Symmetry.

average             -- resolve(x, y) := (x + y) / 2  (V = Q only).
                        Satisfies: Agreement, Idempotence, Symmetry.
                        Sacrifices: Left fidelity AND Right fidelity
                        (whenever x != y -- the resolved value is neither
                        branch's own declaration).

sum                 -- resolve(x, y) := x + y  (V = Q only).
                        Satisfies: Symmetry.
                        Sacrifices: Agreement and Idempotence too (sum(x, x)
                        = 2x, which equals x only when x = 0) -- NOT merely
                        the two fidelities. A sharper sacrifice than average,
                        worth keeping distinct in the table rather than
                        lumping "symmetric-but-unfaithful" resolvers together.

erase               -- resolve(x, y) := a fixed sentinel value (e.g. 0),
                        regardless of x, y.
                        Satisfies: Symmetry.
                        Sacrifices: Agreement, Idempotence, both fidelities --
                        the maximally unfaithful resolver: it does not even
                        recover the shared value when the branches agree.

external_authority  -- resolve(x, y, a) := a, where `a` is a THIRD input --
                        a policy decision, a human reviewer, an out-of-band
                        authority -- not derivable from x and y alone.
                        Satisfies: whatever the authority happens to choose
                        (potentially Agreement, Symmetry, either fidelity, on
                        a case-by-case basis).
                        Sacrifices: closure/purity -- this is not a function
                        of (x, y) alone anymore, so none of §2's properties
                        (all stated as universal facts about a function of
                        two arguments) even type-check as stated. The
                        sacrifice is category-level, not property-level: an
                        external-authority "resolver" has quietly stopped
                        being the kind of object this document's desiderata
                        describe.
```

## 5. Refusal is not a desideratum to satisfy — it is the alternative

Unlike the other five names, "Refusal" in §2 was never a property a
value-producing resolver could hold *alongside* the others — it is the
choice not to have one. This project's own shared-seam compatibility
gate (`interface_disagreement_blocks_glue`) already IS the refusal
option, fully proved, fully implemented (`veribound-fce`'s
`interface_conflict` status). Nothing in this document adds to that;
§4's `refuse` row is included only to keep the classification complete,
not because refusal itself is a new finding.

## 6. Reproducing this

```sh
python conflict_resolution_trilemma_probe.py
python conflict_resolution_lower_bound_probe.py
```

See `docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md`... **no** --
this document intentionally does not attach itself to that status
doc's phase numbering; the conflict-resolution trilemma is a different
mathematical question (about equality and resolvers in the abstract)
from the composition-preservation questions that doc's Phase 5 line
answers, even though both arose from the same shared-seam construction.
Findings are recorded directly in this document (§4, updated after the
probe ran) and in `RESULTS.md`.

## 7. What is proved in Rocq

`rocq/ConflictResolutionTrilemma.v`:

```text
no_single_value_matches_both_declarations :
    forall (V : Type) (x y z : V), x <> y -> ~ (z = x /\ z = y).
    The minimal core fact, exactly as stated in §3, for an arbitrary
    type V -- no refinement-witness or interface-declaration structure
    assumed at all.

full_fidelity_forces_trivial_domain :
    forall (V : Type) (resolve : V -> V -> V),
      (forall x y, resolve x y = x) -> (forall x y, resolve x y = y) ->
      forall x y : V, x = y.
    If a resolver has both full fidelities, EVERY pair of elements of V
    is equal -- V collapses to (at most) one element.

no_resolver_has_both_fidelities_on_nontrivial_domain :
    forall (V : Type) (resolve : V -> V -> V) (a b : V),
      a <> b -> ~ ((forall x y, resolve x y = x) /\ (forall x y, resolve x y = y)).
    The operationally meaningful contrapositive: given ANY witness that V
    has two distinct elements (true of every real interface-value type
    in this project), no resolver can have both fidelities. This is the
    theorem that actually rules out the "just satisfy both branches"
    move for any resolver ever proposed for a real shared-seam interface.
```

`coqchk`-clean, no `Admitted`/`Axiom`/`sorry`, full 16-file dependency
closure. See `RESULTS.md` (R11) for the full account.

## 8. Lossy versus structured resolvers

§3's impossibility is sharper than "conflicts cannot be resolved." It
is specifically about resolvers whose *output* is the same type `V` as
the two disagreeing declarations — call these **lossy** resolvers,
since committing to one value of type `V` necessarily discards
information whenever `x ≠ y` (§3 shows there is no value of type `V`
that could avoid discarding something). Nothing forces the output to be
`V`, though. A resolver can instead be **structured**: its codomain is
some other type `S`, equipped with projections recovering each original
declaration. When `S := V * V` and the resolver is simply
`fun x y => (x, y)`, both projections recover `x` and `y` exactly, for
*every* pair, not only the ones that happened to agree.

```text
pair_resolver_preserves_both_claims :
    forall x y : V, fst (pair_resolver x y) = x /\ snd (pair_resolver x y) = y.
```

This is existence, not impossibility, and it is nearly definitional —
the point is not that the construction is deep, but that it exists at
all and costs nothing beyond widening the output type. **The earlier
impossibility is therefore about single-value (same-type) resolution
specifically, not about preserving information as such**: nothing
prevents a system from keeping both declarations, only from collapsing
them into one value of the original type without loss.

**What structure does not buy you.** If a structured resolver also
exposes a single scalar "resolved" summary field of type `V` (for
compatibility with a consumer that only wants one value), that field is
still a plain `V -> V -> V` function on its own terms, and §3/§7's
impossibility applies to it completely unchanged — wrapping it inside a
larger structure that also happens to carry `x` and `y` alongside it
does not exempt the summary field itself from the trilemma:

```text
structure_does_not_exempt_the_resolved_field :
    forall (resolved : V -> V -> V) (a b : V), a <> b ->
      ~ ((forall x y, resolved x y = x) /\ (forall x y, resolved x y = y)).
```

This is literally the same theorem as
`no_resolver_has_both_fidelities_on_nontrivial_domain` (§7), restated
to make the point explicit: **preserving both claims and having one
faithful combined scalar are different goals, and a structured resolver
achieves only the first.** Choosing what the "resolved" field should
actually contain — `left_wins`, `average`, or anything else from §4's
table — remains exactly as open a question as before; structure changes
what is preserved *alongside* a scalar summary, not the summary's own
fidelity properties.

Checked computationally, not only stated, in
`conflict_resolution_trilemma_probe.py`: `pair_resolver`'s two
projections recover the original test pairs exactly, for every pair
tested, including the disagreeing ones §4's lossy resolvers all fail on
in one direction or the other.

## 9. R12: the non-lossy lower bound

§8 showed structured resolution is *possible*. This section asks how
much structure it actually *requires* -- not a new question invented
for its own sake, but the natural next step once existence is settled:
what is the minimum an honest, non-lossy encoding must do?

**Definition.** An encoding `encode : V -> V -> C` is **non-lossy**
when fixed projection functions `left_read, right_read : C -> V`
recover both original declarations, for every pair:

```text
NonLossy(encode, left_read, right_read) :=
    forall x y, left_read(encode(x, y)) = x /\ right_read(encode(x, y)) = y
```

(`§8`'s `pair_resolver` is exactly the case `C := V * V`, `left_read :=
fst`, `right_read := snd` -- this section generalises to an arbitrary
codomain `C`, not only the literal pair type.)

**The lower bound.** Any non-lossy encoding is injective on `V * V`:

```text
nonlossy_encoding_injective :
    NonLossy(encode, left_read, right_read) ->
    encode(x1, y1) = encode(x2, y2) -> x1 = x2 /\ y1 = y2
```

The proof is short -- apply `left_read` to both sides of
`encode(x1,y1) = encode(x2,y2)` to recover `x1 = x2`; apply
`right_read` for `y1 = y2` -- but the *content* is the point, not the
difficulty: **a non-lossy encoding must assign a genuinely distinct
`C`-value to every distinct ordered pair of declarations**, or its
fixed projections could not tell two different conflicts apart. This is
the information-theoretic fact underneath §8's existence result: pairing
into `V * V` is not merely *one* way to be non-lossy, it is exhibited
here (`structured_pair_is_nonlossy`, restating `pair_resolver`'s
property under this section's vocabulary) as achieving the bound
exactly, with no wasted structure.

**The finite corollary.** For finite `V` with `|V| = n`, injectivity on
`V * V` forces the encoding's codomain to satisfy `|C| >= n^2` (an
injective function's domain cannot exceed its codomain's size). In
particular, **no encoding whose codomain is confined to `V` itself
(size `n`) can be non-lossy once `n > 1`**, since `n^2 > n` whenever
`n > 1` -- a cardinality-flavoured restatement of §3's original
equational impossibility, not a new assumption, and not requiring `V`
to be finite in the first place (`nonlossy_encoding_injective` itself
holds for any type, finite or not; only this specific corollary needs
finiteness to state the gap as a number).

Checked computationally, not only stated, in
`conflict_resolution_lower_bound_probe.py`, for finite test domains of
size `n = 1..6`:

```text
n    n^2   gap = n^2 - n
1    1     0
2    4     2
3    9     6
4    16    12
5    25    20
6    36    30
```

**A scope note worth stating precisely, checked before writing this
down**: this does *not* mean every codomain-`V` ("lossy," in §8's
sense) resolver's actual output range is bounded by `n` in general --
`sum` (§4) is typed `Q -> Q -> Q`, matching `V := Q`, but its outputs
(`x + y`) are not structurally confined to any finite test subset of
`Q`, so counting `sum`'s image size on a finite domain is not the right
demonstration of the bound. The probe instead uses resolvers whose
output is structurally confined to `V` by construction --
`left_wins`/`right_wins` (output is always literally one of the two
inputs) and `erase` (output is always a fixed sentinel already in `V`)
-- and confirms their image sizes exactly: `left_wins`/`right_wins`
achieve `n` (the best a codomain-confined resolver can do, still short
of `n^2` once `n > 1`); `erase` achieves `1` (the worst possible,
regardless of `n`).

**What this settles, and what it does not.** This section characterises
the *shape* a faithful, non-lossy conflict record must have -- an
injective encoding of the ordered pair, nothing looser -- not what
specific fields, names, or format such a record should carry in a real
diagnostic system. That remains entirely undecided, the same as before.

`rocq/ConflictResolutionLowerBound.v`: `nonlossy_encoding_injective` and
`structured_pair_is_nonlossy`, `coqchk`-clean, full 16-file dependency
closure, no `Admitted`/`Axiom`/`sorry`. See `RESULTS.md` (R12) for the
full account.

## 10. What is not claimed

- That §4's seven resolver shapes are exhaustive. They are the
  candidates named in this document's own opening discussion, not a
  closed taxonomy.
- That any of §4's resolvers is recommended, endorsed, or chosen. This
  document deliberately implements none of them.
- That the impossibility in §3/§7 is specific to refinement-witness
  interfaces, coupled parallel composition, or any structure in this
  project. It is a fact about equality and total functions of two
  arguments, true for any type.
- That `external_authority` is a well-defined resolver in the sense
  the other six are. §4 states explicitly why it falls outside the
  desiderata's own type signature, not merely why it under-performs on
  them.
- That this document decides anything about which resolver, if any,
  `veribound-fce` should eventually implement. It narrows the design
  space by ruling out one specific hope (a resolver faithful to both
  branches at once) — nothing more.
- That §8's `pair_resolver` is a proposed implementation. It is an
  existence witness only, showing structured (non-lossy) resolution is
  possible in principle — it says nothing about what a real diagnostic
  layer should store, in what format, or under what field names, and
  does not itself decide what the "resolved" scalar field of a
  structured object should compute.
- That widening the output type "solves" conflict resolution. §8 shows
  only that it avoids the specific impossibility of §3/§7 for the
  *claims themselves*; a structured resolver still owes its consumer
  some scalar summary in most real use cases, and that summary is still
  fully subject to §3/§7 -- structure changes what can be preserved
  alongside a decision, not whether a decision, once reduced to one
  value, can honour both sides.
- That §9's lower bound recommends a specific field layout, encoding, or
  serialisation format for a real diagnostic object. It characterises
  the abstract minimum -- injectivity on `V * V` -- not a concrete
  schema; deciding what a real record should actually contain (field
  names, types, provenance metadata) is unstarted, in either repository.
- That `sum`'s image size on a finite domain is bounded the way
  `left_wins`/`right_wins`/`erase`'s are. §9 states explicitly why that
  comparison would be misleading (`sum`'s outputs are not structurally
  confined to `V`) and does not make it.
