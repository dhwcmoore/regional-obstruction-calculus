(*
   r21_extracted_solve.ml

   Thin adapter around the Rocq-extracted `compute_repair_or_separator`
   (`ocaml/r21_extracted.ml`, regenerated fresh by `make extract-r21` from
   `rocq/ExtractR21.v` -- never committed, see that file's own header).
   This is the "roc-solve-extracted" CLI: parses a `roc-input/v1` file,
   converts to the extracted representation, runs the proved Rocq
   computation, converts the result back, and emits a `repair-or-
   separator/v1` certificate -- exactly the shape `r21_certificate_
   emitter.py` (the hand-written Python generator) already emits.

   THIS ADAPTER IS NOT PART OF THE TRUSTED COMPUTING BASE FOR ACCEPTANCE.
   Every certificate it emits is still gated by the two existing
   independent checkers (`r21_certificate_checker.py`, `roc-verify-
   ocaml`/`r21_verifier.ml`) -- this file does not change what "ACCEPT"
   means, only where the witness came from. See docs/design/
   R21_EXTRACTION_TCB.md for exactly what trusting this adapter's output
   would require, as distinct from trusting either checker's ACCEPT.

   The one representation adapter this pipeline needs, exactly as
   predicted before extraction was attempted: Coq's `Q := Qmake { Qnum :
   Z ; Qden : positive }` has no official extraction realisation and
   extracts as its own natural, UNREDUCED two-field record (`R21_
   extracted.q`), backed by `Big_int_Z.big_int` (confirmed, by direct
   type-check, to be the same type as `Zarith.Z.t`). `q_of_zarith`/
   `zarith_of_q` below convert between that and `Zarith.Q.t` (which
   always keeps a value reduced to lowest terms with a positive
   denominator) via a single call to `Q.make`/`Q.num`/`Q.den` each way --
   not a rewrite of any arithmetic, just a normalisation step. `nat`
   (dimensions) similarly extracts to `Big_int_Z.big_int`; converted
   via `Big_int_Z.big_int_of_int`/`int_of_big_int` since this pipeline's
   own `MAX_DIMENSION` (10,000) is far inside native `int` range.

   Build: requires the opam packages `zarith`, `yojson`, `sha`, plus a
   freshly extracted `ocaml/r21_extracted.ml`/`.mli` (`make extract-r21`
   first). Compiled via:
     ocamlfind ocamlopt -package zarith,yojson,sha -linkpkg \
       r21_extracted.mli r21_extracted.ml r21_format.ml \
       r21_extracted_solve.ml -o roc-solve-extracted

   USAGE:
     roc-solve-extracted input.json --certificate output.json
*)

(* r21_extracted.ml defines its own local `module Z` (a small subset of
   operations backed by Big_int_Z, per ExtrOcamlZBigInt) that would shadow
   Zarith's real Z module if this file opened R21_extracted -- so this
   file deliberately does NOT open it, and instead qualifies every
   reference (R21_extracted.compute_repair_or_separator, R21_extracted.q,
   R21_extracted.RawRepair/RawSeparator) explicitly. *)
open R21_format

let nat_of_int (n : int) : Big_int_Z.big_int = Big_int_Z.big_int_of_int n

let q_of_zarith (x : Q.t) : R21_extracted.q = { R21_extracted.qnum = Q.num x; qden = Q.den x }

let zarith_of_q (x : R21_extracted.q) : Q.t = Q.make x.R21_extracted.qnum x.R21_extracted.qden

let extracted_matrix_of_zarith (d : Q.t array array) : R21_extracted.q list list =
  Array.to_list (Array.map (fun row -> Array.to_list (Array.map q_of_zarith row)) d)

let extracted_vector_of_zarith (v : Q.t array) : R21_extracted.q list =
  Array.to_list (Array.map q_of_zarith v)

let zarith_vector_of_extracted (v : R21_extracted.q list) : Q.t array =
  Array.of_list (List.map zarith_of_q v)

let build_certificate (d : Q.t array array) (r : Q.t array) : string * string =
  let m = Array.length d in
  let n = if m = 0 then 0 else Array.length d.(0) in
  let result =
    R21_extracted.compute_repair_or_separator (nat_of_int m) (nat_of_int n)
      (extracted_matrix_of_zarith d) (extracted_vector_of_zarith r)
  in
  let digest = canonical_input_digest d r in
  let witness_json label vec =
    let entries = Array.to_list (Array.map (fun x -> "\"" ^ q_to_canonical_string x ^ "\"") (zarith_vector_of_extracted vec)) in
    Printf.sprintf
      {|{"schema": "%s", "input_digest": "%s", "result": "%s", "%s": [%s]}|}
      certificate_schema digest label label (String.concat "," entries)
  in
  match result with
  | R21_extracted.RawRepair b -> (witness_json result_repair b, result_repair)
  | R21_extracted.RawSeparator y -> (witness_json result_separator y, result_separator)

let write_certificate (cert : string) (path : string) : unit =
  let oc = open_out path in
  output_string oc cert;
  close_out oc

let () =
  match Array.to_list Sys.argv with
  | [ _; input_path; "--certificate"; cert_path ] -> (
    try
      let d, r = read_input input_path in
      let cert, verdict = build_certificate d r in
      write_certificate cert cert_path;
      Printf.printf "%s: wrote %s\n" (String.uppercase_ascii verdict) cert_path;
      exit 0
    with
    | Reject msg ->
      Printf.printf "REJECT: %s\n" msg;
      exit 1
    | e ->
      Printf.printf "REJECT: %s\n" (Printexc.to_string e);
      exit 1)
  | _ ->
    Printf.eprintf "usage: roc-solve-extracted <input.json> --certificate <output.json>\n";
    exit 2
