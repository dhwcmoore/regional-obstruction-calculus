(*
   RepeatedTripleSupportCandidate3b.v

   A finite-incidence-first formalisation of the sixth realisability
   diagnostic (repeated_triple_support_diagnostic.py,
   docs/diagnostics/REPEATED_TRIPLE_SUPPORT_DIAGNOSTIC.md, commit db6a5cb): the first
   positive linear/rational result in the realisability line, Candidate 3b
   (ordered restriction-to-triple-support outer-slot coupling) run on a
   cover whose four theta-triples share one repeated triple-support point.

   Per the user's explicit direction, this file does NOT begin with a
   geometric/topological theorem about arbitrary point-set covers. It
   isolates the exact combinatorial condition the diagnostic used --
   "all four theta-triple supports resolve to the same singleton" -- as a
   named structure (RepeatedTripleSupport, Part 1), independent of metric
   size, region richness, or point count. Candidate 3b's induced map
   (Part 2) is then pure finite rational linear algebra on the four-
   dimensional carrier rho : RegionIndex -> Q, exactly mirroring how
   FourCycleObstruction.v treats delta0 as a concrete Q-matrix rather than
   re-deriving it from finite_algebra.py/regional_composition.py.

   Two parts, deliberately not merged into one monolithic claim:

   Part 1 (abstract, Point-level): a four-theta-cycle nerve, triple-support
   predicates T12/T23/T34/T14, the RepeatedTripleSupport record, and the
   structural impossibility lemma that gives repeated support no partial
   case: if a point lies in two distinct theta-triples' supports, it lies
   in all four. This is pure set membership -- no finiteness, no decidable
   equality, no point-count assumption anywhere.

   Part 2 (concrete, linear-algebra-level): RegionIndex/Seam as finite
   inductive types, the theta-role table seam_X/seam_Z (copied from the
   COMMITTED diagnostic matrix, not from memory -- see the orientation
   note below), Candidate 3b's induced map B3b, and the three theorems the
   diagnostic checked computationally: genuinely-shared columns, a
   repairable direction inside the image, and a non-repairable direction
   inside the image -- together the Rocq form of "genuinely partial,
   nontrivial obstruction quotient", proved by exhibiting explicit
   witnesses (Sec. 7's exhibit-don't-abstract strategy), not by invoking a
   general-purpose rank library.

   Orientation note, corrected against the committed source, not memory:
   an earlier draft of this plan (from the requesting conversation, not
   this file) guessed theta(e14) = (U1,U4,U2), giving r_e14 = rho1 - rho2.
   The actual, committed, real-code-verified convention
   (repeated_triple_support_diagnostic.THETA, matching
   coupled_realisability_diagnostic.py and lattice_ie_diagnostic.py) is
   theta(e14) = (U4,U1,U2), giving r_e14 = rho4 - rho2 -- checked here by
   printing repeated_triple_support_diagnostic.induced_B() directly before
   writing seam_X/seam_Z below, exactly the kind of slip this project's
   verification discipline exists to catch.

   What this file does NOT prove: it does not mechanise
   regional_composition.py's associator formula, so it does not derive
   "Delta_e = mu_VW - mu_UvV_W + mu_U_VvW - mu_UV collapses to rho_X -
   rho_Z under Candidate 3b" from first principles -- that reduction is
   the Python side's job (verified there against compute_seam_residue
   under random rational parameters; see
   repeated_triple_support_diagnostic.verify_reduction_against_real_code).
   B3b's formula is taken here as the already-verified closed form, the
   same way FourCycleObstruction.v takes delta0's row formula as given
   rather than re-deriving it from finite_algebra.py. It does not claim
   linear coupled generators work in general -- one rule, one cover
   family, a diagnostic witness in Rocq form, not a theorem about
   arbitrary linear couplings.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import FourCycleObstruction.

(* ------------------------------------------------------------------ *)
(* Part 1: the four-theta-cycle nerve, abstractly, and the             *)
(* impossibility of partial repeated triple support.                   *)
(* ------------------------------------------------------------------ *)

