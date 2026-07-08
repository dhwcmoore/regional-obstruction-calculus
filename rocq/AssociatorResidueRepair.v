(*
   AssociatorResidueRepair.v

   Proves the abstract repair-impossibility inference that the associator-
   generation layer (finite_algebra.py, regional_composition.py,
   associator_residue.py, repair_solver.py) exemplifies computationally:

     associator defect -> seam residue -> repair equation
       -> obstruction to global correction.

   Equality on C1 (the repair equation's target type) is a caller-supplied
   equivalence relation `ceq`, not Leibniz `=`. This is not a stylistic
   choice: FourCycleObstruction.v instantiates C1 with 4-tuples of Q, whose
   meaningful equality is componentwise Qeq, and two representations of
   the same rational (1#1 and 2#2) are Qeq-equal but not Leibniz-equal. A
   theorem proved only for `delta0 b = r` (Leibniz) would not, in general,
   rule out a "repair" whose coboundary is rational-equal to r via a
   differently-represented Q value -- it would prove a strictly weaker,
   less meaningful statement while looking superficially identical. Making
   `ceq` an explicit parameter, together with the hypothesis that
   `pairing` respects it, closes that gap once and for all instead of
   leaving each concrete instantiation to notice and patch around it
   individually.

   Four theorems, in increasing specificity:

   1. `nonzero_pairing_blocks_repair_mod_ceq` -- pure cohomology modulo an
      explicit equivalence `ceq` on C1. If a closed cycle z pairs
      non-zero with a residue r, then no b has `ceq (delta0 b) r`.

   2. `nonzero_pairing_blocks_repair` -- the Leibniz-equality specialisation
      of (1), obtained by instantiating `ceq := eq` and discharging the
      resulting `pairing_respects_ceq` obligation trivially (equal terms
      pair equally). Kept only as a convenience corollary for callers whose
      C1 has no finer structure than Leibniz equality (as in the fully
      abstract setting, where Leibniz is the *only* available equality);
      it is not the theorem to reach for once C1 is instantiated with
      something like Q-valued vectors -- see FourCycleObstruction.v, which
      uses (1) directly with `ceq := veq` (componentwise Qeq), not this
      corollary.

   3. `nontrivial_associator_residue_not_repairable_mod_ceq` -- the
      associator layer built on (1). AssocData and BoundaryCorrection are
      left abstract; only the bridge hypothesis that repairing A by b
      forces `ceq (delta0 (correction_coboundary b)) (associator_residue
      A)` is assumed (the Coq-level statement of the paper's repair
      quotient Ob_D = Field^2/im D, Section "Detection, repair, and
      obstruction"). Proved by direct application of (1).

   4. `nontrivial_associator_residue_not_repairable` -- the Leibniz
      specialisation of (3), analogous to (2), kept for the same reason.

   This file does not mechanise finite_algebra.py, regional_composition.py,
   the Venn model, JSON parsing, or any concrete structure constants; the
   concrete, computational side of the same theorem is checked by
   associator_residue.py / repair_solver.py, and the concrete four-cycle
   instance is checked inside Rocq itself by FourCycleObstruction.v, which
   `Require`s this file.

   Associator sign convention: this file is agnostic to how the residue
   was produced, but for the record, the convention used throughout this
   repository (paper Definition "Associator defect",
   finite_algebra.associator, regional_composition.associator_defect) is
   right-minus-left, a*(b*c) - (a*b)*c. Nothing here depends on that
   choice; it is recorded so the convention stays frozen across the
   paper, the Python code, and this file.

   This is a separate file from, and does not import,
   AdmissibleRefinementPersistence.v. The two theorems there concern
   refinement of a residue's *presentation*; the theorems here concern
   *repair* of an associator-generated residue. Nothing here depends on
   refinement, and nothing there depends on associator data. They are not
   merged, by design.

   Rational equality on Q throughout is QArith's setoid equality `==`
   (Qeq), not Coq's Leibniz `=`, for the same reason `ceq` is not Leibniz
   equality on C1: distinct representations of the same rational are
   `==`-equal but not `=`-equal, so Leibniz `<>` would be unsound for the
   non-zero-pairing hypotheses.
*)

Require Import QArith.
Require Import Coq.Classes.RelationClasses.

(* ------------------------------------------------------------------ *)
(* A generic helper: Leibniz equality trivially respects any Q-valued   *)
(* function, used to derive the Leibniz corollaries below.              *)
(* ------------------------------------------------------------------ *)

Lemma eq_respects_pairing :
  forall (Z1 C1 : Type) (pairing : Z1 -> C1 -> Q) (z : Z1) (r r' : C1),
    r = r' -> pairing z r == pairing z r'.
Proof.
  intros Z1' C1' pairing0 z0 r0 r0' Heq.
  rewrite Heq.
  reflexivity.
Qed.

(* ------------------------------------------------------------------ *)
(* Layer 1: pure cohomology, modulo an explicit equivalence on C1.      *)
(* ------------------------------------------------------------------ *)

Theorem nonzero_pairing_blocks_repair_mod_ceq :
  forall (C0 C1 Z1 : Type)
         (delta0 : C0 -> C1)
         (pairing : Z1 -> C1 -> Q)
         (cycle : Z1 -> Prop)
         (ceq : C1 -> C1 -> Prop)
         (ceq_equiv : Equivalence ceq)
         (pairing_respects_ceq :
            forall (z : Z1) (r r' : C1), ceq r r' -> pairing z r == pairing z r')
         (coboundaries_pair_zero :
            forall (z : Z1) (b : C0), cycle z -> pairing z (delta0 b) == 0)
         (r : C1) (z : Z1),
    cycle z ->
    ~ (pairing z r == 0) ->
    ~ (exists b : C0, ceq (delta0 b) r).
Proof.
  intros C0 C1 Z1 delta0 pairing cycle ceq ceq_equiv pairing_respects_ceq
         coboundaries_pair_zero r z Hcycle Hnonzero [b Hceq].
  apply Hnonzero.
  rewrite <- (pairing_respects_ceq z (delta0 b) r Hceq).
  apply coboundaries_pair_zero.
  exact Hcycle.
Qed.

(* The Leibniz specialisation, for callers with no finer structure on C1. *)
Theorem nonzero_pairing_blocks_repair :
  forall (C0 C1 Z1 : Type)
         (delta0 : C0 -> C1)
         (pairing : Z1 -> C1 -> Q)
         (cycle : Z1 -> Prop)
         (coboundaries_pair_zero :
            forall (z : Z1) (b : C0), cycle z -> pairing z (delta0 b) == 0)
         (r : C1) (z : Z1),
    cycle z ->
    ~ (pairing z r == 0) ->
    ~ (exists b : C0, delta0 b = r).
Proof.
  intros C0 C1 Z1 delta0 pairing cycle coboundaries_pair_zero r z Hcycle Hnonzero.
  exact (nonzero_pairing_blocks_repair_mod_ceq
           C0 C1 Z1 delta0 pairing cycle
           (@eq C1) eq_equivalence (eq_respects_pairing Z1 C1 pairing)
           coboundaries_pair_zero r z Hcycle Hnonzero).
Qed.

(* ------------------------------------------------------------------ *)
(* Layer 2: associator-repair language, built on Layer 1, modulo ceq.   *)
(* ------------------------------------------------------------------ *)

Theorem nontrivial_associator_residue_not_repairable_mod_ceq :
  forall (C0 C1 Z1 AssocData BoundaryCorrection : Type)
         (delta0 : C0 -> C1)
         (pairing : Z1 -> C1 -> Q)
         (cycle : Z1 -> Prop)
         (ceq : C1 -> C1 -> Prop)
         (ceq_equiv : Equivalence ceq)
         (pairing_respects_ceq :
            forall (z : Z1) (r r' : C1), ceq r r' -> pairing z r == pairing z r')
         (associator_residue : AssocData -> C1)
         (correction_coboundary : BoundaryCorrection -> C0)
         (repairs : AssocData -> BoundaryCorrection -> Prop)
         (coboundaries_pair_zero :
            forall (z : Z1) (b : C0), cycle z -> pairing z (delta0 b) == 0)
         (repair_means_residue_is_coboundary :
            forall (A : AssocData) (b : BoundaryCorrection),
              repairs A b -> ceq (delta0 (correction_coboundary b)) (associator_residue A))
         (A : AssocData) (z : Z1),
    cycle z ->
    ~ (pairing z (associator_residue A) == 0) ->
    ~ (exists b : BoundaryCorrection, repairs A b).
Proof.
  intros C0 C1 Z1 AssocData BoundaryCorrection delta0 pairing cycle
         ceq ceq_equiv pairing_respects_ceq
         associator_residue correction_coboundary repairs
         coboundaries_pair_zero repair_means_residue_is_coboundary
         A z Hcycle Hnonzero [b Hrepairs].
  apply (nonzero_pairing_blocks_repair_mod_ceq
           C0 C1 Z1 delta0 pairing cycle ceq ceq_equiv pairing_respects_ceq
           coboundaries_pair_zero (associator_residue A) z Hcycle Hnonzero).
  exists (correction_coboundary b).
  exact (repair_means_residue_is_coboundary A b Hrepairs).
Qed.

(* The Leibniz specialisation, for callers with no finer structure on C1. *)
Theorem nontrivial_associator_residue_not_repairable :
  forall (C0 C1 Z1 AssocData BoundaryCorrection : Type)
         (delta0 : C0 -> C1)
         (pairing : Z1 -> C1 -> Q)
         (cycle : Z1 -> Prop)
         (associator_residue : AssocData -> C1)
         (correction_coboundary : BoundaryCorrection -> C0)
         (repairs : AssocData -> BoundaryCorrection -> Prop)
         (coboundaries_pair_zero :
            forall (z : Z1) (b : C0), cycle z -> pairing z (delta0 b) == 0)
         (repair_means_residue_is_coboundary :
            forall (A : AssocData) (b : BoundaryCorrection),
              repairs A b -> delta0 (correction_coboundary b) = associator_residue A)
         (A : AssocData) (z : Z1),
    cycle z ->
    ~ (pairing z (associator_residue A) == 0) ->
    ~ (exists b : BoundaryCorrection, repairs A b).
Proof.
  intros C0 C1 Z1 AssocData BoundaryCorrection delta0 pairing cycle
         associator_residue correction_coboundary repairs
         coboundaries_pair_zero repair_means_residue_is_coboundary
         A z Hcycle Hnonzero.
  exact (nontrivial_associator_residue_not_repairable_mod_ceq
           C0 C1 Z1 AssocData BoundaryCorrection delta0 pairing cycle
           (@eq C1) eq_equivalence (eq_respects_pairing Z1 C1 pairing)
           associator_residue correction_coboundary repairs
           coboundaries_pair_zero repair_means_residue_is_coboundary
           A z Hcycle Hnonzero).
Qed.
