(*
   ConflictDiagnosticCompleteness.v

   R13. Bounded completeness of the conflict-diagnostic fragment defined
   in docs/design/CONFLICT_DIAGNOSTIC_COMPLETENESS.md. Combines R11
   (ConflictResolutionTrilemma.v: no single value matches two
   disagreeing declarations) and R12 (ConflictResolutionLowerBound.v: a
   non-lossy encoding must be injective on V * V) into a closed
   four-shape classification of what a diagnostic about a conflicting
   shared interface can honestly be: a refusal to form a composite, a
   lossy scalar summary, a non-lossy structured diagnostic, or an
   explicitly unresolved case.

   "Bounded" is load-bearing: this is completeness for the specific,
   narrow fragment defined below (a four-constructor inductive type
   matching this project's own proved results and veribound-fce's own
   applied vocabulary), not completeness for all possible fusion,
   policy, or coupled-composition systems. See the design doc's §7 for
   exactly what is and is not claimed.

   Imports ConflictResolutionTrilemma.v and ConflictResolutionLowerBound
   .v and reuses their theorems directly rather than duplicating them --
   the fragment's own vocabulary wraps R11/R12, it does not reprove them.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import ConflictResolutionTrilemma.
Require Import ConflictResolutionLowerBound.

(* ------------------------------------------------------------------ *)
(* 1. R11, repackaged in the diagnostic fragment's own vocabulary: a   *)
(*    scalar summary cannot be fully faithful once x <> y.             *)
(* ------------------------------------------------------------------ *)

Theorem scalar_summary_not_fully_faithful_on_conflict :
  forall (V : Type) (x y z : V), x <> y -> ~ (z = x /\ z = y).
Proof.
  exact no_single_value_matches_both_declarations.
Qed.

(* ------------------------------------------------------------------ *)
(* 2. The R12 bridge, in the fragment's own vocabulary: a structured   *)
(*    diagnostic is non-lossy exactly when both fixed projections      *)
(*    recover the original declarations, for every pair.               *)
(* ------------------------------------------------------------------ *)

Theorem structured_diagnostic_nonlossy :
  forall (V C : Type)
         (encode : V -> V -> C)
         (left_read right_read : C -> V),
    (forall x y, left_read (encode x y) = x) ->
    (forall x y, right_read (encode x y) = y) ->
    forall x y, left_read (encode x y) = x /\ right_read (encode x y) = y.
Proof.
  intros V C encode left_read right_read Hleft Hright x y.
  split.
  - apply Hleft.
  - apply Hright.
Qed.

Theorem nonlossy_diagnostic_injective :
  forall (V C : Type)
         (encode : V -> V -> C)
         (left_read right_read : C -> V),
    (forall x y, left_read (encode x y) = x) ->
    (forall x y, right_read (encode x y) = y) ->
    forall x1 y1 x2 y2 : V,
      encode x1 y1 = encode x2 y2 ->
      x1 = x2 /\ y1 = y2.
Proof.
  intros V C encode left_read right_read Hleft Hright x1 y1 x2 y2 Heq.
  apply (nonlossy_encoding_injective V C encode left_read right_read).
  - intros x y. split; [apply Hleft | apply Hright].
  - exact Heq.
Qed.

(* Thin corollaries at C := V * V, reusing R12's own pairing witness and
   the injectivity theorem just proved above rather than reproving
   either from scratch. *)

Theorem pair_diagnostic_is_nonlossy :
  forall (V : Type) (x y : V), fst (x, y) = x /\ snd (x, y) = y.
Proof.
  intros V x y. split; reflexivity.
Qed.

Theorem pair_encoding_injective :
  forall (V : Type) (x1 y1 x2 y2 : V),
    (x1, y1) = (x2, y2) -> x1 = x2 /\ y1 = y2.
Proof.
  intros V x1 y1 x2 y2 Heq.
  apply (nonlossy_diagnostic_injective V (V * V) (fun x y => (x, y)) fst snd).
  - intros x y; reflexivity.
  - intros x y; reflexivity.
  - exact Heq.
Qed.

(* ------------------------------------------------------------------ *)
(* 3. The bounded fragment itself: a closed, four-constructor          *)
(*    diagnostic type, and the classification into four disjoint       *)
(*    classes. See the design doc §3-4 for why these four, and §6 for  *)
(*    exactly what "total"/"exclusive" mean here (a fact about Coq's   *)
(*    closed inductive types, not a new discovery) versus what the     *)
(*    genuine mathematical content of this phase actually is (R11/R12  *)
(*    pinning down the scalar and structured classes' properties).     *)
(* ------------------------------------------------------------------ *)

Section ConflictDiagnosticFragment.

  Variables V C : Type.

  Inductive ConflictDiagnostic : Type :=
    | RefuseDiagnostic
    | ScalarDiagnostic (z : V)
    | StructuredDiagnostic (c : C)
    | UnresolvedDiagnostic.

  Inductive DiagnosticClass : Type :=
    | no_composite
    | lossy_scalar
    | nonlossy_structured
    | unresolved_case.

  Definition classify (d : ConflictDiagnostic) : DiagnosticClass :=
    match d with
    | RefuseDiagnostic => no_composite
    | ScalarDiagnostic _ => lossy_scalar
    | StructuredDiagnostic _ => nonlossy_structured
    | UnresolvedDiagnostic => unresolved_case
    end.

  (* Totality: every diagnostic in the fragment receives a
     classification. Immediate from classify's own totality as a Coq
     function -- named and proved explicitly anyway, the same
     discipline R11's pair_resolver_preserves_both_claims and R12's
     structured_pair_is_nonlossy already followed for near-definitional
     facts worth stating in the vocabulary being built. This is the
     formal content behind "there is no fifth neutral case": a
     ConflictDiagnostic V C cannot be built from anything outside these
     four constructors, and classify assigns exactly one of the four
     DiagnosticClass values to each. *)
  Theorem conflict_diagnostic_classification_total :
    forall d : ConflictDiagnostic, exists cls : DiagnosticClass, classify d = cls.
  Proof.
    intros d. exists (classify d). reflexivity.
  Qed.

  (* Exclusivity: classify never assigns two different classes to the
     same diagnostic -- immediate since classify is a function
     (single-valued by construction), stated explicitly because the
     completeness claim depends on "exactly one," not merely "at least
     one." *)
  Theorem conflict_diagnostic_classification_exclusive :
    forall (d : ConflictDiagnostic) (c1 c2 : DiagnosticClass),
      classify d = c1 -> classify d = c2 -> c1 = c2.
  Proof.
    intros d c1 c2 H1 H2. rewrite <- H1, <- H2. reflexivity.
  Qed.

  (* The four classes are themselves pairwise distinct, so "exactly one
     of four genuinely different classes" -- not four names for the
     same outcome. *)
  Theorem diagnostic_classes_pairwise_distinct :
    no_composite <> lossy_scalar /\
    no_composite <> nonlossy_structured /\
    no_composite <> unresolved_case /\
    lossy_scalar <> nonlossy_structured /\
    lossy_scalar <> unresolved_case /\
    nonlossy_structured <> unresolved_case.
  Proof.
    repeat split; discriminate.
  Qed.

  (* The four constructors themselves are pairwise distinct as Coq
     terms -- the content behind "the four classes are disjoint," kept
     to the three pairs actually needed (RefuseDiagnostic/
     UnresolvedDiagnostic and StructuredDiagnostic/UnresolvedDiagnostic
     add nothing beyond the same discriminate pattern and are omitted
     per the design doc's explicit "do not overbuild it"). *)
  Theorem no_diagnostic_is_both_refuse_and_scalar :
    forall z : V, RefuseDiagnostic <> ScalarDiagnostic z.
  Proof. discriminate. Qed.

  Theorem no_diagnostic_is_both_refuse_and_structured :
    forall c : C, RefuseDiagnostic <> StructuredDiagnostic c.
  Proof. discriminate. Qed.

  Theorem no_diagnostic_is_both_scalar_and_structured :
    forall (z : V) (c : C), ScalarDiagnostic z <> StructuredDiagnostic c.
  Proof. discriminate. Qed.

End ConflictDiagnosticFragment.

(* ------------------------------------------------------------------ *)
(* 4. The headline sentence: no hidden neutral scalar case. The same   *)
(*    fact as scalar_summary_not_fully_faithful_on_conflict above,     *)
(*    given a second name deliberately -- not reproved -- because this *)
(*    is the sentence meant to be quoted on its own, per the design    *)
(*    doc's §8.                                                        *)
(* ------------------------------------------------------------------ *)

Theorem no_hidden_neutral_scalar_case :
  forall (V : Type) (x y z : V), x <> y -> ~ (z = x /\ z = y).
Proof.
  exact scalar_summary_not_fully_faithful_on_conflict.
Qed.
