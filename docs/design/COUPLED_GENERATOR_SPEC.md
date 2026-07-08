# Coupled Generator Specification

### Shared Point-Universe Architecture for Regional Associator Residues

This document settles one thing only: the architectural correction needed
before a first-order realisability theorem can be non-trivial. It does
not choose a sharing discipline, does not define the coupled
parameter-to-residue map `A_S`, and does not contain code. See
`docs/diagnostics/REALISABILITY_DIAGNOSTICS.md` for the negative result this responds to,
and §7 below for exactly what is still undecided.

## 1. Purpose

`docs/diagnostics/REALISABILITY_DIAGNOSTICS.md` (commit `742766d`) showed that the
current associator generator (`associator_residue.four_cycle_instances()`)
is surjective onto all of `C^1(N;Q)`: every residue is realisable, a
negative result. The diagnosis given there was that the generator's four
seams are "fully independent... with no shared data." This document
sharpens that diagnosis one level further, and states the correction.

The sharper diagnosis: the problem is not merely that the seams *choose*
independent data for a shared region. It is that **there is currently no
regional object whose identity could be shared** — nothing in the code
represents "region `U2`, as it appears in both seam `e12` and seam
`e23`, is the same thing." The correction is not a coupling equation
pasted onto the existing seams; it is an architectural inversion in how
seam-local data are obtained at all.

## 2. Existing algebraic basis

`regional_composition.py`'s own module docstring already states the
right ontology for this, describing the square-zero Venn model of
Example ex:venn:

> "regions are subsets of a finite point universe P... Because extension
> by zero embeds A0(R) into A0(S) as 'zero outside R', an element of
> A(S) can be represented directly as a pair of dictionaries over the
> *global* universe P... This is the same model the paper uses in
> ex:venn; it is not a simplification of the general theory, it is the
> theory's own worked example."

That is: one finite point universe `P`, with regions represented as
subsets of `P`, and restriction (`restrict(x, region)` in
`regional_composition.py`) as the operation that produces a region's
local view of global data. This is already exactly the ontology a
coupled generator needs — a single shared carrier that different regions
and overlaps are views *into*, not separate worlds. The algebra layer is
not the part that needs to change.

## 3. Current architectural failure

The break is one layer up, in `associator_residue.py`:

```python
@dataclass(frozen=True)
class SeamAssociatorInstance:
    seam: str
    mu: SeamCorrectionData
    triple: VennTriple = VennTriple()
```

`VennTriple`'s default fields (`U={1,4,5,7}`, `V={2,4,6,7}`,
`W={3,5,6,7}`, all subsets of a private `P={1,...,7}`) are instantiated
fresh, independently, for every `SeamAssociatorInstance` — including in
`four_cycle_instances()`, which builds four such instances and never
passes a `triple` argument, so all four silently get their own separate
copy of the same toy shape. The internal labels `U`, `V`, `W` inside each
seam's triple have no reference — not even a nominal one — to the coarse
graph's actual regions `U1`, `U2`, `U3`, `U4`. Seam `e12`'s `V` and seam
`e23`'s `U` are unrelated Python objects that happen to reuse the same
small integer point-set by coincidence of sharing a default value, not by
design.

The coarse regional structure enters only *after* the four scalars have
already been generated, when they are placed as coordinates of a
1-cochain matching `refinement_witnesses.COARSE`'s edge order. In summary:

```text
The current independent generator is not a regional generator. It is a
product of four seam-local VennTriple gadgets whose scalar outputs are
later interpreted as a 1-cochain on the coarse graph.
```

That is why the realisability map was full rank: nothing connects what
happens at one seam to what happens at its neighbour, so every
combination of seam outputs is reachable independently.

## 4. Required architectural inversion

Replace:

```text
seam creates its own private local world
```

with:

```text
one shared regional world restricts to each seam's context
```

Concretely, the dependency direction must invert. Currently:

```text
SeamAssociatorInstance()
    -> private VennTriple()
        -> residue r_ij
```

A coupled generator instead needs:

```text
RegionalCoverData
    -> restrict_to_seam(e_ij)
        -> SeamContext
            -> residue r_ij
```

A seam's associator computation should be a *view* obtained from one
shared assignment, never a self-contained construction that happens to
get labelled with a seam name afterward.

## 5. Proposed core objects (spec level only — not implemented)

```text
RegionalCoverData:
    P: finite point universe (shared, not per-seam)
    regions: mapping Ui -> subset of P, one entry per coarse vertex
    overlaps: Ui ∩ Uj, computed as actual set intersections within P,
              not separately declared
    incidence: the coarse nerve/graph data these regions and overlaps
               sit inside (already exists, in refinement_witnesses.COARSE
               / examples/four_cycle.json's shape -- not duplicated here,
               referenced)

SeamContext:
    seam id e_ij
    left region Ui, right region Uj  (both restrictions of RegionalCoverData)
    overlap Ui ∩ Uj  (likewise a restriction, not a fresh declaration)
    local support data obtained by restriction from RegionalCoverData,
    not instantiated independently

CoupledSeamAssociatorInstance:
    constructed from RegionalCoverData.restrict_to_seam(e_ij),
    not from a freshly instantiated VennTriple
```

