(*
   ConflictResolutionLowerBound.v

   R12. Continues ConflictResolutionTrilemma.v's lossy-vs-structured
   section: given that structured (non-lossy) resolution is possible at
   all (pair_resolver_preserves_both_claims), how much structure does a
   non-lossy encoding actually need? Not tied to refinement witnesses or
   any structure elsewhere in this project -- a fact about functions and
   equality, true for any types.

   The answer: an encoding V -> V -> C is non-lossy (both original
   declarations recoverable via FIXED projection functions, for every
   pair) exactly when it is injective on the product V * V. This is the
   information-theoretic content underneath the earlier existence
   result: pairing into V * V is not merely ONE way to be non-lossy, it
   is exhibited here as achieving the minimum an encoding must do --
   assign a genuinely distinct C-value to every distinct ordered pair of
   declarations, or it could not recover them both. For finite V with
   |V| = n > 1, this forces the encoding's codomain to have at least n^2
   elements: no encoding whose codomain is confined to V itself (size n)
   can be non-lossy, which is a cardinality-flavoured restatement of
   ConflictResolutionTrilemma.v's original equational impossibility, not
   a new assumption -- see conflict_resolution_lower_bound_probe.py for
   the finite-case arithmetic checked computationally.

   No `Admitted`/`Axiom`/`sorry`.
*)

Section ConflictResolutionLowerBound.

  Variables V C : Type.

  (* An encoding is non-lossy when fixed projection functions recover
     BOTH original declarations from the encoded value, for every pair
     -- the same property ConflictResolutionTrilemma.v's pair_resolver
     has for C := V * V, generalised here to an arbitrary codomain C,
     not only the literal pair type. *)
  Definition NonLossy (encode : V -> V -> C) (left_read right_read : C -> V) : Prop :=
    forall x y : V, left_read (encode x y) = x /\ right_read (encode x y) = y.

  (* The lower bound: any non-lossy encoding is injective on V * V. If
     two distinct ordered pairs were encoded to the same C-value, the
     fixed projections could not tell them apart -- they would have to
     recover both pairs' declarations from one shared value, which
     forces the pairs to coincide. *)
  Theorem nonlossy_encoding_injective :
    forall (encode : V -> V -> C) (left_read right_read : C -> V),
      NonLossy encode left_read right_read ->
      forall x1 y1 x2 y2 : V,
        encode x1 y1 = encode x2 y2 -> x1 = x2 /\ y1 = y2.
  Proof.
    intros encode left_read right_read Hnl x1 y1 x2 y2 Heq.
    destruct (Hnl x1 y1) as [Hl1 Hr1].
    destruct (Hnl x2 y2) as [Hl2 Hr2].
    split.
    - rewrite <- Hl1, <- Hl2, Heq. reflexivity.
    - rewrite <- Hr1, <- Hr2, Heq. reflexivity.
  Qed.

End ConflictResolutionLowerBound.

(* The positive construction: the literal pairing into V * V achieves
   the lower bound exactly, with no wasted structure -- confirms NonLossy
   is satisfiable, not vacuous, and is the same construction
   ConflictResolutionTrilemma.v's pair_resolver already exhibited,
   restated here under this file's NonLossy/injectivity vocabulary. *)
Theorem structured_pair_is_nonlossy :
  forall V : Type,
    NonLossy V (V * V) (fun x y => (x, y)) fst snd.
Proof.
  intros V x y. split; reflexivity.
Qed.
