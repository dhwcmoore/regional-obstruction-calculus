# Diagnostic Result: Ordered Inclusion-Exclusion Is Too Free by Disguised Independence

**Status: a diagnostic witness, not a theorem and not a release
milestone.** Fourth in the realisability diagnostic chain. See
`docs/design/COUPLED_GENERATOR_SPEC.md` for the architectural question this
tests one candidate against, and `docs/diagnostics/REALISABILITY_DIAGNOSTICS.md` for the
full chain. No tag accompanies this result.

## The construction

Reuses the shared four-region point-set cover already verified in
`coupled_realisability_diagnostic.py` (`REGIONS`: `U1..U4` as subsets of
one point universe, with genuine single-point cyclic-triple overlaps).
`mu` is indexed not by seam label and not by atomic region alone, but by
**ordered pairs of canonical supports** — `frozenset`s of points in the
shared universe:

```text
mu_key(A, B) = (frozenset(A), frozenset(B))
```

so the same lattice-derived support (e.g. `U2 ∩ U3`) resolves to the
same shared parameter everywhere it is referenced, never a seam-private
one. For triple `(X, Y, Z)`, the four real `SeamCorrectionData` slots are
populated by ordered inclusion-exclusion over that shared `mu` dict:

```text
mu_UV      = mu[X, Y]
mu_VW      = mu[Y, Z]
mu_U_VvW   = mu[X, Y] + mu[X, Z] - mu[X, Y∧Z]
mu_UvV_W   = mu[X, Z] + mu[Y, Z] - mu[X∧Y, Z]
```

This is a genuine hypothesis about a shared, non-private, non-zero rule
for the outer slots. It was tested against the real code, not assumed —
see "Verification discipline" below.

## The verified result

```text
16 global shared parameters (mu is indexed globally across all four triples)
rank(B_IE) = 4          (full rank -- dim C^1(N;Q) = 4)
```

**Verdict: too free, by disguised independence.** The construction is
globally shared at the parameter level, but the associator formula
cancels exactly the terms that were actually shared, leaving only terms
that happen never to coincide across triples in this geometry.

## Why, exactly

Substituting the inclusion-exclusion expressions into the already-verified
closed form (`Delta = mu_VW - mu_UvV_W + mu_U_VvW - mu_UV`, cross-checked
internally by `compute_seam_residue` on every call) and simplifying
algebraically:

```text
Delta = mu_VW - (mu[X,Z]+mu[Y,Z]-mu[X∧Y,Z]) + (mu[X,Y]+mu[X,Z]-mu[X,Y∧Z]) - mu_UV
      = mu[X∧Y, Z] - mu[X, Y∧Z]
```

**Every other term cancels exactly** — `mu_UV`, `mu_VW`, and the plain
diagonal `mu[X,Z]` all vanish from the final formula, regardless of their
value. `tests/test_lattice_ie_diagnostic.py::test_setting_only_adjacent_keys_gives_zero_residue`
demonstrates this directly: populating *only* the non-composite (adjacent
and plain-diagonal) keys with an arbitrary nonzero value, leaving every
composite key at its implicit zero, produces the all-zero residue vector.
Those parameters are provably inert.

Only the two composite (meet-based) keys per triple, `mu[X, Y∧Z]` and
`mu[X∧Y, Z]`, survive. And — checked directly against the matrix, not
assumed — **no composite key is shared by two different θ-triples** in
this four-region cover: each triple's `Y∧Z` and `X∧Y` are distinct
point-sets from every other triple's. So although the parameter space is
genuinely global (the adjacent-pair keys really are correctly reused by
the two triples that reference each one), that sharing is invisible to
the residue, because it lands exactly on the terms that cancel. What
remains behaves as four independent single-degree-of-freedom generators
in disguise — hence full rank, the same headline failure as the very
first diagnostic (`742766d`), reached by a structurally different route.

```text
A parameter can be globally indexed and still fail to impose structural
dependence, if the associator formula cancels exactly those globally
shared coordinates.
```

## Verification discipline

Nothing above is taken on symbolic faith:

- `verify_cancellation()` checks the cancellation claim **against the
  real basis-probed matrix**: every column for a non-composite key is
  confirmed entirely zero, structurally, not inferred from the algebra.
- `verify_reduction_against_real_code()` spot-checks
  `Delta = mu[X∧Y,Z] - mu[X,Y∧Z]` against `compute_seam_residue` directly,
  under eight random rational parameter assignments, on two different
  triples with different role assignments (`e12` and `e34`).

This discipline exists because an earlier hand-reasoned "witness" in this
same project (the Boolean proper-crossing rule's first proposed
construction) failed outright when actually run — see
`docs/diagnostics/BOOLEAN_PROPER_CROSSING_DIAGNOSTIC.md`. The reduction here *does*
hold exactly, for a structural reason (it is pure algebra on top of an
identity `compute_seam_residue` already cross-checks internally, not a
claim about which points carry which values) — but that structural
argument is checked computationally here, not trusted because it sounds
plausible.

## Correcting a misreading — read before trusting a nonzero quotient number

An earlier informal read of this computation reported
`dim(im(B_IE)/(im(B_IE) ∩ im δ⁰)) = 1` as "useful" — evidence of a
non-trivial realisable obstruction quotient. **That reading is wrong.**
Whenever `rank(B_IE)` equals `dim(C^1)`, the map is fully surjective:
`image(B_IE)` is literally all of `C^1(N;Q)`, and the "quotient" is simply

```text
C^1(N;Q) / im(delta^0) = H^1(N;Q)
```

a fixed fact about this graph (dimension 1, always, for the four-cycle,
regardless of which generator produced the residue) — not a sign that
this rule is structurally selective. **A nonzero quotient number is only
meaningful evidence of partial realisability when `rank(B) < dim(C^1)`.**
Always check `full_rank` (or equivalently `rank_B == dim_C1`) before
reading anything into the quotient dimension.
`tests/test_lattice_ie_diagnostic.py::test_raw_quotient_equals_H1_dimension_not_partial_selectivity`
locks this distinction in as a regression guard.

## The four-result chain so far

```text
742766d  Independent generator          rank: full (4)   too free (explicit private seam freedom)
d129612  Architectural spec             (no computation -- settles the shared-carrier requirement)
4a303c4  Shared adjacent mu, outer=0    rank: 3, quotient: 0   too strict (coboundary collapse)
f079ea1  Boolean proper-crossing        (no linear rank -- deterministic)   positive existence witness
this     Ordered inclusion-exclusion    rank: full (4)   too free (disguised independence)
```

## What this does and does not show

- It shows a *third*, structurally distinct way a coupled generator can
  fail to be selective: not private-seam freedom stated outright, and
  not zero-slot collapse, but cancellation of exactly the shared terms.
- It does not show every lattice-indexed rule fails this way — only this
  one (ordered inclusion-exclusion with these four slot assignments).
- It sharpens, rather than closes, the open question. The lesson this
  result adds:

```text
For a linear lattice discipline to work, the surviving coordinates of
Delta -- after whatever cancellation the associator formula imposes --
must themselves be shared across more than one seam context. Sharing
parameters that cancel out of Delta does not count.
```

The next candidate should therefore satisfy a sharper criterion than
"globally indexed": **the non-cancelling coordinates of `Delta` must be
globally reused by more than one θ-triple.** That is the live question —
not decided or attempted here.

## Reproducing this result

```sh
python lattice_ie_diagnostic.py
pytest tests/test_lattice_ie_diagnostic.py
```
