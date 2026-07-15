# Complete Obstruction Signatures Under a Selected Basis (R23 scope)

**Status (2026-07-15): design only. Nothing in this document is
committed as a repository proof, and no `rocq/*.v` file should be
created or modified from it until an explicit go-ahead names which of
§3's two candidate theorems (or a scoped variant) to build.** This
document exists to answer, before any `Signature`/`Omega` construction
is written: what a "complete obstruction signature" actually is, which
parts of it are intrinsic to the annihilator space and which depend on
a chosen basis, how a signature should transform under R24 presentation
equivalence, and which of two genuinely different-sized theorems R23
should prove first — matching this repository's own established
discipline (`CERTIFICATE_TRANSPORT_SPEC.md`'s own history is the most
recent example: scope, spike untracked, confirm architecture, only then
commit) of scoping the smallest true statement before writing a general
framework nothing yet needs.

The governing question:

> Given a finite rational repair operator `D`, what does a "complete
> obstruction signature" for a residue `r` consist of, and how much of
> it is intrinsic to `r`'s obstruction versus an artifact of a choice
> made when computing it?

## 0. What already exists, checked directly, not assumed

R21 (`rocq/ExactRationalRepairOrSeparator.v`) computes ONE annihilating
witness `y` per residue -- `compute_repair_or_separator` returns a
single separator, not a basis of `ker(D^T)`, when `r` is not repairable.
Nothing in this repository currently computes, or proves complete, a
*basis* of the annihilator space.

R22 (`rocq/CycleQuotientDuality.v`'s `membership_iff_all_annihilate`,
realised concretely in `rocq/R21CycleQuotientBridge.v`) proves that
`r in im(D)` iff **every** annihilating functional vanishes at `r` --
quantifying over the whole annihilator space, not a finite generating
set of it. This is the intrinsic fact R23 needs to relate a
finite-coordinate signature back to: R23 is not a new mathematical
claim about repairability (R22 already fully characterises that), it is
a question about how to *present* the obstruction as a finite tuple of
numbers usable by an application, and what that presentation does and
does not preserve.

R24 (`rocq/InvertiblePresentation.v`, `rocq/CertificateTransport.v`)
proves that a single annihilating witness `y` transports contravariantly
under a certified invertible presentation change: `y' = B^{-T} y`, with
`(y')^T r' = y^T r` exactly. R23's own governing question -- what
happens to a signature built from `k` witnesses at once -- is a direct
generalisation of an already-proved single-witness fact, not an
unrelated one; §2 below traces exactly how.

Neither file has any notion of a finite basis of an annihilator space,
linear independence, spanning, or a fixed enumeration/ordering of
several witnesses at once. That machinery -- however small a version of
it R23 ends up needing -- does not exist in this repository yet and is
the actual new content this document scopes.

## 1. The three levels, kept distinct -- the central design decision

`docs/design/CYCLE_QUOTIENT_DUALITY_SPEC.md` §5 already flagged, for
R22, that deriving `SeparatesOutside` from general basis-bearing
finite-dimensional infrastructure ("Route B") was the highest-risk route
available and R22 avoided it, choosing instead to construct the
annihilator concretely from R21's own elimination procedure ("Route
C"). R23 revisits basis machinery for a different reason -- not to
*prove* annihilator-completeness (R22 already has that, without a
basis), but to *present* the intrinsic annihilator space as a finite,
application-usable signature. Keeping these three levels distinct,
exactly as the user's own framing states, is the one design decision
this whole document turns on:

1. **Intrinsic annihilator space**: `ker(D^T) = { y : D^T y = 0 }`.
   This is what R22 already fully characterises (`r in im(D) <->
   forall y in ker(D^T), y . r = 0`) and is basis-independent by
   construction -- it is a *set*, not a coordinate representation.
2. **A transported basis**: given a basis `y_1, ..., y_k` of `ker(D^T)`
   for the ORIGINAL presentation, R24 already proves each `y_i`
   transports to `y_i' = B^{-T} y_i` for the new presentation, with
   `(y_i')^T r' = y_i^T r` exactly. Whether `{y_1', ..., y_k'}` is
   itself a basis of `ker(D'^T)` for the transformed system needs its
   own (short) argument -- see §2 -- but is not yet a repository claim.
3. **A basis-relative obstruction signature**: `Omega_Y(r) := (y_1 . r,
   ..., y_k . r)`, a finite tuple depending on the CHOSEN ordered basis
   `Y = (y_1, ..., y_k)`, not on `r` or `D` alone. Two different bases
   of the same `ker(D^T)` give two different (but linearly related)
   signatures for the same `r`.

