# Coupled Parallel Composition: Problem Statement

**Status: problem framing only. No theorem, no probe, no code.** This
document settles which question about coupled parallel composition is
being asked, and picks exactly one first case to make concrete, before
any script or proof is attempted — the same discipline
`docs/design/COUPLED_GENERATOR_SPEC.md` used for the realisability line
and `veribound-fce`'s `docs/design/PARALLEL_WITNESS_COMPOSITION_SPEC.md`
used for disjoint parallel composition before that construction was
probed. Nothing here is claimed to be correct, only well-posed.

## 1. Why this is not "disjoint parallel plus sharing"

`rocq/RefinementWitnessParallelComposition.v` and
`refinement_witness_parallel_disjoint_probe.py` (Phases 4b-4d) settled
disjoint parallel composition completely: two witnesses over
*independent* vertex/edge name universes, combined by literal direct sum
(renamed/prefixed disjoint union at the Python level; a genuine product
type at the Rocq level). The construction works cleanly precisely
because there is no shared identity anywhere — every vertex, edge,
declared cycle, and pairing belongs unambiguously to one branch or the
other, so every condition ((N0), (E0), and, once reformulated,
branchwise (A4)) reduces to a block-diagonal "holds in block A and holds
in block B."

Coupled parallel composition is not that construction with some entries
filled in differently. It is a **different construction entirely**: at
least one piece of identity — a vertex, an edge, a declared cycle, a
policy authority, a downstream target — is *shared* between the two
branches rather than duplicated or kept separate. Once that happens, the
"combined witness" cannot be built by disjoint union at all; it needs an
identification (a gluing, or a pushout-style construction) at the shared
locus, and that identification is exactly the place a new, non-trivial
interaction between the branches can live.

**The framing to hold onto**: coupled parallel composition is not
"parallel composition with noise." It is the first place in this
project's composition programme where *the interface itself* — not
either branch alone — becomes mathematically active. Disjoint parallel
composition's headline lesson (branchwise evidence survives combination,
aggregate evidence need not) was already a warning that combination can
lose information even without any sharing at all. Coupled parallel
composition asks what happens once the branches are no longer free to
combine without touching each other.

## 2. Coupling sources — a taxonomy, not a choice

Several genuinely different things could make two branches "coupled."
Listed here to keep them from being conflated into one vague notion of
"sharing," exactly as `veribound-fce`'s
`docs/design/PARALLEL_WITNESS_COMPOSITION_SPEC.md` §2 separated
"parallel" into disjoint / coupled / parallel-then-merge / policy-
parallel before any of those were probed:

