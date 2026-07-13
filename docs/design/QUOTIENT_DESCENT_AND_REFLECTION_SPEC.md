# Quotient Descent and Reflection: What N0 and E0 Actually Mean on the Obstruction Quotient

**Status (2026-07-12): design only, nothing in this document is
committed as a repository proof.** Every claim below about what is and
is not provable, and under exactly which hypotheses, was checked by
actually compiling a scratch prototype against this repository's real
`RefinementWitnessVerdictComposition.v` (Coq/Rocq 8.18.0, the pinned
toolchain) before being written down here — not derived on paper and
assumed to go through. The prototype is not part of this repository (it
lives outside `rocq/`, is not `Require`-able from any tracked file, and
is not referenced by the Makefile); this document states its results
precisely enough that a future implementation phase does not need to
re-derive them, only re-prove them as tracked, `coqchk`-checked theorems.

The governing question, unchanged from how it was posed:

> Under the existing N0 condition, does residue transport descend to
> equivalence classes modulo coboundaries, and is E0 precisely the
> condition that the descended map is injective?

The answer is yes, precisely, under a hypothesis set that is slightly
more specific than the informal sketch proposing this document assumed
— see §2. That correction does not weaken the result; it is exactly the
kind of thing this project's own discipline (§0 of
`PRESENTATION_INVARIANCE_SPEC.md`) says must be checked, not assumed,
before it goes into a tracked proof.

## 0. What already exists and is reusable

`RefinementWitnessVerdictComposition.v` (built for an unrelated purpose
— proving (E0) composes under sequential refinement) already contains
exactly the "smallest algebraic layer" this ladder needs the shape of:
a `VSpace` record (`carrier`, `vzero`, `vadd`, `vscale`, closure and
distributivity laws), `IsLinear`, `InSpan`, and
`linear_maps_preserve_span`. This is real, `coqchk`-clean, reusable
infrastructure — the danger §0 of `PRESENTATION_INVARIANCE_SPEC.md`
named (recreating the abandoned four-condition scaffold) is
substantially smaller than it looked before checking, because most of
what a fresh build would need already exists, tested, in this
repository.

**It is not, however, sufficient as-is**, and this was not obvious
without trying to use it. §1 states exactly what is missing and why.

## 1. Finding: `VSpace` needs three additional standard laws

`VSpace`'s current fields are `vadd_assoc`, `vadd_zero_l`,
`vscale_distrib_vadd`, `vscale_compose`, `vscale_vzero` — enough to
prove that linear maps preserve spans (addition and scaling only, never
needed subtraction or a scalar identity). Attempting to prove even the
most basic subtraction fact, `vsub a a = vzero` where `vsub a b := vadd
a (vscale (-1) b)`, fails: it is not derivable from what is there. Three
further, entirely standard laws are needed, verified by adding them as
local hypotheses and confirming the intended lemmas then go through:

```coq
vadd_comm  : forall a b, vadd a b = vadd b a
vadd_inv   : forall a,   vadd a (vscale (-1) a) = vzero
vscale_one : forall a,   vscale 1 a = a
```

This is not a defect in `RefinementWitnessVerdictComposition.v` — it
built exactly what its own theorems needed. Every concrete instance
these theorems will ever run against (finite-dimensional `Q^n` under
componentwise operations) satisfies all three for free; adding them as
new `VSpace` record fields (or a `VSpace` extension record, a design
choice for the implementation phase, not this document) is a small,
standard, easily-justified addition — not a new scaffold.

**A second, smaller finding worth flagging now rather than during
implementation**: proving even simple scalar identities like `(-1) * (-1)
= 1` over `Q` needs care. `ring` fails on a bare Leibniz `Q` equality
goal (`Error: Goal is not an equation (of expected equality) Qeq`) —
this repository has hit exactly this Leibniz-versus-`Qeq` distinction
before, which is why `AssociatorResidueRepair.v` was generalised from
Leibniz equality to a caller-supplied `ceq`. `reflexivity` sufficed for
the one identity this prototype needed, because `Qmult` on two already-
reduced integer literals happens to compute to a reduced result
directly — but a real instantiation with less trivial scalars (as
`Qplus` produces, via cross-multiplication, an unreduced fraction) will
likely need the same `ceq`-style treatment this repository already has
a working pattern for, not a fresh one.

## 2. The correction: quotient descent needs `rho1star` linear, not just N0