The central fact R23 must not blur: `Omega_Y(r) = 0` (all coordinates
vanish) is basis-independent -- it holds for one basis of `ker(D^T)` iff
it holds for every basis, since it is equivalent to the basis-free
statement `forall y in ker(D^T), y . r = 0`, which R22 already proves
equivalent to `r in im(D)`. But the individual NUMBERS `y_i . r` are
not basis-independent, and neither, without further argument, is
whether `{y_1, ..., y_k}` is complete (spans all of `ker(D^T)`) --
"complete obstruction signature" in this document's title means
"complete AS A BASIS of the annihilator space", a hypothesis to be
supplied or separately established, not a property of the tuple
`Omega_Y(r)` itself.

## 2. How a signature transports -- traced from R24, not assumed

Given a presentation change `(A, B)` (R24's own `InvertibleMatrix`
records) and a basis `Y = (y_1, ..., y_k)` of `ker(D^T)`, define the
transported basis `Y' := (y_1', ..., y_k')` with `y_i' :=
transport_separator_vector B y_i = B^{-T} y_i` (R24's own operation,
applied pointwise to each basis vector). Two facts, at different levels
of difficulty:

- **Pairing transport, already proved.** For each `i`, IF `y_i . r = c`
  for some fixed scalar `c` in the sense R24's `transport_pairing`
  needs (that theorem is stated for the specific value `1`; the general
  scalar case is a straightforward generalisation, not proved here but
  not expected to be hard -- flagged as an open item, §4.2), THEN
  `y_i' . r' = c` too. Applied to all `k` basis vectors at once, this
  gives `Omega_{Y'}(r') = Omega_Y(r)` COORDINATE-WISE, i.e. the
  transported basis's signature for the transported residue equals the
  original basis's signature for the original residue, exactly, not up
  to reordering or scaling. This is the sense in which "the signature
  transports": under a presentation change AND a correspondingly
  transported basis, the coordinate tuple is invariant.
- **Basis-completeness transport, NOT yet established.** Whether `Y'`
  is still a BASIS of `ker(D'^T)` -- i.e. still linearly independent
  and still spans the transformed annihilator space -- needs its own
  argument. The expected shape (linear independence and spanning are
  both preserved by an invertible linear change of basis on the
  ambient space) is standard linear algebra, but "standard" is exactly
  the phrase this repository's own history (`CYCLE_QUOTIENT_DUALITY
  _SPEC.md` §5, `CERTIFICATE_TRANSPORT_SPEC.md` §2's own
  transpose/inverse identities) has repeatedly found needs an actual
  compiling proof before being trusted, not assumed. This is Open
  Question §4.1, not resolved here.

If a DIFFERENT basis `Z = (z_1, ..., z_k)` of the SAME `ker(D^T)` is
selected instead of transporting `Y`, the two signatures `Omega_Y(r)`
and `Omega_Z(r)` are related by the (invertible) change-of-basis matrix
between `Y` and `Z` -- an ordinary linear-algebra fact about coordinate
representations, not a new theorem about repairability. R23 needs to
state this precisely enough that a reader cannot confuse "the signature
changed" with "the obstruction changed": it did not, only its
coordinates did.

## 3. The two candidate theorems, sized honestly

### 3.1. Modest R23 (recommended first target)

Given a SUPPLIED basis of `ker(D^T)` -- as a hypothesis, not computed --
prove:

```coq
Theorem signature_zero_iff_repairable :
  forall (m n k : nat) (D : MatrixQc m n) (Y : Vector.t (qcvec m) k)
         (r : qcvec m),
    IsBasisOfAnnihilator D Y ->    (* supplied hypothesis, not derived here *)
    (forall i : Fin.t k, dot_qc (Vector.nth Y i) r = Q2Qc 0) <->
    (exists b, mat_vec_qc D b = r).
