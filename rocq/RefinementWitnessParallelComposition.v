(*
   RefinementWitnessParallelComposition.v

   Phase 4b's Rocq step. refinement_witness_parallel_disjoint_probe.py
   probed disjoint parallel (direct-sum) composition of two refinement
   witnesses over 32 cases and found a split: (N0) and (E0) always
   match AND(branch A, branch B); (A4) does not (16/32 mismatches, via
   sign-cancellation of the combined pairing). See docs/design/
   REFINEMENT_WITNESS_COMPOSITION_STATUS.md, Phase 4b, and veribound-
   fce's docs/design/PARALLEL_WITNESS_COMPOSITION_SPEC.md for the full
   account, including why a plain A4_parallel_disjoint statement is
   FALSE, not merely unproved.

   This file proves exactly the two conditions the probe supports:
   N0_parallel_disjoint and E0_parallel_disjoint. It deliberately does
   NOT attempt A4_parallel_disjoint -- that statement is false as a bare
   claim (demonstrated computationally by the probe), and any true
   replacement needs an additional hypothesis (non-cancellation of the
   summed pairing, or a branchwise reformulation) that has not yet been
   designed, let alone proved. Do not add an A4 theorem to this file
   without first settling which of those two replacement statements is
   intended.

   UNLIKE the sequential-composition files (RefinementWitnessComposition
   .v, RefinementWitnessVerdictComposition.v, RefinementWitnessSequential
   Composition.v), which build composite maps by literal function
   COMPOSITION, disjoint parallel composition is built from a DIRECT SUM:
   the combined vertex/edge cochain space is the PRODUCT of the two
   branches' own cochain spaces (matching the Python probe's disjoint
   union of vertex/edge name universes: a function on a disjoint union
   of index sets is exactly a pair of functions, one per branch), and the
   combined coboundary/pullback maps act on each component independently
   ("block-diagonally"). Nothing here is derived from or dependent on the
   sequential-composition proofs; the constructions do not overlap.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import Coq.Lists.List.
Import ListNotations.

(* ------------------------------------------------------------------ *)
(* Part 1: (N0) composes under disjoint parallel composition.          *)
(* Pure product-type case analysis, no vector-space structure needed.  *)
(* ------------------------------------------------------------------ *)