The informal sketch that proposed this document reasoned: "N0 says
`f(B) subseteq B'`. That is exactly what is needed for `f` to descend to
a quotient map." Checked directly, this is imprecise in a way that
matters for what gets declared as a Rocq hypothesis.

N0, exactly as it is stated in `CochainNaturalityDescent.v` and used
throughout this repository (`forall b, rho1star (delta0 b) = delta0'
(rho0star b)`), is a fact about arbitrary **functions** — it assumes no
linearity of `rho1star`, `rho0star`, `delta0`, or `delta0'` anywhere.
Under N0 alone, one specific fact is free: `f` maps `im(delta0)` *into*
`im(delta0')` (apply N0 to any `b`). That is a set-membership fact, not
quotient-map well-definedness.

Well-definedness of the *induced map on the quotient* — `[r] = [s]
implies [f(r)] = [f(s)]` for *arbitrary* `r`, `s`, not merely for `r`,
`s` individually already known to lie in `im(delta0)` — needs `f(r) -
f(s) = f(r - s)`, which holds only if `f` is additive. **This is a
genuinely new hypothesis, not implied by N0 as it is currently stated
anywhere in this repository.** Confirmed directly: the prototype's
`quotient_descent` theorem does not go through without a
`rho1star_linear : IsLinear S1 S1' rho1star` hypothesis declared
explicitly, alongside N0.

This matters for scope, stated precisely: `CommonSubdivisionVerdictInvariance.v`
(R17) works for `rho1star` an **arbitrary function** — it is, in this
specific sense, *more general* than what R18b/R19 below can be. R18b
and R19 are not a strengthening of R17's hypothesis-minimal style; they
are a different, more structured theorem, answering a different
question (what do N0 and E0 mean, algebraically) under a genuinely
narrower hypothesis set (the refinement maps must be linear). This
narrower class is not vacuous — the real four-cycle refinement maps
`refinement_checker.py` actually uses are literally described by
pullback matrices over `Q`, i.e. linear maps by construction — but the
abstract Rocq theorem should not be presented as subsuming R17's
generality, only as explaining what is happening algebraically in the
concrete case R17's theorem already covers structurally.

## 3. The theorem ladder, exact hypotheses, confirmed by a compiling prototype

Notation below matches the prototype exactly: `S0`, `S1`, `S0'`, `S1'`
are `VSpace`s (extended per §1); `delta0 : carrier S0 -> carrier S1`,
`delta0' : carrier S0' -> carrier S1'`, `rho0star : carrier S0 ->
carrier S0'`, `rho1star : carrier S1 -> carrier S1'`.

```coq
Definition vsub (S : VSpace) (a b : carrier S) : carrier S :=
  vadd S a (vscale S (-1)%Q b).

Definition Image (SA SB : VSpace) (f : carrier SA -> carrier SB) (v : carrier SB) : Prop :=
  exists u, f u = v.

Definition CobEquiv (S0_ S1_ : VSpace) (d : carrier S0_ -> carrier S1_) (r s : carrier S1_) : Prop :=
  Image S0_ S1_ d (vsub S1_ r s).
```

### R18a: `CobEquiv` (over `delta0`, on `S1`) is an equivalence relation

Needs: `delta0` linear (`IsLinear S0 S1 delta0`), the §1 `VSpace`
extension on `S1`. `CobEquiv_refl`, `CobEquiv_sym`, `CobEquiv_trans` —
all three confirmed to compile from these hypotheses alone.

### R18b: Quotient descent

```coq
Theorem quotient_descent :
  forall r s : carrier S1,
    CobEquiv S0 S1 delta0 r s -> CobEquiv S0' S1' delta0' (rho1star r) (rho1star s).
```

Needs: N0, and `rho1star` linear (`IsLinear S1 S1' rho1star`) — per §2,
genuinely required, not derivable from N0 alone. Does **not** need
`delta0'` linear, and does not need `rho0star` linear — `rho0star`
appears only through N0's own universally-quantified equation, never
operated on algebraically; this was not assumed, it fell out of the
proof not needing it.

### R19: E0 is equivalent to quotient injectivity

```coq
Definition E0 : Prop :=
  forall x : carrier S1,
    (exists b' : carrier S0', rho1star x = delta0' b') ->
    exists b : carrier S0, x = delta0 b.

Definition QuotientInjective : Prop :=
  forall r s : carrier S1,
    CobEquiv S0' S1' delta0' (rho1star r) (rho1star s) -> CobEquiv S0 S1 delta0 r s.

Theorem E0_iff_quotient_injective : E0 <-> QuotientInjective.
```

