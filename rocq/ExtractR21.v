(* ExtractR21.v

   Rocq extraction entry point for R21's proved computational function.
   Extracts exactly `compute_repair_or_separator`
   (rocq/ExactRationalRepairOrSeparator.v), the function
   `compute_repair_or_separator_correct` proves sound against the
   ORIGINAL D, r (not merely the row-reduced matrix elimination operates
   on):

     compute_repair_or_separator_correct : forall m n D r,
       MatrixShape m n D -> VectorShape m r ->
       match compute_repair_or_separator m n D r with
       | RawRepair b => VectorShape n b /\ VecEq (mat_vec D b) r
       | RawSeparator y => VectorShape m y /\
           VecEq (mat_vec (transpose D n) y) (repeat 0 n) /\ dot y r == 1
       end.

   Deliberately does NOT extract `certified_repair_or_separator`,
   `decide_repair_or_separator`, `RepairOrSeparator`, `RatVec`/
   `RatMatrix`, or any theorem/proof term -- those are proof-carrying
   wrappers and propositions, not the computational content itself. The
   bounded extraction spike that preceded this file confirmed, by
   grepping the actual extracted output, that `compute_repair_or_
   separator` alone -- with no proof-record wrapper -- extracts to plain,
   directly computable OCaml with no axioms, no `failwith` placeholders,
   and no unsafe casts.

   Uses only Coq's own, official extraction realisation files -- no
   project-defined `Extract Constant`/`Extract Inductive` directives of
   any kind:
     - ExtrOcamlBasic: standard bool/option/list/etc. mappings.
     - ExtrOcamlZBigInt: maps positive/Z/N to Zarith's
       `Big_int_Z.big_int` -- confirmed by hand, in this repository's own
       environment, to be the SAME type as Zarith's own `Z.t` (Zarith
       ships `Big_int_Z` as a same-type compatibility shim over its real
       GMP-backed `Z.t`), so this is a same-representation mapping, not a
       wrapper needing runtime conversion.
     - ExtrOcamlNatBigInt: maps `nat` to the same representation.
   Every one of these three files -- and every individual `Extract
   Constant`/`Extract Inductive` line inside them -- is part of the
   extraction trusted computing base. See
   docs/design/R21_EXTRACTION_TCB.md for the itemised list and exactly
   what trusting each one means. `Q` itself (Coq's `Qmake { Qnum : Z ;
   Qden : positive }`) has no official realisation and is left to extract
   as its own natural (unreduced) two-field record -- the one
   representation adapter this pipeline needs, implemented in
   `ocaml/r21_extracted_solve.ml`, not here.

   Output is NOT committed to this repository -- `make extract-r21`
   regenerates `ocaml/r21_extracted.ml`/`.mli` fresh from this file and a
   freshly recompiled `ExactRationalRepairOrSeparator.vo` every time, the
   same way `.vo`/`.cmi`/`.cmx` are never committed. This is not part of
   the `ROCQ_MODULES` proof chain (`check-rocq`/`check-rocq-trust`): it is
   a build/tooling step producing a generated OCaml source file, not a
   mathematical proof module in the R1-R21 ladder.
*)

Require Import ExactRationalRepairOrSeparator.
Require Import Coq.extraction.ExtrOcamlBasic.
Require Import Coq.extraction.ExtrOcamlZBigInt.
Require Import Coq.extraction.ExtrOcamlNatBigInt.

Extraction Language OCaml.

Extraction "../ocaml/r21_extracted.ml" compute_repair_or_separator.
