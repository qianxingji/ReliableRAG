"""Independently validate and round-trip the Apache-2.0-aware candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import zipfile


FORBIDDEN_TEXT = (
    re.compile(r"(?i)(?:(?<![a-z0-9])[a-z]:[\\/]|/users/|/home/|qianx|qianxingji)"),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
)
EXPECTED_STATUS = "LICENSED_CODE_CONTENT_VALIDATED_DISTRIBUTION_WITHHELD_EXTERNAL_REVIEW_PENDING"
LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
CODE_PATHS = {
    "scripts/verify_cas_q3_claim_statistics.py",
    "scripts/empirical_analysis_math.py",
}
ALLOWED_BASES = {
    "APACHE_2_0_LICENSE_TEXT",
    "APACHE_2_0_PROJECT_AUTHORED_CODE",
    "PROJECT_DOCUMENTATION_RELEASE_REVIEW_PENDING",
    "PROJECT_GENERATED_AGGREGATE_RELEASE_REVIEW_PENDING",
}


class Checks:
    def __init__(self) -> None:
        self.count = 0

    def true(self, value: bool, label: str) -> None:
        self.count += 1
        if not value:
            raise ValueError(label)

    def equal(self, actual: object, expected: object, label: str) -> None:
        self.count += 1
        if actual != expected:
            raise ValueError(f"{label}: {actual!r} != {expected!r}")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value or not value:
        raise ValueError(f"unsafe archive member: {value!r}")
    return path


def scan_text(data: bytes, label: str) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"text member is not UTF-8: {label}") from exc
    for pattern in FORBIDDEN_TEXT:
        if pattern.search(text):
            raise ValueError(f"identity or absolute-path pattern in {label}: {pattern.pattern}")


def validate_archive(archive: Path, expected_archive_sha256: str, expected_manifest_sha256: str) -> dict[str, object]:
    checks = Checks()
    archive_bytes = archive.read_bytes()
    checks.equal(digest(archive_bytes), expected_archive_sha256, "external archive pin")
    with zipfile.ZipFile(archive) as bundle:
        infos = bundle.infolist()
        names = [info.filename for info in infos]
        checks.equal(len(names), len(set(names)), "unique archive names")
        checks.true("MANIFEST.json" in names, "manifest present")
        for info in infos:
            safe_name(info.filename)
            mode = info.external_attr >> 16
            checks.true(not info.is_dir(), f"no directory entries: {info.filename}")
            checks.true(not stat.S_ISLNK(mode), f"no symlink entries: {info.filename}")
        manifest_bytes = bundle.read("MANIFEST.json")
        checks.equal(digest(manifest_bytes), expected_manifest_sha256, "external manifest pin")
        manifest = json.loads(manifest_bytes)
        checks.equal(manifest["schema_version"], 1, "manifest schema")
        checks.equal(manifest["status"], EXPECTED_STATUS, "candidate status")
        checks.equal(manifest["scope"], "anonymous_aggregate_reporting_verification_only", "scope")
        checks.equal(manifest["distribution_authorized"], False, "distribution remains blocked")
        checks.equal(manifest["project_license"], "Apache-2.0", "project code license")
        checks.equal(set(manifest["project_license_scope"]), CODE_PATHS, "project code license scope")
        checks.equal(manifest["non_code_members_not_relicensed_by_project_code_license"], True, "non-code scope boundary")
        checks.equal(len(manifest["external_release_gates"]), 6, "external release gates retained")
        checks.equal(manifest["anonymization_profile"], "double_blind_safe_no_identity_no_git_history", "anonymous profile")
        records = manifest["members"]
        record_names = [record["path"] for record in records]
        checks.equal(record_names, sorted(record_names), "sorted manifest members")
        checks.equal(set(names) - {"MANIFEST.json"}, set(record_names), "exact declared membership")
        checks.equal(len(record_names), len(set(record_names)), "unique manifest paths")
        extracted: dict[str, bytes] = {}
        for record in records:
            name = safe_name(record["path"]).as_posix()
            data = bundle.read(name)
            checks.equal(len(data), record["size_bytes"], f"size {name}")
            checks.equal(digest(data), record["sha256"], f"hash {name}")
            checks.equal(record["access_class"], "aggregate_release_candidate_v2", f"candidate class {name}")
            checks.true(record["redistribution_basis"] in ALLOWED_BASES, f"recognized basis {name}")
            if name in CODE_PATHS:
                checks.equal(record["redistribution_basis"], "APACHE_2_0_PROJECT_AUTHORED_CODE", f"code license {name}")
            else:
                checks.true(record["redistribution_basis"] != "APACHE_2_0_PROJECT_AUTHORED_CODE", f"no code-license spillover {name}")
            checks.equal(record["contains_benchmark_text_or_answers"], False, f"no benchmark text {name}")
            checks.equal(record["contains_identity_metadata"], False, f"no identity metadata {name}")
            scan_text(data, name)
            extracted[name] = data
        scan_text(manifest_bytes, "MANIFEST.json")
        checks.equal(digest(extracted["LICENSE"]), LICENSE_SHA256, "exact Apache License 2.0 text")
        checks.true(b"Apache License" in extracted["LICENSE"], "Apache license marker")
        checks.true(b"Version 2.0, January 2004" in extracted["LICENSE"], "Apache version marker")

    with tempfile.TemporaryDirectory(prefix="cas_q3_aggregate_roundtrip_") as temporary:
        root = Path(temporary)
        for name, data in extracted.items():
            target = root.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            checks.equal(digest(target.read_bytes()), digest(data), f"round-trip hash {name}")
        process = subprocess.run(
            [sys.executable, "scripts/verify_cas_q3_claim_statistics.py"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        checks.equal(process.returncode, 0, "round-trip verifier exit")
        checks.equal(process.stderr, "", "round-trip verifier stderr")
        receipt = json.loads(process.stdout)
        checks.equal(receipt["status"], "PASS_CAS_Q3_STATISTICAL_STATEMENT_VERIFICATION", "round-trip verifier status")
        checks.equal(receipt["checks"], 129, "round-trip verifier checks")
    return {
        "status": "PASS_CAS_Q3_APACHE2_AWARE_AGGREGATE_RELEASE_V2_ROUNDTRIP",
        "checks": checks.count,
        "archive_sha256": expected_archive_sha256,
        "manifest_sha256": expected_manifest_sha256,
        "archive_members": len(names),
        "payload_members": len(records),
        "roundtrip_verifier_status": receipt["status"],
        "roundtrip_verifier_checks": receipt["checks"],
        "distribution_authorized": False,
        "project_license": "Apache-2.0",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    result = validate_archive(args.archive, args.archive_sha256, args.manifest_sha256)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