Section N0Parallel.

  (* Branch A's coarse/refined vertex and edge types, and branch B's --
     kept fully independent (no shared type, matching the probe's
     disjoint renamed vertex/edge universes). *)
  Variables CA0 CA1 QA0 QA1 : Type.
  Variables CB0 CB1 QB0 QB1 : Type.

  Variable delta_CA : CA0 -> CA1.
  Variable delta_QA : QA0 -> QA1.
  Variable rho0_A : CA0 -> QA0.
  Variable rho1_A : CA1 -> QA1.

  Variable delta_CB : CB0 -> CB1.
  Variable delta_QB : QB0 -> QB1.
  Variable rho0_B : CB0 -> QB0.
  Variable rho1_B : CB1 -> QB1.

  Hypothesis N0_A : forall c : CA0, delta_QA (rho0_A c) = rho1_A (delta_CA c).
  Hypothesis N0_B : forall c : CB0, delta_QB (rho0_B c) = rho1_B (delta_CB c).

  (* The direct-sum (block-diagonal) combined maps: a function on a
     disjoint union of index sets is a pair of functions, one per
     branch -- so the combined coboundary/pullback act componentwise on
     pairs, exactly as the probe's block-diagonal matrices do. *)
  Definition delta_C_parallel (c : CA0 * CB0) : CA1 * CB1 :=
    (delta_CA (fst c), delta_CB (snd c)).
  Definition delta_Q_parallel (q : QA0 * QB0) : QA1 * QB1 :=
    (delta_QA (fst q), delta_QB (snd q)).
  Definition rho0_parallel (c : CA0 * CB0) : QA0 * QB0 :=
    (rho0_A (fst c), rho0_B (snd c)).
  Definition rho1_parallel (c : CA1 * CB1) : QA1 * QB1 :=
    (rho1_A (fst c), rho1_B (snd c)).

  Theorem N0_parallel_disjoint :
    forall c : CA0 * CB0,
      delta_Q_parallel (rho0_parallel c) = rho1_parallel (delta_C_parallel c).
  Proof.
    intros [ca cb].
    unfold delta_Q_parallel, rho0_parallel, rho1_parallel, delta_C_parallel.
    simpl.
    rewrite (N0_A ca), (N0_B cb).
    reflexivity.
  Qed.

End N0Parallel.

(* ------------------------------------------------------------------ *)
(* Part 2: VSpace direct-sum (product) infrastructure, reusing the     *)
(* VSpace/InSpan/IsLinear machinery from RefinementWitnessVerdict       *)
(* Composition.v (redeclared here so this file stands alone -- it does *)
(* not `Require` that file, matching this project's existing pattern   *)
(* of small self-contained Rocq files rather than a shared import       *)
(* graph).                                                              *)
(* ------------------------------------------------------------------ *)

Record VSpace := mkVSpace {
  carrier : Type;
  vzero : carrier;
  vadd : carrier -> carrier -> carrier;
  vscale : Q -> carrier -> carrier;
  vadd_assoc : forall a b c, vadd (vadd a b) c = vadd a (vadd b c);
  vadd_zero_l : forall a, vadd vzero a = a;
  vscale_distrib_vadd : forall c a b, vscale c (vadd a b) = vadd (vscale c a) (vscale c b);
  vscale_compose : forall c d a, vscale c (vscale d a) = vscale (c * d) a;
  vscale_vzero : forall c, vscale c vzero = vzero;
}.

Fixpoint LinComb (S : VSpace) (terms : list (Q * carrier S)) : carrier S :=
  match terms with
  | nil => vzero S
  | (c, v) :: rest => vadd S (vscale S c v) (LinComb S rest)
  end.

Definition InSpan (S : VSpace) (basis : list (carrier S)) (v : carrier S) : Prop :=
  exists terms : list (Q * carrier S),
    (forall p, In p terms -> In (snd p) basis) /\ v = LinComb S terms.

Definition IsLinear (S1 S2 : VSpace) (f : carrier S1 -> carrier S2) : Prop :=
  f (vzero S1) = vzero S2 /\
  (forall a b, f (vadd S1 a b) = vadd S2 (f a) (f b)) /\
  (forall c a, f (vscale S1 c a) = vscale S2 c (f a)).

Lemma linear_LinComb :
  forall (S1 S2 : VSpace) (f : carrier S1 -> carrier S2),
    IsLinear S1 S2 f ->
    forall terms : list (Q * carrier S1),
      f (LinComb S1 terms) = LinComb S2 (map (fun p => (fst p, f (snd p))) terms).
Proof.
  intros S1 S2 f [Hz [Ha Hs]] terms.
  induction terms as [| [c v] rest IH]; simpl.
  - exact Hz.
  - rewrite Ha, Hs, IH. reflexivity.
Qed.

Theorem linear_maps_preserve_span :
  forall (S1 S2 : VSpace) (f : carrier S1 -> carrier S2),
    IsLinear S1 S2 f ->
    forall (basis : list (carrier S1)) (v : carrier S1),
      InSpan S1 basis v -> InSpan S2 (map f basis) (f v).
Proof.
  intros S1 S2 f HLin basis v [terms [Hin Heq]].
  exists (map (fun p => (fst p, f (snd p))) terms).
  split.
  - intros p Hp.
    apply in_map_iff in Hp.
    destruct Hp as [[c u] [Heqp Hu]].
    simpl in Heqp. subst p. simpl.
    apply in_map. exact (Hin (c, u) Hu).
  - rewrite Heq. apply linear_LinComb. exact HLin.
Qed.

(* Monotonicity of InSpan under basis inclusion -- not needed by the
   sequential-composition file (which only ever transports through a
   linear map), but needed here: the parallel construction repeatedly
   needs "a span computed over one branch's embedded basis is contained
   in the span over the full combined basis," which is basis inclusion,
   not a linear-map transport. *)
Theorem InSpan_incl :
  forall (S : VSpace) (basis1 basis2 : list (carrier S)),
    incl basis1 basis2 ->
    forall v, InSpan S basis1 v -> InSpan S basis2 v.
Proof.
  intros S basis1 basis2 Hincl v [terms [Hin Heq]].
  exists terms.
  split.
  - intros p Hp. apply Hincl. exact (Hin p Hp).
  - exact Heq.
Qed.

(* The direct-sum (product) VSpace: carrier is a pair, every operation
   componentwise. This is the vector-space-level shadow of the probe's
   disjoint union of vertex/edge index sets -- a cochain on a disjoint
   union of index sets is exactly a pair of cochains, one per branch. *)
Definition VSpace_prod (S1 S2 : VSpace) : VSpace :=
  mkVSpace
    (carrier S1 * carrier S2)
    (vzero S1, vzero S2)
    (fun a b => (vadd S1 (fst a) (fst b), vadd S2 (snd a) (snd b)))
    (fun c a => (vscale S1 c (fst a), vscale S2 c (snd a)))
    (fun a b c => f_equal2 pair (vadd_assoc S1 _ _ _) (vadd_assoc S2 _ _ _))
    (fun a => match a with (a1, a2) =>
        f_equal2 pair (vadd_zero_l S1 a1) (vadd_zero_l S2 a2) end)
    (fun c a b => f_equal2 pair (vscale_distrib_vadd S1 c (fst a) (fst b))
                                 (vscale_distrib_vadd S2 c (snd a) (snd b)))
    (fun c d a => f_equal2 pair (vscale_compose S1 c d (fst a))
                                 (vscale_compose S2 c d (snd a)))
    (fun c => f_equal2 pair (vscale_vzero S1 c) (vscale_vzero S2 c)).

Definition embed_left (S1 S2 : VSpace) (v : carrier S1) : carrier (VSpace_prod S1 S2) :=
  (v, vzero S2).
Definition embed_right (S1 S2 : VSpace) (v : carrier S2) : carrier (VSpace_prod S1 S2) :=
  (vzero S1, v).

Lemma embed_left_linear :
  forall (S1 S2 : VSpace), IsLinear S1 (VSpace_prod S1 S2) (embed_left S1 S2).
Proof.
  intros S1 S2.
  unfold IsLinear, embed_left. simpl.
  repeat split.
  - intros a b. f_equal. symmetry. apply (vadd_zero_l S2).
  - intros c a. f_equal. symmetry. apply (vscale_vzero S2).
Qed.

Lemma embed_right_linear :
  forall (S1 S2 : VSpace), IsLinear S2 (VSpace_prod S1 S2) (embed_right S1 S2).
Proof.
  intros S1 S2.
  unfold IsLinear, embed_right. simpl.
  repeat split.
  - intros a b. f_equal. symmetry. apply (vadd_zero_l S1).
  - intros c a. f_equal. symmetry. apply (vscale_vzero S1).
Qed.

(* ------------------------------------------------------------------ *)
(* Part 3: (E0) composes under disjoint parallel composition.          *)
(* ------------------------------------------------------------------ *)

Section E0Parallel.

  Variables SPA SQA SPB SQB : VSpace.

  (* Branch A's and branch B's own coverage (pushforward) maps, coarse
     ("P") level covered by refined ("Q") level, exactly as in the
     sequential file's E0Composes section. *)
  Variable push_A : carrier SQA -> carrier SPA.
  Variable push_B : carrier SQB -> carrier SPB.
  Hypothesis push_A_linear : IsLinear SQA SPA push_A.
  Hypothesis push_B_linear : IsLinear SQB SPB push_B.

  Variable Z1_PA : list (carrier SPA).
  Variable Z1_QA : list (carrier SQA).
  Variable Z1_PB : list (carrier SPB).
  Variable Z1_QB : list (carrier SQB).

  Hypothesis E0_A : forall z, In z Z1_PA -> InSpan SPA (map push_A Z1_QA) z.
  Hypothesis E0_B : forall z, In z Z1_PB -> InSpan SPB (map push_B Z1_QB) z.

  Definition SP := VSpace_prod SPA SPB.
  Definition SQ := VSpace_prod SQA SQB.

  (* The combined (block-diagonal) coverage map. *)
  Definition push_parallel (q : carrier SQ) : carrier SP :=
    (push_A (fst q), push_B (snd q)).

  Lemma push_parallel_linear : IsLinear SQ SP push_parallel.
  Proof.
    unfold IsLinear, push_parallel, SQ, SP. simpl.
    destruct push_A_linear as [HzA [HaA HsA]].
    destruct push_B_linear as [HzB [HaB HsB]].
    repeat split.
    - f_equal; assumption.
    - intros [a1 a2] [b1 b2]. simpl. f_equal; auto.
    - intros c [a1 a2]. simpl. f_equal; auto.
  Qed.

  (* The combined cycle-space spanning sets: branch A's own basis
     embedded on the left (paired with zero on the right), branch B's
     embedded on the right -- the direct sum of the two cycle spaces,
     matching what the kernel of a block-diagonal coboundary map
     actually looks like (ker(diag(D_A,D_B)) = ker(D_A) (+) ker(D_B)). *)
  Definition Z1_P_parallel : list (carrier SP) :=
    map (embed_left SPA SPB) Z1_PA ++ map (embed_right SPA SPB) Z1_PB.
  Definition Z1_Q_parallel : list (carrier SQ) :=
    map (embed_left SQA SQB) Z1_QA ++ map (embed_right SQA SQB) Z1_QB.

  (* The combined pushforward map agrees with "embed, then push
     branchwise" on each branch -- the block-diagonal structure made
     explicit at the level of the embedding. *)
  Lemma push_parallel_left :
    forall q, push_parallel (embed_left SQA SQB q) = embed_left SPA SPB (push_A q).
  Proof.
    intro q. unfold push_parallel, embed_left. simpl.
    f_equal. destruct push_B_linear as [HzB _]. exact HzB.
  Qed.

  Lemma push_parallel_right :
    forall q, push_parallel (embed_right SQA SQB q) = embed_right SPA SPB (push_B q).
  Proof.
    intro q. unfold push_parallel, embed_right. simpl.
    f_equal. destruct push_A_linear as [HzA _]. exact HzA.
  Qed.

  (* Membership-level restatement of the "block-diagonal" fact, avoiding
     any list-equality rewriting: every pushforward of a branch-A basis
     element, embedded on the left, is itself the combined pushforward
     of the corresponding embedded Q-level element -- which lies in the
     combined Q-level basis by construction (the left half of the
     app). Symmetric for branch B. *)
  Lemma pushed_left_incl :
    incl (map (embed_left SPA SPB) (map push_A Z1_QA)) (map push_parallel Z1_Q_parallel).
  Proof.
    intros y Hy.
    apply in_map_iff in Hy.
    destruct Hy as [pa [Heqy Hpa]].
    apply in_map_iff in Hpa.
    destruct Hpa as [q [Heqpa Hq]].
    subst pa. subst y.
    apply in_map_iff.
    exists (embed_left SQA SQB q).
    split.
    - apply push_parallel_left.
    - unfold Z1_Q_parallel. apply in_or_app. left. apply in_map. exact Hq.
  Qed.

  Lemma pushed_right_incl :
    incl (map (embed_right SPA SPB) (map push_B Z1_QB)) (map push_parallel Z1_Q_parallel).
  Proof.
    intros y Hy.
    apply in_map_iff in Hy.
    destruct Hy as [pb [Heqy Hpb]].
    apply in_map_iff in Hpb.
    destruct Hpb as [q [Heqpb Hq]].
    subst pb. subst y.
    apply in_map_iff.
    exists (embed_right SQA SQB q).
    split.
    - apply push_parallel_right.
    - unfold Z1_Q_parallel. apply in_or_app. right. apply in_map. exact Hq.
  Qed.

  Theorem E0_parallel_disjoint :
    forall z, In z Z1_P_parallel -> InSpan SP (map push_parallel Z1_Q_parallel) z.
  Proof.
    intros z Hz.
    unfold Z1_P_parallel in Hz.
    apply in_app_or in Hz.
    destruct Hz as [Hz | Hz].
    - (* z came from branch A *)
      apply in_map_iff in Hz.
      destruct Hz as [za [Heqz Hza]].
      subst z.
      pose proof (linear_maps_preserve_span SPA SP (embed_left SPA SPB)
                    (embed_left_linear SPA SPB) (map push_A Z1_QA) za
                    (E0_A za Hza)) as Hpushed.
      exact (InSpan_incl SP _ _ pushed_left_incl _ Hpushed).
    - (* z came from branch B, symmetric argument *)
      apply in_map_iff in Hz.
      destruct Hz as [zb [Heqz Hzb]].
      subst z.
      pose proof (linear_maps_preserve_span SPB SP (embed_right SPA SPB)
                    (embed_right_linear SPA SPB) (map push_B Z1_QB) zb
                    (E0_B zb Hzb)) as Hpushed.
      exact (InSpan_incl SP _ _ pushed_right_incl _ Hpushed).
  Qed.

End E0Parallel.
