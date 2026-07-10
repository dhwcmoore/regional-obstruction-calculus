(*
   TypedDiagnosticCalculus.v

   Formalises docs/design/TYPED_DIAGNOSTIC_CALCULUS.md: turns R11-R13
   into explicit introduction, elimination, and reduction rules over
   ConflictDiagnostic V C (rocq/ConflictDiagnosticCompleteness.v).
   Imports ConflictResolutionTrilemma.v (R11) and
   ConflictResolutionLowerBound.v (R12) directly rather than duplicating
   them, matching this project's established discipline.

   Stage 1 (judgments, introduction, elimination): SoundL/SoundR define
   what it means for a diagnostic to honestly let you recover the left/
   right declaration. structured_intro/-left-elim/-right-elim restate
   R12 (structured_diagnostic_nonlossy) as rules. scalar_conflict_loss
   restates R11 (no_single_value_matches_both_declarations) as an
   elimination-inadmissibility fact. refuse_no_composite_left/right and
   unresolved_no_claim_left/right show RefuseDiagnostic and
   UnresolvedDiagnostic have no sound elimination of either kind at
   all -- two structurally identical but semantically distinct facts
   (proved impossibility vs. mere absence of computation; see the
   design doc §6 for why they are kept separate rather than merged).
   elimination_soundness is the calculus-level fact tying R11, R12, and
   R13 together: under a genuine conflict, the ONLY diagnostic that can
   be both left- and right-sound is a StructuredDiagnostic.

   Stage 2 (reduction and safety): RefinesByEvidence formalises
   UNRESOLVED-REFINE-BY-EVIDENCE as a one-constructor relation.
   preservation_under_reduction and no_silent_soundness_gain are the
   design doc §8's safety metatheorems -- the latter shows that
   refining Unresolved into a ScalarDiagnostic under conflict is still
   fully subject to scalar_conflict_loss: passing through Unresolved
   buys nothing.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import ConflictResolutionTrilemma.
Require Import ConflictResolutionLowerBound.
Require Import ConflictDiagnosticCompleteness.

(* ------------------------------------------------------------------ *)
(* Stage 1: judgments and introduction/elimination rules.              *)
(* ------------------------------------------------------------------ *)

Definition SoundL (V C : Type) (left_read : C -> V)
                   (d : ConflictDiagnostic V C) (x : V) : Prop :=
  match d with
  | RefuseDiagnostic _ _ => False
  | ScalarDiagnostic _ _ z => z = x
  | StructuredDiagnostic _ _ c => left_read c = x
  | UnresolvedDiagnostic _ _ => False
  end.

Definition SoundR (V C : Type) (right_read : C -> V)
                   (d : ConflictDiagnostic V C) (y : V) : Prop :=
  match d with
  | RefuseDiagnostic _ _ => False
  | ScalarDiagnostic _ _ z => z = y
  | StructuredDiagnostic _ _ c => right_read c = y
  | UnresolvedDiagnostic _ _ => False
  end.

Theorem structured_left_elim :
  forall (V C : Type) (encode : V -> V -> C) (left_read right_read : C -> V),
    (forall x y, left_read (encode x y) = x) ->
    (forall x y, right_read (encode x y) = y) ->
    forall x y : V,
      SoundL V C left_read (StructuredDiagnostic V C (encode x y)) x.
Proof.
  intros V C encode left_read right_read Hleft Hright x y.
  destruct (structured_diagnostic_nonlossy V C encode left_read right_read Hleft Hright x y)
    as [Hl _].
  exact Hl.
Qed.

Theorem structured_right_elim :
  forall (V C : Type) (encode : V -> V -> C) (left_read right_read : C -> V),
    (forall x y, left_read (encode x y) = x) ->
    (forall x y, right_read (encode x y) = y) ->
    forall x y : V,
      SoundR V C right_read (StructuredDiagnostic V C (encode x y)) y.
Proof.
  intros V C encode left_read right_read Hleft Hright x y.
  destruct (structured_diagnostic_nonlossy V C encode left_read right_read Hleft Hright x y)
    as [_ Hr].
  exact Hr.
Qed.

Theorem structured_intro :
  forall (V C : Type) (encode : V -> V -> C) (left_read right_read : C -> V),
    (forall x y, left_read (encode x y) = x) ->
    (forall x y, right_read (encode x y) = y) ->
    forall x y : V,
      SoundL V C left_read (StructuredDiagnostic V C (encode x y)) x /\
      SoundR V C right_read (StructuredDiagnostic V C (encode x y)) y.
Proof.
  intros V C encode left_read right_read Hleft Hright x y.
  split.
  - exact (structured_left_elim V C encode left_read right_read Hleft Hright x y).
  - exact (structured_right_elim V C encode left_read right_read Hleft Hright x y).
Qed.

Theorem scalar_conflict_loss :
  forall (V C : Type) (left_read right_read : C -> V) (x y z : V),
    x <> y ->
    ~ (SoundL V C left_read (ScalarDiagnostic V C z) x /\
       SoundR V C right_read (ScalarDiagnostic V C z) y).
Proof.
  intros V C left_read right_read x y z Hneq [HL HR].
  simpl in HL, HR.
  apply (no_single_value_matches_both_declarations V x y z Hneq).
  split; assumption.
Qed.

Theorem refuse_no_composite_left :
  forall (V C : Type) (left_read : C -> V),
    ~ exists x : V, SoundL V C left_read (RefuseDiagnostic V C) x.
Proof.
  intros V C left_read [x H]. simpl in H. exact H.
Qed.

Theorem refuse_no_composite_right :
  forall (V C : Type) (right_read : C -> V),
    ~ exists y : V, SoundR V C right_read (RefuseDiagnostic V C) y.
Proof.
  intros V C right_read [y H]. simpl in H. exact H.
Qed.

Theorem unresolved_no_claim_left :
  forall (V C : Type) (left_read : C -> V),
    ~ exists x : V, SoundL V C left_read (UnresolvedDiagnostic V C) x.
Proof.
  intros V C left_read [x H]. simpl in H. exact H.
Qed.

Theorem unresolved_no_claim_right :
  forall (V C : Type) (right_read : C -> V),
    ~ exists y : V, SoundR V C right_read (UnresolvedDiagnostic V C) y.
Proof.
  intros V C right_read [y H]. simpl in H. exact H.
Qed.

(* The unifying fact tying R11, R12, and R13 together at the calculus
   level: under a genuine conflict, the ONLY diagnostic that can be
   both left- and right-sound is a StructuredDiagnostic, and its
   projections witness exactly the pair being diagnosed. This is the
   formal cash-out of docs/theory/NO_NEUTRAL_SCALAR_FUSION.md's
   headline sentence -- there is no fifth, hidden way to be doubly
   sound under conflict. *)
Theorem elimination_soundness :
  forall (V C : Type) (left_read right_read : C -> V)
         (d : ConflictDiagnostic V C) (x y : V),
    x <> y ->
    SoundL V C left_read d x ->
    SoundR V C right_read d y ->
    exists c : C, d = StructuredDiagnostic V C c /\
                  left_read c = x /\ right_read c = y.
Proof.
  intros V C left_read right_read d x y Hneq HL HR.
  destruct d as [ | z | c | ]; simpl in HL, HR.
  - contradiction.
  - exfalso.
    apply (no_single_value_matches_both_declarations V x y z Hneq).
    split; assumption.
  - exists c. auto.
  - contradiction.
Qed.

(* ------------------------------------------------------------------ *)
(* Stage 2: reduction and safety.                                      *)
(* ------------------------------------------------------------------ *)

Inductive RefinesByEvidence (V C : Type) : ConflictDiagnostic V C -> ConflictDiagnostic V C -> Prop :=
  | refine_by_evidence :
      forall d : ConflictDiagnostic V C,
        d <> UnresolvedDiagnostic V C ->
        RefinesByEvidence V C (UnresolvedDiagnostic V C) d.

Theorem reduction_source_is_always_unresolved :
  forall (V C : Type) (d d' : ConflictDiagnostic V C),
    RefinesByEvidence V C d d' -> d = UnresolvedDiagnostic V C.
Proof.
  intros V C d d' H. inversion H. reflexivity.
Qed.

Theorem reduction_target_is_never_unresolved :
  forall (V C : Type) (d d' : ConflictDiagnostic V C),
    RefinesByEvidence V C d d' -> d' <> UnresolvedDiagnostic V C.
Proof.
  intros V C d d' H. inversion H. assumption.
Qed.

(* Preservation, honestly stated: this calculus's well-formedness
   judgment (d : ConflictDiagnostic V C) carries no content beyond
   type membership, so classical "type preservation" is automatic --
   the non-trivial invariant reduction actually preserves is that it
   never re-enters or originates anywhere but Unresolved, i.e.
   Unresolved is not a fixed point of its own relation and is the
   unique source. Both halves proved above; bundled here as the named
   preservation_under_reduction theorem the design doc §8 calls for. *)
Theorem preservation_under_reduction :
  forall (V C : Type) (d d' : ConflictDiagnostic V C),
    RefinesByEvidence V C d d' ->
    d = UnresolvedDiagnostic V C /\ d' <> UnresolvedDiagnostic V C.
Proof.
  intros V C d d' H.
  split.
  - exact (reduction_source_is_always_unresolved V C d d' H).
  - exact (reduction_target_is_never_unresolved V C d d' H).
Qed.

(* The interesting one: passing through Unresolved buys nothing. A
   diagnostic reached by refining Unresolved into a ScalarDiagnostic is
   STILL fully subject to scalar_conflict_loss -- the reduction step
   itself contributes no soundness the target would not already have
   (or lack) on its own. Stated narrowly at the scalar target, per the
   design doc's own instruction to prove a narrow version first if the
   general one becomes awkward: the scalar case is exactly where a
   silent soundness gain would be dangerous (mistaking "this used to be
   unresolved, now it's decided" for "this is now trustworthy"), so it
   is the version worth having even alone. *)
Theorem no_silent_soundness_gain :
  forall (V C : Type) (left_read right_read : C -> V) (x y z : V),
    x <> y ->
    RefinesByEvidence V C (UnresolvedDiagnostic V C) (ScalarDiagnostic V C z) ->
    ~ (SoundL V C left_read (ScalarDiagnostic V C z) x /\
       SoundR V C right_read (ScalarDiagnostic V C z) y).
Proof.
  intros V C left_read right_read x y z Hneq Hred.
  exact (scalar_conflict_loss V C left_read right_read x y z Hneq).
Qed.
