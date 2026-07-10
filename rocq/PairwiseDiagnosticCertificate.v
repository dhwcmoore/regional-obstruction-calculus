(*
   PairwiseDiagnosticCertificate.v

   R15. The first bridge between two previously separate proved theories
   in this project: R14's typed diagnostic calculus
   (TypedDiagnosticCalculus.v -- which diagnostic SHAPES preserve which
   declarations) and CoupledParallelCompatibility.v's two-branch,
   one-seam gluing theory (Phase 5c -- what pairwise compatibility and
   incompatibility actually MEAN for keyed declarations). Neither file
   is modified; both are imported and reused exactly as they stand, per
   docs/design/CERTIFICATE_COMPOSITION_SPEC.md's own scoping of
   `pairwise_compatibility` against this specific domain.

   The governing question: can a pairwise diagnostic be constructed so
   that compatibility requires an actual glue witness, incompatibility
   requires an actual local-conflict witness, and unresolved makes no
   semantic claim at all? Answered here, constructively, for the
   Key -> option Value domain CoupledParallelCompatibility.v already
   formalises.

   A DESIGN NOTE ON THE PAYLOAD TYPE, worth recording since it is not
   obvious from the schematic sketch this file implements: the
   StructuredDiagnostic payload is (dA, dB) -- the pair of declarations
   themselves -- NOT the glue witness `g`. This is not a simplification;
   it is required for soundness. A glue `g` alone does not determine
   (dA, dB) uniquely -- e.g. under candidate_glue, dA := (k1 |-> 5),
   dB := (nothing) and dA' := (nothing), dB' := (k1 |-> 5) glue to the
   IDENTICAL g := (k1 |-> 5), so no function of g alone could recover
   which pair produced it. left_read/right_read must work for every
   (x, y), not just one instance (R12's own NonLossy hypothesis), so the
   payload must retain (dA, dB) explicitly -- exactly R12's own
   structured_pair_is_nonlossy witness, instantiated at V := Declaration
   Key Value. `g` is still used, as the CERTIFICATE that a composite
   exists (the CompatibleEvidence constructor's own witness) -- it just
   is not, and cannot be, the diagnostic's stored payload.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import CoupledParallelCompatibility.
Require Import ConflictDiagnosticCompleteness.
Require Import TypedDiagnosticCalculus.

Section PairwiseDiagnosticCertificate.

  Variables Key Value : Type.

  Notation Decl := (Declaration Key Value).

  (* The exact hypothesis shape of incompatible_has_no_glue's own
     premise, given a name -- not a new definition, a name for an
     existing pattern already proved in CoupledParallelCompatibility.v. *)
  Definition LocalConflict (dA dB : Decl) : Prop :=
    exists (k : Key) (va vb : Value),
      dA k = Some va /\ dB k = Some vb /\ va <> vb.

  Definition CompositePayload : Type := (Decl * Decl)%type.

  (* The asymmetry is deliberate: compatibility carries a positive glue;
     incompatibility carries a positive obstruction. No-composite is
     DERIVED from the obstruction (see pairwise_diagnostic_certificate_
     sound below), never stored as primitive evidence -- there is no
     constructor here for a bare "NoAcceptableComposite" claim. *)
  Inductive DecisivePairwiseEvidence (dA dB : Decl) : Type :=
    | CompatibleEvidence :
        forall g : Decl, IsGlue Key Value dA dB g -> DecisivePairwiseEvidence dA dB
    | IncompatibleEvidence :
        LocalConflict dA dB -> DecisivePairwiseEvidence dA dB.

  (* Unresolved lives OUTSIDE the decisive certificate, deliberately:
     it means only "no validated glue or local-conflict certificate is
     being presented," not that any particular search was exhaustive,
     bounded, or correctly executed -- that stronger procedural claim
     would need a separate search semantics this file does not define. *)
  Inductive PairwiseResult (dA dB : Decl) : Type :=
    | Decided : DecisivePairwiseEvidence dA dB -> PairwiseResult dA dB
    | Unresolved : PairwiseResult dA dB.

  (* Erasure into R14's existing diagnostic vocabulary. There is no
     route to ScalarDiagnostic anywhere in this match -- see
     certified_pairwise_never_scalar below for the theorem confirming
     this is not merely an omission but a fact about every possible
     result. *)
  Definition pairwise_diagnostic (dA dB : Decl) (result : PairwiseResult dA dB)
    : ConflictDiagnostic Decl CompositePayload :=
    match result with
    | Decided _ _ (CompatibleEvidence _ _ _ _) => StructuredDiagnostic Decl CompositePayload (dA, dB)
    | Decided _ _ (IncompatibleEvidence _ _ _) => RefuseDiagnostic Decl CompositePayload
    | Unresolved _ _ => UnresolvedDiagnostic Decl CompositePayload
    end.

  (* The central theorem: representation soundness (R14) and semantic
     soundness (CoupledParallelCompatibility.v) combined, case by case.
     The no-glue conclusion in the incompatible branch is OBTAINED from
     interface_disagreement_blocks_glue, applied to the LocalConflict
     witness's own (k, va, vb) -- not stored as a second, independent
     assertion. *)
  Theorem pairwise_diagnostic_certificate_sound :
    forall (dA dB : Decl) (result : PairwiseResult dA dB),
      match result with
      | Decided _ _ (CompatibleEvidence _ _ g Hg) =>
          pairwise_diagnostic dA dB result = StructuredDiagnostic Decl CompositePayload (dA, dB)
          /\ SoundL Decl CompositePayload fst (pairwise_diagnostic dA dB result) dA
          /\ SoundR Decl CompositePayload snd (pairwise_diagnostic dA dB result) dB
          /\ IsGlue Key Value dA dB g
      | Decided _ _ (IncompatibleEvidence _ _ conflict) =>
          pairwise_diagnostic dA dB result = RefuseDiagnostic Decl CompositePayload
          /\ LocalConflict dA dB
          /\ forall g : Decl, ~ IsGlue Key Value dA dB g
      | Unresolved _ _ =>
          pairwise_diagnostic dA dB result = UnresolvedDiagnostic Decl CompositePayload
          /\ ~ SoundL Decl CompositePayload fst (pairwise_diagnostic dA dB result) dA
          /\ ~ SoundR Decl CompositePayload snd (pairwise_diagnostic dA dB result) dB
      end.
  Proof.
    intros dA dB result.
    destruct result as [ev | ].
    - destruct ev as [g Hg | conflict].
      + simpl.
        split; [reflexivity |].
        split; [reflexivity |].
        split; [reflexivity | exact Hg].
      + simpl. destruct conflict as [k [va [vb [HdA [HdB Hneq]]]]].
        split; [reflexivity |].
        split; [exists k, va, vb; auto |].
        intros g. exact (interface_disagreement_blocks_glue Key Value dA dB k va vb HdA HdB Hneq g).
    - simpl.
      split; [reflexivity |].
      split; intro H; exact H.
  Qed.

  (* Supporting results, each isolating one piece of the central
     theorem's content as its own named fact. *)

  Theorem certified_pairwise_never_scalar :
    forall (dA dB : Decl) (result : PairwiseResult dA dB) (z : Decl),
      pairwise_diagnostic dA dB result <> ScalarDiagnostic Decl CompositePayload z.
  Proof.
    intros dA dB result z.
    destruct result as [ev | ]; [destruct ev as [g Hg | conflict] |]; simpl; discriminate.
  Qed.

  Theorem compatible_certificate_preserves_both :
    forall (dA dB g : Decl) (Hg : IsGlue Key Value dA dB g),
      SoundL Decl CompositePayload fst
        (pairwise_diagnostic dA dB (Decided dA dB (CompatibleEvidence dA dB g Hg))) dA
      /\ SoundR Decl CompositePayload snd
        (pairwise_diagnostic dA dB (Decided dA dB (CompatibleEvidence dA dB g Hg))) dB.
  Proof.
    intros dA dB g Hg. simpl. split; reflexivity.
  Qed.

  Theorem incompatible_certificate_blocks_every_glue :
    forall dA dB : Decl, LocalConflict dA dB -> forall g : Decl, ~ IsGlue Key Value dA dB g.
  Proof.
    intros dA dB [k [va [vb [HdA [HdB Hneq]]]]] g.
    exact (interface_disagreement_blocks_glue Key Value dA dB k va vb HdA HdB Hneq g).
  Qed.

  Theorem unresolved_certificate_makes_no_branch_claim :
    forall dA dB : Decl,
      ~ SoundL Decl CompositePayload fst
        (pairwise_diagnostic dA dB (Unresolved dA dB)) dA
      /\ ~ SoundR Decl CompositePayload snd
        (pairwise_diagnostic dA dB (Unresolved dA dB)) dB.
  Proof.
    intros dA dB. simpl. split; intro H; exact H.
  Qed.

  (* The certificate-level safety property this bridge exists to
     establish: within this bridge, a refusal cannot be emitted without
     a LocalConflict witness. Diagnostic shape alone does not warrant
     refusal; checked local evidence authorises the refusal
     constructor. *)
  Theorem refusal_requires_local_conflict :
    forall (dA dB : Decl) (result : PairwiseResult dA dB),
      pairwise_diagnostic dA dB result = RefuseDiagnostic Decl CompositePayload ->
      LocalConflict dA dB.
  Proof.
    intros dA dB result Heq.
    destruct result as [ev | ].
    - destruct ev as [g Hg | conflict].
      + simpl in Heq. discriminate Heq.
      + exact conflict.
    - simpl in Heq. discriminate Heq.
  Qed.

End PairwiseDiagnosticCertificate.
