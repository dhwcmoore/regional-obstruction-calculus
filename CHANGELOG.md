# Changelog

Tags refer to milestones in the admissible-refinement-persistence work
(the paper's "Admissible refinement persistence" section) and, from R17
onward, in the presentation-invariance and quotient-semantics work built
on top of it. Scope discipline kept throughout: A1-A4 alone proves
persistence for a single refinement, not arbitrary refinement invariance;
R17-R20 later prove verdict-level invariance for the descent-safe,
reflecting common-subdivision fragment specifically, not full
presentation invariance through arbitrary or topology-changing
refinement. See the "Presentation fidelity and quotient semantics"
checkpoint below and `docs/theory/THEOREM_CONCORDANCE.md` for the exact
current boundary.

## Unreleased

### Meridian applied layer: tracking-evidence-to-rational adapter, and Stone Soup integration

Not part of the numbered R1-R24 ladder — an applied layer connecting
R21's exact rational repair-or-separator decision to multi-sensor
tracking evidence, per the user's own Meridian priority order (this
work was chosen over R28 as "the strategically stronger sequence
because it directly advances the Meridian integration path").

- `docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md`
  (`09824ba`): the governing design. `Db = r` is equivalent to
  simultaneous repair of declared pairwise track comparisons only if
  the correction is declared per EDGE, not per tracker — the key design
  problem solved here, since naively differencing already-known global
  track states makes `r` a coboundary by construction, so no fixture
  built that way could ever be genuinely obstructed. A real sign bug
  (additive vs. subtractive correction convention) was found and fixed
  during review, caught only by hand-computing concrete numbers.
- Ten-step implementation, each its own commit, `make check-all` green
  throughout: `tracking_adapter_format.py` (closed `tracking-adapter/v1`
  schema, `7003229`), `tracking_adapter_canon.py` (two independently-
  implemented decimal-to-rational rounding routes, cross-checked,
  `a77acfa`), `tracking_adapter_generator.py` (`(D, r)` derivation,
  `2624255`), `tracking_adapter_verifier.py` (the architecturally
  critical independent reconstruction, sharing no semantic code with
  the generator — proved by an AST-import scan and a monkeypatch test,
  `b19a20e`), `tracking_adapter_certificate.py` (`tracking-adapter-
  certificate/v1`, per-value decimal-conversion attestations,
  `verify_chain`, `4869983`), a tracked repairable/obstructed fixture
  corpus (`examples/tracking_adapter/`, `e9ed3c3` — surfaced a genuine
  gauge freedom: R21's deterministic repair witness for the coherent
  fixture, `(-2,-1,1,0)`, differs from the `(0,1,3,2)` used to
  construct it by a multiple of `ker(D)`'s all-ones vector, not a bug),
  52 adversarial-rejection tests (`12ca7d4`), 12 metamorphic properties
  including direct `rank(D)`/`rank(D^T)` checks (`e67969f`), and
  `run_tracking_adapter_pipeline.py` plus `docs/TRACKING_ADAPTER_END_
  TO_END_DEMONSTRATION.md` with its own drift test (`1b8100d`).
- Stone Soup integration (step 10, sub-steps 10A-10F, each its own
  commit): Stone Soup (`stonesoup==1.9.1`, pinned only in
  `requirements-stonesoup.txt`) supplies an OPTIONAL genuine tracking-
  evidence source on top of the same, unmodified adapter boundary —
  mechanically proved never a dependency of the exact adapter or R21
  kernel by `tests/test_stonesoup_import_boundary.py` (`3a8e859`, 10A).
  A minimal, deterministic four-tracker fixture using genuine installed
  Stone Soup objects (`State`/`LinearGaussian`/`Detection`/`Track`, not
  reimplementations) demonstrates both a repairable (coherent
  transformation family, `84c030c`, 10B) and an obstructed (incoherent,
  edge-specific family, independently deriving the repository's own
  canonical `r=(1,1,1,-2)`, `370125d`, 10C) verdict from identical
  underlying evidence — the obstruction comes from the declared
  transformation policy, not from Stone Soup itself. A provenance/data-
  incest layer (`tracking_adapter_provenance.py`, `05b2208`, 10D)
  checks evidentiary admissibility via an independently-computed
  ancestry-graph transitive closure, establishing that numerical
  coherence does not establish evidential independence — R21 is never
  used to detect data incest.
- A bounded, pre-implementation design audit
  (`docs/design/STONESOUP_TRACK_FUSION_EVALUATOR_SPEC.md`) traced Stone
  Soup's own two-radar track-fusion tutorial directly against the
  fetched upstream source at the pinned tag, finding a genuine upstream
  determinism gap (`np.random.seed(...)` does not seed the separately-
  instantiated `np.random.default_rng()` the tutorial's own clutter
  model uses) and establishing, BEFORE any evaluator code was written,
  that the two-track/one-edge comparison topology gives
  `rank(D) = 1 = dim(C^1)` — `D` is surjective, so this topology is
  necessarily repairable for any residue, with or without an artificial
  transformation perturbation. `tracking_adapter_stonesoup_trackfusion.
  py` (10E.1, `d7ab75c`) reproduces that tutorial deterministically
  through genuine installed APIs (`RadarBearingRange`,
  `SingleTargetTracker`, `Tracks2GaussianDetectionFeeder`,
  `ChernoffUpdater`), confirmed byte-identical across fresh subprocess
  runs. `tracking_adapter_stonesoup_trackfusion_emitter.py` (10E.2,
  `4b73def`) projects the captured local tracks into a real `tracking-
  adapter/v1` snapshot (x-position only enters `(D, r)`; velocity and
  covariance survive as digest-bound provenance) and runs it through
  the complete, unmodified verification chain for both the `natural`
  and `artificial_perturbation` policies — confirmed `rank(D) = 1`
  directly via `rational_linear_algebra.nullspace_over_Q`, not merely
  cited from the design doc.
- `docs/TRACKING_ADAPTER_END_TO_END_DEMONSTRATION.md`'s Example 3
  (10F) captures a real, fresh run of the Stone Soup pipeline end to
  end, kept honest against drift by `tests/test_stonesoup_trackfusion_
  documentation_drift.py`.
- No tag has been created for this work; per this repository's own
  discipline, an annotated release tag should point at the commit
  including the final demonstration/evidence artefacts, not an earlier
  one.

### R24: certificate transport under presentation change

- Added `rocq/InvertiblePresentation.v`, `rocq/CertificateTransport.v`,
  `rocq/R24CertificateTransportExamples.v`: certified invertible linear
  presentation changes (`D' = B D A^{-1}`, `r' = B r`, explicit
  two-sided-inverse witnesses via `InvertibleMatrix`, no constructive
  matrix inversion) transport repair witnesses, separator witnesses, and
  separator pairings exactly, in both directions, and therefore
  transport the repairable-versus-obstructed VERDICT itself:
  `r in im(D) <-> r' in im(D')` (`repairable_iff_transport_repairable`)
  and its negation (`nonrepairable_iff_transport_nonrepairable`), plus
  the annihilation-side iff
  (`separator_annihilates_iff_transport_annihilates`) and exact pairing
  preservation both ways (`transport_pairing`/`transport_pairing_reverse`).
- Preceded by an untracked spike (per this repository's own established
  discipline: scope first, spike untracked, confirm the architecture
  works before writing tracked files) that answered the open question in
  `docs/design/CERTIFICATE_TRANSPORT_SPEC.md` §5: the generic theorem,
  over arbitrary certified-invertible `A`/`B`, succeeded cleanly with no
  need for a large new matrix-algebra library or a split into an
  elementary-operations-only milestone plus a follow-up. Almost the
  entire development is built from vector-action lemmas (matrix
  multiplication acts associatively on vectors; transpose reverses
  multiplication under vector action; a two-sided inverse undoes its own
  action and its transpose's action) rather than full matrix Leibniz
  identities -- the sole exception, `transpose_qc_involutive` (double
  transpose), was the only one needed anywhere.
- `PresentationEquivalence` bundles a transformed system with the
  `InvertibleMatrix` witnesses used to reach it, so later results (R23
  signature transport, compositional transport, Meridian-facing
  presentation changes) can depend on one proposition instead of
  repeatedly unfolding `transform_operator`/`transform_residue`.
- Instantiated on a coordinate swap, a nonzero rational scaling, an
  elementary shear, and R1's own four-cycle obstruction under a
  residue-space swap, each checked both directly and by applying the
  generic theorems. Recorded a genuine implementation wrinkle, not a
  soundness bug: exact-rational cancellation (several `1/5` terms
  summing to `0`) can reach the same canonical `Qc` value via two
  computation paths whose `canon` proof components differ syntactically
  even though the rational values agree (no default proof irrelevance
  for `Prop` in Coq's kernel) -- `Qc_is_canon`, not a custom
  extensionality axiom, is the correct repair.
- Explicitly out of scope, stated in every new file's header and in
  `docs/design/CERTIFICATE_TRANSPORT_SPEC.md` §4: translations, affine
  maps, projections, cropping, resolution loss, dimension changes,
  nonlinear transformations, approximate numerical equivalence, and
  arbitrary refinement/common-subdivision.
- Added `InvertiblePresentation`, `CertificateTransport`, and
  `R24CertificateTransportExamples` to `ROCQ_MODULES` (37 modules total,
  36 proof modules plus `ExtractR21`), `coqchk`-clean, zero
  project-added axioms across the full dependency closure.
- Also backfills R22's own public documentation, never added when R22
  was committed (`60eb501`): README.md, STATUS.md, RESULTS.md, and
  PROJECT_MAP.md previously had no R22 entry at all, and the Rocq
  module count had silently drifted (27 in one file, 28 in another,
  neither counting R22's seven modules). Both gaps are now fixed, and
  `tests/test_documentation_module_count.py` checks that the module
  count and both R22's and R24's presence in the docs stay in sync
  going forward -- a real drift, not a hypothetical one, motivated this
  test.

## v0.20-r21-front-to-back

### R21 release-integrity hardening, post-review

An external review of the pushed `v0.20-r21-front-to-back` tag found
several confirmed defects, independently reproduced before being fixed
(not taken on faith):

- **Canonicalisation was not actually enforced.** `"03"`, `"6/2"`,
  `"3/1"`, `"02/10"`, `"1/05"`, and `"-0"` were all accepted as exact
  rational values, despite each being a non-canonical representation the
  schema's own name and documentation already claimed was rejected. Both
  `r21_certificate_format.parse_rational` (Python) and `ocaml/r21_format.
  ml`'s `parse_rational` (OCaml) now recompute the canonical string for
  the parsed value and reject if it does not equal the input exactly.
- **Python's rational regex accepted Unicode digits.** `\d` is
  Unicode-aware and matched Arabic-indic and fullwidth digit characters
  (`"١/٢"`, `"１２/３"`) that the OCaml parser's always-ASCII grammar
  rejected -- a genuine cross-language disagreement. The regex now uses
  `[0-9]` explicitly.
- **The published `MAX_RATIONAL_CHARS = 100_000` limit was fiction on the
  Python side.** CPython's own `int(str)` conversion refuses strings over
  `sys.get_int_max_str_digits()` (4,300 by default, a CVE-2020-10735
  mitigation), so Python silently rejected legitimate values the OCaml
  side (Zarith, no comparable ceiling) accepted -- confirmed directly: a
  5,001-digit rational was accepted by `roc-verify-ocaml` and rejected by
  `r21_certificate_checker.py`. Lowered to `MAX_RATIONAL_CHARS = 1_000` on
  both sides -- comfortably under 4,300, needing no interpreter
  reconfiguration, and already far more digits than this repository's own
  examples use.
- **No limit on total matrix entries or raw file size.** `MAX_DIMENSION`
  (10,000) bounds rows and columns individually but not their product (a
  nominal 10,000 x 10,000 matrix is 100 million entries). Added
  `MAX_TOTAL_ENTRIES` (1,000,000) and `MAX_INPUT_BYTES` (10 MB, checked
  before the file is even opened for JSON parsing) to both `r21_
  certificate_format.py` and `ocaml/r21_format.ml`.
- **19 `subprocess.run` calls across the R21 test files had no
  `timeout=`.** A hung checker or generator could hang the suite
  indefinitely instead of failing the test. All 19 now pass
  `timeout=30`.
- **CI never built or exercised the R21 OCaml/extraction binaries.** The
  Python CI job ran `make check-python` alone, under which 105-123 R21
  tests skip gracefully (by design, so a plain `pytest` without an
  OCaml/opam-or-apt toolchain still passes) -- meaning CI could go green
  while that coverage silently never ran. Added a fifth CI job (`r21`)
  that apt-installs the same packages this repository's own Dockerfile
  uses, builds both binaries, and explicitly fails if the pytest run
  reports any skip.
- **Module-count and test-count drift across README/STATUS/
  REPRODUCIBILITY/CHANGELOG.** "27 proof modules plus ExtractR21" (= 28)
  was an off-by-one -- `rocq/*.v` has 27 files total (26 proof modules
  plus `ExtractR21.v`), not 28. Test counts had also drifted as new R21
  test files were added without updating every count claim
  (`REPRODUCIBILITY.md` still said 212). Corrected throughout; current
  counts are 254 passed (no R21 OCaml/extraction toolchain) or 377 passed,
  0 skipped (both binaries built).
- Pinned `pytest==9.1.1` in `requirements.txt` (previously unpinned).
- Added `version: v0.20-r21-front-to-back` to `CITATION.cff`.

None of this changes the mathematical-soundness TCB (`docs/design/
R21_CERTIFICATE_TCB.md`'s own layered account already scoped
canonicalisation/resource-limit defects to provenance-binding/DoS
resistance, not soundness) -- every fix here is either a stricter input
gate (reject more, never accept more) or process/documentation hygiene.
See that document's own "Hardening" section for the corrected, detailed
account.

### R21 end-to-end demonstration and independence nuance

- Added `docs/R21_END_TO_END_DEMONSTRATION.md`: a canonical reference
  example using real, actually-run commands and captured output from a
  fresh clone -- not reconstructed from memory. Covers one repairable
  system and R1's own four-cycle obstruction, from `roc-input/v1` through
  `make extract-r21` and `roc-solve-extracted` to the emitted
  `repair-or-separator/v1` certificate, ACCEPT from both independent
  verifiers, the exact equations checked, byte-identical independently
  computed digests, and the exact git commit / Rocq / OCaml / Python /
  library versions used. States explicitly that the verified boundary
  begins at canonical rational `(D, r)`, not raw domain data.
- Added `tests/test_r21_demonstration.py` (3 tests) so the demonstration
  document cannot silently drift from what the repository actually does:
  re-runs both captured pipelines and asserts the certificate contents,
  digests, and verdicts still match what the document records verbatim.
- Documented, in both `docs/design/R21_CERTIFICATE_TCB.md` and
  `docs/design/R21_EXTRACTION_TCB.md`, a precise independence nuance:
  the extracted generator's OCaml adapter (`ocaml/r21_extracted_
  solve.ml`) and the OCaml verifier (`ocaml/r21_verifier.ml`) share
  `ocaml/r21_format.ml` (schema/canonicalisation code, not the
  arithmetic check itself), so they are not independent with respect to
  that code -- only the Python verifier's independence from either
  generator is unconditional. Does not reopen the mathematical-soundness
  TCB (the arithmetic check never depends on `r21_format.ml`'s output),
  but the exact relationship was not stated anywhere until now.

### R21 Rocq extraction: a proof-derived generator, still gated by both checkers

- Extracted `compute_repair_or_separator` -- the function `compute_
  repair_or_separator_correct` proves sound against the original `D`, `r`
  -- from Rocq to OCaml via a new tracked entry point,
  `rocq/ExtractR21.v`, using only Coq 8.18.0's own official extraction
  realisation files (`ExtrOcamlBasic`, `ExtrOcamlZBigInt`,
  `ExtrOcamlNatBigInt`) -- zero project-defined `Extract Constant`/
  `Extract Inductive` directives. `make extract-r21` regenerates
  `ocaml/r21_extracted.ml`/`.mli` fresh every time; neither is committed
  (the same discipline already applied to `.vo`/`.cmi`/`.cmx`).
- Preceded by an untracked bounded extraction spike (not committed):
  extracted the definition exactly as it stood, with no redesign, and
  inspected the output by hand -- no `failwith`/`Obj.magic`/axiom stubs;
  confirmed `Z`/`positive`/`nat` extract to Zarith's own `Z.t` (a
  same-type compatibility shim, not a wrapper); ran it on the
  repository's own four-cycle data and reproduced R1's exact canonical
  witness; ran it on a 30-digit-numerator case, cross-checked
  independently against Python's `Fraction`; every resulting certificate
  was accepted by both existing checkers. The tracked `ExtractR21.v`
  reproduces this spike's output byte-for-byte.
- Added `ocaml/r21_extracted_solve.ml` (`roc-solve-extracted`), a thin
  adapter: converts Coq's unreduced `Qmake { Qnum ; Qden }` extraction
  representation to `Zarith.Q` (one `Q.make` call each way -- the single
  representation adapter this pipeline needed, predicted before the
  spike was run and confirmed by it), runs the extracted computation,
  and emits the same `repair-or-separator/v1` certificate the
  hand-written generator does.
- Factored `ocaml/r21_verifier.ml`'s schema/canonicalisation/JSON/digest
  code out into a new shared module, `ocaml/r21_format.ml`, reused by
  both the checker and the new adapter -- mirroring `r21_certificate_
  format.py`'s existing role on the Python side. No behavioural change;
  confirmed by rerunning the full existing R21 test suite unchanged
  after the refactor.
- Added `rocq/ExtractR21.v` to `ROCQ_MODULES` (compiled and `coqchk`-ed
  alongside the 26 proof modules, despite having no `Theorem`/`Lemma` of
  its own) so `check-rocq-inventory`'s exact-match discipline is not
  carved out for it. The active Rocq chain is now 27 modules (26 proof
  modules plus ExtractR21) -- an earlier revision of this entry said 28,
  an off-by-one that also propagated into README.md/STATUS.md/
  REPRODUCIBILITY.md before being caught and corrected.
- Added `make extract-r21` and `make check-r21-extraction` (compiles
  `roc-solve-extracted`); `check-all` now runs
  `check-r21-ocaml` -> `check-r21-extraction` -> `check-python`, so the
  R21 cross-language, canonical-vector, and extracted-generator test
  suites all find their binaries already built rather than skipping.
- Added `tests/test_r21_extracted_generator.py` (48 tests): every
  certificate the extracted generator produces is judged by whether
  **both existing checkers** independently accept it -- never by the
  generator's own opinion. Covers repairable, separator, R1's four-cycle
  (exact witness match), zero-/minimal-dimensional boundaries,
  rectangular matrices, a case requiring a row swap, a case requiring
  non-trivial rational pivot normalisation, negative coefficients,
  30-digit exact numerators, and 30 deterministically-seeded random
  small systems (`r` defined as `D@b` via a from-scratch reference
  computation, not either checker's own code). Two deliberately
  different comparisons against the hand-written Python generator:
  witness-identity parity for determinate systems (both algorithms use
  the same pivot-selection order, so they coincide), vs. semantic
  equivalence only (both accepted, witnesses not required to match) for
  an underdetermined system with more than one valid repair.
- `r21_repair_or_separator.py` (the hand-written generator) is
  unchanged and retained -- as a reference implementation, the parity
  suite's differential-testing partner, an independent source of test
  cases, and a diagnostic fallback needing only Python.
- Documented two installation paths for `zarith`/`yojson`/`sha` in
  `REPRODUCIBILITY.md` (apt, matching this repository's "apt not opam"
  policy; opam, for developers without root) -- unchanged by this phase,
  since extraction needs no library beyond what the second checker
  already required (`ExtrOcamlZBigInt`/`ExtrOcamlNatBigInt` are part of
  the Coq distribution itself).
- Added `docs/design/R21_EXTRACTION_TCB.md`: the exact Rocq definition
  extracted, the theorem proving it sound, every extraction directive
  used (itemised, all from Coq's own official files), the representation
  adapter, confirmation the generated OCaml is never committed, and what
  this phase does and does not establish -- explicitly, that both
  checkers still gate every certificate from either generator, and that
  extraction does not shrink the mathematical-soundness TCB the way the
  second checker did.

### R21 second checker: OCaml, cross-language agreement, canonical digest vectors

- Added `ocaml/r21_verifier.ml` (`roc-verify-ocaml`), a second,
  independently written checker for `repair-or-separator/v1`
  certificates. Shares with the Python checker only the published
  specification -- schema, canonicalisation rule, resource limits, test
  fixtures -- and no code: independent strict rational parsing, JSON
  handling (`Yojson.Safe`, with its own duplicate-key detection),
  canonicalisation/digest (`Sha256`), and matrix/vector arithmetic, all
  over `Zarith.Q` (GMP-backed, so an untrusted numerator/denominator
  cannot silently overflow a machine int) rather than Python's
  `Fraction`. Not a generator, not a Rocq extraction.
- Fixed `r21_certificate_format.parse_rational` to explicitly raise
  `ValueError` on a zero denominator (e.g. `"3/0"`) instead of leaving
  `ZeroDivisionError` to surface from `Fraction`'s own constructor --
  still caught fail-closed either way, but now caught by the same
  specific handlers as every other malformed-rational case, and now has
  its own dedicated test.
- Added `tests/test_r21_cross_language_agreement.py`: a 23-case corpus
  spanning hand-authored fixtures (simple repair, simple separator, R1's
  own four-cycle separator, zero- and minimal-dimensional boundary
  cases, each with `Db=r` or `D^Ty=0,y.r=1` checked by hand in a
  comment), constructed-valid certificates (`D` and the witness chosen
  first, `r` defined from them via a from-scratch reference computation,
  not either checker's own code), and malformed/tampered/resource-limit
  cases (schema, duplicate keys, unknown fields, changed matrix/residue/
  witness/digest, oversized rationals/dimensions, ragged matrices, shape
  mismatches, zero denominators, non-canonical rationals, truncated
  JSON) -- every case run through both checkers and required to agree,
  69 tests total (23 x Python-verdict, OCaml-verdict, agreement).
- Added `tests/test_r21_canonical_vectors.py` and `tests/r21_canonical_
  vectors.json`: 8 frozen canonical-digest vectors (negative rationals,
  zero normalisation, denominators, row order, column order, empty
  collections, multi-digit dimensions, large integers) generated with a
  from-scratch `Fraction`/`hashlib` script, never through `canonical_
  input_digest` itself -- both checkers are tested against this fixed
  third value, not against each other's live output, so a mistake shared
  by both implementations of the canonicalisation rule would still be
  caught.
- Added `make check-r21-ocaml` (builds `roc-verify-ocaml`) and reordered
  `check-all` to run it before `check-python`, so the cross-language and
  canonical-vector suites exercise the OCaml checker instead of skipping
  during a full `make check-all` run; a plain `make check-python`/
  `pytest` without the OCaml/opam-or-apt toolchain still passes, with
  those cases skipped rather than failed.
- Documented two installation paths in `REPRODUCIBILITY.md`: apt
  (`libzarith-ocaml-dev`, `libyojson-ocaml-dev`, `libsha-ocaml-dev`,
  matching this repository's existing "apt, not opam" policy) and opam
  (for developers without root). Updated `Dockerfile` to install the
  three apt packages and added them to its pinned-version check.
- Rewrote `docs/design/R21_CERTIFICATE_TCB.md` around a four-layer
  picture -- mathematical specification (Rocq), independent runtime
  checkers (Python, OCaml), shared specification surface (schema,
  canonicalisation, limits, test vectors), and still-untrusted
  components (generator, domain adapter, runtimes, compilers) -- and
  states explicitly what cross-language agreement does and does not
  establish: it reduces implementation risk, but does not prove either
  checker correct, and does not by itself validate the shared
  specification layer, which only the Rocq theorem and the
  independently-generated digest vectors give any check at all.

### R21 certificate pipeline: schema, untrusted generator, independent checker

- Added the `repair-or-separator/v1` certificate schema
  (`r21_certificate_format.py`): binds a certificate to the exact `(D, r)`
  it certifies via a canonical SHA-256 `input_digest`, so a certificate
  valid for one problem cannot be attached to another.
- Added `r21_repair_or_separator.py`, a hand-written (not extracted)
  Python mirror of R21's augmented-elimination algorithm on
  `[D | r | I_m]` (Route C2 of `docs/design/
  EXACT_RATIONAL_SEPARATION_SPEC.md`) -- deliberately treated as
  untrusted; see the module's own docstring for why a bug here can only
  produce a certificate the checker then rejects, never one it wrongly
  accepts.
- Added `r21_certificate_emitter.py` (`roc-solve`) and
  `r21_certificate_checker.py` (`roc-verify`) as a genuine two-process
  command pair: the checker does not import the generator or the
  emitter, independently recomputes `Db = r` or `D^Ty = 0 /\ y.r = 1`
  from the certificate's own claimed witness using
  `rational_linear_algebra.py`'s already-audited primitives, and is
  fail-closed -- every rejection path is an explicit `.reject(...)`,
  never a silent pass-through accept.
- 31 tests (`tests/test_r21_certificates.py`): valid certificates for both
  outcomes (including the four-cycle separator recovering R1's own
  normalised witness `(1/5,1/5,1/5,-1/5)` through the full CLI
  roundtrip), malformed certificates, tampered certificates, a
  certificate genuinely valid for one problem rejected against another,
  determinism (byte-identical repeated emission, digest stability), and
  hardening (closed schema, duplicate JSON keys, oversized rationals and
  dimensions, ragged matrices, mismatched residue length).
- Hardening added to `r21_certificate_format.py` after review: a closed
  certificate/input schema (`validate_closed_keys`), rejection of
  duplicate JSON keys at any level (`strict_json_load`), resource limits
  on rational-string length and matrix/vector dimension
  (`MAX_RATIONAL_CHARS`, `MAX_DIMENSION`), rectangularity and
  `D`/`r`-shape validation at input time, and a top-level `try`/`except`
  in `check_certificate` so an unexpected exception is a rejection, never
  a crash. Fail-closed mathematical checking is not the same as
  resistance to a certificate or input file crafted to exhaust memory or
  CPU before either equation is evaluated.
- Corrected the digest's trusted-computing-base claim: a defect in
  `canonical_input_digest` cannot bypass the independent mathematical
  checks (mathematical-soundness TCB), but it could weaken the claimed
  identity binding between a certificate and its input
  (provenance-binding TCB) -- these are two different claims, not one.
- See `docs/design/R21_CERTIFICATE_TCB.md` for what this closes and what
  it does not: the generator is still a hand-written mirror of the Rocq
  algorithm, not an extraction of it.

### Exact rational repair-or-separator

- Added R21, `rocq/ExactRationalRepairOrSeparator.v`: a general
  constructive exact alternative for any rational system `D b = r`
  (`D`: `m x n`, `r`: length `m`) --
  `(exists b, D b = r) \/ (exists y, D^T y = 0 /\ dot y r == 1)` --
  decided by verified exact-rational Gauss-Jordan elimination on the
  augmented matrix `[D | r]`. The executable
  `compute_repair_or_separator` returns one witness or the other, and
  `compute_repair_or_separator_correct` proves the returned value
  correct against the ORIGINAL `D`, `r`, not merely the row-reduced
  matrix elimination operates on.
- The repair branch's correctness needed a solution-set equivalence
  (`SolvesAug`) proved preserved by each of `swap_rows`/`scale_row`/
  `add_scaled_row` independently and threaded through the whole
  elimination trace by induction -- the transformation-matrix
  invariant the separator branch uses does not by itself relate the
  reduced matrix's solution set back to the original system.
- `repair_and_separator_disjoint` proves the two witnesses cannot
  coexist as its own theorem (`1 = y.r = y.(D b) = (D^T y).b = 0`),
  not by appeal to the algorithm returning only one constructor.
- Verified against the repository's own R1 four-cycle witness
  (`examples/four_cycle.json`): the internal inconsistent-row
  extraction recovers the paper's canonical cycle `z=(-1,-1,-1,1)`
  with pairing `c=-5` before normalisation, exactly matching R1; the
  public certificate is the normalised `-1/5 z = (1/5,1/5,1/5,-1/5)`.
  Checked against seven `vm_compute` sandbox cases (a repairable
  system, a synthetic inconsistent one, the four-cycle system, and
  four tamper-rejection cases), via independent executable checkers
  (`check_repair`/`check_separator`) reusing no elimination machinery.
- Self-contained: no `Require` of any other file in this repository.
  `Print Assumptions` on `rational_repair_or_separator`,
  `repair_and_separator_disjoint`, and
  `compute_repair_or_separator_correct` each report "Closed under the
  global context" -- zero project-added axioms.
- The active formal chain now contains 26 Rocq modules.

### Presentation fidelity and quotient semantics

- Added R17, `rocq/CommonSubdivisionVerdictInvariance.v`: the first
  combined verdict-invariance theorem for two presentations related
  through a common subdivision whose refinement legs are both
  descent-safe (N0) and exactness-reflecting (E0). Proves both the
  exactness-side equivalence and its fully constructive obstruction-side
  contraposition. Introduces no new primitive preservation mechanism;
  its contribution is the first formal assembly of the existing N0/E0
  results.
- Added
  `docs/design/PRESENTATION_INVARIANCE_SPEC.md`, which established before
  implementation that most of the proposed presentation-invariance
  ladder already existed in separate form and identified the combined
  verdict equivalence as the precise missing theorem.
- Added R18-R19, `rocq/QuotientDescentReflection.v`: introduces the small
  `CoboundaryQuotientLaws` extension without strengthening the existing
  `VSpace` record; proves coboundary equivalence is an equivalence
  relation under the stated hypotheses; proves N0 preserves
  coboundary equivalence; proves E0 is equivalent to reflection of
  coboundary equivalence; and packages N0 plus E0 as faithful quotient
  descent for linear refinement maps.
- Added
  `docs/design/QUOTIENT_DESCENT_AND_REFLECTION_SPEC.md`, based on a
  compiling scratch prototype against the repository's actual algebraic
  infrastructure. The prototype identified both the extra quotient laws
  missing from `VSpace` and the independent linearity hypothesis required
  for quotient descent.
- Added R20, `rocq/QuotientVerdictClosure.v`: rederives R17's
  distinguished-residue verdict equivalence through the R18-R19 quotient
  machinery, confirming that the direct and quotient-level
  formalisations agree.
- The active formal chain now contains 25 Rocq modules. `make check-all`
  runs Python, Rocq compilation, complete `coqchk` trust checking, the
  OCaml refinement checker, assembly parity, and contribution parity.
- Scope remains deliberately limited. No full quotient-space
  isomorphism, arbitrary presentation invariance, topology-changing
  invariance, cycle-space/quotient duality theorem, or general
  functoriality result is claimed.

- Generalised `rocq/AssociatorResidueRepair.v` from Leibniz equality on
  `C1` to an explicit, caller-supplied equivalence relation `ceq`
  (`nonzero_pairing_blocks_repair_mod_ceq`,
  `nontrivial_associator_residue_not_repairable_mod_ceq`), with the
  hypothesis that `pairing` respects `ceq`. This closes, at the abstract
  level, the same gap `FourCycleObstruction.v` first worked around
  file-locally: Leibniz equality is too strict once `C1` is instantiated
  concretely (e.g. as `Q`-valued vectors, where `1#1` and `2#2` are
  `Qeq`-equal but not Leibniz-equal), so a theorem proved only for
  Leibniz `delta0 b = r` does not, in general, rule out a "repair" via a
  differently-represented but rational-equal coboundary. The original
  Leibniz-based theorems (`nonzero_pairing_blocks_repair`,
  `nontrivial_associator_residue_not_repairable`) are kept, now as
  one-line corollaries obtained by instantiating `ceq := eq`, for callers
  with no finer structure on `C1` than Leibniz equality. Updated
  `rocq/FourCycleObstruction.v` so `four_cycle_not_repairable` is obtained
  by *direct application* of the new `..._mod_ceq` theorem with
  `ceq := veq` (the file's pre-existing componentwise-`Qeq` relation),
  rather than a hand-written, file-local proof; `pairing_congr` is now
  literally the `pairing_respects_ceq` witness the abstract theorem
  requires. `four_cycle_not_repairable_leibniz` is kept as a secondary,
  strictly weaker corollary. No `Admitted`/`Axiom`/`sorry`.
- Added `rocq/FourCycleObstruction.v`: instantiates
  `AssociatorResidueRepair.v`'s abstract Layer-1 theorem concretely, over
  `Q`, with the paper's own numbers -- `r = (1,1,1,-2)`, `z = (-1,-1,-1,1)`,
  and `delta0` matching `examples/four_cycle.json`'s `coboundary_0` matrix
  row-for-row. Proves `<z,r> == -5`, `<z,r> <> 0`, and
  `four_cycle_not_repairable`, all inside Rocq. Caught and documented a
  real subtlety along the way: the 4-tuple-of-`Q` type's meaningful
  equality is componentwise `Qeq` (`veq`), not Leibniz `=` -- two
  representations of the same rational are `veq`-equal but not
  Leibniz-equal, so a non-repairability theorem stated only for Leibniz
  equality would not, in general, rule out a "repair" via a
  differently-represented coboundary. `four_cycle_not_repairable` is
  stated and proved with `veq`, matching the paper; a second, strictly
  weaker `four_cycle_not_repairable_leibniz` corollary is also proved, by
  unmodified direct application of `AssociatorResidueRepair.v`'s theorem,
  to confirm that file needs no repackaging (it is already
  `forall`-quantified, not built from top-level `Parameter`s) to be
  reused. Does not instantiate the associator-layer theorem (`AssocData`
  left abstract) -- that still requires a concrete `AssocData` matching
  `regional_composition.py`, deferred as before. No
  `Admitted`/`Axiom`/`sorry`.
- Added `rocq/AssociatorResidueRepair.v`: an abstract Rocq proof of the
  repair-impossibility inference the associator-generation layer below
  exemplifies computationally (associator defect -> seam residue -> repair
  equation -> obstruction to global correction). Two theorems:
  `nonzero_pairing_blocks_repair` (pure cohomology, same content as
  `AdmissibleRefinementPersistence.v`'s cycle-pairing lemma, restated with
  `delta0`/`pairing`/`cycle` naming to match `repair_solver.py`) and
  `nontrivial_associator_residue_not_repairable` (the associator layer,
  with `AssocData`/`BoundaryCorrection` left abstract and proved by direct
  application of the first theorem). No `Admitted`/`Axiom`/`sorry`. Does
  not mechanise `finite_algebra.py`/`regional_composition.py`/the Venn
  model, and does not import or build on
  `AdmissibleRefinementPersistence.v` -- the two files are deliberately
  kept separate (refinement of presentation vs. repair of an
  associator-generated residue).
- Added an associator-generation layer beneath the existing classifier:
  `finite_algebra.py` (structure-constant Q-algebra with a literal, not
  shortcut, associator computation), `regional_composition.py` (the
  square-zero Venn model of Example ex:venn, boundary-corrected products,
  and associator defects computed by direct expansion of the paper's
  definitions and cross-checked against the closed-form four-term formula
  of Proposition prop:four-term), `associator_residue.py` (compiles the
  four coarse seam values of the Section-7 witness from four independent
  associator instances instead of declaring them), `repair_solver.py`
  (obstruction-language wrapper reusing `rational_linear_algebra`),
  `certificate_emitter.py`, and `run_associator_obstruction.py`. New
  example `examples/four_cycle_associator.json` and five new test files.
  The resulting residue is checked to equal both
  `refinement_witnesses.COARSE.residue` and the residue in the pre-existing
  `examples/four_cycle.json`, and to produce an identical verdict when run
  through the unmodified `residue_classifier.classify`. This does not
  change the historical record: the paper's displayed residue was
  originally posited directly (see below), and none of items 1-6 are
  modified by this addition.

- **Fixed a real exactness bug**: `residue_classifier.py` computed its
  coboundary-solvability check with `numpy.linalg.lstsq` on a `float` cast
  of the exact rational data, then rounded back to `Fraction` via
  `limit_denominator` — not exact rational linear algebra, despite the
  "exact rational classifier" framing. Replaced with the same exact
  Gauss-Jordan elimination `refinement_checker.py` already used. Both now
  import a shared `rational_linear_algebra.py` (`mat_vec`, `row_vec_mat`,
  `dot`, `is_zero`, `solve_over_Q`) instead of each having its own copy.
  `numpy` is no longer a dependency of any active code path.
- Added `tests/test_random_residue_regression.py`: the 1000-case
  property-based regression test the paper claimed but the repository
  didn't contain — bounded random rational residues on the four-cycle,
  checking `δ⁰b = r` solvable `<=>` `⟨z,r⟩ = 0`, plus 250+250 forced
  exact/obstruction control cases and a direct check of the paper's
  displayed residue. Fixed seed for reproducibility.
- Moved the old, superseded universal-refinement scaffold (four-condition
  scheme with adjointness and H₁-surjectivity, three placeholder checks,
  hardcoded legacy pairing values, non-compiling Rocq skeleton, and four
  now-inactive design docs) into
  `archive/deprecated_universal_refinement_scaffold/`, with its own README
  explaining what's there and why. Nothing in the current checked result
  depends on it.
- Updated the paper: renamed the theorem from "Universal admissible-
  refinement persistence" to "A1-A4 admissible-refinement persistence"
  (the old name risked being misread as unrestricted refinement
  invariance, which is explicitly not claimed); simplified the refinement
  witness table to computed-pairing-and-verdict only, moving the legacy
  `(-7/2, -4, -5/4, -5)` values into the correction note where they were
  already explained rather than displaying them as a table column;
  corrected the "1000 passed cases" claim to match the now-real test;
  added reproducibility commands for the random-residue test and the Rocq
  proof; clarified that the Rocq proof is of the abstract theorem, not a
  verified kernel for the concrete classifier.
- Added `Makefile` (`check-python`, `check-random`, `check-rocq`,
  `check-ocaml`, `clean`), `requirements.txt` (just `pytest`), `.gitignore`,
  and a GitHub Actions workflow (`.github/workflows/python.yml`) running
  the Python checks on push/PR. Rocq and OCaml CI workflows intentionally
  not added yet — not claiming CI for those until a workflow actually
  passes on GitHub's runners, not just locally.

## v0.6-rocq-a1-a4-persistence

- Added `rocq/AdmissibleRefinementPersistence.v`: an abstract Rocq proof of
  the paper's admissible-refinement persistence theorem, conditions
  (A1)-(A4) only. No adjointness, no H₁-surjectivity, no presentation
  invariance, no `Admitted`/`Axiom`/`sorry`. Compiles clean with `coqc`.
- Does not build on and does not touch `rocq/UniversalRefinement.v`, which
  remains deprecated (targets the old, superseded four-condition scheme and
  contains `sorry`).

## v0.5-admissible-refinement-parity

- Added `refinement_witnesses.py`: explicit refined-complex constructions
  for the four refinement witnesses (subdivide `U1`, subdivide `U2`,
  subdivide all regions, insert bridge) — vertices, oriented edges,
  pullback data (`over`/`over_sign`), and a declared refined cycle `z'` for
  each, replacing hardcoded table values with an actual construction.
- Added `refinement_checker.py`: checks conditions (A1)-(A4) exactly as
  stated in the paper's theorem (not the old, stronger four-condition
  scheme involving adjointness and H₁-surjectivity), and computes
  `⟨z', ρ*r⟩` by construction. Reports an independent exact-Gaussian-
  elimination solver cross-check alongside the cycle-pairing certificate.
- Added `tests/test_refinement_witnesses.py`: 17 regression tests locking
  down the computed values and the solver/pairing agreement.
- Added `ocaml/refinement_witnesses.ml` + `ocaml/refinement_checker.ml`: an
  independent OCaml mirror of the above, using `zarith`'s exact `Q.t`.
  Computes the identical pairings; the values appear as literals only in
  the parity self-check against Python.
- **Corrected the paper's refinement witness table.** The previous table
  claimed pairings `(-7/2, -4, -5/4, -5)` that were never produced by any
  refined complex, pullback map, or declared cycle — they were literal
  constants in `ocaml/refinement_theorem.ml`. The corrected, independently
  computed values (Python and OCaml agree) are `(5, 5, 5, -5)`; only the
  bridge witness matches the old claim. Added prose explaining why the
  three subdivision witnesses agree (internal split edges have `over =
  None`, so they don't contribute to the pairing) and why the bridge sign
  differs (declared cycle orientation, not a mathematical inconsistency).
  Old values retained in the table only as a labelled "legacy claim" column.
- Marked `refinement_classifier.py`, `ocaml/refinement_algebra.ml`,
  `ocaml/refinement_theorem.ml`, `ocaml/refinement_types.ml`, and
  `ocaml/refinement_verification.ml` as deprecated (header comments only,
  not deleted): they check a different, stronger four-condition scheme
  than the paper's actual theorem, with three of four checks hardcoded as
  placeholders, and (for the OCaml files) depend on `Core`/`Batteries`,
  neither of which had `ocamlfind` dev files available when checked.

## Initial import

- `d7de826`: associator-fields paper (`paper/associator_fields_ACS_revised.tex`
  / `.pdf`) and its accompanying code: `residue_classifier.py` (working,
  exact-rational four-region obstruction witness), plus the
  refinement-persistence scaffolding later found to be non-functional and
  superseded above.
