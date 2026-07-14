(*
   r21_verifier.ml

   A second, independently written checker for `repair-or-separator/v1`
   certificates -- the OCaml counterpart to `r21_certificate_checker.py`
   for R21 (`rocq/ExactRationalRepairOrSeparator.v`). This is a VERIFIER,
   not a generator: it does not attempt to decide `Db = r` by running
   elimination, and it is not a Rocq extraction of anything. Its only job
   is to recompute the two certificate equations directly and reject
   anything that does not check out.

   INDEPENDENCE BOUNDARY. This file shares with the Python side only the
   published specification: the `repair-or-separator/v1` and
   `roc-input/v1` schemas, the canonicalisation rule for `input_digest`,
   the resource limits, and the test fixtures both are checked against
   (all in `r21_format.ml` -- see that module's own header for why
   sharing schema/canonicalisation code, but no solver logic, does not
   weaken independence). It contains no translated or generated copy of
   `r21_certificate_checker.py` or `r21_certificate_format.py`: the
   matrix/vector arithmetic below (`mat_vec`/`transpose`/`dot`/
   `is_zero_vec`) is its own implementation, over `Zarith.Q` rather than
   Python's `fractions.Fraction`.

   `r21_format.ml` is also used by `r21_extracted_solve.ml` (the thin
   adapter around the Rocq-extracted generator), but this file is NOT:
   this checker imports neither the hand-written generator
   (`r21_repair_or_separator.py`/its own would-be OCaml equivalent) nor
   the extracted one, and its soundness does not depend on either being
   correct.

   Build: requires the opam packages `zarith`, `yojson`, `sha` (see
   REPRODUCIBILITY.md for exact setup). Compiled via:
     ocamlfind ocamlopt -package zarith,yojson,sha -linkpkg \
       r21_format.ml r21_verifier.ml -o roc-verify-ocaml

   USAGE:
     roc-verify-ocaml <input.json> <certificate.json>   -- verify (ACCEPT/REJECT, exit 0/1)
     roc-verify-ocaml --digest <input.json>              -- print only "sha256:<hex>" (exit 0/1)

   Fail-closed: every parse, validation, and arithmetic failure raises
   `R21_format.Reject`, caught once at the top of `verify` (or the CLI's
   `--digest` branch) and turned into a rejection -- never a silent
   accept, and never an uncaught exception that could look like "no
   verdict" to a caller instead of "REJECT". Unlike `r21_certificate_
   checker.py`, which can record several independent reasons for one
   rejection, this file stops at the first failure and reports just that
   one reason -- a stylistic difference with no effect on the
   accept/reject verdict itself, which is the only thing the
   cross-language agreement tests require to match.
*)

open R21_format

(* ------------------------------------------------------------------ *)
(* Exact-rational matrix/vector arithmetic -- independent implementations
   of the same four operations rational_linear_algebra.py provides,
   over Zarith.Q instead of Fraction. *)
(* ------------------------------------------------------------------ *)

let mat_vec (d : Q.t array array) (v : Q.t array) : Q.t array =
  Array.map
    (fun row ->
      let acc = ref Q.zero in
      Array.iteri (fun j x -> acc := Q.add !acc (Q.mul x v.(j))) row;
      !acc)
    d

let transpose (d : Q.t array array) (ncols : int) : Q.t array array =
  Array.init ncols (fun j -> Array.map (fun row -> row.(j)) d)

let dot (u : Q.t array) (v : Q.t array) : Q.t =
  let acc = ref Q.zero in
  Array.iteri (fun i x -> acc := Q.add !acc (Q.mul x v.(i))) u;
  !acc

let is_zero_vec (v : Q.t array) : bool = Array.for_all (fun x -> Q.equal x Q.zero) v

let vec_equal (u : Q.t array) (v : Q.t array) : bool =
  Array.length u = Array.length v && Array.for_all2 Q.equal u v

(* ------------------------------------------------------------------ *)
(* Verifying repair-or-separator/v1: closed schema, digest binding, then
   exactly the two certificate equations R21 proves the alternative for. *)
(* ------------------------------------------------------------------ *)

type check_result = { accepted : bool; reasons : string list }

let verify (d : Q.t array array) (r : Q.t array) (cert : Yojson.Safe.t) : check_result =
  try
    let kvs = get_assoc "certificate" cert in
    let schema = get_string "certificate schema" (assoc_required "schema" kvs "certificate") in
    if schema <> certificate_schema then
      raise (Reject (Printf.sprintf "unrecognized certificate schema: %S" schema));
    let expected_digest = canonical_input_digest d r in
    let recorded_digest = get_string "input_digest" (assoc_required "input_digest" kvs "certificate") in
    if recorded_digest <> expected_digest then
      raise
        (Reject
           (Printf.sprintf
              "input_digest mismatch: certificate is bound to %S, but the supplied (D, r) digests to %S -- \
               this certificate does not certify this problem"
              recorded_digest expected_digest));
    let m = Array.length d in
    let n = if m = 0 then 0 else Array.length d.(0) in
    let verdict = get_string "result" (assoc_required "result" kvs "certificate") in
    if verdict = result_repair then begin
      validate_closed_keys kvs certificate_keys_repair "certificate";
      let b = parse_vector "repair" (assoc_required "repair" kvs "certificate") in
      if Array.length b <> n then
        raise (Reject (Printf.sprintf "repair witness has length %d, expected %d" (Array.length b) n));
      let reproduced = mat_vec d b in
      if not (vec_equal reproduced r) then raise (Reject "D b does not equal r")
    end
    else if verdict = result_separator then begin
      validate_closed_keys kvs certificate_keys_separator "certificate";
      let y = parse_vector "separator" (assoc_required "separator" kvs "certificate") in
      if Array.length y <> m then
        raise (Reject (Printf.sprintf "separator witness has length %d, expected %d" (Array.length y) m));
      let dty = mat_vec (transpose d n) y in
      if not (is_zero_vec dty) then raise (Reject "D^T y is not the zero vector");
      let pairing = dot y r in
      if not (Q.equal pairing Q.one) then raise (Reject "y.r is not exactly 1")
    end
    else raise (Reject (Printf.sprintf "unrecognized result: %S" verdict));
    { accepted = true; reasons = [] }
  with
  | Reject msg -> { accepted = false; reasons = [ msg ] }
  | e -> { accepted = false; reasons = [ Printf.sprintf "unexpected error during verification: %s" (Printexc.to_string e) ] }

let check_files (input_path : string) (cert_path : string) : check_result =
  match
    try Ok (read_input input_path) with
    | Reject msg -> Error (Printf.sprintf "malformed input file: %s" msg)
    | e -> Error (Printf.sprintf "malformed input file: %s" (Printexc.to_string e))
  with
  | Error msg -> { accepted = false; reasons = [ msg ] }
  | Ok (d, r) -> (
    match
      try Ok (strict_json_load cert_path) with
      | Reject msg -> Error (Printf.sprintf "malformed certificate file: %s" msg)
      | e -> Error (Printf.sprintf "malformed certificate file: %s" (Printexc.to_string e))
    with
    | Error msg -> { accepted = false; reasons = [ msg ] }
    | Ok cert -> verify d r cert)

(* ------------------------------------------------------------------ *)
(* CLI: mirrors r21_certificate_checker.py's roc-verify contract exactly
   (same ACCEPT/REJECT stdout tags, same exit codes), plus a --digest mode
   used only by the canonical-digest-vector cross-language tests. *)
(* ------------------------------------------------------------------ *)

let () =
  match Array.to_list Sys.argv with
  | [ _; "--digest"; input_path ] -> (
    try
      let d, r = read_input input_path in
      print_endline (canonical_input_digest d r);
      exit 0
    with
    | Reject msg ->
      Printf.printf "REJECT: %s\n" msg;
      exit 1
    | e ->
      Printf.printf "REJECT: %s\n" (Printexc.to_string e);
      exit 1)
  | [ _; input_path; cert_path ] ->
    let result = check_files input_path cert_path in
    if result.accepted then begin
      Printf.printf "ACCEPT: %s\n" cert_path;
      exit 0
    end
    else begin
      Printf.printf "REJECT: %s\n" cert_path;
      List.iter (fun reason -> Printf.printf "  - %s\n" reason) result.reasons;
      exit 1
    end
  | _ ->
    Printf.eprintf "usage: roc-verify-ocaml <input.json> <certificate.json>\n";
    Printf.eprintf "       roc-verify-ocaml --digest <input.json>\n";
    exit 2
