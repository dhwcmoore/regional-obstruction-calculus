#!/usr/bin/env python3
"""
run_tracking_adapter_pipeline.py

Step 9 of the tracking-adapter implementation order: an orchestration
script composing already-existing public CLI boundaries into one
front-to-back run, for both tracked example scenarios
(examples/tracking_adapter/):

    tracking snapshot
        -> independent adapter verification   (tracking_adapter_verifier.py)
        -> adapter certificate                 (tracking_adapter_certificate.py emit)
        -> canonical roc-input/v1              (embedded in the certificate)
        -> real R21 emitter                    (r21_certificate_emitter.py)
        -> repair-or-separator/v1
        -> Python R21 verifier                 (r21_certificate_checker.py)
        -> OCaml R21 verifier                  (roc-verify-ocaml, if built)
        -> complete chain verification         (tracking_adapter_certificate.py verify-chain)

TRUST BOUNDARY, stated precisely: this script is NOT another trusted
verifier. It is an untrusted coordinator. Every accept/reject decision
along the way is made by the independent adapter verifier or an
existing R21 verifier, each invoked as its own real subprocess against
its own public CLI -- this script contains no matrix, residue,
rational-conversion, or certificate-semantic logic of its own. Its only
jobs are: run each stage, fail immediately if any stage exits nonzero,
and compare regenerated artifacts against the tracked fixtures
byte-for-byte. If this script had a bug that skipped a stage or
miscompared two files, the worst outcome is a false FAIL (this script
wrongly reports success) or a false stage-order confusion -- it can
never cause an actual unsound (D, r) or certificate to be accepted,
since acceptance itself always comes from a real, separately-invoked
verifier subprocess's own exit code.

All temporary artifacts are written under a `tempfile.TemporaryDirectory`
and discarded automatically -- a clean checkout is left exactly as clean
after running this script as before.

USAGE:
    python run_tracking_adapter_pipeline.py
    python run_tracking_adapter_pipeline.py --json summary.json
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
FIXTURE_DIR = REPO_ROOT / "examples" / "tracking_adapter"
OCAML_CHECKER = REPO_ROOT / "roc-verify-ocaml"
SUBPROCESS_TIMEOUT = 30


class StageFailure(RuntimeError):
    pass


def _run(cmd, label):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT)
    if result.returncode != 0:
        raise StageFailure(
            f"stage {label!r} failed (exit {result.returncode}): {' '.join(str(c) for c in cmd)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def _load(path) -> dict:
    return json.loads(Path(path).read_text())


def run_scenario(scenario: str, expected_result: str) -> dict:
    tracked_snapshot = FIXTURE_DIR / f"{scenario}_snapshot.json"
    tracked_cert = FIXTURE_DIR / f"{scenario}_adapter_certificate.json"
    tracked_roc_input = FIXTURE_DIR / f"{scenario}_roc_input.json"
    tracked_r21_cert = FIXTURE_DIR / f"{scenario}_r21_certificate.json"

    with tempfile.TemporaryDirectory(prefix=f"tracking-adapter-{scenario}-") as tmp:
        tmp = Path(tmp)
        cert_path = tmp / "certificate.json"
        roc_input_path = tmp / "roc_input.json"
        r21_cert_path = tmp / "r21_certificate.json"

        # 1. Independent adapter verification.
        _run(
            [sys.executable, str(REPO_ROOT / "tracking_adapter_verifier.py"), str(tracked_snapshot)],
            f"{scenario}: verify snapshot",
        )

        # 2. Emit adapter certificate.
        _run(
            [sys.executable, str(REPO_ROOT / "tracking_adapter_certificate.py"), "emit",
             str(tracked_snapshot), "--output", str(cert_path)],
            f"{scenario}: emit certificate",
        )
        regenerated_cert = _load(cert_path)
        if regenerated_cert != _load(tracked_cert):
            raise StageFailure(f"{scenario}: regenerated adapter certificate does not byte-match the tracked file")

        # 3. Canonical roc-input/v1 (embedded in the certificate).
        roc_input_path.write_text(json.dumps(regenerated_cert["roc_input"]))
        if regenerated_cert["roc_input"] != _load(tracked_roc_input):
            raise StageFailure(f"{scenario}: regenerated roc-input/v1 does not byte-match the tracked file")

        # 4. Real R21 emitter.
        _run(
            [sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(roc_input_path),
             "--certificate", str(r21_cert_path)],
            f"{scenario}: R21 emitter",
        )
        regenerated_r21_cert = _load(r21_cert_path)
        if regenerated_r21_cert != _load(tracked_r21_cert):
            raise StageFailure(f"{scenario}: regenerated R21 certificate does not byte-match the tracked file")
        if regenerated_r21_cert["result"] != expected_result:
            raise StageFailure(
                f"{scenario}: expected R21 result {expected_result!r}, got {regenerated_r21_cert['result']!r}"
            )

        # 5. Python R21 verifier.
        _run(
            [sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"), str(roc_input_path), str(r21_cert_path)],
            f"{scenario}: Python R21 verifier",
        )

        # 6. OCaml R21 verifier -- optional toolchain, same convention as
        # every other OCaml-dependent check in this repository: run it if
        # built, do not fail the pipeline if it is not.
        ocaml_ran = False
        if OCAML_CHECKER.exists():
            _run([str(OCAML_CHECKER), str(roc_input_path), str(r21_cert_path)], f"{scenario}: OCaml R21 verifier")
            ocaml_ran = True

        # 7. Complete chain verification.
        _run(
            [sys.executable, str(REPO_ROOT / "tracking_adapter_certificate.py"), "verify-chain",
             str(tracked_snapshot), str(cert_path), str(r21_cert_path)],
            f"{scenario}: complete chain verification",
        )

        return {
            "scenario": scenario,
            "D": regenerated_cert["D"],
            "r": regenerated_cert["r"],
            "r21_result": regenerated_r21_cert["result"],
            "witness": regenerated_r21_cert.get("repair") or regenerated_r21_cert.get("separator"),
            "r21_input_digest": regenerated_cert["r21_input_digest"],
            "ocaml_verifier_ran": ocaml_ran,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Front-to-back demonstration of the tracking-adapter certificate pipeline."
    )
    parser.add_argument("--json", help="optional path to write a JSON summary to")
    args = parser.parse_args()

    summaries = []
    try:
        summaries.append(run_scenario("repairable", "repair"))
        print(f"repairable: PASS (R21 result={summaries[-1]['r21_result']}, witness={summaries[-1]['witness']})")
        summaries.append(run_scenario("obstructed", "separator"))
        print(f"obstructed: PASS (R21 result={summaries[-1]['r21_result']}, witness={summaries[-1]['witness']})")
    except StageFailure as e:
        print(f"PIPELINE FAILED: {e}", file=sys.stderr)
        raise SystemExit(1)

    print("ALL STAGES PASSED for both tracked scenarios.")
    if args.json:
        Path(args.json).write_text(json.dumps(summaries, indent=2))
    raise SystemExit(0)


if __name__ == "__main__":
    main()