| Coupling source | What is shared |
|---|---|
| shared seam | an edge (and its pullback data) appears in both branches' refined complexes |
| shared declared cycle | both branches' (A4) obligation is tested against the *same* cycle, not two independent ones |
| shared vertex or region carrier | a coarse vertex (and its own local data) is the same object in both branches, not two same-named-but-independent copies |
| shared policy authority | mathematically disjoint branches, still coupled by a downstream decision that consumes both certificates jointly (per the applied-layer spec's "policy-parallel" row — a coupling that lives entirely outside the refinement-witness mathematics) |
| downstream fusion target | both branches' outputs are consumed by one merge step, whose own obligations are a separate question (`PARALLEL_WITNESS_COMPOSITION_SPEC.md` §5) but which can retroactively make the branches interdependent |
| common restriction/downgrade operation | both branches are post-processed by the same operation before comparison, potentially reintroducing a dependency the branches didn't have on their own |
| cross-branch pairing constraint | some explicit relationship is imposed between branch A's and branch B's residues or cycles, beyond what either branch's own witness states |

**This list is illustrative, not exhaustive or verified as a closed
taxonomy** — the same caveat `PARALLEL_WITNESS_COMPOSITION_SPEC.md` §9
already carries for its own, shorter version of this list. Nothing below
attempts all seven at once.

## 3. The first case: shared seam / shared declared cycle

Of the sources above, **shared seam and shared declared cycle** are
picked as the first case to make concrete. Reasoning, not a default:

- They are the closest relatives of the mechanism already fully
  understood. Disjoint parallel composition's one real finding was that
  (A4)'s combined pairing is a *sum* of two independent pairings, and
  sums can cancel. A shared declared cycle changes that mechanism at its
  root: instead of two independent cycles being concatenated, there is
  *one* cycle being tested against pullback data from *two* branches at
  once — a genuinely different algebraic object, not a variation on
  summation.
- They are internal to the refinement-witness mathematics already built
  in this project (`refinement_checker.py`'s (A1)-(A4)/(N0)/(E0), the
  same primitives every other phase of this composition line has used).
  Policy authority and downstream fusion targets, by contrast, live
  partly or wholly outside that mathematics (per
  `PARALLEL_WITNESS_COMPOSITION_SPEC.md`'s own framing) and would need
  new machinery, not just a new witness construction, to make precise.
- They are plausible sources of *new* obstruction, not just broken
  preservation. A shared seam means the two branches' pullback maps
  could genuinely disagree about the same edge's coboundary data — a
  live candidate for an (N0)-style naturality conflict that has no
  analogue in the disjoint case at all, where (N0) always held
  block-diagonally.

**What is deliberately excluded from this first case**: policy
authority, downstream fusion targets, and cross-branch pairing
constraints (rows 4, 5, 7 of §2's table) are not addressed here. Neither
is any real sensor-fusion or multi-branch domain modelling — the same
exclusion this project has held throughout the composition line.

## 4. The question, stated precisely

For two refinement witnesses $A: X_0 \to X_1$ and $B: Y_0 \to Y_1$ that
share exactly one seam (an edge $e$ appearing in both $X_1$ and $Y_1$,
with potentially *different* pullback data assigned to it by each
branch) or exactly one declared cycle (the same cycle vector $z$ used as
both branches' (A4) witness, rather than each branch declaring its own):

> **What is the right combined witness construction when two branches
> are not disjoint but share exactly one seam or one declared cycle —
> and, once that construction is fixed, do (N0), (A4), and (E0) still
> reduce to any clean combination rule, or does the shared locus
> introduce genuinely new obstruction that neither branch's own
> admissibility could have predicted?**

Two sub-cases worth keeping apart from the outset, since they may behave
differently:

1. **Shared seam, consistent pullback data.** Both branches assign the
   *same* pullback data to the shared edge. The natural conjecture is
   that this degenerates back toward the disjoint case (the sharing is
   redundant, not load-bearing) — worth checking computationally rather
   than assumed.
2. **Shared seam, conflicting pullback data.** The two branches assign
   *different* pullback data to the same edge. There is no obvious
   "combined" value — averaging, taking one branch's value
   preferentially, or declaring the combination inadmissible are all
   live candidates, and picking one is itself a modelling decision, not
   a computation.

The declared-cycle version of the question is structurally similar but
distinct: a single shared cycle tested against both branches' pullback
data at once raises the question of whether the (A3) admissibility
condition (the cycle being a genuine element of the refined complex's
cycle space) can even be stated coherently when "the refined complex" is
now the shared-seam gluing of two branches' complexes, not a disjoint
union.

## 5. What would count as an interesting result

Following this project's own established standard (Candidate 3b's
classification, the disjoint-parallel A4 split): a result is interesting
if it **distinguishes cases**, not if it proves one uniform verdict.
Plausible shapes, none assumed:

- Consistent-data sharing degenerates to the disjoint case exactly (a
  clean reduction, closing sub-case 1 quickly and leaving conflicting
  data as the real question).
- Conflicting-data sharing forces a genuine three-way classification —
  inadmissible, resolvable by an explicit tie-breaking rule, or
  obstruction-producing in a way with no disjoint-case analogue — mirror
  ing how Candidate 3b's classification had two genuinely different
  regimes (cover-inert vs. genuinely partial), not one.
- Shared-seam coupling and shared-cycle coupling turn out to behave
  differently from each other (one degenerates, one does not), which
  would itself be worth recording as a finding, the same way this
  project already recorded that N0/E0 and A4 behave differently under
  disjoint parallel composition.

A "no clean result, only case-by-case behavior" outcome is itself an
acceptable, recordable finding — consistent with how the independent
generator (too free) and the zero-outer-slot generator (too collapsed)
were both recorded as real, useful negative results earlier in this
project's realisability line, not treated as failures to find something
better.

## 6. What is explicitly not attempted here

- No probe script. Per the established order (probe before proof, spec
  before probe), the next step — if and when this document is judged
  ready — is a small Python probe analogous to
  `refinement_witness_parallel_disjoint_probe.py`, testing sub-cases 1
  and 2 of §4 on concrete witness data. Not started.
- No Rocq file, no theorem name proposed. Coupled parallel composition
  has no preservation candidate anywhere in this project
  (`PARALLEL_WITNESS_COMPOSITION_SPEC.md` §4 names it a possible
  *source* of obstruction, deliberately not a candidate) — this document
  does not change that, and does not propose one.
- No claim about which sub-case (consistent or conflicting shared data)
  is more realistic or more important for any applied use — that
  judgment is deferred.
- Policy authority, downstream fusion targets, and cross-branch pairing
  constraints (§2's other rows) — not addressed, not scheduled.
- Any real sensor-fusion or multi-branch domain modelling.

## 7. Open questions

- Whether "shared seam" and "shared declared cycle" should be treated as
  one combined first case or two genuinely separate probes — not
  decided; §4 poses them together but a probe implementation may need to
  separate them cleanly to avoid conflating two different mechanisms.
- What the right combined-complex construction even *is* for the
  conflicting-pullback-data sub-case (§4, sub-case 2) — averaging,
  branch-preference, or inadmissibility are named as candidates, not
  chosen.
- Whether (A3) admissibility itself needs restating before (N0)/(A4)/(E0)
  can even be asked about a shared-seam combined witness, or whether the
  existing definitions transfer unchanged — not checked.
- Whether the branchwise/aggregate distinction that turned out to matter
  for disjoint parallel (A4) has any analogue here, or whether shared
  data breaks that distinction's premise (that each branch's own
  evidence is well-defined independently of the other) from the start.
