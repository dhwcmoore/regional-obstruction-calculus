(*
   CandidateThreeBDistinctSupportClassification.v

   The negative-direction half of the Candidate 3b classification,
   completing the pair started by RepeatedTripleSupportCandidate3b.v.
   That file proves: when a cover forces all four theta-triples to share
   ONE repeated support point, Candidate 3b's induced map has rank 2, a
   genuinely partial obstruction quotient, and genuinely-shared columns.
   This file proves the other half, at the same machine-checked level:
   when the four triple supports are instead pairwise DISTINCT, Candidate
   3b is cover-inert -- every carrier coordinate is privately supported
   by exactly one seam, and the induced map is full rank.

   Together, the two files give the classification stated informally in
   candidate_discipline_diagnostic.py and repeated_triple_support_
   diagnostic.py (docs/diagnostics/REPEATED_TRIPLE_SUPPORT_DIAGNOSTIC.md):

       Candidate 3b is structurally selective only when triple support is
       genuinely forced to repeat. Distinct support degenerates into
       independent seam-local freedom.

   Scope, stated precisely (the theorem is only as general as the proof
   supports, not "all distinct-support systems" by assumption)
   -----------------------------------------------------------------------
   The hypothesis proved from here is PAIRWISE DISTINCTNESS of the four
   triple-support VALUES, abstracted as an arbitrary type `Support` with
   decidable equality -- not "singleton overlap" (a separate well-
   formedness condition on the underlying associator computation, already
   enforced elsewhere by associator_residue.compute_seam_residue, and not
   re-derived here, exactly as RepeatedTripleSupportCandidate3b.v does not
   re-derive Delta_e = rho_X,T - rho_Z,T from regional_composition.py's
   literal associator formula -- both files take Candidate 3b's already-
   verified closed form as given). Distinctness of the four support
   VALUES turns out to be exactly what the rank argument needs; no
   assumption about what points are inside U1..U4, and no Point type at
   all, appears anywhere below.

   `RegionIndex`, `Seam`, `seam_X`, `seam_Z` are reused unchanged from
   RepeatedTripleSupportCandidate3b.v -- the theta-role table is a fact
   about the four-cycle nerve's combinatorics, independent of which
   support regime is under discussion.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import RepeatedTripleSupportCandidate3b.

Section DistinctSupportClassification.

  Variable Support : Type.
  Variable Support_eq_dec : forall x y : Support, {x = y} + {x <> y}.
  Variable theta_support : Seam -> Support.

  Definition Injective (f : Seam -> Support) : Prop :=
    forall a b, f a = f b -> a = b.

  Hypothesis theta_injective : Injective theta_support.

  (* Carrier coordinates for Candidate 3b under an arbitrary per-seam
     support assignment: (region, support-value) pairs. When
     theta_support is CONSTANT (every seam gets the same support point),
     this is the repeated-support regime RepeatedTripleSupportCandidate3b.
     v handles directly on RegionIndex -> Q; here theta_support is
     injective instead, the opposite regime. *)
  Definition Carrier : Type := (RegionIndex * Support)%type.

  Definition Carrier_eq_dec : forall x y : Carrier, {x = y} + {x <> y}.
  Proof.
    intros [r1 s1] [r2 s2].
    destruct (RegionIndex_eq_dec r1 r2) as [Hr | Hr];
      destruct (Support_eq_dec s1 s2) as [Hs | Hs].
    - left; subst; reflexivity.
    - right; intro H; inversion H; contradiction.
    - right; intro H; inversion H; contradiction.
    - right; intro H; inversion H; contradiction.
  Defined.

  (* Candidate 3b's induced map, generalised over an arbitrary per-seam
     support assignment: Delta_e = rho_{X,theta(e)} - rho_{Z,theta(e)},
     the same closed form used throughout this project, taken as given
     (see header comment). *)
  Definition B3b_general (rho : Carrier -> Q) (e : Seam) : Q :=
    rho (seam_X e, theta_support e) - rho (seam_Z e, theta_support e).

  Lemma seam_X_ne_seam_Z : forall e, seam_X e <> seam_Z e.
  Proof. intro e; destruct e; discriminate. Qed.

  (* The headline structural theorem: under pairwise-distinct support,
     no two DIFFERENT seams can ever reference the same carrier
     coordinate -- the Rocq form of the diagnostic's
     {private_residual: 8, genuinely_shared: 0, zero_column: 0}. This
     does not depend on which regions happen to coincide as sets, only
     on the support values themselves being distinct: two carrier
     coordinates (r1,s1) and (r2,s2) already differ when s1<>s2,
     regardless of r1 vs r2. *)
  Theorem distinct_support_no_shared_coordinate :
    forall e1 e2, e1 <> e2 ->
      (seam_X e1, theta_support e1) <> (seam_X e2, theta_support e2) /\
      (seam_X e1, theta_support e1) <> (seam_Z e2, theta_support e2) /\
      (seam_Z e1, theta_support e1) <> (seam_X e2, theta_support e2) /\
      (seam_Z e1, theta_support e1) <> (seam_Z e2, theta_support e2).
  Proof.
    intros e1 e2 Hne.
    assert (Hts : theta_support e1 <> theta_support e2).
    { intro Heq; apply Hne; apply theta_injective; exact Heq. }
    repeat split; intro H; inversion H; contradiction.
  Qed.

  Definition unit_at (target c : Carrier) : Q :=
    if Carrier_eq_dec c target then 1 else 0.

  (* The consequence: every seam's residue can be isolated -- set to 1
     while every other seam's residue is forced to 0 -- so the induced
     map achieves all four standard basis directions of Q^4. Since Q^4
     is 4-dimensional and Seam has exactly 4 elements, this is full
     rank: the Rocq form of the diagnostic's "too free" / "cover-inert"
     / rank(B)=4 verdict, generalised to ANY cover whose four triple
     supports are pairwise distinct, not just the one concrete witness
     cover the Python diagnostic ran. *)
  Theorem distinct_support_full_rank :
    forall e : Seam,
      exists rho : Carrier -> Q,
        B3b_general rho e == 1 /\
        (forall e', e' <> e -> B3b_general rho e' == 0).
  Proof.
    intro e.
    exists (unit_at (seam_X e, theta_support e)).
    split.
    - unfold B3b_general, unit_at.
      destruct (Carrier_eq_dec (seam_X e, theta_support e) (seam_X e, theta_support e))
        as [_ | Hc]; [ | contradiction Hc; reflexivity].
      destruct (Carrier_eq_dec (seam_Z e, theta_support e) (seam_X e, theta_support e))
        as [Heq | _].
      + exfalso; apply (seam_X_ne_seam_Z e).
        pose proof (f_equal fst Heq) as HZX; simpl in HZX; symmetry; exact HZX.
      + simpl; ring.
    - intros e' Hne.
      destruct (distinct_support_no_shared_coordinate e' e Hne) as [H1 [_ [H3 _]]].
      unfold B3b_general, unit_at.
      destruct (Carrier_eq_dec (seam_X e', theta_support e') (seam_X e, theta_support e))
        as [Heq1 | _]; [exfalso; apply H1; exact Heq1 | ].
      destruct (Carrier_eq_dec (seam_Z e', theta_support e') (seam_X e, theta_support e))
        as [Heq2 | _]; [exfalso; apply H3; exact Heq2 | ].
      simpl; ring.
  Qed.

End DistinctSupportClassification.

(* ------------------------------------------------------------------ *)
(* Concrete instantiation: the actual distinct-support cover used by    *)
(* candidate_discipline_diagnostic.py (coupled_realisability_diagnostic *)
(* .REGIONS), where T12={a}, T23={b}, T34={c}, T14={d} are four         *)
(* distinct labelled points -- confirming the abstract theorem above    *)
(* actually specialises to the concrete diagnostic, not just a          *)
(* hypothetical cover.                                                  *)
(* ------------------------------------------------------------------ *)

Module ConcreteDistinctSupportWitness.

  (* a=0, b=1, c=2, d=3, matching the diagnostic's four distinct
     single-point triple overlaps. *)
  Inductive Label := La | Lb | Lc | Ld.

  Definition Label_eq_dec : forall x y : Label, {x = y} + {x <> y}.
  Proof. decide equality. Defined.

  Definition concrete_theta (e : Seam) : Label :=
    match e with
    | SE12 => La
    | SE23 => Lb
    | SE34 => Lc
    | SE14 => Ld
    end.

  Lemma concrete_theta_injective : Injective Label concrete_theta.
  Proof. intros e1 e2 Heq; destruct e1, e2; simpl in Heq; congruence. Qed.

  Theorem concrete_witness_full_rank :
    forall e : Seam,
      exists rho : (RegionIndex * Label)%type -> Q,
        B3b_general Label concrete_theta rho e == 1 /\
        (forall e', e' <> e -> B3b_general Label concrete_theta rho e' == 0).
  Proof.
    exact (distinct_support_full_rank Label Label_eq_dec concrete_theta
             concrete_theta_injective).
  Qed.

End ConcreteDistinctSupportWitness.
