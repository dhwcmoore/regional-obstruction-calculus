(*
   AssociatorContributionCertificate.v

   Phase 3B of the pairwise-to-global provenance bridge (docs/design/
   VERIFIED_CONTRIBUTION_CERTIFICATE.md, Phase 3A's own design
   document). Answers the governing question that document posed:
   what minimal registered orientation data makes the associator
   contribution a well-defined exact rational function of a committed
   local instance?

   TWO HONEST SCOPING DECISIONS, made explicit here because they
   change what later theorems in this file can truthfully claim --
   recorded per this project's standing discipline of stating
   interpretive choices rather than silently picking one.

   DECISION 1 -- the registered orientation is a STIPULATED
   convention, not a structural derivation from delta0's formula.
   associator_residue.py's own module docstring already admits this
   directly: "This module does not claim to reconstruct the historical
   derivation of the paper's displayed residue (1,1,1,-2); the
   CHANGELOG documents that it was originally posited directly." And
   four_cycle_instances()'s own docstring calls its choice of which
   SeamCorrectionData field carries each seam's target value "a free
   modelling choice." There is no existing rule, anywhere in this
   project, connecting FourCycleObstruction.v's delta0 (an abstract
   coboundary map on four formal vertices, with signs coming from
   graph incidence) to regional_composition.py's associator_defect (a
   three-region Venn-algebra construction, with no vertices, edges, or
   incidence structure at all) -- they are different mathematical
   objects with no a priori structural connection. Theorem 5 below
   ("registry_orientation_agrees_with_delta0") is therefore a CHECKED
   fact for the four registered four-cycle interfaces specifically,
   using FourCycleObstruction.v's own r constant as ground truth --
   not a general derivation, and not claimed as one.

   DECISION 2 -- associatorContribution formalises closed_form_delta,
   not associator_defect's full expansion. regional_composition.py's
   own closed_form_delta docstring already states the relationship
   precisely: "Provided only as an independent cross-check of
   associator_defect -- it is never used to *compute* the defect,"
   and associator_residue.py's compute_seam_residue cross-checks the
   two computations agree, at the Python level, for every instance it
   builds. That agreement (Proposition prop:four-term) is a
   paper-level and Python-checked fact, not formalised in Rocq by this
   file or any other file in this repository -- mechanising
   associator_defect's DualNumber/region/restriction machinery is out
   of scope here, matching this project's standing practice of proving
   a bridge against one narrow, concrete function rather than the
   whole regional obstruction calculus at once (see
   GLOBAL_COHERENCE_CERTIFICATE_SPEC.md section 2's identical scoping
   choice for a different bridge).

   A consequence of Decision 2 worth stating plainly: this file does
   NOT model the ordered triple (U, V, W) at all -- only the four
   seam-correction constants closed_form_delta actually reads. The
   "slot" below (which of the four constants carries the registered
   interface's value) is therefore the only orientation-relevant
   structure this file can honestly reason about; a stronger
   reorientation theorem naming (U, V, W)-permutation behaviour would
   require formalising associator_defect itself, not attempted here.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import Coq.QArith.QArith.
Require Import Coq.Lists.List.
Import ListNotations.

Section AssociatorContributionCertificate.

  (* ---- Slot: which of the four fixed-coefficient positions in the
     closed-form four-term formula a committed instance's declared
     magnitude occupies. Not a further free "sign" on top of this --
     the formula's own coefficients (+1, -1, +1, -1) are fixed by the
     formula itself, not independently choosable per instance. ---- *)

  Inductive Slot := SlotVW | SlotUvV_W | SlotU_VvW | SlotUV.

  Definition slot_coefficient (s : Slot) : Q :=
    match s with
    | SlotVW => 1
    | SlotUvV_W => -1
    | SlotU_VvW => 1
    | SlotUV => -1
    end.

  Definition slot_eq_dec (s t : Slot) : {s = t} + {s <> t}.
  Proof. decide equality. Defined.

  (* The registered orientation for one interface (docs/design/
     VERIFIED_CONTRIBUTION_CERTIFICATE.md section 4's Gamma,
     restricted to what section 3 there settled it reduces to). *)
  Record Orientation := mkOrientation { orient_slot : Slot }.

  (* Mirrors regional_composition.py's SeamCorrectionData exactly --
     four independent rationals, general (not restricted to a single
     nonzero slot at the type level; that restriction is a hypothesis
     of specific theorems below, not baked into the type). *)
  Record SeamCorrectionData := mkSeamCorrectionData {
    mu_VW : Q;
    mu_UvV_W : Q;
    mu_U_VvW : Q;
    mu_UV : Q;
  }.

  Definition closed_form_delta (mu : SeamCorrectionData) : Q :=
    mu_VW mu - mu_UvV_W mu + mu_U_VvW mu - mu_UV mu.

  Definition slot_value (s : Slot) (mu : SeamCorrectionData) : Q :=
    match s with
    | SlotVW => mu_VW mu
    | SlotUvV_W => mu_UvV_W mu
    | SlotU_VvW => mu_U_VvW mu
    | SlotUV => mu_UV mu
    end.

  (* "the committed instance uses only the registered slot" -- the
     well-formedness condition tying a raw SeamCorrectionData to one
     particular registered interface's canonical orientation. *)
  Definition other_slots_zero (s : Slot) (mu : SeamCorrectionData) : Prop :=
    match s with
    | SlotVW => mu_UvV_W mu == 0 /\ mu_U_VvW mu == 0 /\ mu_UV mu == 0
    | SlotUvV_W => mu_VW mu == 0 /\ mu_U_VvW mu == 0 /\ mu_UV mu == 0
    | SlotU_VvW => mu_VW mu == 0 /\ mu_UvV_W mu == 0 /\ mu_UV mu == 0
    | SlotUV => mu_VW mu == 0 /\ mu_UvV_W mu == 0 /\ mu_U_VvW mu == 0
    end.

  (* ---- The committed local instance and the registry entry ------ *)

  Record CommittedLocalInstance := mkCommittedLocalInstance {
    cli_mu : SeamCorrectionData;
  }.

  Variable InterfaceId : Type.
  Hypothesis interface_id_eq_dec : forall (i j : InterfaceId), {i = j} + {i <> j}.

  Record RegisteredInterface := mkRegisteredInterface {
    reg_interface : InterfaceId;
    reg_orientation : Orientation;
  }.

  (* ---- associatorContribution (Decision 2): the closed-form
     four-term arithmetic, nothing more. ---- *)

  Definition associatorContribution (x : CommittedLocalInstance) : Q :=
    closed_form_delta (cli_mu x).

  (* ---- The governing judgement --------------------------------- *)

  Definition AssociatorContributionValid
      (R : RegisteredInterface) (x : CommittedLocalInstance) (c : Q) : Prop :=
    other_slots_zero (orient_slot (reg_orientation R)) (cli_mu x) /\
    c == associatorContribution x.

  (* ============ Theorem 1: canonical_orientation_determines_slot === *)

  Theorem canonical_orientation_determines_slot :
    forall R x c,
      AssociatorContributionValid R x c ->
      other_slots_zero (orient_slot (reg_orientation R)) (cli_mu x).
  Proof.
    intros R x c [Hslot _]. exact Hslot.
  Qed.

  (* ============ Theorem 2: canonical_orientation_determines_sign === *)

  Theorem canonical_orientation_determines_sign :
    forall R x c,
      AssociatorContributionValid R x c ->
      c == slot_coefficient (orient_slot (reg_orientation R)) * slot_value (orient_slot (reg_orientation R)) (cli_mu x).
  Proof.
    intros R x c [Hslot Hval].
    rewrite Hval. unfold associatorContribution, closed_form_delta.
    destruct (orient_slot (reg_orientation R)) eqn:Hs; simpl in *; destruct Hslot as [H1 [H2 H3]]; ring_simplify;
      rewrite H1, H2, H3; ring.
  Qed.

  (* ============ Theorem 3: associator_contribution_functional ===== *)

  Theorem associator_contribution_functional :
    forall R x c1 c2,
      AssociatorContributionValid R x c1 ->
      AssociatorContributionValid R x c2 ->
      c1 == c2.
  Proof.
    intros R x c1 c2 [_ H1] [_ H2]. rewrite H1, H2. reflexivity.
  Qed.

  (* ============ Theorem 4: magnitude-negation reversal ============

     Honestly scoped per this file's own header (Decision 2): this is
     NOT the stronger endpoint-swap reorientation theorem
     PAIRWISE_TO_GLOBAL_PROVENANCE.md section 4 states but leaves
     unproved (reverse(i, c) = (i^op, -c), naming an opposite
     INTERFACE). This file does not model (U, V, W) or interface
     reversal at all -- see header. What IS provable at this file's
     own scope: negating the committed magnitude at the SAME
     registered slot negates the contribution. A consequence of
     closed_form_delta's linearity in each slot, not a new fact about
     orientation -- named as its own theorem because the design
     document's theorem ladder calls for it, not because it is deep. *)

  Definition negate_at_slot (s : Slot) (mu : SeamCorrectionData) : SeamCorrectionData :=
    match s with
    | SlotVW => mkSeamCorrectionData (- mu_VW mu) (mu_UvV_W mu) (mu_U_VvW mu) (mu_UV mu)
    | SlotUvV_W => mkSeamCorrectionData (mu_VW mu) (- mu_UvV_W mu) (mu_U_VvW mu) (mu_UV mu)
    | SlotU_VvW => mkSeamCorrectionData (mu_VW mu) (mu_UvV_W mu) (- mu_U_VvW mu) (mu_UV mu)
    | SlotUV => mkSeamCorrectionData (mu_VW mu) (mu_UvV_W mu) (mu_U_VvW mu) (- mu_UV mu)
    end.

  Theorem magnitude_negation_negates_contribution :
    forall R x c,
      AssociatorContributionValid R x c ->
      AssociatorContributionValid R (mkCommittedLocalInstance (negate_at_slot (orient_slot (reg_orientation R)) (cli_mu x))) (- c).
  Proof.
    intros R x c [Hslot Hval].
    unfold AssociatorContributionValid, associatorContribution, closed_form_delta in *.
    destruct (orient_slot (reg_orientation R)) eqn:Hs.
    - simpl in Hslot. destruct Hslot as [H1 [H2 H3]].
      split.
      + simpl. auto.
      + simpl. rewrite Hval. rewrite H1, H2, H3. ring.
    - simpl in Hslot. destruct Hslot as [H1 [H2 H3]].
      split.
      + simpl. auto.
      + simpl. rewrite Hval. rewrite H1, H2, H3. ring.
    - simpl in Hslot. destruct Hslot as [H1 [H2 H3]].
      split.
      + simpl. auto.
      + simpl. rewrite Hval. rewrite H1, H2, H3. ring.
    - simpl in Hslot. destruct Hslot as [H1 [H2 H3]].
      split.
      + simpl. auto.
      + simpl. rewrite Hval. rewrite H1, H2, H3. ring.
  Qed.

  (* ============ Theorem 6: verified_contribution_sound ============ *)

  Definition verifyContribution (R : RegisteredInterface) (x : CommittedLocalInstance) (c : Q) : bool :=
    let s := orient_slot (reg_orientation R) in
    let mu := cli_mu x in
    (match s with
     | SlotVW => andb (Qeq_bool (mu_UvV_W mu) 0) (andb (Qeq_bool (mu_U_VvW mu) 0) (Qeq_bool (mu_UV mu) 0))
     | SlotUvV_W => andb (Qeq_bool (mu_VW mu) 0) (andb (Qeq_bool (mu_U_VvW mu) 0) (Qeq_bool (mu_UV mu) 0))
     | SlotU_VvW => andb (Qeq_bool (mu_VW mu) 0) (andb (Qeq_bool (mu_UvV_W mu) 0) (Qeq_bool (mu_UV mu) 0))
     | SlotUV => andb (Qeq_bool (mu_VW mu) 0) (andb (Qeq_bool (mu_UvV_W mu) 0) (Qeq_bool (mu_U_VvW mu) 0))
     end)
    && Qeq_bool c (associatorContribution x).

  Theorem verified_contribution_sound :
    forall R x c,
      verifyContribution R x c = true ->
      AssociatorContributionValid R x c.
  Proof.
    intros R x c H.
    unfold verifyContribution in H.
    apply andb_true_iff in H. destruct H as [Hslot Hval].
    apply Qeq_bool_iff in Hval.
    split; [| exact Hval].
    destruct (orient_slot (reg_orientation R)) eqn:Hs; simpl in Hslot;
      apply andb_true_iff in Hslot; destruct Hslot as [H1 H23];
      apply andb_true_iff in H23; destruct H23 as [H2 H3];
      apply Qeq_bool_iff in H1; apply Qeq_bool_iff in H2; apply Qeq_bool_iff in H3;
      simpl; repeat split; assumption.
  Qed.

End AssociatorContributionCertificate.

(* ======================================================================
   Concrete four-cycle instantiation: theorems 5 and 7.

   InterfaceId := string, matching FourCycleObstruction.v's own seam
   naming ("e12","e23","e34","e14") and associator_residue.py's
   SEAM_ORDER exactly. All four registered orientations use SlotVW --
   matching what regional_composition.py's four_cycle_instances()
   actually does (every instance sets mu_VW := target, the other three
   zero; SlotVW is not independently chosen per seam anywhere in the
   existing Python fixture, despite the general Slot type above
   supporting the other three in principle).
   ====================================================================== *)

Require Import Coq.Strings.String.
Require Import FourCycleObstruction.

Open Scope string_scope.

Section FourCycleContributionInstantiation.

  Definition seam_orientation : Orientation := mkOrientation SlotVW.

  Definition registered_e12 := mkRegisteredInterface string "e12" seam_orientation.
  Definition registered_e23 := mkRegisteredInterface string "e23" seam_orientation.
  Definition registered_e34 := mkRegisteredInterface string "e34" seam_orientation.
  Definition registered_e14 := mkRegisteredInterface string "e14" seam_orientation.

  (* Exact values from regional_composition.py's four_cycle_instances():
     targets = {"e12": 1, "e23": 1, "e34": 1, "e14": -2}, mu_VW := target,
     the other three fields zero for every seam. *)
  Definition instance_e12 := mkCommittedLocalInstance (mkSeamCorrectionData 1 0 0 0).
  Definition instance_e23 := mkCommittedLocalInstance (mkSeamCorrectionData 1 0 0 0).
  Definition instance_e34 := mkCommittedLocalInstance (mkSeamCorrectionData 1 0 0 0).
  Definition instance_e14 := mkCommittedLocalInstance (mkSeamCorrectionData (-2) 0 0 0).

  (* ============ Theorem 7: the four concrete coordinate facts ====== *)

  Theorem e12_contribution_is_1 :
    AssociatorContributionValid string registered_e12 instance_e12 1.
  Proof. split; [simpl; repeat split; reflexivity | reflexivity]. Qed.

  Theorem e23_contribution_is_1 :
    AssociatorContributionValid string registered_e23 instance_e23 1.
  Proof. split; [simpl; repeat split; reflexivity | reflexivity]. Qed.

  Theorem e34_contribution_is_1 :
    AssociatorContributionValid string registered_e34 instance_e34 1.
  Proof. split; [simpl; repeat split; reflexivity | reflexivity]. Qed.

  Theorem e14_contribution_is_neg2 :
    AssociatorContributionValid string registered_e14 instance_e14 (-2).
  Proof. split; [simpl; repeat split; reflexivity | reflexivity]. Qed.

  (* ============ Theorem 5: registry_orientation_agrees_with_delta0 =

     A CHECKED fact for these four registered interfaces specifically
     -- not a structural derivation from delta0's formula (see this
     file's header, Decision 1: no such derivation exists to
     formalise; associator_defect and delta0 are different
     mathematical objects). What is proved: assembling the four
     contributions theorem 7 establishes, in FourCycleObstruction.v's
     own SEAM_ORDER (e12, e23, e34, e14), reproduces EXACTLY that
     file's own r constant -- the vector its cycle/pairing/
     non-repairability theorems already treat as the four-cycle's
     residue. This is the sense in which the registered orientation
     "agrees with delta0": not because one is derived from the other,
     but because the registered, stipulated convention is checked,
     coordinate by coordinate, against the value the existing global
     theory already committed to. *)

  Theorem registry_orientation_agrees_with_delta0 :
    veq (mkvec4 (associatorContribution instance_e12)
                (associatorContribution instance_e23)
                (associatorContribution instance_e34)
                (associatorContribution instance_e14))
        r.
  Proof.
    unfold veq, r, associatorContribution, closed_form_delta.
    simpl.
    repeat split; ring.
  Qed.

End FourCycleContributionInstantiation.
