# Diagnostic Result: Boolean Proper-Crossing Rule Produces a Non-Degenerate Obstruction Witness

**Status: a diagnostic witness, not a theorem and not a release
milestone.** This document records one verified computation and what it
does and does not establish. See `docs/design/COUPLED_GENERATOR_SPEC.md` for the
architectural question this is one data point toward, and
`docs/diagnostics/REALISABILITY_DIAGNOSTICS.md` for the broader realisability line this
sits inside. No tag accompanies this result — see "Status" at the bottom.

## What kind of result this is

This is **not** the linear shared-adjacent-overlap test of
`coupled_realisability_diagnostic.py`. That test had a free rational
parameter space (`mu12, mu23, mu34, mu41`) and asked about the rank and
image of a linear map `B`. This result has **no free parameters at all**.
The correction slots are *derived*, deterministically, from the region
lattice itself, via the Boolean proper-crossing rule:

```text
mu(A, B) = 1   iff   A n B != empty, and neither A subseteq B nor B subseteq A
mu(A, B) = 0   otherwise
```

applied to populate all four `SeamCorrectionData` slots (`mu_UV`,
`mu_VW`, `mu_U_VvW`, `mu_UvV_W`) for each cyclic triple. Because there is
no free parameter, there is no matrix, no rank, and no quotient to
compute here — only the question of whether one specific choice of
shared point universe `P` and regions `U1..U4` produces a residue that is
or is not a coboundary. This document answers that for exactly one
recorded, non-degenerate witness.

## The witness

```text
P  = {0,1,2,3,4}

U1 = {0,1,2}
U2 = {0,1,3}
U3 = {0,2,3}
U4 = {1,2,3,4}
```

`boolean_crossing_diagnostic.WITNESS`, verified by
`tests/test_boolean_crossing_diagnostic.py` and reproducible by
`python boolean_crossing_diagnostic.py`.

## The six validation gates

Every candidate in the search that produced this witness — and this
witness itself — was checked against the real repository code at every
gate, not accepted on hand arithmetic. An earlier hand-reasoned "witness"
for this same rule (a different point-set, proposed before this search
existed) failed when actually run: three of its four seams had empty, not
single-point, triple overlaps, so `compute_seam_residue` raised
`ValueError` rather than producing the claimed residue. That failure is
exactly why these six gates exist and why nothing here is reported
without gate 3 (actual code execution) succeeding.

**Gate 0: Non-degeneracy — passed.**
- `|Ui| >= 3` for all four regions (all strictly greater than the
  minimum of 1 required).
- No `Ui` is contained in `Uj` for any `i != j` (all six pairs checked).
- The four adjacent pairs are genuine proper crossings: `U1∩U2={0,1}`,
  `U2∩U3={0,3}`, `U3∩U4={2,3}`, `U4∩U1={1,2}`.

This gate exists because the first witness the search found *without* it
was degenerate: `U1={0}`, a single point contained in every other region,
producing curvature "for free" because the proper-crossing rule forces
every `mu(U1, ·)` slot to 0 by containment, not by any genuine lattice
structure. That witness is recorded in
`tests/test_boolean_crossing_diagnostic.py` precisely to document why it
was excluded (it passes every other gate), not as the result.

**Gate 1: Support validity — passed.**

```text
U1 n U2 n U3 = {0}
U2 n U3 n U4 = {3}
U3 n U4 n U1 = {2}
U4 n U1 n U2 = {1}
```

Four distinct points, not a single point reused across triples (unlike
the degenerate witness, where all four triple overlaps coincided at the
same point). This is the modelling requirement of Theorem
thm:triple-localisation, enforced directly by
`associator_residue.compute_seam_residue`, which raises rather than
silently proceeding if a triple overlap is not a genuine singleton.

**Gate 2: the Boolean proper-crossing rule populated the actual
correction slots** — not a scalar formula printed alongside the real
computation, the actual `SeamCorrectionData` values fed into the real
`associator_defect` machinery.

**Gate 3: `compute_seam_residue` succeeded on all four seams** — the real
literal-expansion code, internally cross-checked against
`regional_composition.closed_form_delta` on every call, exactly as it is
everywhere else in this repository.

**Gate 4: the real residue vector is not a coboundary — passed.**

```text
(e12, e23, e34, e14) = (0, -1, 0, 1)
```

confirmed by exact `solve_over_Q` against the paper's own `coboundary_0`
matrix (`examples/four_cycle.json`'s matrix, not a reconstructed one).

**Gate 5: independent classifier confirmation — passed.**
`residue_classifier.classify()` returns `nontrivial_H1_obstruction`,
with cycle pairing `<z,r> = 2` (non-zero) — a second, unrelated
certificate of the same fact, in the same two-independent-checks
discipline this repository uses everywhere else.

## Orientation warning — read before trusting any "sum" shortcut

The naive coordinate sum `r_e12 + r_e23 + r_e34 + r_e14` is **not** the
coboundary test for this seam ordering, and evaluates to `0` for this
witness despite the residue genuinely not being a coboundary. That
"sum = 0" shortcut only coincided with coboundary-ness in
`coupled_realisability_diagnostic.py`'s all-forward cyclic orientation
convention (`e41 : U4->U1`). The paper's actual convention has `e14`
running `U1->U4` — not cyclic-forward `U4->U1` — so the sum is not the
right invariant here. The authoritative tests, computed directly above,
are gate 4 (exact `solve_over_Q` against the real `coboundary_0`) and
gate 5 (the classifier); neither is a sum, and both agree.

## Interpretation

This witness shows that the Boolean proper-crossing rule *can* produce
genuine curvature in a non-degenerate four-region shared-`P` cover — the
obstruction arises from a lattice-level relation change under union (a
pair transitions from properly crossing to one containing the other when
the union is taken), not from private seam-local parameters, and not
from a degenerate single-point region.

**What this does not show:**
- It does not show the Boolean rule *always* produces curvature — only
  that it can, for this one construction. Most candidates checked in the
  search that found this witness (78 of 79 that reached gate 1) turned
  out to be coboundaries.
- It is not a realisability theorem. There is no parameter space here,
  so there is no image, no rank, and no obstruction quotient to report —
  see `docs/diagnostics/REALISABILITY_DIAGNOSTICS.md` for why that question needs a
  *linear* coupled generator, which this deterministic rule is not.
- It does not resolve the open question `docs/design/COUPLED_GENERATOR_SPEC.md`
  §7 and the shared-adjacent-`mu` collapse result left open (what shared,
  non-private, non-zero rule for the outer correction slots produces
  curvature *as a function of free parameters*). This witness uses no
  free parameters at all, so it is a different kind of evidence: an
  existence result for one deterministic rule, not progress on the
  linear picture the rank/quotient framework needs.

## Reproducing this result

```sh
python boolean_crossing_diagnostic.py              # verify the recorded witness
python boolean_crossing_diagnostic.py --search --n 5   # re-run the search that found it
pytest tests/test_boolean_crossing_diagnostic.py
```

## Status

Diagnostic witness only. Not committed as a theorem, not a realisability
result, no analyser module, no certificate format, and **no tag** — a tag
would require the rule, script, witness, and interpretation to be stable
and reproduced under CI or at minimum a committed test (which exists:
`tests/test_boolean_crossing_diagnostic.py`), but the mathematical
question this points toward (a non-trivial *linear* realisable
obstruction quotient) remains open.
