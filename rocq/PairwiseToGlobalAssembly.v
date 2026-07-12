(*
   PairwiseToGlobalAssembly.v

   Formal representation and co-reference soundness for the
   pairwise-to-global provenance bridge's Phase 2 assembler
   (docs/design/PAIRWISE_TO_GLOBAL_PROVENANCE.md; the Python
   implementation is veribound-fce's src/pairwise_to_global_
   assembly.py, commit f3d4b12).

   The governing question this file answers: what can be proved about
   global assembly solely from the STRUCTURE and PROVENANCE of the
   supplied evidence, without assuming the certified contribution
   values are semantically correct? Contribution evidence is therefore
   modelled with an OPAQUE witness type -- this file proves nothing
   about whether a contribution value correctly computes an associator
   residue. That is deliberately a later, separate phase (see
   docs/design/PAIRWISE_TO_GLOBAL_PROVENANCE.md decision 1): the
   contribution certificate's own soundness is not this file's subject.

   Admissibility evidence, by contrast, is NOT abstracted away: this
   file reuses R15's own PairwiseDiagnosticCertificate.v directly
   (DecisivePairwiseEvidence / PairwiseResult, CompatibleEvidence /
   IncompatibleEvidence / Unresolved), unmodified. admissibility_kind
   below ERASES that rich evidence into a plain three-way classification
   for the assembler's own case analysis -- exactly the same erasure
   pattern R15's own pairwise_diagnostic uses relative to R14's
   ConflictDiagnostic, not a new technique introduced here. The genuine
   PairwiseResult evidence is still carried inside every
   AdmissibilityCertificate (adm_result), never discarded.

   ON EXTRACTION: this repository has never used Rocq's Extraction
   vernacular before this file, and does not start here either. The
   "existing verification pattern" this project actually has is a
   HAND-WRITTEN, independent OCaml mirror of a Python implementation,
   cross-checked for parity (ocaml/refinement_checker.ml vs.
   refinement_checker.py) -- not one artefact mechanically derived from
   another. This file's connection to ocaml/assembly_checker.ml follows
   that same established pattern: an independently written OCaml
   implementation of this specification, checked for outcome agreement
   against both this Rocq model's theorems and the Python assembler on
   a shared fixture corpus -- not literal Coq extraction. See
   ocaml/assembly_checker.ml's own header for why.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import CoupledParallelCompatibility.
Require Import PairwiseDiagnosticCertificate.
Require Import Coq.QArith.QArith.
Require Import Coq.Lists.List.
Require Import Lia.
Import ListNotations.

Section PairwiseToGlobalAssembly.

  Variables Key Value InterfaceId Digest Witness : Type.
  Hypothesis interface_id_eq_dec : forall (i j : InterfaceId), {i = j} + {i <> j}.
  Hypothesis digest_eq_dec : forall (d e : Digest), {d = e} + {d <> e}.

  Notation Decl := (Declaration Key Value).

  Definition interface_id_eqb (i j : InterfaceId) : bool :=
    if interface_id_eq_dec i j then true else false.

  Definition digest_eqb (d e : Digest) : bool :=
    if digest_eq_dec d e then true else false.

  Lemma interface_id_eqb_true_iff :
    forall i j, interface_id_eqb i j = true <-> i = j.
  Proof.
    intros i j. unfold interface_id_eqb.
    destruct (interface_id_eq_dec i j); split; intro H; try discriminate; auto.
  Qed.

  Lemma digest_eqb_true_iff :
    forall d e, digest_eqb d e = true <-> d = e.
  Proof.
    intros d e. unfold digest_eqb.
    destruct (digest_eq_dec d e); split; intro H; try discriminate; auto.
  Qed.

  (* ---- Evidence types -------------------------------------------- *)

  (* R15's own evidence, unmodified -- no schema change here, exactly
     as docs/design/PAIRWISE_TO_GLOBAL_PROVENANCE.md section 2 requires. *)
  Inductive AdmissibilityKind := KindCompatible | KindIncompatible | KindUnresolved.

  Definition admissibility_kind (dA dB : Decl) (r : PairwiseResult Key Value dA dB)
      : AdmissibilityKind :=
    match r with
    | Decided _ _ _ _ (CompatibleEvidence _ _ _ _ _ _) => KindCompatible
    | Decided _ _ _ _ (IncompatibleEvidence _ _ _ _ _) => KindIncompatible
    | Unresolved _ _ _ _ => KindUnresolved
    end.

  Record RequiredInterface := mkRequiredInterface {
    req_interface : InterfaceId;
    req_digest : Digest;
  }.

  (* Wraps R15's own PairwiseResult with the interface/provenance
     metadata that certificate's schema deliberately does not carry --
     mirrors veribound-fce's VerifiedPairwiseCertificate exactly. *)
  Record AdmissibilityCertificate := mkAdmissibilityCertificate {
    adm_interface : InterfaceId;
    adm_digest : Digest;
    adm_left : Decl;
    adm_right : Decl;
    adm_result : PairwiseResult Key Value adm_left adm_right;
  }.

  (* Contribution evidence: OPAQUE witness, per this file's own
     governing question (see header). No claim the witness proves
     anything about contrib_value. *)
  Record ContributionCertificate := mkContributionCertificate {
    contrib_interface : InterfaceId;
    contrib_digest : Digest;
    contrib_value : Q;
    contrib_witness : Witness;
  }.

  Inductive UnresolvedReason :=
    | MissingAdmissibility
    | MissingContribution
    | UnresolvedAdmissibility
    | CoreferenceMismatch
    | DuplicateInterfaceEvidence
    | UnexpectedInterface.

  Record UnresolvedInterfaceReason := mkUnresolvedInterfaceReason {
    ur_interface : InterfaceId;
    ur_reason : UnresolvedReason;
  }.

  Record RefusedInterface := mkRefusedInterface {
    rf_interface : InterfaceId;
    rf_certificate : AdmissibilityCertificate;
  }.

  Record VerifiedInterfaceEvidence := mkVerifiedInterfaceEvidence {
    vie_admissibility : AdmissibilityCertificate;
    vie_contribution : ContributionCertificate;
  }.

  Record AssembledResidue := mkAssembledResidue {
    ordered_interfaces : list InterfaceId;
    residue : list Q;
    interface_evidence : list VerifiedInterfaceEvidence;
  }.

  Inductive AssemblyOutcome :=
    | AssemblyComplete : AssembledResidue -> AssemblyOutcome
    | AssemblyUnresolved : list UnresolvedInterfaceReason -> AssemblyOutcome
    | AssemblyRefused : list RefusedInterface -> AssemblyOutcome.

  (* ---- Matching by interface_id, mirroring the Python assembler's
     grouping step exactly (src/pairwise_to_global_assembly.py's
     _group_by_interface) ---------------------------------------- *)

  Definition matching_adm (i : InterfaceId) (adm_l : list AdmissibilityCertificate)
      : list AdmissibilityCertificate :=
    filter (fun c => interface_id_eqb (adm_interface c) i) adm_l.

  Definition matching_contrib (i : InterfaceId) (contrib_l : list ContributionCertificate)
      : list ContributionCertificate :=
    filter (fun c => interface_id_eqb (contrib_interface c) i) contrib_l.

  Definition required_ids (required : list RequiredInterface) : list InterfaceId :=
    map req_interface required.

  Definition is_required (required_id_list : list InterfaceId) (i : InterfaceId) : bool :=
    existsb (interface_id_eqb i) required_id_list.

  Definition unexpected_adm_ids
      (required_id_list : list InterfaceId) (adm_l : list AdmissibilityCertificate)
      : list InterfaceId :=
    map adm_interface (filter (fun c => negb (is_required required_id_list (adm_interface c))) adm_l).

  Definition unexpected_contrib_ids
      (required_id_list : list InterfaceId) (contrib_l : list ContributionCertificate)
      : list InterfaceId :=
    map contrib_interface
      (filter (fun c => negb (is_required required_id_list (contrib_interface c))) contrib_l).

  (* ---- Per-interface classification -------------------------------

     Mirrors src/pairwise_to_global_assembly.py's per-interface loop
     body exactly, including its classification ORDER: duplicate check
     first, then missing admissibility, then admissibility co-reference,
     then admissibility kind (Incompatible / Unresolved / Compatible),
     then missing contribution, then contribution co-reference. *)

  Inductive InterfaceStatus :=
    | IStatusSatisfied : VerifiedInterfaceEvidence -> InterfaceStatus
    | IStatusRefused : AdmissibilityCertificate -> InterfaceStatus
    | IStatusUnresolved : UnresolvedReason -> InterfaceStatus.

  Definition classify_interface
      (req : RequiredInterface)
      (adm_l : list AdmissibilityCertificate) (contrib_l : list ContributionCertificate)
      : InterfaceStatus :=
    match matching_adm (req_interface req) adm_l, matching_contrib (req_interface req) contrib_l with
    | (_ :: _ :: _), _ => IStatusUnresolved DuplicateInterfaceEvidence
    | _, (_ :: _ :: _) => IStatusUnresolved DuplicateInterfaceEvidence
    | [], _ => IStatusUnresolved MissingAdmissibility
    | [adm], contrib_matches =>
        if negb (digest_eqb (adm_digest adm) (req_digest req)) then
          IStatusUnresolved CoreferenceMismatch
        else
          match admissibility_kind _ _ (adm_result adm) with
          | KindIncompatible => IStatusRefused adm
          | KindUnresolved => IStatusUnresolved UnresolvedAdmissibility
          | KindCompatible =>
              match contrib_matches with
              | [] => IStatusUnresolved MissingContribution
              | [contrib] =>
                  if negb (digest_eqb (contrib_digest contrib) (req_digest req)) then
                    IStatusUnresolved CoreferenceMismatch
                  else
                    IStatusSatisfied (mkVerifiedInterfaceEvidence adm contrib)
              | _ :: _ :: _ => IStatusUnresolved DuplicateInterfaceEvidence
              end
          end
    end.

  Definition classify_all
      (required : list RequiredInterface)
      (adm_l : list AdmissibilityCertificate) (contrib_l : list ContributionCertificate)
      : list (RequiredInterface * InterfaceStatus) :=
    map (fun req => (req, classify_interface req adm_l contrib_l)) required.

  (* ---- The assembler itself ---------------------------------------

     Refusal-first, matching src/pairwise_to_global_assembly.py's own
     assemble_global_evidence exactly: any refusal anywhere makes the
     whole result AssemblyRefused, regardless of unresolved reasons
     elsewhere; only once no refusal exists are unresolved reasons
     (including unexpected-interface findings) checked; AssemblyComplete
     only when every required interface is IStatusSatisfied. *)

  Definition assemble
      (required : list RequiredInterface)
      (adm_l : list AdmissibilityCertificate) (contrib_l : list ContributionCertificate)
      : AssemblyOutcome :=
    let required_id_list := required_ids required in
    let classified := classify_all required adm_l contrib_l in
    let refused :=
      flat_map (fun p => match snd p with
                          | IStatusRefused c => [mkRefusedInterface (req_interface (fst p)) c]
                          | _ => []
                          end) classified in
    match refused with
    | _ :: _ => AssemblyRefused refused
    | [] =>
        let unresolved_reasons :=
          flat_map (fun p => match snd p with
                              | IStatusUnresolved r => [mkUnresolvedInterfaceReason (req_interface (fst p)) r]
                              | _ => []
                              end) classified
          ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
                 (unexpected_adm_ids required_id_list adm_l)
          ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
                 (unexpected_contrib_ids required_id_list contrib_l)
        in
        match unresolved_reasons with
        | _ :: _ => AssemblyUnresolved unresolved_reasons
        | [] =>
            let satisfied :=
              flat_map (fun p => match snd p with
                                  | IStatusSatisfied vie => [vie]
                                  | _ => []
                                  end) classified in
            AssemblyComplete (mkAssembledResidue required_id_list
                                 (map (fun vie => contrib_value (vie_contribution vie)) satisfied)
                                 satisfied)
        end
    end.

  (* ---- Pointwise facts about matching --------------------------- *)

  Lemma matching_adm_singleton_spec :
    forall i adm_l adm,
      matching_adm i adm_l = [adm] ->
      In adm adm_l /\ adm_interface adm = i.
  Proof.
    intros i adm_l adm Heq.
    assert (Hin : In adm (matching_adm i adm_l)) by (rewrite Heq; left; reflexivity).
    unfold matching_adm in Hin.
    apply filter_In in Hin.
    destruct Hin as [Hin Hfil].
    split; auto.
    apply interface_id_eqb_true_iff; auto.
  Qed.

  Lemma matching_contrib_singleton_spec :
    forall i contrib_l contrib,
      matching_contrib i contrib_l = [contrib] ->
      In contrib contrib_l /\ contrib_interface contrib = i.
  Proof.
    intros i contrib_l contrib Heq.
    assert (Hin : In contrib (matching_contrib i contrib_l)) by (rewrite Heq; left; reflexivity).
    unfold matching_contrib in Hin.
    apply filter_In in Hin.
    destruct Hin as [Hin Hfil].
    split; auto.
    apply interface_id_eqb_true_iff; auto.
  Qed.

  (* ---- Pointwise soundness of classify_interface ------------------

     The forward direction only (IStatusSatisfied implies the good
     properties) -- this file's theorems are all of the form "for
     every AssemblyComplete, prove X", never the converse. *)

  Lemma classify_interface_satisfied_sound :
    forall req adm_l contrib_l vie,
      classify_interface req adm_l contrib_l = IStatusSatisfied vie ->
      In (vie_admissibility vie) adm_l /\
      In (vie_contribution vie) contrib_l /\
      adm_interface (vie_admissibility vie) = req_interface req /\
      contrib_interface (vie_contribution vie) = req_interface req /\
      adm_digest (vie_admissibility vie) = req_digest req /\
      contrib_digest (vie_contribution vie) = req_digest req /\
      admissibility_kind _ _ (adm_result (vie_admissibility vie)) = KindCompatible.
  Proof.
    intros req adm_l contrib_l vie H.
    unfold classify_interface in H.
    destruct (matching_adm (req_interface req) adm_l) as [| adm [| adm2 rest_a]] eqn:Hadm;
    destruct (matching_contrib (req_interface req) contrib_l) as [| contrib [| contrib2 rest_c]] eqn:Hcontrib;
    simpl in H; try discriminate H.
    all: try (destruct (digest_eqb (adm_digest adm) (req_digest req)) eqn:Edig; simpl in H; try discriminate H;
               destruct (admissibility_kind (adm_left adm) (adm_right adm) (adm_result adm)) eqn:Hkind;
               discriminate H).
    (* Exactly one goal remains: matching_adm = [adm], matching_contrib = [contrib]. *)
    destruct (digest_eqb (adm_digest adm) (req_digest req)) eqn:Edig; simpl in H; try discriminate H.
    destruct (admissibility_kind (adm_left adm) (adm_right adm) (adm_result adm)) eqn:Hkind; try discriminate H.
    destruct (digest_eqb (contrib_digest contrib) (req_digest req)) eqn:Edig2; simpl in H; try discriminate H.
    injection H as H. subst vie. simpl.
    pose proof (matching_adm_singleton_spec _ _ _ Hadm) as [Hin_a Hi_a].
    pose proof (matching_contrib_singleton_spec _ _ _ Hcontrib) as [Hin_c Hi_c].
    apply digest_eqb_true_iff in Edig.
    apply digest_eqb_true_iff in Edig2.
    repeat split; auto.
  Qed.

  (* ---- Lifting classify_interface's pointwise facts to assemble --- *)

  Lemma flat_map_eq_nil_iff :
    forall (A B : Type) (f : A -> list B) (l : list A),
      flat_map f l = [] <-> (forall x, In x l -> f x = []).
  Proof.
    intros A B f l.
    induction l as [| a l' IH]; simpl; split; intro H.
    - intros x Hin; inversion Hin.
    - reflexivity.
    - intros x Hin.
      apply app_eq_nil in H. destruct H as [Hfa Hfl].
      destruct Hin as [Heq | Hin]; [subst; assumption | apply IH; assumption].
    - rewrite (H a (or_introl eq_refl)). simpl.
      apply IH. intros x Hin. apply H. right. assumption.
  Qed.

  (* Every entry of classify_all a completed assembly touches is
     IStatusSatisfied -- the structural fact that AssemblyComplete
     could only have been reached because nothing else fired. *)
  Lemma assemble_complete_all_satisfied :
    forall required adm_l contrib_l r,
      assemble required adm_l contrib_l = AssemblyComplete r ->
      forall req, In req required ->
        exists vie, classify_interface req adm_l contrib_l = IStatusSatisfied vie.
  Proof.
    intros required adm_l contrib_l r Hassemble req Hin.
    unfold assemble in Hassemble.
    set (classified := classify_all required adm_l contrib_l) in *.
    set (refused := flat_map (fun p => match snd p with
                                        | IStatusRefused c => [mkRefusedInterface (req_interface (fst p)) c]
                                        | _ => []
                                        end) classified) in *.
    destruct refused eqn:Hrefused; try discriminate Hassemble.
    set (unresolved_reasons :=
      flat_map (fun p => match snd p with
                          | IStatusUnresolved rn => [mkUnresolvedInterfaceReason (req_interface (fst p)) rn]
                          | _ => []
                          end) classified
      ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
             (unexpected_adm_ids (required_ids required) adm_l)
      ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
             (unexpected_contrib_ids (required_ids required) contrib_l)) in *.
    destruct unresolved_reasons eqn:Hunresolved; try discriminate Hassemble.
    assert (Hnorefused : forall p, In p classified -> forall c, snd p <> IStatusRefused c). {
      intros p Hp c Heq.
      pose proof (proj1 (flat_map_eq_nil_iff _ _ _ classified) Hrefused p Hp) as Hf.
      simpl in Hf. rewrite Heq in Hf. discriminate Hf.
    }
    assert (Hnounresolved1 : flat_map (fun p => match snd p with
                          | IStatusUnresolved rn => [mkUnresolvedInterfaceReason (req_interface (fst p)) rn]
                          | _ => []
                          end) classified = []). {
      assert (Hcomb : flat_map (fun p => match snd p with
                          | IStatusUnresolved rn => [mkUnresolvedInterfaceReason (req_interface (fst p)) rn]
                          | _ => []
                          end) classified
        ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
               (unexpected_adm_ids (required_ids required) adm_l)
        ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
               (unexpected_contrib_ids (required_ids required) contrib_l) = []) by exact Hunresolved.
      apply app_eq_nil in Hcomb. destruct Hcomb as [Hcomb1 _]. exact Hcomb1.
    }
    assert (Hnounresolved : forall p, In p classified -> forall rn, snd p <> IStatusUnresolved rn). {
      intros p Hp rn Heq.
      pose proof (proj1 (flat_map_eq_nil_iff _ _ _ classified) Hnounresolved1 p Hp) as Hf.
      simpl in Hf. rewrite Heq in Hf. discriminate Hf.
    }
    assert (Hpin : In (req, classify_interface req adm_l contrib_l) classified). {
      unfold classified, classify_all.
      apply in_map_iff. exists req. split; [reflexivity | exact Hin].
    }
    destruct (classify_interface req adm_l contrib_l) as [vie | c | rn] eqn:Hcl.
    - exists vie. reflexivity.
    - exfalso. apply (Hnorefused (req, IStatusRefused c) Hpin c). reflexivity.
    - exfalso. apply (Hnounresolved (req, IStatusUnresolved rn) Hpin rn). reflexivity.
  Qed.

  (* The list-level correspondence: given that no required interface's
     classification is Refused or Unresolved, the flat_map of
     satisfied evidence is in exact one-to-one, position-preserving
     correspondence with `required` itself. Proved by structural
     induction on `required`, never needing decidable equality on
     RequiredInterface itself (positions are matched by cons structure,
     not by lookup). *)
  Lemma classify_all_satisfied_correspondence :
    forall required adm_l contrib_l,
      (forall req, In req required -> forall c, classify_interface req adm_l contrib_l <> IStatusRefused c) ->
      (forall req, In req required -> forall rn, classify_interface req adm_l contrib_l <> IStatusUnresolved rn) ->
      exists vies : list VerifiedInterfaceEvidence,
        length vies = length required /\
        flat_map (fun p => match snd p with IStatusSatisfied vie => [vie] | _ => [] end)
                 (classify_all required adm_l contrib_l) = vies /\
        (forall k : nat, (k < length required)%nat ->
           exists req vie, nth_error required k = Some req /\ nth_error vies k = Some vie /\
                            classify_interface req adm_l contrib_l = IStatusSatisfied vie).
  Proof.
    induction required as [| req0 rest IH]; intros adm_l contrib_l Hnr Hnu.
    - exists []. repeat split; auto. intros k Hk. simpl in Hk. lia.
    - assert (Hnr' : forall req, In req rest -> forall c, classify_interface req adm_l contrib_l <> IStatusRefused c)
        by (intros req Hin c; apply Hnr; right; assumption).
      assert (Hnu' : forall req, In req rest -> forall rn, classify_interface req adm_l contrib_l <> IStatusUnresolved rn)
        by (intros req Hin rn; apply Hnu; right; assumption).
      destruct (IH adm_l contrib_l Hnr' Hnu') as [vies_rest [Hlen [Heq Hcorr]]].
      destruct (classify_interface req0 adm_l contrib_l) as [vie0 | c0 | rn0] eqn:Hcl0.
      + exists (vie0 :: vies_rest). repeat split.
        * simpl. f_equal. exact Hlen.
        * simpl. unfold classify_all. simpl. rewrite Hcl0. simpl.
          fold (classify_all rest adm_l contrib_l).
          f_equal. exact Heq.
        * intros k Hk. destruct k as [| k'].
          -- exists req0, vie0. repeat split; simpl; auto.
          -- simpl in Hk. assert (Hk' : (k' < length rest)%nat) by lia.
             destruct (Hcorr k' Hk') as [req [vie [Hreq [Hvie Hcli]]]].
             exists req, vie. repeat split; simpl; auto.
      + exfalso. apply (Hnr req0 (or_introl eq_refl) c0 Hcl0).
      + exfalso. apply (Hnu req0 (or_introl eq_refl) rn0 Hcl0).
  Qed.

  (* Whenever assemble reaches AssemblyComplete, its result is built
     exactly as assemble's own source constructs it -- restated as a
     standalone, reusable fact so downstream theorems do not each need
     to re-derive assemble's internal case structure. *)
  Lemma assemble_complete_shape :
    forall required adm_l contrib_l r,
      assemble required adm_l contrib_l = AssemblyComplete r ->
      r = mkAssembledResidue (required_ids required)
            (map (fun vie => contrib_value (vie_contribution vie))
                 (flat_map (fun p => match snd p with IStatusSatisfied vie => [vie] | _ => [] end)
                           (classify_all required adm_l contrib_l)))
            (flat_map (fun p => match snd p with IStatusSatisfied vie => [vie] | _ => [] end)
                      (classify_all required adm_l contrib_l)).
  Proof.
    intros required adm_l contrib_l r Hassemble.
    unfold assemble in Hassemble.
    destruct (flat_map (fun p => match snd p with
                                  | IStatusRefused c => [mkRefusedInterface (req_interface (fst p)) c]
                                  | _ => []
                                  end) (classify_all required adm_l contrib_l)) eqn:Hrefused;
      try discriminate Hassemble.
    destruct (flat_map (fun p => match snd p with
                                  | IStatusUnresolved rn => [mkUnresolvedInterfaceReason (req_interface (fst p)) rn]
                                  | _ => []
                                  end) (classify_all required adm_l contrib_l)
              ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
                     (unexpected_adm_ids (required_ids required) adm_l)
              ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
                     (unexpected_contrib_ids (required_ids required) contrib_l))
      eqn:Hunresolved; try discriminate Hassemble.
    injection Hassemble as Hassemble. subst r. reflexivity.
  Qed.

  (* ---- Theorem 1: representation and provenance soundness --------

     For every AssemblyComplete, restates the design document's own
     six-point obligation list as one machine-checked fact: every
     required interface occurs exactly once (NoDup hypothesis, matching
     the Python assembler's own RequiredInterfaceError precondition,
     plus the length/position correspondence below); every assembled
     coordinate comes from a supplied contribution certificate and
     equals its exact certified value; the output order equals the
     registered required-interface order; every included interface has
     compatible pairwise evidence. Point 6 (no missing, duplicate,
     unexpected, incompatible, or mismatched evidence can produce
     AssemblyComplete) is structural: classify_interface's own
     definition makes IStatusSatisfied mutually exclusive with every
     branch that would report one of those problems (see
     classify_interface_satisfied_sound and
     classify_all_satisfied_correspondence above), not a separate fact
     to prove again here. *)
  Theorem assemble_complete_representation_soundness :
    forall required adm_l contrib_l r,
      NoDup (required_ids required) ->
      assemble required adm_l contrib_l = AssemblyComplete r ->
      ordered_interfaces r = required_ids required /\
      length (interface_evidence r) = length required /\
      residue r = map (fun vie => contrib_value (vie_contribution vie)) (interface_evidence r) /\
      (forall k : nat, (k < length required)%nat ->
         exists req vie,
           nth_error required k = Some req /\
           nth_error (interface_evidence r) k = Some vie /\
           In (vie_admissibility vie) adm_l /\
           In (vie_contribution vie) contrib_l /\
           adm_interface (vie_admissibility vie) = req_interface req /\
           contrib_interface (vie_contribution vie) = req_interface req /\
           adm_digest (vie_admissibility vie) = req_digest req /\
           contrib_digest (vie_contribution vie) = req_digest req /\
           admissibility_kind _ _ (adm_result (vie_admissibility vie)) = KindCompatible).
  Proof.
    intros required adm_l contrib_l r Hnodup Hassemble.
    assert (Hsat : forall req, In req required -> exists vie, classify_interface req adm_l contrib_l = IStatusSatisfied vie)
      by (apply (assemble_complete_all_satisfied required adm_l contrib_l r Hassemble)).
    assert (Hnr : forall req, In req required -> forall c, classify_interface req adm_l contrib_l <> IStatusRefused c). {
      intros req Hin c Heq. destruct (Hsat req Hin) as [vie Hvie]. rewrite Heq in Hvie. discriminate Hvie.
    }
    assert (Hnu : forall req, In req required -> forall rn, classify_interface req adm_l contrib_l <> IStatusUnresolved rn). {
      intros req Hin rn Heq. destruct (Hsat req Hin) as [vie Hvie]. rewrite Heq in Hvie. discriminate Hvie.
    }
    destruct (classify_all_satisfied_correspondence required adm_l contrib_l Hnr Hnu) as [vies [Hlen [Heq Hcorr]]].
    pose proof (assemble_complete_shape required adm_l contrib_l r Hassemble) as Hshape.
    rewrite Heq in Hshape.
    subst r. simpl.
    split; [reflexivity |].
    split; [rewrite Hlen; reflexivity |].
    split; [reflexivity |].
    intros k Hk.
    destruct (Hcorr k Hk) as [req [vie [Hreq [Hvie Hcli]]]].
    exists req, vie.
    pose proof (classify_interface_satisfied_sound req adm_l contrib_l vie Hcli)
      as [Hin_a [Hin_c [Hi_a [Hi_c [Hd_a [Hd_c Hkind]]]]]].
    repeat split; auto.
  Qed.

  (* ---- Theorem 2: registered co-reference consistency -------------

     A separate, deliberately WEAKER named theorem, extracted from
     Theorem 1's combined statement rather than proved independently
     (both rest on the same underlying facts). States only that the
     admissibility and contribution evidence both agree with the
     REQUIRED interface's own registered digest -- provenance
     consistency, not semantic derivability.

     Explicitly NOT claimed, and not claimable from anything in this
     file: `admissibility_kind ... = KindCompatible -> <contribution c
     is semantically correct>`. No such predicate is even defined here
     -- contrib_witness is opaque (see file header). Compatibility
     authorises assembly at the pairwise layer; it says nothing about
     whether the contribution's value is right. *)
  Theorem assemble_complete_coreference_consistency :
    forall required adm_l contrib_l r,
      NoDup (required_ids required) ->
      assemble required adm_l contrib_l = AssemblyComplete r ->
      forall k : nat, (k < length required)%nat ->
        exists req vie,
          nth_error required k = Some req /\
          nth_error (interface_evidence r) k = Some vie /\
          adm_digest (vie_admissibility vie) = req_digest req /\
          contrib_digest (vie_contribution vie) = req_digest req.
  Proof.
    intros required adm_l contrib_l r Hnodup Hassemble k Hk.
    destruct (assemble_complete_representation_soundness required adm_l contrib_l r Hnodup Hassemble)
      as [_ [_ [_ Hall]]].
    destruct (Hall k Hk) as [req [vie [Hreq [Hvie [_ [_ [_ [_ [Hda [Hdc _]]]]]]]]]].
    exists req, vie. auto.
  Qed.

  (* ---- Theorem 3: outcome separation and refusal precedence ------ *)

  Lemma classify_interface_refused_sound :
    forall req adm_l contrib_l c,
      classify_interface req adm_l contrib_l = IStatusRefused c ->
      In c adm_l /\ adm_interface c = req_interface req /\ adm_digest c = req_digest req /\
      admissibility_kind _ _ (adm_result c) = KindIncompatible.
  Proof.
    intros req adm_l contrib_l c H.
    unfold classify_interface in H.
    destruct (matching_adm (req_interface req) adm_l) as [| adm [| adm2 rest_a]] eqn:Hadm;
    destruct (matching_contrib (req_interface req) contrib_l) as [| contrib [| contrib2 rest_c]] eqn:Hcontrib;
    simpl in H; try discriminate H.
    - (* matching_adm = [adm], matching_contrib = [] *)
      destruct (digest_eqb (adm_digest adm) (req_digest req)) eqn:Edig; simpl in H; try discriminate H.
      destruct (admissibility_kind (adm_left adm) (adm_right adm) (adm_result adm)) eqn:Hkind; try discriminate H.
      injection H as H. subst c. simpl.
      pose proof (matching_adm_singleton_spec _ _ _ Hadm) as [Hin_a Hi_a].
      apply digest_eqb_true_iff in Edig.
      repeat split; auto.
    - (* matching_adm = [adm], matching_contrib = [contrib] *)
      destruct (digest_eqb (adm_digest adm) (req_digest req)) eqn:Edig; simpl in H; try discriminate H.
      destruct (admissibility_kind (adm_left adm) (adm_right adm) (adm_result adm)) eqn:Hkind.
      + (* KindCompatible: still gated by the inner contrib-digest check *)
        destruct (digest_eqb (contrib_digest contrib) (req_digest req)) eqn:Edig2; simpl in H; discriminate H.
      + (* KindIncompatible *)
        injection H as H. subst c. simpl.
        pose proof (matching_adm_singleton_spec _ _ _ Hadm) as [Hin_a Hi_a].
        apply digest_eqb_true_iff in Edig.
        repeat split; auto.
      + (* KindUnresolved *)
        discriminate H.
  Qed.

  Lemma flat_map_nonempty_witness :
    forall (A B : Type) (f : A -> list B) (l : list A) (b : B) (rest : list B),
      flat_map f l = b :: rest ->
      exists x, In x l /\ In b (f x).
  Proof.
    induction l as [| a l' IH]; intros b rest H.
    - simpl in H. discriminate H.
    - simpl in H. destruct (f a) as [| b0 bs] eqn:Hfa.
      + simpl in H. destruct (IH b rest H) as [x [Hin Hinfx]]. exists x. split; [right | ]; assumption.
      + simpl in H. injection H as Hb Hrest. exists a. split; [left; reflexivity |]. rewrite Hfa. left. assumption.
  Qed.

  (* Reusable shape fact, mirroring assemble_complete_shape's own
     successful proof pattern (both destructs performed explicitly, so
     every branch is concretely discriminable -- a stuck match on an
     abstract list is not enough for `discriminate` even when every
     possible branch happens to disagree). Keeps the rf :: rest
     decomposition, not just the bare equality, since the
     nonemptiness is exactly what the next theorem needs. *)
  Lemma assemble_refused_shape :
    forall required adm_l contrib_l refs,
      assemble required adm_l contrib_l = AssemblyRefused refs ->
      exists rf rest,
        refs = rf :: rest /\
        flat_map (fun p => match snd p with
                            | IStatusRefused c => [mkRefusedInterface (req_interface (fst p)) c]
                            | _ => []
                            end) (classify_all required adm_l contrib_l) = rf :: rest.
  Proof.
    intros required adm_l contrib_l refs H.
    unfold assemble in H.
    destruct (flat_map (fun p => match snd p with
                                  | IStatusRefused c => [mkRefusedInterface (req_interface (fst p)) c]
                                  | _ => []
                                  end) (classify_all required adm_l contrib_l)) as [| rf rest] eqn:Hrefused.
    - destruct (flat_map (fun p => match snd p with
                                    | IStatusUnresolved rn => [mkUnresolvedInterfaceReason (req_interface (fst p)) rn]
                                    | _ => []
                                    end) (classify_all required adm_l contrib_l)
                ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
                       (unexpected_adm_ids (required_ids required) adm_l)
                ++ map (fun i => mkUnresolvedInterfaceReason i UnexpectedInterface)
                       (unexpected_contrib_ids (required_ids required) contrib_l));
        discriminate H.
    - injection H as H. subst refs. exists rf, rest. auto.
  Qed.

  (* 3(a): AssemblyRefused implies some required interface is verified
     Incompatible. *)
  Theorem assemble_refused_implies_incompatible :
    forall required adm_l contrib_l refs,
      assemble required adm_l contrib_l = AssemblyRefused refs ->
      exists req c, In req required /\ In c adm_l /\
                     adm_interface c = req_interface req /\ adm_digest c = req_digest req /\
                     admissibility_kind _ _ (adm_result c) = KindIncompatible.
  Proof.
    intros required adm_l contrib_l refs H.
    destruct (assemble_refused_shape required adm_l contrib_l refs H) as [rf [rest [Hrefs_eq Hrefused]]].
    destruct (flat_map_nonempty_witness _ _ _ _ rf rest Hrefused) as [p [Hp_in Hp_result]].
    unfold classify_all in Hp_in. apply in_map_iff in Hp_in.
    destruct Hp_in as [req [Hp_eq Hreq_in]].
    subst p. simpl in Hp_result.
    destruct (classify_interface req adm_l contrib_l) as [vie | c | rn] eqn:Hcl; simpl in Hp_result.
    - inversion Hp_result.
    - exists req, c. split; [assumption |].
      apply (classify_interface_refused_sound req adm_l contrib_l c Hcl).
    - inversion Hp_result.
  Qed.

  (* 3(b): AssemblyUnresolved implies no required interface's
     classification is Refused. Scoped precisely to classify_interface's
     own result, not to "no Incompatible certificate exists anywhere in
     adm_l" -- a genuinely Incompatible certificate for a required
     interface could still be masked by an earlier-precedence Duplicate
     or CoreferenceMismatch finding for that same interface (classify_
     interface checks those first), so the stronger informal claim would
     overreach what is actually true. *)
  Theorem assemble_unresolved_no_refused_classification :
    forall required adm_l contrib_l reasons,
      assemble required adm_l contrib_l = AssemblyUnresolved reasons ->
      forall req, In req required -> forall c, classify_interface req adm_l contrib_l <> IStatusRefused c.
  Proof.
    intros required adm_l contrib_l reasons H req Hreq c Heq.
    unfold assemble in H.
    destruct (flat_map (fun p => match snd p with
                                  | IStatusRefused c' => [mkRefusedInterface (req_interface (fst p)) c']
                                  | _ => []
                                  end) (classify_all required adm_l contrib_l)) eqn:Hrefused;
      try discriminate H.
    assert (Hin : In (req, IStatusRefused c) (classify_all required adm_l contrib_l)). {
      unfold classify_all. apply in_map_iff. exists req. split; [rewrite Heq; reflexivity | assumption].
    }
    assert (Hcontra : In (mkRefusedInterface (req_interface req) c)
                          (flat_map (fun p => match snd p with
                                               | IStatusRefused c' => [mkRefusedInterface (req_interface (fst p)) c']
                                               | _ => []
                                               end) (classify_all required adm_l contrib_l))). {
      apply in_flat_map. exists (req, IStatusRefused c). split; [assumption | simpl; left; reflexivity].
    }
    rewrite Hrefused in Hcontra. inversion Hcontra.
  Qed.

  (* 3(c): a refused or unresolved outcome never coexists with a
     completed residue -- assemble is a function, so this is a fact
     about equality of a deterministic computation, not new content
     beyond AssemblyOutcome's own constructor distinctness. *)
  Theorem assemble_outcomes_mutually_exclusive :
    forall required adm_l contrib_l,
      (forall refs, assemble required adm_l contrib_l = AssemblyRefused refs ->
         forall r, assemble required adm_l contrib_l <> AssemblyComplete r) /\
      (forall reasons, assemble required adm_l contrib_l = AssemblyUnresolved reasons ->
         forall r, assemble required adm_l contrib_l <> AssemblyComplete r).
  Proof.
    intros required adm_l contrib_l.
    split; intros x Hx r Hr; rewrite Hx in Hr; discriminate Hr.
  Qed.

  (* 3(d): refusal precedence. A verified Incompatible finding on any
     required interface forces AssemblyRefused, regardless of what
     other problems (missing, duplicate, mismatched evidence) exist
     elsewhere -- refusal is checked before any unresolved
     determination, unconditionally. *)
  Theorem assemble_refusal_precedence :
    forall required adm_l contrib_l req c,
      In req required ->
      classify_interface req adm_l contrib_l = IStatusRefused c ->
      exists refs, assemble required adm_l contrib_l = AssemblyRefused refs /\ In (mkRefusedInterface (req_interface req) c) refs.
  Proof.
    intros required adm_l contrib_l req c Hreq Hcl.
    unfold assemble.
    assert (Hin : In (mkRefusedInterface (req_interface req) c)
                      (flat_map (fun p => match snd p with
                                           | IStatusRefused c' => [mkRefusedInterface (req_interface (fst p)) c']
                                           | _ => []
                                           end) (classify_all required adm_l contrib_l))). {
      apply in_flat_map. exists (req, IStatusRefused c). split.
      - unfold classify_all. apply in_map_iff. exists req. split; [rewrite Hcl; reflexivity | assumption].
      - simpl. left. reflexivity.
    }
    destruct (flat_map (fun p => match snd p with
                                  | IStatusRefused c' => [mkRefusedInterface (req_interface (fst p)) c']
                                  | _ => []
                                  end) (classify_all required adm_l contrib_l)) eqn:Hrefused.
    - inversion Hin.
    - exists (r :: l). split; [reflexivity | exact Hin].
  Qed.

End PairwiseToGlobalAssembly.
