(*
   r21_format.ml

   Shared, solver-independent primitives for R21 (`rocq/
   ExactRationalRepairOrSeparator.v`) certificates: the schema tags,
   strict canonical-rational parsing, JSON helpers (duplicate-key
   rejection, closed-schema validation), resource limits, and the
   canonical `(D, r)` input digest -- the OCaml counterpart to
   `r21_certificate_format.py`.

   This module is used by BOTH `r21_verifier.ml` (the independent
   checker) and `r21_extracted_solve.ml` (the thin adapter around the
   Rocq-extracted generator). That is the same narrow, deliberate
   exception `r21_certificate_format.py`'s own header documents on the
   Python side: canonical serialisation, schema validation, and hashing
   are not solver logic -- neither checker's mathematical verdict (`Db=r`
   or `D^Ty=0, y.r=1`) depends on anything in this module being correct,
   only on the digest *matching* what the generator side computed, which
   is a provenance-binding property, not a soundness one (see
   docs/design/R21_CERTIFICATE_TCB.md's mathematical-soundness vs.
   provenance-binding TCB split for the precise distinction, which
   applies identically here).

   Depends on `Yojson.Safe` (JSON), `Zarith.Q` (exact rationals), and
   `Sha256` (the `sha` package) -- mature libraries for those primitives;
   every function below (parsing, validation, canonicalisation) is this
   module's own, not shared with or translated from the Python side.
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