Section ThetaCycleSupport.

  Variable Point : Type.
  Variable U1 U2 U3 U4 : Point -> Prop.

  (* theta(e12)=(U1,U2,U3), theta(e23)=(U2,U3,U4), theta(e34)=(U3,U4,U1),
     theta(e14)=(U4,U1,U2) -- the same four triples Part 2's seam_X/
     seam_Z are built from; order within each conjunction does not
     affect the *set* T_e denotes, only which coordinate plays the "X"
     or "Z" role once Candidate 3b is applied in Part 2. *)
  Definition T12 (p : Point) : Prop := U1 p /\ U2 p /\ U3 p.
  Definition T23 (p : Point) : Prop := U2 p /\ U3 p /\ U4 p.
  Definition T34 (p : Point) : Prop := U3 p /\ U4 p /\ U1 p.
  Definition T14 (p : Point) : Prop := U4 p /\ U1 p /\ U2 p.

  (* The structural fact from repeated_triple_support_diagnostic.
     verify_opposite_pair_sharing_forces_global(), proved here in
     general rather than checked on one concrete cover: any two
     theta-triples' region-sets already cover all four regions (each
     triple omits exactly one region; T12 omits U4, T34 omits U2), so a
     point in both T12 and T34 lies in all four regions, hence in T23
     and T14 too. This is the fact that rules out an "opposite pairs,
     distinct points" repeated-support pattern -- no finiteness or
     decidable equality is used anywhere in this proof. *)
  Lemma T12_T34_forces_all_regions :
    forall p, T12 p -> T34 p -> U1 p /\ U2 p /\ U3 p /\ U4 p.
  Proof.
    intros p [Hu1 [Hu2 Hu3]] [Hu3' [Hu4 Hu1']].
    repeat split; assumption.
  Qed.

  Theorem T12_T34_forces_T23_T14 :
    forall p, T12 p -> T34 p -> T23 p /\ T14 p.
  Proof.
    intros p H12 H34.
    destruct (T12_T34_forces_all_regions p H12 H34) as [Hu1 [Hu2 [Hu3 Hu4]]].
    unfold T23, T14.
    split; repeat split; assumption.
  Qed.

  (* RepeatedTripleSupport: the finite incidence condition db6a5cb
     actually depended on, made a named structure rather than an
     informal hypothesis. All four singleton conditions are listed as
     fields (matching the diagnostic's check_triple_overlaps_singleton_
     and_equal, which checks all four); T12_T34_forces_T23_T14 above
     shows rts_t23_in/rts_t14_in are not logically independent of
     rts_t12_in/rts_t34_in -- listing all four is a faithful record of
     what the diagnostic checked, not a claim that the fields are a
     minimal independent basis. *)
  Record RepeatedTripleSupport := mkRepeatedTripleSupport {
    rts_point : Point;
    rts_t12_in : T12 rts_point;
    rts_t23_in : T23 rts_point;
    rts_t34_in : T34 rts_point;
    rts_t14_in : T14 rts_point;
    rts_t12_unique : forall p, T12 p -> p = rts_point;
    rts_t23_unique : forall p, T23 p -> p = rts_point;
    rts_t34_unique : forall p, T34 p -> p = rts_point;
    rts_t14_unique : forall p, T14 p -> p = rts_point;
  }.

End ThetaCycleSupport.

