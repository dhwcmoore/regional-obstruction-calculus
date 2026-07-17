# Tracking Adapter End-to-End Demonstration: Canonical Snapshot to Independently Checked Verdict

**Status (2026-07-17): canonical reference example, now including a
Stone Soup-derived example (Example 3).** Every command and output
below was actually run against this repository's own tracked fixtures
(`examples/tracking_adapter/`) or, for Example 3, a fresh Stone Soup run
against the pinned version in `requirements-stonesoup.txt` — none
reconstructed from memory or hand-edited afterward. `tests/test_
tracking_adapter_documentation_drift.py` (Examples 1-2) and `tests/
test_stonesoup_trackfusion_documentation_drift.py` (Example 3) re-run
the same pipelines and assert the commands, filenames, schema versions,
and witness values below still hold — this document cannot silently
drift from what the repository actually does without those tests
failing.

## Scope of what this demonstrates

This shows the complete chain for the tracking adapter (see
`docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md`):

```text
tracking-adapter/v1 snapshot
          |
          v
independent adapter verification (tracking_adapter_verifier.py)
          |
          v
tracking-adapter-certificate/v1  (tracking_adapter_certificate.py emit)
          |
          v
canonical roc-input/v1  (embedded in the certificate)
          |
          v
real R21 emitter (r21_certificate_emitter.py)
          |
          v
repair-or-separator/v1 certificate
          +-------------------------+
          v                         v
   Python R21 verifier        OCaml R21 verifier
 (r21_certificate_checker.py)   (roc-verify-ocaml)
          +-------------------------+
                      |
                      v
      complete chain verification
   (tracking_adapter_certificate.py verify-chain)
```

It does **not** demonstrate, and this repository does not claim, that
Stone Soup (or any other real tracking evidence producer) has been
verified to correctly compile into a `tracking-adapter/v1` snapshot, or
that the adapter's own policy matches any external (e.g. MIST) standard.
Both tracked scenarios are hand-authored fixtures matching the design
doc's own feasibility-spike construction, not a real sensor feed. See
`docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md` §19 and
`examples/tracking_adapter/README.md` for exactly what is and is not
claimed about them.

`run_tracking_adapter_pipeline.py` — the orchestration script this
document's commands are drawn from — is **not** another trusted
verifier. It is an untrusted coordinator: every accept/reject decision
below comes from a real, separately-invoked subprocess (the adapter
verifier or one of the two R21 verifiers), never from the orchestration
script's own logic. See that script's own module docstring for the full
statement.

## Commit and toolchain versions

Captured from the actual run, in this repository's own working tree:

```text
git commit:  e67969f036fe6a9b06fd5a5e9bbf8c3f003c046c (e67969f)
Python:      3.12.3
pytest:      9.1.1
Coq/Rocq:    8.18.0
OCaml:       4.14.1 (ocamlopt)
```

Run the whole thing in one command:

```sh
make check-tracking-adapter
```

or directly:

```sh
python3 run_tracking_adapter_pipeline.py
```

## Example 1: `repairable` — a coherent transformation family

Snapshot: `examples/tracking_adapter/repairable_snapshot.json` — four
tracks, all reporting raw state `100`, with a COHERENT per-track
transformation offset (`t1: 0, t2: 1, t3: 3, t4: 2`, the same value
regardless of which edge references it).

```sh
$ python3 tracking_adapter_verifier.py examples/tracking_adapter/repairable_snapshot.json
ACCEPT: examples/tracking_adapter/repairable_snapshot.json

$ python3 tracking_adapter_certificate.py emit examples/tracking_adapter/repairable_snapshot.json --output cert.json
EMIT ACCEPT: wrote cert.json
```

Canonical `roc-input/v1` (embedded in the certificate as `roc_input`,
also tracked standalone as `repairable_roc_input.json`):

```json
{"schema": "roc-input/v1", "D": [["-1", "1", "0", "0"], ["0", "-1", "1", "0"], ["0", "0", "-1", "1"], ["-1", "0", "0", "1"]], "r": ["1", "2", "-1", "2"]}
```

```sh
$ python3 r21_certificate_emitter.py roc_input.json --certificate r21_cert.json
REPAIR: wrote r21_cert.json
```

Emitted R21 certificate:

```json
{"schema": "repair-or-separator/v1", "input_digest": "sha256:b6d1eb992e0b98950549bfc82313889d82883d83bc62668837222aa781c64ac2", "result": "repair", "repair": ["-2", "-1", "1", "0"]}
```

**Claims recorded for this fixture:**

