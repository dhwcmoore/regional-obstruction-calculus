(*
   AbstractSeparation.v

   R22, layer 1 (abstract): the vector-space and separation
   infrastructure `docs/design/CYCLE_QUOTIENT_DUALITY_SPEC.md` scoped as
   missing before D1's hard direction, D2's mirror, or D4 (certificate
   completeness) could be proved -- none of which is free, that document
   found, and none of which was previously committed to any tracked file.

   WHY A NEW RECORD, NOT THE EXISTING VSpace: this repository already has
   a `VSpace` record (`RefinementWitnessParallelComposition.v` and
   others), but it is deliberately minimal -- five laws (associativity,
   LEFT identity only, scalar distributing over vector addition, scalar
   composition, scale-by-zero-vector) -- sufficient for its own uses
   (LinComb, InSpan span arguments) but not for this file's purposes.
   Checked directly, by compiling three small probes against that exact
   record before writing this one: `vadd a vzero = a` (right identity),
   `vadd a b = vadd b a` (commutativity), and `vscale 1 a = a` are each
   NOT derivable from its five laws. Consequently no additive inverse is
   derivable either, and the injectivity direction of cycle-quotient
   duality needs one: the natural proof separates `r1` and `r2` by
   applying `SeparatesOutside` to their difference, which cannot even be
   constructed, let alone reasoned about, without one. `AbelianVSpace`
   below is a strictly stronger, separate record for this reason --
   deliberately not an extension of the existing `VSpace` (which would
   require updating every existing `mkVSpace` call site to supply new
   proof obligations for laws those files never needed) and not reused by
   any other file in this repository.

   WHY NOT SETOID-BASED FROM THE START: `CYCLE_QUOTIENT_DUALITY_SPEC.md`
   itself already found that a *Q-valued* Leibniz `VSpace` (`QSpace`)
   fails to exist, because `Qplus_assoc`/`Qmult_assoc` in the standard
   library are `Qeq`, not Leibniz, facts -- the same wrinkle
   `AssociatorResidueRepair.v`'s `ceq` generalisation already worked
   around once. `IsLinearFunctional` below sidesteps that specific
   problem exactly as that design document did: `phi`'s CODOMAIN
   equations are stated with `==` (`Qeq`), never requiring `Q` itself to
   be an `AbelianVSpace` instance. `phi`'s DOMAIN, `carrier S`, is a
   genuine `AbelianVSpace` with Leibniz `=` laws -- which a *further*
   check (not this file's problem to solve, flagged for whoever writes
   the concrete instance) found is not free either for `carrier := list
   Q` under pointwise operations, for the identical underlying reason:
   `Qplus`'s general/symbolic associativity is not Leibniz-provable
   (`reflexivity`/`ring` both fail on the universally quantified
   statement, confirmed directly, even though some concrete numeral
   instances happen to compute out equal). This file does not attempt a
   concrete instance and takes no position on how that will be resolved.

   Nothing in this file depends on any other file in this repository, in
   keeping with `ExactRationalRepairOrSeparator.v` (R21)'s own
   self-contained precedent.
*)

Require Import Coq.QArith.QArith.

