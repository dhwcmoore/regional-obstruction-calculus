# Diagnostic Result: Repeated Triple-Support Linear Coupling (Candidate 3b)

**Status: a positive linear diagnostic witness, not a theorem and not a
release milestone.** Sixth in the realisability diagnostic chain (fifth
counting only the linear/rational family: items 14/15/17 negative, item
16 a non-linear existence witness, this one the first linear/rational
*positive* result). See `docs/design/COUPLED_GENERATOR_SPEC.md` for the
architectural question this tests one candidate against, and
`docs/diagnostics/REALISABILITY_DIAGNOSTICS.md` for the full chain. No tag accompanies
this result.

## The precise claim

```text
A linear/rational globally shared outer-slot discipline CAN produce a
genuinely partial, nontrivial obstruction quotient -- neither full rank
nor coboundary collapse -- when the cover has repeated triple support.
```

That is the whole result. It is a diagnostic witness for one candidate
rule (Candidate 3b) on one family of covers (repeated triple support),
not a general theorem about linear couplings. See "What this does not
show" below.

## The construction: Candidate 3b

For each seam context `theta(e) = (X, Y, Z)`, let `T = X ∩ Y ∩ Z` (the
triple's own support). Carrier coordinates are ordered restriction
parameters `rho_{A,T}`, keyed exactly like
`carrier_matrix_infrastructure.py`'s canonical `(frozenset, frozenset)`
pair. Only the two **outer** slots are populated — the adjacent slots
`mu_UV`, `mu_VW` are pinned to zero, so this candidate cannot degenerate
into item 15's adjacency-gradient collapse:

```text
mu_UV      = 0
mu_VW      = 0
mu_U_VvW   = rho_{X,T}
mu_UvV_W   = rho_{Z,T}
```

Under the fixed closed-form coefficients (`mu_U_VvW: +1`, `mu_UvV_W: -1`),
this gives `Delta_e = rho_{X,T} - rho_{Z,T}` per seam — an ordered
restriction difference, not a cyclic gradient of one shared 0-cochain,
and not the inclusion-exclusion cancellation pattern of item 17 either.

## The five-point story

**1. Candidate 3b fails on distinct triple-support covers because every
surviving coordinate is private.**

Run first on the standard cover (`coupled_realisability_diagnostic.REGIONS`,
where the four cyclic triple overlaps are four distinct points `{a},{b},
{c},{d}`) — `candidate_discipline_diagnostic.py`. Every `rho_{A,T}`
carrier coordinate came back `private_residual`: 8 parameters, 0 shared,
full rank 4. Not because the rule is too free in the item-17 sense — this
cover never gives it a chance to be shared at all: no two theta-triples'
overlaps coincide, so no two `rho_{A,T}` keys can ever be equal. This is
a **cover-inert** result, not the same kind of negative result as item
17: it shows the cover cannot test the rule, not that the rule fails its
own intended sharing condition.

**2. In a four θ-cycle, any repeated triple-support point is forced into
all four triple overlaps; opposite-pair sharing without global sharing is
impossible.**

The four theta-triples are `(U1,U2,U3)`, `(U2,U3,U4)`, `(U3,U4,U1)`,
`(U4,U1,U2)` — each is "all four regions minus one". Any two distinct
theta-triples' region-sets already union to all four regions (they omit
two different regions). So if a point lies in two different triples'
overlaps, it lies in all four regions, hence in **all four** triple
overlaps — not just the two it was placed in for.
`repeated_triple_support_diagnostic.verify_opposite_pair_sharing_forces_global()`
checks this by direct construction: forcing a point `t` into `T12` and
`T34`'s defining regions is shown to force `t` into `T23` and `T14` too,
ruling out an independent second shared point for the opposite pair. The
only repeated-triple-support cover consistent with every theta-triple
overlap remaining a genuine singleton (required by
`associator_residue.compute_seam_residue`) is: **all four triple supports
equal to one shared global point.**

**3. Under global repeated triple support `T`, Candidate 3b has four
carrier coordinates `rho_{Ui,T}`, all genuinely shared.**