- reconstructed `D = [[-1,1,0,0],[0,-1,1,0],[0,0,-1,1],[-1,0,0,1]]`, `r = (1,2,-1,2)`;
- R21's actual witness: `b = (-2,-1,1,0)`;
- the construction witness (chosen first, per design doc §13.1, before
  deriving `r` via coherent per-edge transforms): `b_constructed =
  (0,1,3,2)`;
- their difference, `b_constructed - b = (2,2,2,2) = 2*(1,1,1,1)`, lies
  in `ker(D)` (`rank(D) = 3`, so `ker(D)` is 1-dimensional, spanned by
  the all-ones vector — checked directly in `tests/test_tracking_
  adapter_metamorphic.py`, not assumed);
- both satisfy `Db = r` exactly — this is a genuine gauge freedom of the
  comparison-graph formulation (`examples/tracking_adapter/README.md`),
  not a discrepancy between construction and R21's output.

Both independent verifiers:

```sh
$ python3 r21_certificate_checker.py roc_input.json r21_cert.json
ACCEPT: r21_cert.json          # exit 0

$ ./roc-verify-ocaml roc_input.json r21_cert.json
ACCEPT: r21_cert.json          # exit 0
```

Complete chain:

```sh
$ python3 tracking_adapter_certificate.py verify-chain \
    examples/tracking_adapter/repairable_snapshot.json cert.json r21_cert.json
CHAIN ACCEPT
```

## Example 2: `obstructed` — an incoherent, edge-specific transformation family