(* ------------------------------------------------------------------ *)
(* AbelianVSpace: a genuine finite-dimensional-capable vector space
   over Q, under Leibniz equality. Strictly stronger than this
   repository's existing VSpace record -- see header. *)
(* ------------------------------------------------------------------ *)

Record AbelianVSpace := mkAbelianVSpace {
  carrier : Type;
  vzero : carrier;
  vadd : carrier -> carrier -> carrier;
  vneg : carrier -> carrier;
  vscale : Q -> carrier -> carrier;
  vadd_assoc : forall a b c, vadd (vadd a b) c = vadd a (vadd b c);
  vadd_zero_l : forall a, vadd vzero a = a;
  vadd_comm : forall a b, vadd a b = vadd b a;
  vadd_zero_r : forall a, vadd a vzero = a;
  vadd_vneg : forall a, vadd a (vneg a) = vzero;
  vscale_distrib_vadd : forall c a b, vscale c (vadd a b) = vadd (vscale c a) (vscale c b);
  vscale_compose : forall c d a, vscale c (vscale d a) = vscale (c * d) a;
  vscale_vzero : forall c, vscale c vzero = vzero;
  vscale_one : forall a, vscale 1 a = a;
  vscale_qplus : forall c d a, vscale (c + d) a = vadd (vscale c a) (vscale d a);
}.

Arguments vzero {_}.
Arguments vadd {_} _ _.
Arguments vneg {_} _.
Arguments vscale {_} _ _.

(* Subtraction, derived, not primitive -- exists precisely because
   AbelianVSpace (unlike the existing VSpace) supplies vneg. *)
Definition vsub (S : AbelianVSpace) (a b : carrier S) : carrier S :=
  vadd a (vneg b).

Lemma vsub_self : forall (S : AbelianVSpace) (a : carrier S), vsub S a a = vzero.
Proof. intros S a. unfold vsub. apply vadd_vneg. Qed.

(* Scaling by the rational 0 gives the zero vector -- for a general
   vector, not just vzero itself (that is vscale_vzero, a different,
   primitive law). Derived from idempotence (vscale 0 a = vadd (vscale 0 a)
   (vscale 0 a), via vscale_qplus at 0 = 0 + 0) plus cancellation. *)
Lemma vscale_zero_vec : forall (S : AbelianVSpace) (a : carrier S), vscale 0 a = vzero.
Proof.
  intros S a.
  assert (Hidem : vscale 0 a = vadd (vscale 0 a) (vscale 0 a)).
  {
    rewrite <- (vscale_qplus S 0 0 a).
    f_equal; ring.
  }
  set (X := vscale 0 a) in *.
  assert (Hvz : vadd (vneg X) X = vzero).
  { rewrite (vadd_comm S (vneg X) X). apply vadd_vneg. }
  assert (Hchain : vadd (vneg X) (vadd X X) = X).
  {
    rewrite <- (vadd_assoc S (vneg X) X X).
    rewrite Hvz.
    apply vadd_zero_l.
  }
  rewrite <- Hidem in Hchain.
  rewrite Hvz in Hchain.
  symmetry. exact Hchain.
Qed.

Lemma vsub_add_cancel :
  forall (S : AbelianVSpace) (a b : carrier S), vadd b (vsub S a b) = a.
Proof.
  intros S a b. unfold vsub.
  rewrite <- (vadd_assoc S b a (vneg b)).
  rewrite (vadd_comm S b a).
  rewrite (vadd_assoc S a b (vneg b)).
  rewrite (vadd_vneg S b).
  apply vadd_zero_r.
Qed.

(* ------------------------------------------------------------------ *)
(* Linear functionals into Q, and the separation property. Codomain
   equations use Qeq (==), never requiring Q itself to be an
   AbelianVSpace instance -- see header. *)
(* ------------------------------------------------------------------ *)

Definition IsLinearFunctional (S : AbelianVSpace) (phi : carrier S -> Q) : Prop :=
  phi vzero == 0 /\
  (forall a b : carrier S, phi (vadd a b) == phi a + phi b) /\
  (forall (c : Q) (a : carrier S), phi (vscale c a) == c * phi a).

Definition Annihilator (S : AbelianVSpace) (B : carrier S -> Prop)
    (phi : carrier S -> Q) : Prop :=
  forall b : carrier S, B b -> phi b == 0.

Definition SeparatesOutside (S : AbelianVSpace) (B : carrier S -> Prop) : Prop :=
  forall x : carrier S,
    ~ B x ->
    exists phi : carrier S -> Q,
      IsLinearFunctional S phi /\ Annihilator S B phi /\ ~ (phi x == 0).

(* Additive inverses are unique in any AbelianVSpace: if vadd b x = vzero
   and vadd b y = vzero then x = y. Used once below to identify
   vscale (-1) b with vneg b. *)
Lemma vadd_inverse_unique :
  forall (S : AbelianVSpace) (b x y : carrier S),
    vadd b x = vzero -> vadd b y = vzero -> x = y.
Proof.
  intros S b x y Hx Hy.
  assert (Hx' : vadd (vneg b) (vadd b x) = vadd (vneg b) vzero) by (rewrite Hx; reflexivity).
  assert (Hy' : vadd (vneg b) (vadd b y) = vadd (vneg b) vzero) by (rewrite Hy; reflexivity).
  rewrite <- (vadd_assoc S (vneg b) b x) in Hx'.
  rewrite <- (vadd_assoc S (vneg b) b y) in Hy'.
  rewrite (vadd_comm S (vneg b) b) in Hx', Hy'.
  rewrite (vadd_vneg S b) in Hx', Hy'.
  rewrite (vadd_zero_l S x) in Hx'.
  rewrite (vadd_zero_l S y) in Hy'.
  rewrite (vadd_zero_r S (vneg b)) in Hx', Hy'.
  rewrite Hx', Hy'.
  reflexivity.
Qed.

(* vneg is exactly scaling by -1 -- lets linearity's own scaling clause
   compute phi (vneg b) directly. *)
Lemma vneg_is_scale_neg_one : forall (S : AbelianVSpace) (b : carrier S), vneg b = vscale (-1) b.
Proof.
  intros S b.
  apply (vadd_inverse_unique S b).
  - apply vadd_vneg.
  - rewrite <- (vscale_one S b) at 1.
    rewrite <- (vscale_qplus S 1 (-1) b).
    replace (1 + -1) with 0 by reflexivity.
    apply vscale_zero_vec.
Qed.

(* A linear functional's value on a difference: phi (a - b) == phi a - phi b.
   Needed by QuotientEvaluation.v; stated here since it is a direct
   consequence of IsLinearFunctional alone (additivity plus the c = -1
   scaling case), not of SeparatesOutside. *)
Lemma linear_functional_vsub :
  forall (S : AbelianVSpace) (phi : carrier S -> Q) (a b : carrier S),
    IsLinearFunctional S phi -> phi (vsub S a b) == phi a - phi b.
Proof.
  intros S phi a b [Hzero [Hadd Hscale]].
  unfold vsub.
  rewrite Hadd.
  rewrite (vneg_is_scale_neg_one S b).
  rewrite (Hscale (-1) b).
  ring.
Qed.