These names are provisional and exist to fix the *shape* of the
dependency graph in §4, not to commit to field-level design. Building
them is future work (§7 lists what's still undecided that any
implementation would need to resolve first).

## 6. What is settled

- One shared finite point universe `P`, not one per seam.
- Regions `U1..U4` are subsets of that one `P`.
- Overlaps `Ui ∩ Uj` are actual set intersections computed within `P`,
  not independently declared per seam.
- Seam instances must be constructed by restriction from
  `RegionalCoverData`; instantiating a private `VennTriple` per seam is
  the specific pattern to remove.
- Residues are generated by restricting shared regional data to each
  seam's context, not by running four unrelated local experiments and
  labelling the outputs afterward.
- The algebra layer (`DualNumber`, pointwise product, `restrict`) does
  not need to change; it already has the right ontology (§2). The
  correction is entirely in how `associator_residue.py` uses it.

## 7. What remains open

This is the next mathematical decision, and it is deliberately not made
here:

- Whether `mu` correction data is assigned per region, per overlap, per
  triple/seam context, by a restriction-compatibility requirement, by a
  declared support discipline, or by some minimal combination of these
  — the four candidate sharing disciplines already under discussion
  (shared region algebra / shared overlap correction / shared restriction
  agreement / shared support discipline), and how they interact or
  subsume one another.
- The exact algebraic content of a region's or overlap's shared datum
  (is it a full local algebra, a set of correction constants, something
  else).
- How `restrict_to_seam` is actually defined once the above are decided.

None of these should be resolved by extending this document. They are
the subject of the next design conversation.

**Related, but not a resolution of the above:**
`docs/diagnostics/BOOLEAN_PROPER_CROSSING_DIAGNOSTIC.md` records a deterministic
(parameter-free) rule for populating correction slots — including the
outer ones this section leaves open — and shows it produces a
non-degenerate residue outside `im(delta^0)` for one specific cover. That
rule is not one of this section's candidates: it has no free parameters
at all, so it cannot be plugged into the rank/quotient framework §8
describes. It is evidence that *some* sharing rule can produce curvature,
not a decision about which linear sharing discipline this document's open
question calls for.

**A tested linear candidate, and why it failed instructively:**
`docs/diagnostics/LATTICE_IE_DIAGNOSTIC.md` records an actual attempt at this
section's open question — `mu` indexed globally by ordered pairs of
lattice-derived supports (not seam-local), with the outer slots populated
by inclusion-exclusion over that shared index. Checked against the real
code: the associator formula cancels exactly the terms that were
genuinely shared, leaving only per-triple-unique composite terms, so the
map is full rank despite the parameter space being global. The lesson
this adds to this section's still-open question: a candidate rule must
not just be globally indexed — its terms must *survive* the associator's
cancellation and still be shared across more than one seam context. That
is a real constraint on any future candidate, not yet satisfied by
anything tried so far.

**A first positive linear result, and the precondition it depends on:**
`docs/diagnostics/REPEATED_TRIPLE_SUPPORT_DIAGNOSTIC.md` records the first
linear/rational rule in this line to produce a genuinely partial,
nontrivial obstruction quotient — Candidate 3b (ordered
restriction-to-triple-support coordinates), tested on a cover whose four
θ-triples share one repeated triple-support point rather than four
distinct ones. On the standard distinct-support cover, the same rule is
cover-inert (every carrier coordinate is private, not because the rule is
too free but because the cover never gives it a chance to be shared —
see `candidate_discipline_diagnostic.py`). On a repeated-support cover —
verified to be the *only* structurally achievable kind of repeated
support in a four-θ-cycle (any two triples sharing a point forces that
point into all four) — the induced map has rank 2, intersects `im δ⁰` in
dimension 1, and has quotient dimension 1, invariant under enriching the
cover up to `|Ui|=12`. This answers the sharpened open question above
(from `docs/diagnostics/LATTICE_IE_DIAGNOSTIC.md`) in the affirmative for one
construction: a linear rule *can* have its
surviving (non-cancelling) coordinates genuinely shared across more than
one seam context, when the cover is chosen so that sharing is possible at
all. It does not settle which sharing discipline is "the right one" —
see that document's "What this does not show" section.

## 8. Rank and obstruction tests (for later, not defined here)

Once a sharing discipline `S` is chosen and `RegionalCoverData` is given
concrete algebraic content, it induces a parameter-to-residue map `A_S`,
exactly as `realisability_diagnostic.py` built `A` for the independent
generator. The same two tests apply:

```text
rank(A_S) < dim C^1(N;Q)
```

as a first diagnostic (does coupling even reduce the realisable space at
all), and, more importantly,

```text
im(A_S) / (im(A_S) ∩ im(delta^0))
```

as the real obstruction diagnostic — which realisable first-order
residues survive repair, i.e. which obstruction classes are structurally
forced by the coupled regional discipline rather than merely
constructible.

**This document does not define `A_S`. It defines the regional carrier
required before `A_S` can be meaningful.**