Snapshot: `examples/tracking_adapter/obstructed_snapshot.json` — the
same four tracks and raw state `100`, but each track's transformation
offset now DIFFERS depending on which edge references it (e.g. track
`t2`'s offset is `1` under edge `e12` but `0` under edge `e23`).

```sh
$ python3 tracking_adapter_verifier.py examples/tracking_adapter/obstructed_snapshot.json
ACCEPT: examples/tracking_adapter/obstructed_snapshot.json

$ python3 tracking_adapter_certificate.py emit examples/tracking_adapter/obstructed_snapshot.json --output cert.json
EMIT ACCEPT: wrote cert.json
```

Canonical `roc-input/v1` — reproducing the repository's own canonical
four-cycle obstruction (`examples/four_cycle.json`,
`rocq/FourCycleObstruction.v`) bit-exactly, derived from evidence, not
copied in as a literal (also tracked standalone as
`obstructed_roc_input.json`):

```json
{"schema": "roc-input/v1", "D": [["-1", "1", "0", "0"], ["0", "-1", "1", "0"], ["0", "0", "-1", "1"], ["-1", "0", "0", "1"]], "r": ["1", "1", "1", "-2"]}
```

```sh
$ python3 r21_certificate_emitter.py roc_input.json --certificate r21_cert.json
SEPARATOR: wrote r21_cert.json
```

Emitted R21 certificate:

```json
{"schema": "repair-or-separator/v1", "input_digest": "sha256:3db7d90d805d5e8f20708609a395c479951dc1e4ab18901c363f9269ad5bb240", "result": "separator", "separator": ["1/5", "1/5", "1/5", "-1/5"]}
```

Note this `input_digest` is identical to `docs/R21_END_TO_END_
DEMONSTRATION.md`'s own four-cycle example — the same `(D, r)`,
independently re-derived here from tracking evidence rather than typed
in directly, digests identically.

**Claims recorded for this fixture:**

- reconstructed `r = (1,1,1,-2)`;
- `D^T y = 0` (the zero vector of length 4);
- `y . r = 1`, exactly;
- `y = (1/5, 1/5, 1/5, -1/5)`, matching R21/R24's own `y4` for this same
  four-cycle exactly (`rocq/R21CycleQuotientBridge.v`,
  `rocq/R24CertificateTransportExamples.v`);
- `rank(D^T) = 3`, so `ker(D^T)` is 1-dimensional — meaning the
  NORMALIZED separator above is not merely one member of an equivalence
  class, it is the *unique* separator satisfying `y.r = 1` for this
  system (checked directly, not assumed, in `tests/test_tracking_
  adapter_metamorphic.py`).

Both independent verifiers:

```sh
$ python3 r21_certificate_checker.py roc_input.json r21_cert.json
ACCEPT: r21_cert.json          # exit 0

$ ./roc-verify-ocaml roc_input.json r21_cert.json
ACCEPT: r21_cert.json          # exit 0
```

Complete chain:

```sh
$ python3 tracking_adapter_certificate.py verify-chain \
    examples/tracking_adapter/obstructed_snapshot.json cert.json r21_cert.json
CHAIN ACCEPT
```

## Example 3: Stone Soup track fusion — real sensor-derived evidence, not a hand-authored fixture

**Status update, superseding the closing section below as originally
written**: Examples 1 and 2 above are hand-authored fixtures. This
example runs the identical, unmodified chain on evidence produced by a
genuinely different source: a deterministic reconstruction of Stone
Soup's own two-radar track-fusion tutorial (`docs/examples/trackfusion/
track_fusion_example.py`, pinned at `stonesoup==1.9.1`), traced and
audited before implementation in
`docs/design/STONESOUP_TRACK_FUSION_EVALUATOR_SPEC.md`. See that
document for the full upstream-artefact audit, the state-projection and
covariance-boundary decisions, and — critically — §9's topology
argument, established *before* any evaluator code was written.

Stone Soup is an OPTIONAL evidence producer, never a dependency of the
exact adapter or R21 kernel: `tests/test_stonesoup_import_boundary.py`
proves this mechanically (AST scan plus a runtime `sys.modules` check),
and `tracking_adapter_stonesoup_trackfusion.py`/`tracking_adapter_
stonesoup_trackfusion_emitter.py` are the only two files in this example
that import it at all.

```text
Stone Soup (real installed APIs: RadarBearingRange, SingleTargetTracker,
Tracks2GaussianDetectionFeeder, ChernoffUpdater, PointProcessMultiTarget
Tracker) -- deterministic reconstruction
          |
          v
tracking_adapter_stonesoup_trackfusion.py: run_scenario()
    captures 2 local tracks (x, vx, y, vy + 4x4 covariance) immediately
    before Tracks2GaussianDetectionFeeder, and the fused track (reporting
    only)
          |
          v
tracking_adapter_stonesoup_trackfusion_emitter.py: build_snapshot(policy)
    projects state index 0 (x-position) into a tracking-adapter/v1
    snapshot; velocity + covariance retained as Detection-level
    provenance only
          |
          v
[ the same unmodified chain as Examples 1-2: independent verification,
  adapter certificate, real R21 emitter, both real R21 checkers,
  complete chain verification ]
```

Two declared transformation policies over the SAME captured Stone Soup
evidence:

```sh
$ python3 tracking_adapter_stonesoup_trackfusion_emitter.py \
    --output snapshot.json --policy natural
EMIT ACCEPT: wrote snapshot.json (policy=natural)

$ python3 tracking_adapter_verifier.py snapshot.json
ACCEPT: snapshot.json

$ python3 tracking_adapter_certificate.py emit snapshot.json --output cert.json
EMIT ACCEPT: wrote cert.json
```

Captured local track x-positions at the one shared evaluation timestamp
(`track:kf-1` and `track:kf-2`, seed `20260117`, `NUMBER_OF_STEPS = 5`):

```text
track:kf-1  x = 26.98039176055807
track:kf-2  x = 26.927482582803126
```

**`natural` policy** (identity transformation for both tracks — Stone
Soup's own Unscented Kalman filters already produce both tracks in one
common global frame, design doc §4):

```json
{"schema": "roc-input/v1", "D": [["-1", "1"]], "r": ["-52909/1000000"]}
```

```sh
$ python3 r21_certificate_emitter.py roc_input.json --certificate r21_cert.json
REPAIR: wrote r21_cert.json
```

```json
{"schema": "repair-or-separator/v1", "input_digest": "sha256:e6d3b9545ee213f7f4fb32f7c03d108daa08bbfa469d4a19f61ea41b5e239cda", "result": "repair", "repair": ["52909/1000000", "0"]}
```

**`artificial_perturbation` policy** (a clearly labelled, evaluator-
imposed offset of `10` added to `track:kf-2` only — testing
transformation HANDLING, never presented as an attempt to manufacture an
obstruction, design doc §9):

```json
{"schema": "roc-input/v1", "D": [["-1", "1"]], "r": ["9947091/1000000"]}
```

```sh
$ python3 r21_certificate_emitter.py roc_input.json --certificate r21_cert.json
REPAIR: wrote r21_cert.json
```

```json
{"schema": "repair-or-separator/v1", "input_digest": "sha256:0a624b744a847da1fe45feacb12bde2a563aedbca7c9299872c0c13b3198db18", "result": "repair", "repair": ["-9947091/1000000", "0"]}
```

Both independent verifiers accept both certificates, and the complete
chain verifies for both:

```sh
$ python3 r21_certificate_checker.py roc_input.json r21_cert.json
ACCEPT: r21_cert.json          # exit 0

$ ./roc-verify-ocaml roc_input.json r21_cert.json
ACCEPT: r21_cert.json          # exit 0

$ python3 tracking_adapter_certificate.py verify-chain \
    snapshot.json cert.json r21_cert.json
CHAIN ACCEPT
```

**Why both policies are necessarily repairable — checked directly, not
assumed:** the comparison topology here is two tracks, one edge, no
cycle: `D = (-1, 1)` is `1x2`, and `rank(D) = 1 = dim(C^1)` (confirmed
directly via `rational_linear_algebra.nullspace_over_Q` in `tests/
test_stonesoup_trackfusion.py`), so `D` is surjective onto the one-
dimensional residue space — no residue on this topology can ever be
obstructed, with or without the artificial perturbation. This is
`docs/design/STONESOUP_TRACK_FUSION_EVALUATOR_SPEC.md` §9's central,
checked-before-implementation finding: the empirical content of this
example is the actual residue value and repair witness a real Stone
Soup pipeline produces, not whether a witness exists at all. A cyclic,
obstruction-capable Stone Soup topology is future work, not attempted
here.

**Provenance**: the two radar detection streams are genuinely disjoint
`source_record` ancestors (confirmed in the design doc §7 by tracing
the fetched upstream source directly — each `RadarBearingRange`
generates its own, numerically distinct, detection at every timestep),
so `tracking_adapter_provenance.check_independence` returns PROVENANCE
ACCEPT for the one declared comparison, for both policies. This says
`comparison:kf1-kf2` shares no sensor-record ancestor — **it does not
say the two tracks are statistically independent estimators of the one
shared simulated target**, a distinction the design doc's own §7 states
explicitly as a non-claim, not an oversight.

**Stone Soup's own fused-track output**, captured for side-by-side
reporting only, never read by the adapter or fed into the verdict above:

```json
{"stonesoup_fused_track_position_x": "26.521051413273668"}
```

This is the STRUCTURAL result (do the declared local-track comparisons
repair coherently?), not a STATISTICAL one (is Stone Soup's own fusion
estimate itself accurate or well-calibrated?) — the two are not the same
claim, and this document does not make the second one.

Commands and captured values above were run against this repository's
own working tree at commit `4b73def`, Python 3.12.3, Stone Soup 1.9.1,
in a separate `.venv-stonesoup` environment (see `requirements-
stonesoup.txt`) — never committed, never part of the main project venv.
`tests/test_stonesoup_trackfusion_documentation_drift.py` re-runs this
exact pipeline and asserts the values above still hold, skipping (not
failing) when Stone Soup is not installed, matching every other Stone-
Soup-dependent test file in this repository.

## What this licenses saying, precisely

You can say: for a `tracking-adapter/v1` snapshot matching this
adapter's current scope (one target, four trackers, one timestamp,
exact rationals, the `additive_offset` transformation family), this
repository provides an independent verifier that reconstructs `(D, r)`
from scratch (sharing no semantic logic with the generator that
proposed it), a certificate binding that reconstruction to R21's own
input digest with per-value decimal-conversion attestations, and a
chain verifier that checks the whole thing end to end — including R21's
own two independently-implemented verifiers on the resulting linear
system.

**You can now also say**: this repository has run one real, deterministic,
upstream-derived Stone Soup track-fusion pipeline (Example 3 above)
through the exact same unmodified certificate chain, on genuinely
captured local-tracker evidence (not hand-typed literals), and
independently confirmed the repair witness in both a natural and a
labelled artificially-perturbed transformation policy. Velocity and
covariance survive as digest-bound provenance without ever entering
`(D, r)`.

**You still cannot say**: that this specific two-track topology
demonstrates, or could ever demonstrate, an obstruction — `docs/design/
STONESOUP_TRACK_FUSION_EVALUATOR_SPEC.md` §9 shows directly it cannot,
for any residue value. That Stone Soup's own Chernoff/PHD fusion
output, or its statistical calibration, has been validated by anything
here — Example 3's fused-track value is reported, never verified. That
a `PROVENANCE ACCEPT` verdict means the two tracks are statistically
independent estimators of one shared physical target — it means only
that their declared comparison shares no sensor-record ancestor. Nor,
more generally, can you say this from raw tracking data or a real
(non-simulated) sensor feed in general: the verified boundary begins at
an already-encoded canonical `tracking-adapter/v1` snapshot, not at
whatever produced it, and Example 3's own evidence, while genuinely
Stone-Soup-derived, remains a deterministic, noise-suppressed,
clutter-free simulation, not a live sensor feed.