`CANONICAL_REGIONS` (`repeated_triple_support_diagnostic.py`): one shared
global point `t=0`, one private point per region (so no `Ui ⊆ Uj`), and
one point shared by each of the six unordered region pairs — four
adjacent, two diagonal — placed in exactly its two regions and nowhere
else, so no triple's singleton-overlap requirement is ever broken. `|Ui|
= 5` for every region; every pair properly crosses
(`boolean_crossing_diagnostic.properly_crosses`). All four carrier
coordinates come back `genuinely_shared`: `(U1,t)` and `(U3,t)` shared
across `e12`/`e34`; `(U2,t)` and `(U4,t)` shared across `e23`/`e14` — the
opposite-pair structure forced by point 2.

**4. The induced map has rank 2, intersects `im δ⁰` in dimension 1, and
has quotient dimension 1.**

```text
n_params = 4
sharing = {zero_column: 0, private_residual: 0, genuinely_shared: 4}
rank(B) = 2
dim(im(B) ∩ im δ⁰) = 1
dim(quotient) = 1
verdict = genuinely_partial_nontrivial_quotient
B matches independent real-generator basis probe = True
```

Structurally: `r_e12 = -r_e34 = rho_{U1,t} - rho_{U3,t}` and `r_e23 =
-r_e14 = rho_{U2,t} - rho_{U4,t}` (checked directly, not asserted — see
`tests/test_repeated_triple_support_diagnostic.py::test_opposite_seam_rows_are_negatives_of_each_other`).
A genuine, non-repairable residue this rule can produce, alongside a
repairable one — neither the item-14/17 full-rank failure nor the
item-15 total collapse.

**5. Enriching the cover does not change the linear algebra, because the
map depends only on θ-role incidence and the common triple support `T`.**

`richness_invariance_check()` reruns the full computation on six more
covers, deterministically enriched up to `|Ui| = 12` (more private
points, more pairwise points, all still properly crossing, still
singleton-and-equal triple overlaps) — **every number above is
unchanged, in every trial.** This is not a coincidence of trying enough
covers; it is forced by the construction: Candidate 3b only ever reads
off the *whole region* `X`/`Z` playing a role in a seam and the *shared
support point* `T` — never anything else a region contains. So there is
no "richer witness to search for" in the sense of changing the verdict.
Richness is a variable this construction is provably indifferent to.

## Verification discipline

Nothing above is taken on symbolic faith, following the same discipline
as items 16-17 (an earlier hand-reasoned "witness" in this project failed
outright when actually run — see
`docs/diagnostics/BOOLEAN_PROPER_CROSSING_DIAGNOSTIC.md`):

- `verify_opposite_pair_sharing_forces_global()` checks the structural
  fact of point 2 by direct construction, not hand argument alone.
- `check_triple_overlaps_singleton_and_equal()` checks every cover used
  (canonical and all six enrichment trials) actually has the
  repeated-support property claimed, not assumed.
- `verify_B_matches_real_generator()` basis-probes the real generator
  (`compute_seam_residue`, internally cross-checked against
  `closed_form_delta` on every call) independently of the abstract `D·R`
  composition and checks they agree column for column.
- `verify_reduction_against_real_code()` spot-checks `Delta_e =
  rho_{X,T} - rho_{Z,T}` against `compute_seam_residue` directly, under
  eight random rational parameter assignments, on two different seams.
- `richness_invariance_check()` reruns the entire diagnosis on six
  independently-generated enriched covers rather than asserting the
  invariance argument holds.

## The diagnostic chain so far

```text
742766d  Independent generator            rank: full (4)   too free (explicit private seam freedom)
d129612  Architectural spec               (no computation -- settles the shared-carrier requirement)
4a303c4  Shared adjacent mu, outer=0      rank: 3, quotient: 0   too strict (coboundary collapse)
f079ea1  Boolean proper-crossing          (no linear rank -- deterministic)   positive existence witness
3ad4bbd  Ordered inclusion-exclusion      rank: full (4)   too free (disguised independence)
this     Candidate 3b, distinct cover     rank: full (8 params, all private)   cover-inert, not a rule failure
this     Candidate 3b, repeated cover     rank: 2, quotient: 1   FIRST positive linear/rational result
```

## What this does not show

- It does not solve arbitrary linear coupling. It is one rule (Candidate
  3b), tested on one family of covers.
- It depends on repeated triple support — a real precondition, not a
  minor detail: `test_distinct_support_cover_is_not_repeated_support`
  confirms the standard cover fails this precondition, so it is a genuine
  dividing line, not vacuous.
- It does not apply to distinct-triple-support covers — point 1 above,
  `candidate_discipline_diagnostic.py`, is the same rule failing for a
  structurally different (simpler, more direct) reason than item 17's
  cancellation failure.
- It is a diagnostic witness, not yet a general theorem. Nothing here
  claims Candidate 3b is *the* right sharing discipline, only that it is
  a rule capable of producing a genuine, non-collapsing, non-surjective
  obstruction quotient under a specific structural precondition.
- It does not replace `docs/diagnostics/BOOLEAN_PROPER_CROSSING_DIAGNOSTIC.md`'s
  result — that is a different, non-linear (parameter-free) positive
  case with no rank/quotient to compute at all. This is a different,
  linear/rational positive case, reached by a different mechanism.

## Rocq formalisation

`rocq/RepeatedTripleSupportCandidate3b.v` formalises this result as a
**finite incidence condition first**, not a geometric/topological theorem
first — `db6a5cb` never depended on metric size, region richness, or
point count beyond the support pattern, so the Rocq file isolates exactly
that pattern rather than proving something about arbitrary point-set
covers.

**Part 1 (abstract, Point-level).** Over an arbitrary `Point` type and
region predicates `U1 U2 U3 U4 : Point -> Prop`, `T12`/`T23`/`T34`/`T14`
are the triple-support predicates, and `RepeatedTripleSupport` is a
record bundling a point `t` with membership and uniqueness for all four
triple supports — the formal version of point 3's precondition. The
impossibility-of-partial-sharing fact (point 2) is proved as a *general*
theorem, `T12_T34_forces_T23_T14`: for any `p`, `T12 p -> T34 p -> T23 p
/\ T14 p`, by direct case analysis on set membership — no finiteness, no
decidable equality, no point-count assumption anywhere in this part.

**Part 2 (concrete, linear-algebra-level).** `RegionIndex` and `Seam` are
finite inductive types; `seam_X`/`seam_Z` encode the theta-role table —
copied from the **printed, committed** `repeated_triple_support_
diagnostic.induced_B()` matrix, not from memory (an earlier hand-recalled
`theta(e14)=(U1,U4,U2)` was wrong; the real, verified convention is
`theta(e14)=(U4,U1,U2)`, giving `r_e14 = rho4 - rho2`, not `rho1 - rho2`
— exactly the kind of orientation slip this project's discipline exists
to catch, caught here before compiling rather than after). `B3b : Q^4 ->
Q^4` is Candidate 3b's induced map, taken as the already-verified closed
form (this file does not mechanise `regional_composition.py`'s
associator formula — same scope limit as `FourCycleObstruction.v` taking
`delta0`'s row formula as given rather than re-deriving it).

Three theorems, each proved by exhibiting explicit witnesses rather than
invoking a general-purpose rank library (per point 7's exhibit-don't-
abstract strategy):

```coq
B3b_unit_columns_genuinely_shared :
  forall u : RegionIndex, exists e1 e2 : Seam,
    e1 <> e2 /\ ~ (B3b (unit_rho u) e1 == 0) /\ ~ (B3b (unit_rho u) e2 == 0).

