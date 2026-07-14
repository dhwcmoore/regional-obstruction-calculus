# R21 End-to-End Demonstration: Canonical Rational Input to Independently Checked Verdict

**Status (2026-07-14): canonical reference example.** Every command and
output below was actually run, from a fresh `git clone` of this
repository at the commit named below, not reconstructed from memory or
hand-edited afterward. `tests/test_r21_demonstration.py` re-runs the same
two pipelines and asserts the certificate contents, digests, and verdicts
below still hold — this document cannot silently drift from what the
repository actually does without that test failing.

## Scope of what this demonstrates

This shows the complete chain for **canonical finite rational matrix
input** `(D, r)`:

```text
canonical rational input (D, r)
          |
          v
Rocq function with proved soundness (compute_repair_or_separator)
          |
          v
official Rocq-to-OCaml extraction (rocq/ExtractR21.v, make extract-r21)
          |
          v
thin rational + certificate adapter (ocaml/r21_extracted_solve.ml)
          |
          v
repair-or-separator/v1 certificate
          +-------------------------+
          v                         v
   Python verifier            OCaml verifier
   (r21_certificate_checker.py)  (roc-verify-ocaml)
          +-------------------------+
                      |
                      v
            fail-closed accepted verdict
```

It does **not** demonstrate, and this repository does not claim, that any
real-world domain problem (sensor data, GIS files, accounting records,
policy documents, ...) has been verified to correctly compile into
`(D, r)` in the first place. That translation step — a domain adapter —
is separate, out of scope here, and would need its own verification per
domain. See `docs/design/R21_CERTIFICATE_TCB.md` and `docs/design/
R21_EXTRACTION_TCB.md` for the complete trusted-computing-base account
this demonstration is an instance of, not a replacement for.

## Commit and toolchain versions

Captured from the actual run, in a clean clone of this repository:

```text
git commit:  b17ff069435709de1558e25b7abfa114e84cbac0 (b17ff06)
Python:      3.12.3
pytest:      9.1.1
Coq/Rocq:    8.18.0
OCaml:       4.14.1 (ocamlopt)
zarith:      1.14 (opam; 1.13 via apt libzarith-ocaml-dev)
yojson:      3.0.0 (opam; apt libyojson-ocaml-dev ships no META version field)
sha:         v1.15.4
```

Build commands, in order (see `REPRODUCIBILITY.md` for full setup):

```sh
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
eval $(opam env)   # or: apt-get install ocaml-findlib libzarith-ocaml-dev libyojson-ocaml-dev libsha-ocaml-dev
make extract-r21          # regenerates ocaml/r21_extracted.ml/.mli fresh (never committed)
make check-r21-ocaml      # compiles roc-verify-ocaml
make check-r21-extraction # compiles roc-solve-extracted (depends on extract-r21's output)
```

## Example 1: a repairable system

Input (`roc-input/v1`):

```json
{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5"]}
```

Run the Rocq-extracted generator:

```sh
$ ./roc-solve-extracted input.json --certificate cert.json
REPAIR: wrote cert.json
```

Emitted certificate (`repair-or-separator/v1`):

```json
{"schema": "repair-or-separator/v1", "input_digest": "sha256:6ed797d190fcb066aece62d0a70065c8ea46f812b4e8e819cbdd8433a4f08b62", "result": "repair", "repair": ["3","5"]}
```

Both independent verifiers, run separately:

```sh
$ python r21_certificate_checker.py input.json cert.json
ACCEPT: cert.json          # exit 0

$ ./roc-verify-ocaml input.json cert.json
ACCEPT: cert.json          # exit 0
```

**Equation independently checked by both verifiers:** `D b = r`, exactly,
over exact rationals — `[[1,0],[0,1]] @ (3,5) = (3,5) = r`. Trivial by
construction here (the identity matrix), included as the simplest
possible instance of the `RawRepair` branch.

## Example 2: R1's own four-cycle — a genuinely obstructed system

Input (the repository's own central example, `examples/four_cycle.json`'s
`coboundary_0`/`residue`, encoded as `roc-input/v1`):

```json
{"schema": "roc-input/v1", "D": [["-1","1","0","0"],["0","-1","1","0"],["0","0","-1","1"],["-1","0","0","1"]], "r": ["1","1","1","-2"]}
```

Run the Rocq-extracted generator:

```sh
$ ./roc-solve-extracted input.json --certificate cert.json
SEPARATOR: wrote cert.json
```

Emitted certificate:

```json
{"schema": "repair-or-separator/v1", "input_digest": "sha256:3db7d90d805d5e8f20708609a395c479951dc1e4ab18901c363f9269ad5bb240", "result": "separator", "separator": ["1/5","1/5","1/5","-1/5"]}
```

This is R1's own canonical witness, produced by the actual Rocq-extracted
computation, not asserted: `z = (-1,-1,-1,1)` with pairing `c = -5`
(`FourCycleObstruction.v`'s own values), normalised to `-1/5 z =
(1/5,1/5,1/5,-1/5)` — matching README.md/STATUS.md's independently
recorded statement of this fact exactly.

Both independent verifiers:

```sh
$ python r21_certificate_checker.py input.json cert.json
ACCEPT: cert.json          # exit 0

$ ./roc-verify-ocaml input.json cert.json
ACCEPT: cert.json          # exit 0
```

**Equations independently checked by both verifiers:**
`D^T y = 0` (the zero vector of length 4) and `y . r = 1`, exactly, over
exact rationals — confirming `r` is *not* in the image of `D` (not
repairable), and exhibiting the specific linear functional that proves
it, rather than merely asserting non-repairability.

## Digest agreement, independently computed

The `input_digest` above was computed twice, independently — once by
each verifier's own canonicalisation code, over the same `(D, r)` — and
matched exactly, byte for byte:

```sh
$ ./roc-verify-ocaml --digest input.json
sha256:3db7d90d805d5e8f20708609a395c479951dc1e4ab18901c363f9269ad5bb240

$ python -c "from r21_certificate_format import canonical_input_digest, parse_matrix, parse_vector; \
             import json; d = json.load(open('input.json')); \
             print(canonical_input_digest(parse_matrix(d['D']), parse_vector(d['r'])))"
sha256:3db7d90d805d5e8f20708609a395c479951dc1e4ab18901c363f9269ad5bb240
```

## What this licenses saying, precisely

You can say: for canonical finite rational systems `D b = r`, this
repository provides a proof-derived repair-or-separator generator,
extracted from the Rocq function whose returned witnesses are formally
proved sound, and every emitted certificate must independently pass two
separately implemented exact-arithmetic verifiers — sharing no code with
each other except a published schema and a small OCaml-side
canonicalisation module (see `docs/design/R21_EXTRACTION_TCB.md`'s "A
nuance the independence claim needs stated precisely" for the exact,
narrower relationship between the OCaml verifier and the extracted
generator's own OCaml adapter) — before an accepted verdict is produced.

You cannot say this from raw domain data. The verified boundary begins at
an already-encoded canonical rational `(D, r)`, not at a sensor feed, a
GIS file, an accounting ledger, or any other domain representation. A
domain adapter proving that translation correct is a separate,
per-domain verification task this demonstration does not attempt.