(* ------------------------------------------------------------------ *)
(* Part 2: Candidate 3b's induced map, as concrete finite rational      *)
(* linear algebra -- independent of any particular Point instantiation, *)
(* justified by Part 1 whenever a RepeatedTripleSupport witness exists. *)
(* ------------------------------------------------------------------ *)

Inductive RegionIndex := RU1 | RU2 | RU3 | RU4.
Inductive Seam := SE12 | SE23 | SE34 | SE14.

Definition RegionIndex_eq_dec : forall x y : RegionIndex, {x = y} + {x <> y}.
Proof. decide equality. Defined.

(* theta-role table, copied from the printed, committed
   repeated_triple_support_diagnostic.induced_B() matrix -- not from
   memory. See the orientation note in the header comment: e14's X role
   is RU4, not RU1. *)
Definition seam_X (e : Seam) : RegionIndex :=
  match e with
  | SE12 => RU1
  | SE23 => RU2
  | SE34 => RU3
  | SE14 => RU4
  end.

Definition seam_Z (e : Seam) : RegionIndex :=
  match e with
  | SE12 => RU3
  | SE23 => RU4
  | SE34 => RU1
  | SE14 => RU2
  end.

(* Candidate 3b: mu_UV = mu_VW = 0, mu_U_VvW = rho_{X,T}, mu_UvV_W =
   rho_{Z,T}; under the verified closed form Delta_e = mu_VW - mu_UvV_W +
   mu_U_VvW - mu_UV, this reduces to rho_X - rho_Z (taken as given here,
   not re-derived -- see header comment). *)
Definition B3b (rho : RegionIndex -> Q) (e : Seam) : Q :=
  rho (seam_X e) - rho (seam_Z e).

(* The same map, as a vec4 in (e12,e23,e34,e14) order -- exactly
   FourCycleObstruction.v's C1 layout -- so it can be compared directly
   against delta0's image. *)
Definition B3b_vec4 (rho : RegionIndex -> Q) : vec4 :=
  mkvec4 (B3b rho SE12) (B3b rho SE23) (B3b rho SE34) (B3b rho SE14).

Definition unit_rho (u : RegionIndex) : RegionIndex -> Q :=
  fun r => if RegionIndex_eq_dec r u then 1 else 0.

(* ------------------------------------------------------------------ *)
(* Theorem: the surviving columns are genuinely shared -- the Rocq form *)
(* of the diagnostic's sharing check summary                            *)
(* {zero_column: 0, private_residual: 0, genuinely_shared: 4}.          *)
(* ------------------------------------------------------------------ *)

Theorem B3b_unit_columns_genuinely_shared :
  forall u : RegionIndex,
    exists e1 e2 : Seam,
      e1 <> e2 /\ ~ (B3b (unit_rho u) e1 == 0) /\ ~ (B3b (unit_rho u) e2 == 0).
Proof.
  intro u.
  destruct u.
  - exists SE12, SE34.
    unfold B3b, seam_X, seam_Z, unit_rho; simpl.
    repeat split; try discriminate; intro H; compute in H; discriminate H.
  - exists SE23, SE14.
    unfold B3b, seam_X, seam_Z, unit_rho; simpl.
    repeat split; try discriminate; intro H; compute in H; discriminate H.
  - exists SE12, SE34.
    unfold B3b, seam_X, seam_Z, unit_rho; simpl.
    repeat split; try discriminate; intro H; compute in H; discriminate H.
  - exists SE23, SE14.
    unfold B3b, seam_X, seam_Z, unit_rho; simpl.
    repeat split; try discriminate; intro H; compute in H; discriminate H.
Qed.

(* ------------------------------------------------------------------ *)
(* The two spanning directions of the image, matching the diagnostic's  *)
(* rank(B)=2: g1 (the e12/e34 direction) turns out to be repairable,    *)
(* g2 (the e23/e14 direction) does not -- exactly dim_intersection=1,   *)
(* dim_quotient=1.                                                      *)
(* ------------------------------------------------------------------ *)

Definition g1 : vec4 := mkvec4 1 0 (-1) 0.
Definition g2 : vec4 := mkvec4 0 1 0 (-1).

(* Every B3b image vector is exactly a*g1 + b*g2 for a = rho(RU1) -
   rho(RU3), b = rho(RU2) - rho(RU4) -- the Rocq form of rank(B3b)=2,
   proved by exhibiting the coefficients rather than invoking a rank
   library. *)
Theorem B3b_image_in_span_g1_g2 :
  forall rho : RegionIndex -> Q,
    veq (B3b_vec4 rho)
        (mkvec4
           ((rho RU1 - rho RU3) * 1 + (rho RU2 - rho RU4) * 0)
           ((rho RU1 - rho RU3) * 0 + (rho RU2 - rho RU4) * 1)
           ((rho RU1 - rho RU3) * (-1) + (rho RU2 - rho RU4) * 0)
           ((rho RU1 - rho RU3) * 0 + (rho RU2 - rho RU4) * (-1))).
Proof.
  intro rho.
  unfold veq, B3b_vec4, B3b, seam_X, seam_Z; simpl.
  repeat split; ring.
Qed.

Theorem g1_g2_independent :
  forall a b : Q,
    veq (mkvec4 (a * 1 + b * 0) (a * 0 + b * 1) (a * (-1) + b * 0) (a * 0 + b * (-1)))
        (mkvec4 0 0 0 0) ->
    a == 0 /\ b == 0.
Proof.
  intros a b [H0 [H1 [_ _]]]; simpl in H0, H1.
  split.
  - rewrite Qmult_1_r, Qmult_0_r, Qplus_0_r in H0. exact H0.
  - rewrite Qmult_0_r, Qmult_1_r, Qplus_0_l in H1. exact H1.
Qed.

(* ------------------------------------------------------------------ *)
(* g1 is repairable (lies in im(delta0)); g2 is not. Together, the      *)
(* Rocq form of "genuinely partial, nontrivial quotient": the image     *)
(* contains a repairable direction and a non-repairable direction,      *)
(* neither everything nor nothing.                                      *)
(* ------------------------------------------------------------------ *)

Theorem g1_in_image_delta0 :
  exists b : vec4, veq (delta0 b) g1.
Proof.
  exists (mkvec4 0 1 1 0).
  unfold veq, delta0, g1; simpl; repeat split; ring.
Qed.

Theorem g2_not_in_image_delta0 :
  ~ (exists b : vec4, veq (delta0 b) g2).
Proof.
  intros [b Hveq].
  unfold veq, delta0, g2 in Hveq; simpl in Hveq.
  destruct Hveq as [H0 [H1 [H2 H3]]].
  assert (Hsum : v3 b - v0 b == (v1 b - v0 b) + (v2 b - v1 b) + (v3 b - v2 b)) by ring.
  rewrite H0, H1, H2 in Hsum.
  rewrite H3 in Hsum.
  compute in Hsum.
  discriminate Hsum.
Qed.

(* unit_rho RU1 realises g1 exactly (a=1,b=0); unit_rho RU2 realises g2
   exactly (a=0,b=1) -- checked directly, not assumed from the span
   theorem above. *)
Theorem B3b_unit_RU1_is_g1 : veq (B3b_vec4 (unit_rho RU1)) g1.
Proof.
  unfold veq, B3b_vec4, B3b, seam_X, seam_Z, unit_rho, g1; simpl.
  repeat split; ring.
Qed.

Theorem B3b_unit_RU2_is_g2 : veq (B3b_vec4 (unit_rho RU2)) g2.
Proof.
  unfold veq, B3b_vec4, B3b, seam_X, seam_Z, unit_rho, g2; simpl.
  repeat split; ring.
Qed.

(* ------------------------------------------------------------------ *)
(* The headline theorem: under a RepeatedTripleSupport witness (Part 1),*)
(* Candidate 3b's induced map has genuinely shared columns and realises *)
(* a residue that is NOT repairable -- together with g1_in_image_delta0 *)
(* above (a realised residue that IS repairable), this is the Rocq form *)
(* of "genuinely partial, nontrivial realisable obstruction quotient",  *)
(* neither full-rank surjectivity (everything obstructed and repairable *)
(* alike, no structure) nor coboundary collapse (nothing obstructed).   *)
(* ------------------------------------------------------------------ *)

Theorem repeated_triple_support_realises_nonrepairable_residue :
  forall (Point : Type) (U1 U2 U3 U4 : Point -> Prop),
    RepeatedTripleSupport Point U1 U2 U3 U4 ->
    exists rho : RegionIndex -> Q,
      (exists e1 e2 : Seam,
         e1 <> e2 /\ ~ (B3b rho e1 == 0) /\ ~ (B3b rho e2 == 0)) /\
      ~ (exists b : vec4, veq (delta0 b) (B3b_vec4 rho)).
Proof.
  intros Point U1 U2 U3 U4 _.
  exists (unit_rho RU2).
  split.
  - exact (B3b_unit_columns_genuinely_shared RU2).
  - intros [b Hb].
    apply g2_not_in_image_delta0.
    exists b.
    intros; unfold veq in *.
    destruct Hb as [Hb0 [Hb1 [Hb2 Hb3]]].
    pose proof B3b_unit_RU2_is_g2 as [Hg0 [Hg1 [Hg2 Hg3]]].
    unfold veq; repeat split.
    + rewrite Hb0; exact Hg0.
    + rewrite Hb1; exact Hg1.
    + rewrite Hb2; exact Hg2.
    + rewrite Hb3; exact Hg3.
Qed.

Theorem repeated_triple_support_also_realises_a_repairable_residue :
  forall (Point : Type) (U1 U2 U3 U4 : Point -> Prop),
    RepeatedTripleSupport Point U1 U2 U3 U4 ->
    exists rho : RegionIndex -> Q,
      (exists e1 e2 : Seam,
         e1 <> e2 /\ ~ (B3b rho e1 == 0) /\ ~ (B3b rho e2 == 0)) /\
      (exists b : vec4, veq (delta0 b) (B3b_vec4 rho)).
Proof.
  intros Point U1 U2 U3 U4 _.
  exists (unit_rho RU1).
  split.
  - exact (B3b_unit_columns_genuinely_shared RU1).
  - destruct g1_in_image_delta0 as [b Hb].
    exists b.
    pose proof B3b_unit_RU1_is_g1 as [Hg0 [Hg1 [Hg2 Hg3]]].
    destruct Hb as [Hb0 [Hb1 [Hb2 Hb3]]].
    unfold veq; repeat split.
    + rewrite Hg0; exact Hb0.
    + rewrite Hg1; exact Hb1.
    + rewrite Hg2; exact Hb2.
    + rewrite Hg3; exact Hb3.
Qed.
