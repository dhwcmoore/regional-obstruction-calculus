# Stone Soup Track-Fusion Evaluator: Pre-Implementation Audit (step 10E)

**Status (2026-07-17): design/audit only. No `rocq/*.v`, no `tracking_
adapter_*.py`, no `tests/test_stonesoup_*.py` file implementing 10E
should be written from this document until it is reviewed and a
go-ahead is given.** Steps 10A-10D established a stable, exact boundary
around a deliberately minimal scalar four-cycle fixture. Step 10E
imports a genuinely different, much richer object -- an operational
Stone Soup track-fusion pipeline with multidimensional Gaussian states,
nonlinear measurement models, covariance, clutter, and stochastic
simulation. The risk this document exists to bound is semantic
misrepresentation of that richer system, not another schema gap -- so
every claim below was checked against the actual upstream source at the
pinned version, not assumed from documentation or memory.

The governing question:

> Given the local tracks produced by this deterministic Stone Soup
> track-fusion scenario, are the selected projected track comparisons
> simultaneously repairable under the declared correction and
> transformation policy?

This is **not** "is Chernoff fusion mathematically correct?" and **not**
"are Stone Soup's estimates statistically optimal?" -- both explicitly
out of scope, stated again in SS9 and in "What this document does not
claim" below.

**One correction made during review, before any code was written**: the
governing question above is answered by TOPOLOGY, not by running the
scenario -- SS9 shows `rank(D) = 1 = dim(C^1)` for a two-track, one-edge
comparison, so the answer is *necessarily* "yes, repairable" for any
residue this scenario could produce, checked directly rather than
assumed. The evaluator's genuine empirical content is the actual
residue value and repair witness R21 returns on real Stone Soup output,
not whether one exists -- read SS9 in full before treating "expected
verdict" language elsewhere in this document as open.

## 1. Exact upstream artefact

Fetched directly from GitHub at the tag matching this repository's own
pinned version (`requirements-stonesoup.txt`: `stonesoup==1.9.1`), not
`latest`:

```text
File:      docs/examples/trackfusion/track_fusion_example.py
Repo:      https://github.com/dstl/Stone-Soup
Tag:       v1.9.1
Tag commit (annotated tag object): d9e6fb16f5ae176817aeb6a6fc3a39f544694408
Underlying commit:                 a4336b920a799cfe0a77ecb05867c5deeb371c7a
File blob SHA (git):                ed29306613e2d570442d8e88c9713d32f58e7418
File SHA-256 (fetched content):
  fe1dc7b10d568065fa5097d6561dec2e783be2f998aaedbc1cba3addea3a5b8e
Length: 536 lines
```

**Not vendored.** This example is a documentation/tutorial script, not
part of the installed `stonesoup` wheel (confirmed directly: the
installed package under `.venv-stonesoup/.../site-packages/stonesoup/`
contains `updater/chernoff.py` and `feeder/track.py` -- the real classes
the example uses -- but no `docs/examples/` tree at all; PyPI wheels
ship the library, not its documentation examples). The evaluator will
therefore be a **minimally adapted rewrite invoked through installed
APIs** (`ChernoffUpdater`, `Tracks2GaussianDetectionFeeder`,
`RadarBearingRange`, `SingleTargetTracker`, etc., all imported from the
installed package as steps 10B-10D already do), not a vendored copy of
the tutorial file, and not an execution of the tutorial file itself.

A second, related example exists at
`docs/examples/trackfusion/Track2Track_Fusion_Example.py` (727 lines,
SHA-256 `ce90e8bf276a109aeee02d958e60a5346384e1839775bebfb1a134f11076f50a`)
comparing FIVE tracker/updater architectures (PDA, JPDA, GNN, LCC, PHD)
across multiple full sections. **Rejected as the 10E base**: it is
structured as a comparison of association/update algorithms, not a
single clean track-to-track fusion pipeline, and would multiply this
audit's scope rather than bound it. `track_fusion_example.py` is the
right base: one ground truth, two sensors, two local trackers (Kalman
and, separately, particle -- see SS9 for which is kept), one Chernoff
fusion stage.

