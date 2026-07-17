# Tracking-adapter example corpus

Two scenarios, each carried through the full evidence chain this
repository's tracking adapter implements (see
`docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md`):

```text
tracking snapshot -> verified (D, r) -> canonical roc-input/v1 -> R21 certificate
```

Both scenarios use the same fixed four-tracker comparison graph
(`T1-T2-T3-T4-T1`, oriented edges `e12, e23, e34, e14`) as the
repository's own canonical four-cycle example
(`examples/four_cycle.json`). All four tracks report the identical raw
state (`100`); every discrepancy between them comes purely from the
declared per-edge transformation offsets (design doc §6), not from the
raw states themselves -- this is what makes the obstructed case a
genuine, transformation-derived obstruction rather than a manufactured
literal.

**Every file here is regenerated from the exact same builder code and
compared byte-for-byte against the tracked copy in
`tests/test_tracking_adapter_fixtures.py`** -- this corpus is not
hand-edited, and any drift in canonicalisation (rational-string
formatting, digest serialisation, JSON key order) would fail that test
immediately.

## `repairable_*` -- coherent transformation family

Each track's transformation offset is the SAME regardless of which edge
references it (`t1: 0, t2: 1, t3: 3, t4: 2`). The resulting residue is
exactly `Db` for `b = (0, 1, 3, 2)` -- chosen first, per the design
doc's own required construction order, not read off a precomputed
residue.

- `repairable_snapshot.json` -- the `tracking-adapter/v1` evidence.
- `repairable_adapter_certificate.json` -- the `tracking-adapter-
  certificate/v1` binding the verified derivation.
- `repairable_roc_input.json` -- the resulting `roc-input/v1`.
- `repairable_r21_certificate.json` -- R21's own `repair-or-separator/v1`
  certificate: `result: "repair"`, `repair: ["-2", "-1", "1", "0"]`.

  **Not `(0, 1, 3, 2)`, the vector used to construct `r` as `Db`.** The
  four-cycle's incidence matrix `D` has a 1-dimensional kernel spanned
  by the all-ones vector `(1,1,1,1)` -- shifting every track's
  correction by the same constant changes no pairwise discrepancy at
  all, since every row of `D` is a difference of two columns. `(0,1,3,2)`
  and R21's own witness `(-2,-1,1,0)` are both exact repairs for the
  same `r`, differing by exactly `2*(1,1,1,1)`. This is a genuine gauge
  freedom of the comparison-graph formulation (design doc §4's `b_i`
  is only ever meaningful up to this shared additive constant), not a
  discrepancy between the fixture's construction and R21's output --
  the tracked certificate records whatever R21's own deterministic
  solver actually produces for this `roc-input/v1`.

## `obstructed_*` -- incoherent, edge-specific transformation family

Each track's transformation offset DIFFERS depending on which edge
references it (e.g. track `t2`'s offset is `1` under edge `e12` but `0`
under edge `e23`) -- this is what makes the residue genuinely not a
coboundary of any single global assignment (design doc §5's central
concern). The resulting residue reproduces the repository's own
canonical four-cycle obstruction, `r = (1, 1, 1, -2)`
(`rocq/FourCycleObstruction.v`, `examples/four_cycle.json`), bit-exactly
-- derived from evidence, not copied in as a literal.

- `obstructed_snapshot.json`, `obstructed_adapter_certificate.json`,
  `obstructed_roc_input.json` -- as above.
- `obstructed_r21_certificate.json` -- `result: "separator"`,
  `separator: ["1/5", "1/5", "1/5", "-1/5"]`, matching R21/R24's own
  `y4` for this same four-cycle exactly (`rocq/R21CycleQuotientBridge.v`,
  `rocq/R24CertificateTransportExamples.v`).

## What is deliberately NOT here

Malformed and tampered variants (bad references, tampered digests,
misattributed decimal conversions, mix-and-match certificate
substitution, ...) are exercised in-memory in `tests/test_tracking_
adapter_verifier.py` and `tests/test_tracking_adapter_certificate.py`,
not stored as additional fixture files -- this directory stays a small,
legible demonstration corpus, not an exhaustive negative-case archive.
