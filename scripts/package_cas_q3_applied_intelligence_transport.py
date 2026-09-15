#!/usr/bin/env python3
"""Build a private complete-source Applied Intelligence transport candidate.

The tracked authored-source preflight deliberately excludes publisher template
files.  This builder combines that frozen authored source with the exact
authenticated Springer Nature class and bibliography style in a new external
directory.  It does not submit or authorize distribution of the result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_cas_q3_applied_intelligence_preflight import (
    OFFICIAL_TEMPLATE_SHA256,
    template_member,
)


PREFLIGHT_RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_APPLIED_INTELLIGENCE_MODERN_PREFLIGHT.json"
ARCHIVE_NAME = "applied_intelligence_complete_source_transport_candidate.zip"
AUTHORED_MEMBERS = [
    "Fig1.pdf",
    "Fig2.pdf",
    "manuscript.bbl",
    "manuscript.tex",
    "references.bib",
    "table_main_results.tex",
    "table_primary_comparisons.tex",
    "table_study_design.tex",
]
TEMPLATE_MEMBERS = ["sn-basic.bst", "sn-jnl.cls"]


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def safe_flat_member(name: str) -> bool:
    parsed = PurePosixPath(name)
    return (
        name == parsed.name
        and not parsed.is_absolute()
        and "\\" not in name
        and name not in {"", ".", ".."}
        and ".." not in parsed.parts
    )


def deterministic_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name in sorted(members):
            if not safe_flat_member(name):
                raise AssertionError(f"unsafe or nested member: {name}")
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, members[name])


def build(template_zip: Path, authored_zip: Path, output_dir: Path) -> dict[str, object]:
    template_zip = template_zip.resolve()
    authored_zip = authored_zip.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"refusing to reuse output directory: {output_dir}")
    if digest(template_zip) != OFFICIAL_TEMPLATE_SHA256:
        raise AssertionError("official template ZIP hash mismatch")

    preflight = json.loads(PREFLIGHT_RECEIPT.read_text(encoding="utf-8"))
    if digest(authored_zip) != preflight["artifacts"]["authored_source_zip_sha256"]:
        raise AssertionError("authored-source ZIP hash mismatch")
    with zipfile.ZipFile(authored_zip) as authored:
        names = authored.namelist()
        if names != AUTHORED_MEMBERS:
            raise AssertionError(f"authored-source allowlist mismatch: {names}")
        if any(not safe_flat_member(name) for name in names):
            raise AssertionError("authored-source ZIP is not flat and safe")
        members = {name: authored.read(name) for name in names}

    with zipfile.ZipFile(template_zip) as official:
        members["sn-jnl.cls"] = template_member(official, "/sn-jnl.cls")
        members["sn-basic.bst"] = template_member(official, "/bst/sn-basic.bst")

    source = members["manuscript.tex"].decode("utf-8")
    if r"\documentclass[pdflatex,sn-basic,Numbered]{sn-jnl}" not in source:
        raise AssertionError("transport source does not use the accepted modern profile")
    if "Anonymous" not in source or "qianxingji" in source.lower() or "@" in source:
        raise AssertionError("transport source anonymity boundary failed")

    output_dir.mkdir(parents=True)
    archive = output_dir / ARCHIVE_NAME
    deterministic_zip(archive, members)
    result = {
        "schema_version": 1,
        "decision": "PASS_PRIVATE_COMPLETE_SOURCE_TRANSPORT_CANDIDATE_BUILT_SUBMISSION_UNAUTHORIZED",
        "cas_q3_status": "NOT_READY",
        "archive": str(archive).replace("\\", "/"),
        "archive_sha256": digest(archive),
        "archive_members": sorted(members),
        "archive_member_count": len(members),
        "member_sha256": {name: digest_bytes(members[name]) for name in sorted(members)},
        "official_template_zip_sha256": OFFICIAL_TEMPLATE_SHA256,
        "authored_source_zip_sha256": digest(authored_zip),
        "template_dependencies_included": TEMPLATE_MEMBERS,
        "flat_archive": True,
        "anonymous": True,
        "smallcondensed_profile_used": False,
        "smallcondensed_equivalence_proved": False,
        "submission_authorized": False,
        "distribution_authorized": False,
        "scientific_payloads_read": False,
        "model_forwards": 0,
        "scientific_fits": 0,
    }
    (output_dir / "BUILD_RECEIPT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-zip", type=Path, required=True)
    parser.add_argument(
        "--authored-zip",
        type=Path,
        default=ROOT / "output" / "target_profiles" / "applied_intelligence_modern_preflight"
        / "applied_intelligence_authored_source_preflight.zip",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.template_zip, args.authored_zip, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
