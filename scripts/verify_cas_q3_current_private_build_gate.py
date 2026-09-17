#!/usr/bin/env python3
"""Verify that incomplete private owner input stops before transport or output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from typing import Any

try:
    from scripts.build_cas_q3_applied_intelligence_private_submission import build
    from scripts.verify_cas_q3_owner_inputs import ROOT, TEMPLATE, validate
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from build_cas_q3_applied_intelligence_private_submission import build
    from verify_cas_q3_owner_inputs import ROOT, TEMPLATE, validate


DEFAULT_INPUT = ROOT / "docs" / "cas_q3" / "OWNER_INPUTS.local.json"
RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_CURRENT_PRIVATE_BUILD_GATE_VERIFICATION.json"


class TransportAccessTripwire:
    """Duck-typed path that records any attempt to reach transport validation."""

    def __init__(self) -> None:
        self.accessed = False

    def resolve(self) -> Path:
        self.accessed = True
        raise AssertionError("transport access tripwire reached")


def evaluate(
    data: dict[str, Any],
    *,
    expected_missing: int | None = None,
    input_matches_empty_template: bool,
) -> dict[str, object]:
    validation = validate(data)
    tripwire = TransportAccessTripwire()
    build_error_category: str | None = None
    unexpected_error: str | None = None
    with tempfile.TemporaryDirectory(prefix="reliablerag_private_gate_") as temporary:
        output = Path(temporary) / "must_not_be_created"
        try:
            build(data, tripwire, "never-read", output)  # type: ignore[arg-type]
        except ValueError as exc:
            if str(exc) == "owner inputs are incomplete or invalid":
                build_error_category = "OWNER_INPUTS_INCOMPLETE_OR_INVALID"
            else:
                unexpected_error = type(exc).__name__
        except Exception as exc:  # pragma: no cover - failure is reported below.
            unexpected_error = type(exc).__name__
        output_created = output.exists()

    missing_count = len(validation["missing_field_paths"])
    error_count = len(validation["validation_error_paths"])
    passed = (
        validation["complete"] is False
        and build_error_category == "OWNER_INPUTS_INCOMPLETE_OR_INVALID"
        and unexpected_error is None
        and tripwire.accessed is False
        and output_created is False
        and (expected_missing is None or missing_count == expected_missing)
    )
    return {
        "schema_version": 1,
        "decision": (
            "PASS_OWNER_INPUT_GATE_REJECTS_BEFORE_TRANSPORT_OR_OUTPUT"
            if passed
            else "FAIL_OWNER_INPUT_GATE_DID_NOT_PRESERVE_PRE_TRANSPORT_BOUNDARY"
        ),
        "owner_input_validation_decision": validation["decision"],
        "owner_inputs_complete": validation["complete"],
        "missing_field_count": missing_count,
        "validation_error_count": error_count,
        "expected_missing_field_count": expected_missing,
        "input_matches_empty_template": input_matches_empty_template,
        "build_error_category": build_error_category,
        "transport_access_attempted": tripwire.accessed,
        "output_created": output_created,
        "author_populated_package_built": False,
        "private_values_emitted": False,
        "private_input_hash_emitted": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--expected-missing", type=int)
    parser.add_argument("--check-template", action="store_true")
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args()
    if args.check_template and args.write_receipt:
        parser.error("--check-template cannot write the current-private-input receipt")
    path = TEMPLATE if args.check_template else args.input
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        print(json.dumps({
            "schema_version": 1,
            "decision": "FAIL_CLOSED_OWNER_INPUT_FILE_MISSING",
            "private_values_emitted": False,
            "cas_q3_status": "NOT_READY",
        }, indent=2))
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    result = evaluate(
        data,
        expected_missing=args.expected_missing,
        input_matches_empty_template=data == template,
    )
    result["input_scope"] = "TRACKED_EMPTY_TEMPLATE" if args.check_template else "LOCAL_GIT_IGNORED_OWNER_INPUT"
    if args.write_receipt:
        RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["decision"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