**Modifications required for determinism** (see SS6 for the complete
inventory; summarised here as it bears on "what changes from upstream"):
replace `datetime.now()` with a fixed timestamp; the existing
`np.random.seed(2000)` call does **not** actually make the clutter model
deterministic (SS6 explains the exact reason, a genuine upstream
gotcha); the clutter model and particle-filter branch are candidates for
removal, not merely seeding, for the FIRST evaluator (SS9).

## 2. Adapter insertion point

Traced directly from the fetched source, the actual object chain is:

```text
SingleTargetGroundTruthSimulator (one simulated target, 4D state: x, vx, y, vy)
    -> tee'd into two PlatformDetectionSimulator instances (one per radar)
    -> RadarBearingRange (nonlinear, bearing+range) sensor detections, per platform
    -> SingleTargetTracker (UnscentedKalmanPredictor/Updater) PER SENSOR
        -> LOCAL TRACKS (Track objects, GaussianState sequence, 4D: x, vx, y, vy)
    -> Tracks2GaussianDetectionFeeder(MultiDataFeeder([...])) -- treats each
       LOCAL TRACK's current state as a Gaussian "detection" for the next stage
    -> ChernoffUpdater (measurement_model=None) inside a
       PointProcessMultiTargetTracker (PHDUpdater wrapping ch_updater)
    -> FUSED TRACK
```

Per this step's own instruction, **the evaluator captures LOCAL TRACKS
immediately before `Tracks2GaussianDetectionFeeder`** -- i.e., each
`SingleTargetTracker`'s own track output, the cleanest point for
comparing the declarations fusion is about to combine, since it is the
last point at which "track 1's estimate" and "track 2's estimate" are
still separate, addressable objects with their own ancestry, before
`Tracks2GaussianDetectionFeeder` erases that distinction by presenting
them as generic Gaussian detections to `ChernoffUpdater`.

