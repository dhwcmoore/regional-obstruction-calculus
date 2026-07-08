(*
   FourCycleObstruction.v

   A concrete instantiation, inside Rocq, of the four-cycle obstruction
   witness of the paper's Section "The four-region obstruction witness"
   (examples/four_cycle.json, residue_classifier.py, refinement_witnesses
   .COARSE): the same coboundary map, residue r = (1,1,1,-2), and cycle
   z = (-1,-1,-1,1), with the pairing <z,r> computed and shown non-zero
   *inside* Rocq, concluding non-repairability via direct application of
   AssociatorResidueRepair.v's abstract Layer-1 theorem
   `nonzero_pairing_blocks_repair_mod_ceq`, instantiated with `ceq := veq`
   (componentwise Qeq on 4-tuples, defined below) -- not its Leibniz
   specialisation.

   What this file does NOT prove: it does not prove that the Python
   associator compiler (associator_residue.py) generated this r, and it
   does not mechanise finite_algebra.py or regional_composition.py. It
   proves that the concrete four-cycle obstruction, once stated inside
   Rocq with the paper's own numbers, has the claimed cohomological
   content:

       r = (1, 1, 1, -2)
       z = (-1, -1, -1, 1)
       <z, r> = -5
       -5 <> 0
       therefore r is not a coboundary
       therefore no repair exists, by AssociatorResidueRepair.v.

   Vertices/corrections b, and seams, are represented as 4-tuples of Q
   (`vec4` below): C0 in the order (U1,U2,U3,U4), C1/Z1 in the order
   (e12,e23,e34,e14) -- matching examples/four_cycle.json's
   `coboundary_0` matrix and refinement_witnesses.COARSE exactly:

       delta0 b = (b1-b0, b2-b1, b3-b2, b3-b0)

   (row 4 is b3-b0, i.e. -1,0,0,1 on (b0,b1,b2,b3), matching the JSON
   matrix's fourth row ["-1","0","0","1"] and Edge("e14","U1","U4")).

   On equality: vec4's meaningful equality is *componentwise Qeq*
   (`veq` below), not Leibniz `=`. Two representations of the same
   rational (e.g. 1#1 and 2#2) are veq-equal but not Leibniz-equal, and a
   non-repairability theorem stated only for Leibniz equality on `delta0
   b = r` would not, in general, rule out a "repair" whose coboundary is
   rational-equal to r via a differently-represented Q value. This used
   to require a hand-written, file-local proof of that fact; now that
   AssociatorResidueRepair.v takes the equivalence relation as an
   explicit parameter, `four_cycle_not_repairable` below is obtained by
   *direct application* of its abstract theorem with `ceq := veq`, and
   `pairing_congr` below is exactly the `pairing_respects_ceq` witness
   that theorem requires.

   A second, Leibniz-flavoured corollary (`four_cycle_not_repairable_
   leibniz`) is also proved, by direct application of
   AssociatorResidueRepair.v's `nonzero_pairing_blocks_repair` (itself now
   a corollary of the ceq-generalised theorem) with no adaptation, kept
   only to demonstrate that convenience corollary is still directly usable.
   It is a strictly weaker statement than `four_cycle_not_repairable`
   (Leibniz-equal implies veq-equal, so ruling out fewer b's is an easier
   claim) and is not the paper's actual claim.

   The associator layer of AssociatorResidueRepair.v
   (`nontrivial_associator_residue_not_repairable_mod_ceq`, with
   `AssocData` / `BoundaryCorrection` left abstract) is deliberately not
   instantiated here. Doing so honestly requires a concrete `AssocData`
   matching regional_composition.py's construction, which is the
   expensive mechanisation step explicitly deferred; a dummy `AssocData`
   whose residue is definitionally `r` would prove nothing beyond what
   `four_cycle_not_repairable` already proves.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import Coq.Classes.RelationClasses.
Require Import AssociatorResidueRepair.

(* ------------------------------------------------------------------ *)
(* Concrete cochain spaces.                                             *)
(* ------------------------------------------------------------------ *)

Record vec4 := mkvec4 { v0 : Q; v1 : Q; v2 : Q; v3 : Q }.

Definition veq (x y : vec4) : Prop :=
  v0 x == v0 y /\ v1 x == v1 y /\ v2 x == v2 y /\ v3 x == v3 y.

Lemma veq_refl : forall x, veq x x.
Proof. intro x; unfold veq; repeat split; reflexivity. Qed.

Lemma veq_sym : forall x y, veq x y -> veq y x.
Proof.
  intros x y [h0 [h1 [h2 h3]]]; unfold veq; repeat split; symmetry; assumption.
Qed.

Lemma veq_trans : forall x y w, veq x y -> veq y w -> veq x w.
Proof.
  intros x y w [h0 [h1 [h2 h3]]] [k0 [k1 [k2 k3]]]; unfold veq; repeat split.
  - rewrite h0; exact k0.
  - rewrite h1; exact k1.
  - rewrite h2; exact k2.
  - rewrite h3; exact k3.
Qed.

Instance veq_equivalence : Equivalence veq := {
  Equivalence_Reflexive := veq_refl;
  Equivalence_Symmetric := veq_sym;
  Equivalence_Transitive := veq_trans
}.

(* delta^0 : C0 -> C1, matching examples/four_cycle.json's coboundary_0
   matrix row-for-row (see header comment for the row-4 orientation). *)
Definition delta0 (b : vec4) : vec4 :=
  mkvec4 (v1 b - v0 b) (v2 b - v1 b) (v3 b - v2 b) (v3 b - v0 b).

(* <z, r> = z0 r0 + z1 r1 + z2 r2 + z3 r3, matching
   rational_linear_algebra.dot / Lemma lem:cycle-pairing. *)
Definition pairing (z r : vec4) : Q :=
  v0 z * v0 r + v1 z * v1 r + v2 z * v2 r + v3 z * v3 r.

(* Exactly the `pairing_respects_ceq` obligation of
   nonzero_pairing_blocks_repair_mod_ceq, instantiated with ceq := veq. *)
Lemma pairing_congr :
  forall z x y, veq x y -> pairing z x == pairing z y.
Proof.
  intros z x y [h0 [h1 [h2 h3]]]; unfold pairing; rewrite h0, h1, h2, h3; reflexivity.
Qed.

(* z is a cycle iff it annihilates every coboundary -- proved for the
   declared z below (z_is_cycle), not assumed. *)
Definition cycle (w : vec4) : Prop :=
  forall b : vec4, pairing w (delta0 b) == 0.

(* Exactly the `coboundaries_pair_zero` obligation of both Layer-1
   theorems; a one-line unfolding of `cycle`'s own definition. *)
Lemma coboundaries_pair_zero :
  forall (w : vec4) (b : vec4), cycle w -> pairing w (delta0 b) == 0.
Proof.
  intros w b Hcycle; apply Hcycle.
Qed.

(* ------------------------------------------------------------------ *)
(* The declared witness data, matching examples/four_cycle.json /       *)
(* refinement_witnesses.COARSE exactly.                                 *)
(* ------------------------------------------------------------------ *)

Definition r : vec4 := mkvec4 1 1 1 (-2).
Definition z : vec4 := mkvec4 (-1) (-1) (-1) 1.

Lemma z_is_cycle : cycle z.
Proof.
  unfold cycle, pairing, delta0, z; intro b; simpl; ring.
Qed.

Lemma four_cycle_pairing : pairing z r == -5.
Proof. unfold pairing, r, z; simpl; ring. Qed.

Lemma four_cycle_pairing_nonzero : ~ (pairing z r == 0).
Proof.
  rewrite four_cycle_pairing.
  intro H.
  compute in H.
  discriminate H.
Qed.

(* ------------------------------------------------------------------ *)
(* The theorem that matches the paper's claim: direct application of    *)
(* AssociatorResidueRepair.v's abstract theorem with ceq := veq.        *)
(* ------------------------------------------------------------------ *)

Theorem four_cycle_not_repairable :
  ~ (exists b : vec4, veq (delta0 b) r).
Proof.
  exact (nonzero_pairing_blocks_repair_mod_ceq
           vec4 vec4 vec4 delta0 pairing cycle
           veq veq_equivalence pairing_congr
           coboundaries_pair_zero r z z_is_cycle four_cycle_pairing_nonzero).
Qed.

(* ------------------------------------------------------------------ *)
(* A Leibniz-flavoured corollary, by direct, unmodified application of  *)
(* AssociatorResidueRepair.v's Leibniz-specialised theorem -- included   *)
(* only to demonstrate that convenience corollary is still directly     *)
(* usable. Note this is a strictly weaker statement than                *)
(* four_cycle_not_repairable above; see the header comment.             *)
(* ------------------------------------------------------------------ *)

Theorem four_cycle_not_repairable_leibniz :
  ~ (exists b : vec4, delta0 b = r).
Proof.
  exact (nonzero_pairing_blocks_repair
           vec4 vec4 vec4 delta0 pairing cycle
           coboundaries_pair_zero r z z_is_cycle four_cycle_pairing_nonzero).
Qed.