```

`IsBasisOfAnnihilator` would need only: each `Y i` annihilates `D`
(`mat_vec_qc (transpose_qc D) (Y i) = zero`), and completeness in the
weak sense R22 already gives access to -- `(forall i, dot_qc (Y i) r =
0) -> mat_vec_qc (transpose_qc D) y = zero -> dot_qc y r = 0` for
arbitrary `y` (i.e. `Y`'s annihilation is equivalent to full
annihilator-membership for the purposes of THIS residue `r`), rather
than a full independent basis/spanning proof for `ker(D^T)` as an
abstract vector space. This is deliberately weaker than "`Y` spans
`ker(D^T)`" as a general fact and is likely provable directly from
R22's `membership_iff_all_annihilate` plus R21's own linear algebra,
without new basis-theory infrastructure.

This avoids implementing basis COMPUTATION entirely -- the caller
supplies `Y` and its annihilation/completeness evidence, exactly as
R24's `InvertibleMatrix` avoids implementing matrix inversion by taking
the inverse as a supplied witness. Mathematically clean, small, and
directly buildable from R22 and R21 as they stand today.

### 3.2. Full computational R23 (separately scoped, larger)

Compute an actual basis of `ker(D^T)` from `D` (almost certainly via a
variant of R21's own Gauss-Jordan elimination, extracting the full
nullspace rather than one witness), and certify:

- **annihilation**: every computed `y_i` satisfies `D^T y_i = 0`;
- **linear independence**: no nontrivial rational combination of the
  `y_i` is zero;
- **spanning**: every `y` with `D^T y = 0` is a rational combination of
  the `y_i`;
- **deterministic ordering**: the same `D` always produces the same
  `Y` in the same order, so `Omega_Y` is a well-defined function of `D`
  alone (not merely of `D` and an arbitrary choice).

This is a genuinely larger milestone: it needs proof-carrying basis
computation (extending R21's elimination to expose the FULL nullspace,
not just an inconsistent-row witness) and completeness evidence in the
strong sense, not the weak per-residue sense §3.1 needs. It is the
"Route B"-flavoured risk `CYCLE_QUOTIENT_DUALITY_SPEC.md` §5 already
named for R22 and R22 avoided -- not identical (this is concrete `Qc`
matrix nullspace computation, not abstract `VSpace` basis theory,
closer to that document's "Route C"), but comparable in that it is a
real, separate piece of exact-rational linear algebra this repository
does not have, not a small extension of what R21/R22/R24 already prove.

### 3.3. Recommendation

Modest R23 (§3.1) first, completely, before deciding whether full
computational R23 (§3.2) is needed at all. Meridian's own near-term
signature use ("these four transformation declarations form an
inconsistent loop", per the Meridian roadmap's R30 rationale) may only
need §3.1's guarantee -- that a *given* annihilator basis correctly
detects repairability -- with basis computation handled outside Rocq
(e.g. by R21's existing elimination, informally, with the Rocq theorem
providing the correctness guarantee once a basis is in hand) until a
concrete need for a certified computation surfaces. This mirrors R24's
own resolved question (explicit witnesses now, constructive inversion
deferred) and R22's own resolved question (Route C, not Route B).

## 4. Open questions this document does not resolve

1. **Whether transported basis-completeness (§2) needs its own Rocq
   proof before Modest R23, or can be deferred.** Modest R23 (§3.1)
   does not itself require this -- it takes `Y` and its completeness as
   a hypothesis for A GIVEN presentation, not across a transport. It
   only becomes necessary once R23 is combined with R24 to state
   "signatures transport", which is a natural but SEPARATE corollary,
   not part of Modest R23's own content.
2. **Whether `transport_pairing`/`transport_pairing_reverse` need
   generalising from the fixed scalar `1` to an arbitrary scalar `c`.**
   Used informally in §2; not yet stated or proved as a repository
   theorem. Likely a straightforward generalisation of the existing
   proof (replace the hypothesis `dot_qc y r = Q2Qc 1` with `dot_qc y r
   = c` throughout and re-check `ring`/`Qc` arithmetic steps go through
   unchanged), but not yet checked by an actual compiling proof, so not
   assumed.
3. **Whether `IsBasisOfAnnihilator`'s weak, per-residue-implicit
   completeness notion (§3.1) is the right long-term vocabulary, or
   whether R23 will eventually need genuine linear-independence/
   spanning definitions regardless (e.g. to state that two different
   supplied bases give consistent signatures in general, not just for
   one `r` at a time).** Deferred; §3.1's weak notion is recommended as
   the smaller starting hypothesis, not claimed to be the final one.
4. **Whether a signature needs its own certificate-schema field**,
   mirroring `CERTIFICATE_TRANSPORT_SPEC.md` §5.5's identical open
   question for presentation transforms. Recommend the same answer:
   out of scope for the Rocq theorem itself, picked up only once a
   concrete adapter needs it.

## 5. What this document does not claim

- That `IsBasisOfAnnihilator`, `signature_zero_iff_repairable`, or any
  other named construction above has been proved, prototyped, or even
  fully checked to typecheck as stated -- every theorem signature in §3
  is a proposed target, not a result.
- That the transported-basis-completeness argument sketched informally
  in §2 has been verified by an actual compiling Rocq proof -- flagged
  in §4.1 as an open question, not assumed to be easy or hard.
- That Modest R23 (§3.1) and Full computational R23 (§3.2) are the only
  two possible scopings -- they are the two this document identifies as
  most useful to distinguish; a future revision may find a different
  cut point more useful once §3.1 is actually attempted.
- That this connects to any real Meridian signature use case --
  `docs/design/CERTIFICATE_TRANSPORT_SPEC.md` §4's own caveat about not
  decomposing real Meridian scenarios applies equally here.
- That this is the next authorized phase. Per this repository's own
  precedent, starting any tracked implementation from this document --
  including §3.1's smaller first theorem -- needs its own explicit
  go-ahead.