The **fused track is captured too, but only for side-by-side reporting**
(SS9's "Stone Soup's fused output" column) -- never as an input to the
structural verdict. The structural verdict is computed entirely from the
two LOCAL tracks and the declared transformation/correction policy;
Stone Soup's own fused estimate is reported next to it as a point of
comparison, not consumed by `tracking_adapter_generator.py`/`tracking_
adapter_verifier.py` in any way.

## 3. State projection

Confirmed directly from the source: the target's `GaussianState` is
4-dimensional, `[x, vx, y, vy]` (`CombinedLinearGaussianTransitionModel`
over two independent `ConstantVelocity` models), with `position_mapping
= (0, 2)` on both `RadarBearingRange` sensors -- i.e., the state's
Cartesian position components are at indices 0 (x) and 2 (y), velocity
at 1 (vx) and 3 (vy). Units are the example's own arbitrary simulation
units (metres-equivalent for position; the example never assigns
physical units explicitly, and this document does not invent any).

**Decision: analyse ONE declared scalar coordinate at a time, per this
step's own recommendation.** The first evaluator projects onto the
**x-position component (state index 0)** of each local track's current
`GaussianState.state_vector`, exactly as `tracking_adapter_format.py`'s
existing `state_values` field already expects (a length-1 list). This
is a genuine PROJECTION, stated as such in the snapshot's own
`state_space`/provenance metadata (`{"stone_soup_state_index": 0,
"stone_soup_state_dimension": 4}` or equivalent), not a silent
flattening -- the adapter never sees or claims anything about indices
1-3.

- **x and y are NOT evaluated as one block system in this first
  evaluator.** They are two structurally independent scalar problems if
  ever both are wanted; running a second `(D, r)` instance over index 2
  (y-position) with its own projection metadata is the natural next
  step, explicitly NOT attempted here. A combined block-matrix adapter
  (both coordinates coupled in one linear system) is future work, not
  scoped by this document at all.
- **Velocity (indices 1, 3) is recorded as provenance only** -- captured
  in the snapshot's per-track metadata for auditability, never entering
  `state_values`, `(D, r)`, or any transformation.
- **Covariance is provenance only** -- see SS5, its own section, since
  the instructions single it out.
- **Timestamps**: the simulation advances in fixed 1-second steps
  (`timedelta(seconds=1)`) from one fixed `start_time` (SS6). The
  evaluator selects ONE evaluation timestep (a specific loop iteration,
  fixed by index, e.g. the final completed step) and uses both local
  trackers' states AT THAT SAME timestep -- both `SingleTargetTracker`
  instances advance in lockstep already (the example's own loop calls
  `next()` on both every iteration), so no additional timestamp
  propagation/interpolation logic is needed for the first evaluator; a
  scenario where the two trackers' update times genuinely diverge would
  need one, explicitly deferred.

## 4. Transformation semantics

Traced through the actual pipeline: both `FixedPlatform` sensors
(`sensor1_platform` at `[10, 0, 80, 0]`, `sensor2_platform` at `[75, 0,
10, 0]`) report their OWN position via `position_mapping`, but
`RadarBearingRange`'s bearing/range measurements are converted back to
the SAME GLOBAL Cartesian frame by the (Unscented) Kalman
predictor/updater internally -- **both `SingleTargetTracker` instances
already produce state estimates in one common global frame**, not a
sensor-relative one. Stone Soup itself has therefore already performed
the sensor-mounting/registration transformation, internally, before the
evaluator ever sees a local track.

**Consequence, stated precisely so it is not glossed over**: for THIS
example, in its natural (unperturbed) form, the adapter's own declared
transformation for each track is the **identity** (`additive_offset`
with `offset = "0"`) for both tracks -- there is no separate
platform-to-global registration left for the adapter to apply, because
Stone Soup's own filters already did it. This is a real, checked
finding, not an assumption: introducing a NONTRIVIAL adapter
transformation on top of already-global-frame estimates would be
inventing a correction with no motivating registration problem behind
it, exactly the "same coordinate change applied twice" failure this
step's own instructions warn against.

**What the adapter's transformation slot IS for in this scenario**,
precisely enumerated against the six candidates this step lists:

- Platform-to-global registration: **already done by Stone Soup**, not
  the adapter's job here.
- Sensor mounting: **already absorbed into Stone Soup's own measurement
  model** (`RadarBearingRange`'s own geometry).
- State-space projection: **the adapter's own job** (SS3 -- extracting
  index 0 from the 4D state), but this is a projection, not an
  `additive_offset` transformation in the existing schema's sense.
- Timestamp propagation: **not needed** for this first evaluator (SS3).
- Track-to-track coordinate alignment: **not needed** here, since both
  tracks are already co-registered (see above) -- would matter if the
  two trackers used different local frames, which they do not.
- Deliberately imposed evaluator transformations: **the one genuine use
  of the adapter's transformation slot in this scenario** -- reserved
  for SS9's explicitly labelled artificial perturbation (an evaluator-
  imposed nonzero offset added deliberately to manufacture an
  obstructed case for comparison, clearly distinguished from the
  natural result).

## 5. Covariance boundary

Per this step's own instruction, stated as the binding policy for 10E:

- **Captured**: each local track's own `covar` (a 4x4 `CovarianceMatrix`
  at the point of capture, SS2) is read directly from the genuine Stone
  Soup `GaussianState`.
- **Canonically serialised**: as canonical decimal-string matrix rows
  (the same string discipline `tracking_adapter_canon.py` already
  enforces for every other numeric field), attached as track-level
  metadata, NOT as a new required top-level schema field -- reusing the
  existing "provenance is optional, additive metadata" pattern from step
  10D rather than widening `LocalTrack`'s own required-field set.
- **Bound by the snapshot digest**: since it lives inside the snapshot
  document (as track metadata), `compute_payload_digest`'s existing
  whole-evidence hashing already covers it once it is placed inside
  `tracks`/`detections`, with no change to `compute_payload_digest`
  needed (unlike step 10D's `provenance`/`independence_policy` fields,
  which needed an explicit, separate fix because they are NEW top-level
  keys the old digest function never saw at all).
