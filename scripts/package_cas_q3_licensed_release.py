"""Build the deterministic Apache-2.0-aware aggregate release candidate.

The package remains non-distributable pending legal, institutional and
third-party review. It copies only the fixed allowlist below and never traverses
the repository or private output namespaces. Apache-2.0 is scoped only to the
two project-authored code members.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "paired_rag_repair_aggregate_apache2_candidate_v2.zip"
FORBIDDEN_TEXT = (
    re.compile(r"(?i)(?:(?<![a-z0-9])[a-z]:[\\/]|/users/|/home/|qianx|qianxingji)"),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
)


@dataclass(frozen=True)
class Member:
    source: str
    destination: str
    role: str
    redistribution_basis: str
    benchmark_derived_aggregate: bool = False


MEMBERS = (
    Member("release/cas_q3_aggregate_v2/README.md", "README.md", "package_scope_and_verification_runbook", "PROJECT_DOCUMENTATION_RELEASE_REVIEW_PENDING"),
    Member("release/cas_q3_aggregate_v2/CLAIM_EVIDENCE_SUMMARY.md", "CLAIM_EVIDENCE_SUMMARY.md", "claim_and_evidence_boundary", "PROJECT_DOCUMENTATION_RELEASE_REVIEW_PENDING"),
    Member("release/cas_q3_aggregate_v2/DATA_AND_CODE_AVAILABILITY.md", "DATA_AND_CODE_AVAILABILITY.md", "availability_and_exclusion_boundary", "PROJECT_DOCUMENTATION_RELEASE_REVIEW_PENDING"),
    Member("release/cas_q3_aggregate_v2/THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.md", "third_party_asset_and_dependency_inventory", "PROJECT_DOCUMENTATION_RELEASE_REVIEW_PENDING"),
    Member("LICENSE", "LICENSE", "apache_2_0_license_text", "APACHE_2_0_LICENSE_TEXT"),
    Member("scripts/verify_cas_q3_claim_statistics.py", "scripts/verify_cas_q3_claim_statistics.py", "aggregate_reporting_verifier", "APACHE_2_0_PROJECT_AUTHORED_CODE"),
    Member("scripts/empirical_analysis_math.py", "scripts/empirical_analysis_math.py", "frozen_statistical_source", "APACHE_2_0_PROJECT_AUTHORED_CODE"),
    Member("outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json", "outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json", "sealed_aggregate_point_estimates", "PROJECT_GENERATED_AGGREGATE_RELEASE_REVIEW_PENDING", True),
    Member("outputs/cas_q2/empirical_analysis_v1/INTERVALS.json", "outputs/cas_q2/empirical_analysis_v1/INTERVALS.json", "sealed_aggregate_interval_summary", "PROJECT_GENERATED_AGGREGATE_RELEASE_REVIEW_PENDING", True),
    Member("outputs/cas_q2/empirical_analysis_v1/SHA256_MANIFEST.json", "outputs/cas_q2/empirical_analysis_v1/SHA256_MANIFEST.json", "sealed_analysis_stage_manifest", "PROJECT_GENERATED_AGGREGATE_RELEASE_REVIEW_PENDING", True),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def safe_destination(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value or not value:
        raise ValueError(f"unsafe archive member: {value!r}")
    return path


def scan_text(data: bytes, label: str) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"allowlisted text member is not UTF-8: {label}") from exc
    for pattern in FORBIDDEN_TEXT:
        if pattern.search(text):
            raise ValueError(f"identity or absolute-path pattern in {label}: {pattern.pattern}")


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def build(project_root: Path, output_dir: Path) -> dict[str, object]:
    project_root = project_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    prepared: list[tuple[Member, bytes]] = []
    destinations: set[str] = set()
    for member in MEMBERS:
        source = (project_root / member.source).resolve()
        try:
            source.relative_to(project_root)
        except ValueError as exc:
            raise ValueError(f"source escapes project root: {member.source}") from exc
        destination = safe_destination(member.destination).as_posix()
        if destination in destinations or destination == "MANIFEST.json":
            raise ValueError(f"duplicate or reserved destination: {destination}")
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"missing or non-regular allowlisted source: {member.source}")
        data = source.read_bytes()
        scan_text(data, member.source)
        prepared.append((member, data))
        destinations.add(destination)

    records = []
    for member, data in sorted(prepared, key=lambda item: item[0].destination):
        records.append({
            "path": member.destination,
            "size_bytes": len(data),
            "sha256": digest(data),
            "role": member.role,
            "access_class": "aggregate_release_candidate_v2",
            "redistribution_basis": member.redistribution_basis,
            "contains_benchmark_text_or_answers": False,
            "contains_benchmark_derived_aggregate": member.benchmark_derived_aggregate,
            "contains_identity_metadata": False,
        })
    manifest = {
        "schema_version": 1,
        "status": "LICENSED_CODE_CONTENT_VALIDATED_DISTRIBUTION_WITHHELD_EXTERNAL_REVIEW_PENDING",
        "scope": "anonymous_aggregate_reporting_verification_only",
        "distribution_authorized": False,
        "project_license": "Apache-2.0",
        "project_license_scope": [
            "scripts/verify_cas_q3_claim_statistics.py",
            "scripts/empirical_analysis_math.py"
        ],
        "non_code_members_not_relicensed_by_project_code_license": True,
        "external_release_gates": [
            "legal copyright holder and year/range",
            "institutional NOTICE or release-review decision",
            "Qwen research-license compatibility review",
            "DeBERTa non-c training-data-terms review",
            "journal-approved restricted-evidence access route",
            "persistent immutable archive identifier"
        ],
        "anonymization_profile": "double_blind_safe_no_identity_no_git_history",
        "excluded_classes": [
            "benchmark_text_and_answers",
            "per_question_outcomes_actions_and_bootstrap_multiplicities",
            "model_weights_indexes_and_learned_estimators",
            "private_reproduction_archives",
            "absolute_path_receipts_and_identity_metadata",
            "git_history",
        ],
        "members": records,
    }
    manifest_bytes = canonical_json(manifest)
    archive = output_dir / ARCHIVE_NAME
    with tempfile.NamedTemporaryFile(dir=output_dir, prefix=ARCHIVE_NAME + ".", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for member, data in sorted(prepared, key=lambda item: item[0].destination):
                bundle.writestr(zip_info(member.destination), data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            bundle.writestr(zip_info("MANIFEST.json"), manifest_bytes, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        temporary.replace(archive)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "status": "BUILT_CAS_Q3_APACHE2_AWARE_AGGREGATE_RELEASE_CANDIDATE_V2",
        "archive": str(archive),
        "archive_sha256": digest(archive.read_bytes()),
        "manifest_sha256": digest(manifest_bytes),
        "payload_members": len(records),
        "archive_members": len(records) + 1,
        "uncompressed_payload_bytes": sum(record["size_bytes"] for record in records),
        "distribution_authorized": False,
        "project_license": "Apache-2.0",
        "license_file_sha256": digest((project_root / "LICENSE").read_bytes()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.project_root, args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