g1_in_image_delta0 :        exists b : vec4, veq (delta0 b) g1.
g2_not_in_image_delta0 :  ~ (exists b : vec4, veq (delta0 b) g2).
```

where `g1 = (1,0,-1,0)` and `g2 = (0,1,0,-1)` are the two spanning
directions of `B3b`'s image (`B3b_image_in_span_g1_g2` proves every image
vector is `a·g1 + b·g2`; `g1_g2_independent` proves the two are
independent — together the Rocq form of `rank(B3b)=2`, without a formal
rank definition). `g1` turns out repairable and `g2` does not — exactly
`dim(im(B)∩im δ⁰)=1`, `dim(quotient)=1`. The headline theorems bundle
these into the Rocq form of "genuinely partial, nontrivial quotient":

```coq
repeated_triple_support_realises_nonrepairable_residue :
  forall (Point : Type) (U1 U2 U3 U4 : Point -> Prop),
    RepeatedTripleSupport Point U1 U2 U3 U4 ->
    exists rho : RegionIndex -> Q,
      (exists e1 e2, e1 <> e2 /\ ~(B3b rho e1==0) /\ ~(B3b rho e2==0)) /\
      ~ (exists b, veq (delta0 b) (B3b_vec4 rho)).

repeated_triple_support_also_realises_a_repairable_residue :
  (* same shape, with the negation dropped -- exists b, veq ... *)
```

`FourCycleObstruction.v`'s own `vec4`/`delta0`/`veq` are reused directly
(`Require Import FourCycleObstruction`) rather than redefined, since it
is exactly the same coboundary map on the same coarse graph — a stronger
connection than redefining an equivalent-but-separate `delta0` would be.
`coqchk` confirms **zero axioms** across the full dependency closure
(`AssociatorResidueRepair.v` + `FourCycleObstruction.v` + this file). No
`Admitted`/`Axiom`/`sorry`.

```sh
cd rocq && coqc AssociatorResidueRepair.v && coqc FourCycleObstruction.v && coqc RepeatedTripleSupportCandidate3b.v
```

## Reproducing this result

```sh
python candidate_discipline_diagnostic.py
pytest tests/test_candidate_discipline_diagnostic.py
python repeated_triple_support_diagnostic.py
pytest tests/test_repeated_triple_support_diagnostic.py
cd rocq && coqc AssociatorResidueRepair.v && coqc FourCycleObstruction.v && coqc RepeatedTripleSupportCandidate3b.v
```
