# Tracking Adapter End-to-End Demonstration: Canonical Snapshot to Independently Checked Verdict

**Status (2026-07-16): canonical reference example.** Every command and
output below was actually run against this repository's own tracked
fixtures (`examples/tracking_adapter/`), not reconstructed from memory or
hand-edited afterward. `tests/test_tracking_adapter_documentation_drift
.py` re-runs the same pipeline and asserts the commands, filenames,
schema versions, and witness values below still hold — this document
cannot silently drift from what the repository actually does without
that test failing.

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

You cannot say this from raw tracking data, a real sensor feed, or
Stone Soup output. The verified boundary begins at an already-encoded
canonical `tracking-adapter/v1` snapshot, not at whatever produced it.
Whether Stone Soup (or any other evidence source) populates that
snapshot correctly is a separate verification task, out of scope for
this demonstration — see `docs/design/TRACKING_EVIDENCE_TO_RATIONAL
_ADAPTER_SPEC.md` §18 for what that later integration is and is not
expected to add.