- **Retained as provenance, excluded from `(D, r)`**: `state_values`
  contains ONLY the projected scalar mean (SS3); covariance never enters
  `tracking_adapter_generator.py`/`tracking_adapter_verifier.py`'s
  reconstruction of `(D, r)` at all, unless and until a separately
  justified theorem (not existing in this repository today, and not
  proposed by this document) says otherwise.

**The exact claim this licenses, stated once, precisely, for reuse in
10E's own module docstrings**:

> R21 certifies structural compatibility of the projected TRACK MEANS
> under the declared correction policy. It does not verify covariance
> intersection, Chernoff weighting, or statistical calibration of any
> kind.

## 6. Determinism modifications -- every source of variation checked directly

| Source | Found in upstream? | Disposition for 10E |
|---|---|---|
| `datetime.now()` | YES -- `start_time = datetime.now().replace(microsecond=0)` | Replace with one fixed UTC timestamp, matching steps 10B-10D's own `FIXED_TIMESTAMP` convention. |
| NumPy global state (`np.random.seed`) | YES -- `np.random.seed(2000)` | Kept, but see the next row -- **this call alone does NOT make the scenario deterministic**, a genuine upstream gotcha worth stating plainly: `np.random.seed(...)` only seeds NumPy's legacy `RandomState` global instance; it has no effect on `np.random.default_rng()`, a SEPARATE RNG system (the modern `Generator` API) introduced in NumPy 1.17. The example calls BOTH. |
| `default_rng()` (unseeded) | YES -- `clutter_model = ClutterModel(..., distribution=np.random.default_rng().uniform, ...)`, called with NO seed argument | This is the actual nondeterminism source the `np.random.seed(2000)` comment ("Random seed for reproducibility") does not fix. Must be replaced with `np.random.default_rng(SEED)` (an explicit, project-chosen seed) -- or clutter removed entirely (see below). |
| Stone Soup component seeds | Radar noise (`radar_noise = CovarianceMatrix(...)`) is a fixed covariance, not sampled directly by the example's own code -- the ACTUAL noise sampling happens inside `RadarBearingRange`'s own `function(..., noise=True)` default call path (the example never passes `noise=False` anywhere), which uses `numpy.random.multivariate_normal` seeded by the (partially fixed) global `RandomState`. | For a genuinely deterministic evaluator, every sensor `.function()`/measurement-generation call needs its own explicit seed or `noise=False`, matching steps 10B-10D's own established policy exactly -- this is the single largest determinism change from upstream, since the WHOLE example is built around noisy, associative (GNN) tracking, not a noise-free identity path. |
| Process-dependent IDs | Track `id`s are Stone Soup's own auto-generated UUIDs (`Track()` constructed with no explicit `id=` anywhere in the upstream example) | Must supply explicit `id=` at every `Track()`/`Detection()` construction, exactly as steps 10B-10D's own source-policy test already requires and checks by AST scan. |
| Set/dict iteration | YES -- `PF_track1, PF_track2, KF_track1, KF_track2 = set(), set(), set(), set()`, `truths = set()` | Python's own `set` iteration order for these specific object types is insertion-stable in CPython for the types involved here (checked: no float/complex keys), but this should not be relied upon silently -- the evaluator must sort or otherwise canonicalise before emitting anything from a set-typed collection, not merely "hope" iteration order is stable. |
| Clutter | YES -- `ClutterModel(clutter_rate=0.75, ...)`, actively used by both `RadarBearingRange` sensors | **Removed for the first evaluator** (`clutter_model=None`), consistent with steps 10B-10D's own "no clutter of any kind" policy, not merely seeded -- clutter also feeds `GNNWith2DAssignment`'s association logic, which is itself a second source of run-to-run branching (which detection associates to which track) this document is not prepared to certify deterministic just by seeding the clutter draw. |
| Measurement noise | YES, on by default (`RadarBearingRange.function` with implicit `noise=True`) | **Disabled** (`noise=False` at every measurement call, exactly steps 10B-10D's own policy) for the first evaluator's natural (unperturbed) scenario. |
| Platform simulation | `FixedPlatform` -- not itself stochastic (positions are fixed), no change needed beyond the timestamp/seed items above. | No change needed. |
| Plotting/metric code | YES -- `Plotterly`, `MetricPlotter`, `SIAPMetrics`, `MultiManager`, `TrackToTruth` -- roughly a third of the 536-line file. | **Removed entirely** from the evaluator script -- no plotting or metrics computation belongs in a deterministic evidence-capture pipeline; SS10 records this as a real dependency-cost finding (matplotlib/plotly need not be imported by the evaluator itself, even though they remain in `requirements-stonesoup.txt` as Stone Soup's own transitive dependencies). |

**With clutter removed and noise disabled, `GNNWith2DAssignment`'s
association problem becomes trivial** (exactly one detection per sensor
per timestep, unambiguous nearest-neighbour assignment) -- this is
DELIBERATE: it converts the association/data-associator machinery from
a second, separate source of nondeterminism into a structurally trivial
pass-through for the first evaluator, without removing the tracker
components themselves (`SingleTargetTracker`, `UnscentedKalmanUpdater`,
`GNNWith2DAssignment` all remain genuine Stone Soup objects, per this
step's own requirement that the evaluator use real APIs, not
reimplement them).

**Particle-filter branch**: the upstream example runs BOTH a Kalman
branch and a particle-filter branch (`n_particles = 2**10`) through the
same fusion machinery, comparing them. **The first evaluator keeps only
the Kalman (`UnscentedKalmanPredictor`/`UnscentedKalmanUpdater`)
branch** -- the particle-filter branch introduces its own resampling
randomness (`ESSResampler`) as a THIRD source of variation this document
is not prepared to audit and seed in the same pass; it is a natural,
separately-scoped follow-up once the Kalman branch's evaluator is
working and reviewed.

## 7. Provenance mapping

Mapped directly against `tracking_adapter_format.py`'s existing
`AncestryNode` types (step 10D):

| Stone Soup object | Ancestry node type | Project-controlled ID convention |
|---|---|---|
| `FixedPlatform` (`sensor1_platform`, `sensor2_platform`) | (platform identity, carried as `Source.platform_id`, not its own ancestry node type -- matching steps 10B-10D's existing `Source` schema, which already has a `platform_id` field) | `platform-radar-1`, `platform-radar-2` |
| `RadarBearingRange` (`radar1`, `radar2`) | `source_record` -- each sensor's own detection-generating identity | `source_record:radar-1`, `source_record:radar-2` |
| Detection produced by each radar, per timestep | `detection` | `detection:radar-1:t{n}`, `detection:radar-2:t{n}` |
| `SingleTargetTracker` (`KF_tracker_1`, `KF_tracker_2`) | (tracker identity, carried as `LocalTrack.tracker_id`, matching existing schema) | `tracker-kf-1`, `tracker-kf-2` |
| `Track` object each tracker produces | `local_track` | `track:kf-1`, `track:kf-2` |
| `Tracks2GaussianDetectionFeeder` | `track_feeder` -- the fusion-input bridge, per this step's own required chain | `feeder:chernoff-fusion-input` |
| `PointProcessMultiTargetTracker` (the Chernoff fusion tracker) fused output | `fusion_stage_track` (captured for reporting only, SS2 -- never an ancestry PARENT of the structural verdict's own declared_comparison) | `fusion:chernoff-fused` |
| The evaluator's own declared pairwise comparison of `track:kf-1` vs `track:kf-2` | `declared_comparison` | `comparison:kf1-kf2` |

**Confirming, not assuming, whether the two radar tracks have disjoint
source evidence** (this step's own explicit instruction): traced
directly through the fetched source -- `gt_sims = tee(groundtruth_
simulation, 2)` tees ONE ground-truth generator so both radar simulators
observe the SAME simulated target trajectory, but each `RadarBearingRange`
instance (`radar1`, `radar2`) generates its OWN detection at each
timestep via its OWN call to its measurement model -- two textually and
numerically DIFFERENT `Detection` objects per timestep (different
bearing/range values, since the two platforms sit at different
positions, `[10,0,80,0]` vs `[75,0,10,0]`; even with noise disabled, the
geometric projection differs). **Under this adapter's own `source_
record`-level independence definition (step 10D), these two detection
streams ARE disjoint `source_record` ancestors** -- radar1's detections
never appear anywhere in radar2's ancestry chain, and vice versa.

**This is explicitly NOT the same claim as "the two tracks are about
unrelated targets."** Both tracks are correlated at the level of the
shared, single, simulated ground-truth object -- a form of correlation
this adapter's ancestry graph does not represent at all (it tracks
shared EVIDENCE RECORDS, i.e. sensor readings, not shared underlying
physical truth). Stating this precisely, as a non-claim, matters more
here than in the synthetic 10D fixtures, since a real two-sensor,
one-target scenario is exactly the case where a reader could wrongly
assume "same target" and "shared ancestry" mean the same thing:

> A `PROVENANCE ACCEPT` verdict for this scenario means the two local
> tracks' declared comparison does not share a common SENSOR-RECORD
> ancestor. It does not mean, and this document does not claim, that the
> two tracks are statistically independent estimates of the target's
> position -- both estimates are, physically, about the same one moving
> object, and any two unbiased estimators of the same true quantity are
> correlated with each other in that sense regardless of sensor-record
> independence. The adapter's ancestry graph has no representation of
> "same underlying physical target" as a form of shared ancestry, and
> this document does not propose adding one.

## 8. Evaluator question

Restated once, exactly, as the module docstring 10E's implementation
must carry verbatim:

> Given the local tracks produced by this deterministic Stone Soup
> track-fusion scenario, are the selected projected track comparisons
> simultaneously repairable under the declared correction and
> transformation policy?

## 9. The verdict is topologically predetermined -- checked, not assumed

**Correction to an earlier draft of this section, caught before
implementation**: with two local tracks compared once at one evaluation
time, the comparison graph has two vertices, one edge, no cycle. Its
incidence matrix is, up to orientation,

```text
D = (-1  1)     (a single row, two columns)
```

`rank(D) = 1`, which already equals `dim(C^1)` (the one-edge residue
space) -- so `D : Q^2 -> Q^1` is surjective, `im(D) = Q^1` entire.
Checked directly, not asserted: for ANY scalar `r`, `b = (0, r)` gives
`Db = -0 + r = r` exactly, confirmed by direct computation.

```text
dim C^1 = 1     rank(D) = 1     dim(C^1 / im D) = 0
```

**Consequence: the natural (unperturbed) scenario's verdict is not
"likely repairable" -- it is *necessarily* repairable, for every
possible value of `r`, by the comparison topology alone, before any
Stone Soup number is ever computed.** This is not a property of noise-
free measurement, of Stone Soup's own co-registration (SS4), or of
anything empirical about this scenario at all -- it is a property of
comparing exactly two tracks with exactly one declared edge: a
one-dimensional residue space with a surjective, rank-1 `D` has no
room for a nonzero cokernel, so no residue vector on this topology can
ever be obstructed. This is not a flaw in R21 or in Stone Soup -- the
comparison topology simply contains no cycle for an obstruction to live
on (contrast the four-cycle fixtures of steps 10B-10D, where `D` is
`4x4` with `rank(D) = 3`, leaving a genuine 1-dimensional cokernel --
`docs/TRACKING_ADAPTER_END_TO_END_DEMONSTRATION.md` and `tests/test_
tracking_adapter_metamorphic.py` both check this directly).

**The artificial perturbation (SS4's "deliberately imposed evaluator
transformation" category) does not change this.** A nonzero
`additive_offset` on one track changes `r`'s specific VALUE, but every
value in `Q^1` is repairable on this topology -- so the perturbed
scenario remains repairable too, by the same argument, for any offset
chosen. **The perturbation therefore tests transformation HANDLING
(does the adapter correctly derive a different `r` and a different
repair witness `b` from a different declared offset?), not obstruction
capability** -- it must not be described, implemented, or reported as an
attempt to manufacture an obstruction, since none is topologically
possible here.

**An obstruction-capable realistic evaluation needs a genuinely
different topology** -- three or more tracks arranged in a cycle,
several context-dependent comparisons between the same tracks, multiple
timestamps sharing the same correction variables, a fused-track
triangle (if its provenance and correction semantics were separately
justified), or any other topology with a nontrivial cycle space. None
of these is attempted by this document or by 10E -- a natural, separate
follow-up once the two-radar evaluator itself is working and reviewed.

**What 10E genuinely establishes, restated precisely**: not an open
search for obstruction, but a realistic pipeline-integration and
topology sanity check --

> The natural two-radar comparison is necessarily repairable because its
> comparison graph is acyclic. R21 returns a concrete repair witness,
> confirming the topology-derived expectation on evidence produced by
> the official Stone Soup pipeline.

That is itself a meaningful result: it shows the calculus does not
manufacture obstructions where none can exist, on evidence a real
(deterministic, trimmed) Stone Soup pipeline actually produced, not a
hand-authored fixture. The empirical content of running the evaluator
is the actual residue value and the actual witness R21 returns, not
whether a witness exists at all -- that part is settled by SS9 above,
before the evaluator runs.

10E demonstrates, concretely: a real Stone Soup tracking pipeline can be
reproduced deterministically; local tracks can be captured at the
correct fusion boundary; multidimensional Gaussian tracks can be
projected under an explicit policy; covariance and velocity can be
preserved as digest-bound provenance; Stone Soup ancestry can be
reconstructed; the exact adapter can operate on naturally generated
tracking estimates, not just hand-authored ones; the repair certificate
correctly reflects the acyclic comparison topology; and the fused Stone
Soup output can be reported without becoming evidence for its own
validation.

The evaluator's report must include, per this step's own list:
provenance outcome; reconstructed `(D, r)`; repair-or-separator verdict
and certificate; Stone Soup's own fused-track output (position mean,
for comparison only); and an explicit statement of the difference
between the structural conclusion (this document's own scope) and any
statistical conclusion (out of scope, not claimed) -- including the
topology-vs-statistics distinction this section itself turns on.

## 10. Performance and dependency cost

Measured directly against the fetched example and this repository's own
pinned environment:

- **Scenario runtime**: `number_of_steps = 75` in the upstream example;
  the trimmed (no clutter, no particle filter, no plotting/metrics)
  Kalman-only evaluator is expected to run in low single-digit seconds
  on ordinary hardware -- confirmed at implementation time, not
  asserted here in advance.
- **Snapshot size**: two tracks, one comparison, one timestep captured
  -- comparable in size to the existing four-cycle fixtures (a few KB),
  plus covariance provenance metadata (a 4x4 matrix per track, ~16
  canonical decimal strings) -- still small.
- **Matrix dimensions for `(D, r)` itself**: 1 comparison, 2 tracks --
  `D` is `1x2`, `r` is length 1. Trivially small; the Stone Soup
  simulation's own 4x4 covariance/state matrices never enter `(D, r)`
  at all (SS5).
- **Certificate size**: comparable to existing tracking-adapter
  certificates (a few KB), dominated by the (small, fixed-size)
  conversion-attestation list, not by anything Stone-Soup-specific.
- **Verification time**: sub-second, matching every existing tracking-
  adapter verification (no dependency on simulation runtime at all,
  since the verifier only ever sees the already-captured snapshot).
- **Stone Soup environment size**: `requirements-stonesoup.txt` (step
  10A) already pins the FULL transitive tree, including `matplotlib`,
  `scipy`, `plotly`, and `pymap3d` -- none of which the evaluator itself
  needs to import (SS6's removal of all plotting/metrics code) once
  built, though `pip install -r requirements-stonesoup.txt` still
  installs them all, since Stone Soup's own `pyproject.toml` declares
  them as required, not optional, dependencies. **This is the single
  largest practical cost for an edge-computing deployment**: a full
  Stone Soup install pulls in a plotting/scientific
  stack (matplotlib+scipy+plotly+contourpy+kiwisolver+pillow+...) an
  edge deployment would need to either accept or work around (e.g. via
  a constrained install excluding Stone Soup's own optional extras, not
  attempted by this document) even though the evaluator's own code path
  never touches any of it at runtime.

  **This cost belongs entirely to the OPTIONAL evaluator environment,
  never to the exact adapter or R21 kernel** -- step 10A's own import-
  boundary test (`tests/test_stonesoup_import_boundary.py`) already
  proves `tracking_adapter_format/canon/verifier/certificate/generator/
  provenance.py` and every R21 module import cleanly with no Stone Soup
  dependency at all, and that remains true regardless of how heavy
  Stone Soup's own dependency tree is. An edge deployment running only
  the independent adapter verifier and R21 -- checking an already-
  captured snapshot, never producing one -- carries none of this cost;
  it only applies to whatever machine actually RUNS the Stone Soup
  evaluator to produce a snapshot in the first place, which need not be
  the same machine, or even the same class of machine, as the one that
  verifies it.

## Expected files and tests (implementation, not this document)

- `docs/design/STONESOUP_TRACK_FUSION_EVALUATOR_SPEC.md` -- this file.
- `tracking_adapter_stonesoup_trackfusion.py` -- the evaluator itself
  (naming matches the `tracking_adapter_stonesoup_*.py` convention
  already established by steps 10B-10D).
- `tests/test_stonesoup_trackfusion.py` -- end-to-end: snapshot
  verification, provenance check, certificate emission, real R21
  emitter, both real R21 checkers, process-level determinism (matching
  every prior Stone-Soup-dependent test file's own pattern).
- `tests/test_stonesoup_trackfusion_source_policy.py` -- AST-scan
  determinism-policy test, matching step 10B's own `test_stonesoup_
  source_policy.py` pattern, extended to cover the additional
  determinism surface this richer scenario introduces (explicit
  `noise=False` at every sensor call, `clutter_model=None`, explicit
  seeded `default_rng()` wherever randomness remains, explicit `id=` at
  every `Track()`/`Detection()` construction).
- Update to `docs/TRACKING_ADAPTER_END_TO_END_DEMONSTRATION.md` or a new
  document -- deferred to step 10F, not attempted here.

## What this document does not claim

- That the two-radar, one-comparison topology could ever produce an
  obstructed verdict -- SS9 shows directly (`rank(D) = 1 = dim(C^1)`,
  so `D` is surjective) that it cannot, for any residue value, with or
  without the artificial perturbation. This document does not claim to
  have searched for an obstruction and not found one; it claims the
  topology makes one impossible, checked, not assumed.
- That this evaluator is, or is intended to be, an obstruction-capable
  realistic test -- SS9 states plainly that a cyclic or repeated-context
  topology is needed for that, deferred to a later, separate step.
- That Chernoff fusion, covariance intersection, or Stone Soup's PHD/GNN
  tracking machinery has been validated, reviewed, or is claimed correct
  by anything in this document.
- That a `PROVENANCE ACCEPT` verdict says anything about statistical
  independence of the two tracks as ESTIMATORS of one shared physical
  target -- SS7 states this distinction explicitly as a non-claim, not
  an oversight.
- That removing clutter, disabling noise, and dropping the particle-
  filter branch leaves "the same scenario" in any statistical sense --
  it leaves a DIFFERENT, deliberately simplified scenario suitable for
  exact certification, clearly documented as a simplification, not
  presented as equivalent to the upstream tutorial's own (noisy,
  cluttered, dual-filter) scenario.
- That this is the next authorized phase. Implementing `tracking_
  adapter_stonesoup_trackfusion.py` from this document needs its own
  explicit go-ahead, per this repository's established discipline.