Note `E0` here is stated *exactly* as it already appears in
`CochainNaturalityDescent.v` and `ExactnessReflection.v` — unchanged,
not a new definition invented for this document, so a future proof of
this theorem can cite the existing condition directly rather than
introduce a rephrased one that needs its own justification of
equivalence to the original.

Needs, confirmed both directions compile from exactly these and no
more: N0, `rho1star` linear, `delta0` linear (needed for `CobEquiv` on
the `S1` side to be meaningful/an equivalence relation, via R18a).
**`delta0'` linear is not needed by this theorem's own proof term** —
it is needed only if one separately wants `CobEquiv` on the `S1'` side
to itself be a bona fide equivalence relation (R18a's mirror image on
the target side), a natural expectation for a symmetric-looking
definition, but logically independent of `E0_iff_quotient_injective`
itself. State both facts separately in the eventual tracked proof
rather than silently bundling `delta0'` linearity into this theorem's
hypotheses where it is not load-bearing.

No cycle space, transpose map, or annihilator/duality argument is used
anywhere in this derivation, confirming the informal sketch's own
observation that the quotient-kernel argument does not need them.

## 4. The dual characterisation: deferred, and correctly so

`ExactnessReflection.v` characterises E0 as `Z1(coarse) subseteq
rho_*(Z1(refined))` — cycle-space surjectivity via the pushforward,
`rational_linear_algebra.py`'s actual computational implementation.
Proving that characterisation equivalent to `QuotientInjective` above
needs the annihilator/duality fact this document's §3 explicitly does
not use. That remains genuinely later work, exactly as proposed: it
would connect the computational checker, the cycle-certificate
interpretation, and this quotient theory, but nothing in §3 depends on
it, and it should not be attempted inside the same proof file as R18a–
R19.

## 5. R20 is not "two injections therefore isomorphic" — restated correctly before any code is written

Once quotient descent exists for both legs of a common subdivision
(`rho1 : N12 -> N1`, `rho2 : N12 -> N2`, both descent-safe and
reflecting), R17 already gives `[r1] = 0 <-> [r2] = 0`. Quotient descent
plus R19 would additionally give that the induced maps `rho1bar :
Q1 -> Q12` and `rho2bar : Q2 -> Q12` (`Qi := C1_i / im(delta0_i)`) are
both injective. **Two injections into a common codomain do not, by
themselves, give an isomorphism `Q1 iso Q2`** — that needs their images
in `Q12` to coincide, or an explicit surjectivity condition, neither of
which follows from injectivity alone. The correct next honest claim,
once this ladder exists, is:

> The two distinguished obstruction classes `[r1]`, `[r2]` embed
> faithfully into the common-subdivision quotient `Q12`, and have the
> same image there (`rho1bar([r1]) = rho2bar([r2])`, immediate from
> `rho1_1star r1 = rho2_1star r2`, the shared-transferred-residue
> hypothesis every theorem in this line already carries).

That is strictly stronger than R17's simultaneous-vanishing statement,
and strictly weaker than a claimed isomorphism `Q1 iso Q2` — proving the
latter is not proposed here and should not be attempted without first
checking, the same way §2 checked quotient descent, exactly what
hypothesis it would actually require.

## 6. What this document does not claim

- That any of R18a, R18b, R19 exist yet as tracked, `coqchk`-checked
  Rocq theorems. Only a scratch prototype exists, outside version
  control, used to verify the claims above are actually provable before
  writing them down as a plan.
- That the `VSpace` extension (§1) has been added to
  `RefinementWitnessVerdictComposition.v` or anywhere else in this
  repository. Whether to extend that record in place, or introduce a
  separate, richer record for this ladder specifically, is an open
  implementation decision, not resolved here.
- That R18b/R19's hypothesis set (linear `delta0`, linear `rho1star`)
  generalises, subsumes, or narrows R17. It is a different theorem
  about a narrower class of refinement maps (§2), answering a different
  question (what N0/E0 mean algebraically), not a strictly stronger
  version of R17.
- That the cycle-surjectivity characterisation of E0
  (`ExactnessReflection.v`'s own framing) has been shown equivalent to
  quotient injectivity. §4 states precisely what remains to prove and
  why it is deferred.
- That class-level invariance in the strong sense (`Q1 iso Q2`) has been
  established, or is even the correct next target. §5 states the
  honest, weaker, actually-supported next claim.
- That any code outside this document (Python, OCaml, or `veribound-fce`)
  is affected by anything here.
