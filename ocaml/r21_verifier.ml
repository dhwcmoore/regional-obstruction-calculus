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
   the resource limits (`max_rational_chars`, `max_dimension`), and the
   test fixtures both are checked against. It contains no translated or
   generated copy of `r21_certificate_checker.py` or `r21_certificate_
   format.py` -- every function below (rational parsing, schema
   validation, canonicalisation, matrix/vector arithmetic, verdict
   gating) is its own implementation in a different language, over a
   different exact-arithmetic representation (`Zarith.Q`, a GMP-backed
   rational type, vs. Python's `fractions.Fraction`), using a different
   JSON library (`Yojson.Safe` vs. Python's `json`) and a different SHA-256
   implementation (the `sha` opam package vs. Python's `hashlib`).

   Per the user's own framing motivating this file: independence does not
   require hand-writing a JSON lexer or an arbitrary-precision arithmetic
   library -- those are exactly the primitives it is appropriate to take
   from mature, independent libraries (`Yojson`, `Zarith`, `sha`). What
   this file writes independently is the schema validation, the
   canonicalisation, the certificate semantics, and the verdict gating --
   the actual content of the specification, not generic infrastructure.

   Build: requires the opam packages `zarith`, `yojson`, `sha` (see
   REPRODUCIBILITY.md for exact setup). Compiled via:
     ocamlfind ocamlopt -package zarith,yojson,sha -linkpkg \
       r21_verifier.ml -o roc-verify-ocaml

   USAGE:
     roc-verify-ocaml <input.json> <certificate.json>   -- verify (ACCEPT/REJECT, exit 0/1)
     roc-verify-ocaml --digest <input.json>              -- print only "sha256:<hex>" (exit 0/1)

   Fail-closed: every parse, validation, and arithmetic failure raises
   `Reject`, caught once at the top of `verify` (or the CLI's `--digest`
   branch) and turned into a rejection -- never a silent accept, and never
   an uncaught exception that could look like "no verdict" to a caller
   instead of "REJECT". Unlike `r21_certificate_checker.py`, which can
   record several independent reasons for one rejection, this file stops
   at the first failure and reports just that one reason -- a stylistic
   difference with no effect on the accept/reject verdict itself, which is
   the only thing the cross-language agreement tests require to match.
*)

exception Reject of string

let certificate_schema = "repair-or-separator/v1"
let input_schema = "roc-input/v1"
let result_repair = "repair"
let result_separator = "separator"

(* Must match r21_certificate_format.py's MAX_RATIONAL_CHARS/MAX_DIMENSION
   exactly -- the cross-language agreement corpus tests both checkers at
   and around these limits, so a mismatch here would itself be a
   cross-language disagreement. *)
let max_rational_chars = 100_000
let max_dimension = 10_000

let input_keys = [ "schema"; "D"; "r" ]
let certificate_keys_repair = [ "schema"; "input_digest"; "result"; "repair" ]
let certificate_keys_separator = [ "schema"; "input_digest"; "result"; "separator" ]

(* ------------------------------------------------------------------ *)
(* Strict exact-rational parsing: only `-?digits` or `-?digits/digits`,
   matching r21_certificate_format.py's _RATIONAL_RE exactly (no decimal
   notation, no leading `+`, no whitespace), written here from scratch
   rather than via a regex library -- this is schema-level parsing logic,
   not a generic primitive. *)
(* ------------------------------------------------------------------ *)

let is_digit c = c >= '0' && c <= '9'

let parse_rational (s : string) : Q.t =
  let len = String.length s in
  if len = 0 then raise (Reject (Printf.sprintf "not a canonical exact-rational string: %S" s));
  if len > max_rational_chars then
    raise (Reject (Printf.sprintf "rational string exceeds %d characters" max_rational_chars));
  let i = ref 0 in
  let negative = if s.[0] = '-' then (incr i; true) else false in
  let num_start = !i in
  while !i < len && is_digit s.[!i] do incr i done;
  if !i = num_start then raise (Reject (Printf.sprintf "not a canonical exact-rational string: %S" s));
  let num_digits = String.sub s num_start (!i - num_start) in
  let signed_num = if negative then "-" ^ num_digits else num_digits in
  if !i = len then Q.of_bigint (Z.of_string signed_num)
  else if s.[!i] = '/' then begin
    incr i;
    let den_start = !i in
    while !i < len && is_digit s.[!i] do incr i done;
    if !i = den_start || !i <> len then
      raise (Reject (Printf.sprintf "not a canonical exact-rational string: %S" s));
    let den_digits = String.sub s den_start (!i - den_start) in
    let den = Z.of_string den_digits in
    if Z.equal den Z.zero then raise (Reject (Printf.sprintf "zero denominator: %S" s));
    Q.make (Z.of_string signed_num) den
  end
  else raise (Reject (Printf.sprintf "not a canonical exact-rational string: %S" s))

let q_to_canonical_string (q : Q.t) : string =
  if Z.equal (Q.den q) Z.one then Z.to_string (Q.num q)
  else Z.to_string (Q.num q) ^ "/" ^ Z.to_string (Q.den q)

(* ------------------------------------------------------------------ *)
(* JSON: Yojson.Safe for lexing/parsing (a mature library, not hand-
   written), but duplicate-key rejection, closed-schema validation, and
   every accessor below are written for this schema specifically. *)
(* ------------------------------------------------------------------ *)

let rec check_no_duplicate_keys (j : Yojson.Safe.t) : unit =
  match j with
  | `Assoc kvs ->
    let seen = Hashtbl.create 8 in
    List.iter
      (fun (k, v) ->
        if Hashtbl.mem seen k then raise (Reject (Printf.sprintf "duplicate JSON key: %S" k));
        Hashtbl.add seen k ();
        check_no_duplicate_keys v)
      kvs
  | `List l -> List.iter check_no_duplicate_keys l
  | _ -> ()

let strict_json_load (path : string) : Yojson.Safe.t =
  let j =
    try Yojson.Safe.from_file path
    with
    | Yojson.Json_error msg -> raise (Reject (Printf.sprintf "malformed JSON: %s" msg))
    | Sys_error msg -> raise (Reject msg)
  in
  check_no_duplicate_keys j;
  j

let get_assoc (label : string) (j : Yojson.Safe.t) : (string * Yojson.Safe.t) list =
  match j with
  | `Assoc kvs -> kvs
  | _ -> raise (Reject (Printf.sprintf "%s is not a JSON object" label))

let get_string (label : string) (j : Yojson.Safe.t) : string =
  match j with
  | `String s -> s
  | _ -> raise (Reject (Printf.sprintf "%s is not a JSON string" label))

let get_list (label : string) (j : Yojson.Safe.t) : Yojson.Safe.t list =
  match j with
  | `List l -> l
  | _ -> raise (Reject (Printf.sprintf "%s is not a JSON array" label))

let assoc_required (key : string) (kvs : (string * Yojson.Safe.t) list) (label : string) : Yojson.Safe.t =
  match List.assoc_opt key kvs with
  | Some v -> v
  | None -> raise (Reject (Printf.sprintf "%s missing required field %S" label key))

let validate_closed_keys (kvs : (string * Yojson.Safe.t) list) (allowed : string list) (label : string) : unit
  =
  List.iter
    (fun (k, _) ->
      if not (List.mem k allowed) then
        raise (Reject (Printf.sprintf "%s has unrecognized field %S" label k)))
    kvs

(* ------------------------------------------------------------------ *)
(* Vector/matrix parsing, with the same shape and resource-limit
   validation as r21_certificate_format.py: MAX_DIMENSION on row/column
   counts, rectangularity, and D/r shape agreement. *)
(* ------------------------------------------------------------------ *)

let parse_vector (label : string) (j : Yojson.Safe.t) : Q.t array =
  let items = get_list label j in
  let n = List.length items in
  if n > max_dimension then
    raise (Reject (Printf.sprintf "vector length %d exceeds MAX_DIMENSION=%d" n max_dimension));
  Array.of_list (List.map (fun x -> parse_rational (get_string (label ^ " entry") x)) items)

let parse_matrix (label : string) (j : Yojson.Safe.t) : Q.t array array =
  let rows = get_list label j in
  let m = List.length rows in
  if m > max_dimension then
    raise (Reject (Printf.sprintf "row count %d exceeds MAX_DIMENSION=%d" m max_dimension));
  let parsed = Array.of_list (List.mapi (fun i row -> parse_vector (Printf.sprintf "%s row %d" label i) row) rows) in
  if Array.length parsed > 0 then begin
    let n = Array.length parsed.(0) in
    Array.iter
      (fun row -> if Array.length row <> n then raise (Reject "matrix is not rectangular: rows have differing lengths"))
      parsed;
    if n > max_dimension then raise (Reject (Printf.sprintf "column count %d exceeds MAX_DIMENSION=%d" n max_dimension))
  end;
  parsed

let validate_problem_shape (d : Q.t array array) (r : Q.t array) : unit =
  if Array.length r <> Array.length d then
    raise (Reject (Printf.sprintf "D has %d rows but r has length %d" (Array.length d) (Array.length r)))

(* ------------------------------------------------------------------ *)
(* Canonical (D, r) digest -- must match r21_certificate_format.py's
   canonical_input_digest byte-for-byte: "MxN", newline, each D row's
   entries comma-joined, newline, r's entries comma-joined, no trailing
   newline, SHA-256 over the UTF-8 bytes, hex-encoded, "sha256:" prefix. *)
(* ------------------------------------------------------------------ *)

let canonical_input_digest (d : Q.t array array) (r : Q.t array) : string =
  let m = Array.length d in
  let n = if m = 0 then 0 else Array.length d.(0) in
  let buf = Buffer.create 256 in
  Buffer.add_string buf (Printf.sprintf "%dx%d" m n);
  Array.iter
    (fun row ->
      Buffer.add_char buf '\n';
      Buffer.add_string buf (String.concat "," (Array.to_list (Array.map q_to_canonical_string row))))
    d;
  Buffer.add_char buf '\n';
  Buffer.add_string buf (String.concat "," (Array.to_list (Array.map q_to_canonical_string r)));
  "sha256:" ^ Sha256.to_hex (Sha256.string (Buffer.contents buf))

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
(* Reading roc-input/v1: closed schema, shape validation. *)
(* ------------------------------------------------------------------ *)

let read_input (path : string) : Q.t array array * Q.t array =
  let j = strict_json_load path in
  let kvs = get_assoc "input file" j in
  let schema = get_string "input file schema" (assoc_required "schema" kvs "input file") in
  if schema <> input_schema then raise (Reject (Printf.sprintf "unrecognized input schema: %S" schema));
  validate_closed_keys kvs input_keys "input file";
  let d = parse_matrix "D" (assoc_required "D" kvs "input file") in
  let r = parse_vector "r" (assoc_required "r" kvs "input file") in
  validate_problem_shape d r;
  (d, r)

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
