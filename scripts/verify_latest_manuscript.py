#!/usr/bin/env python3
"""Verify the author-designated latest manuscript artifact."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "paper/LATEST_MANUSCRIPT.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> str:
    return subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def main() -> int:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    artifact = ROOT / receipt["authoritative_artifact"]
    checks: list[str] = []

    require(
        receipt["decision"] in {"AUTHOR_DESIGNATED_LATEST_MANUSCRIPT", "AUTHOR_REQUESTED_REPRODUCIBILITY_UPGRADE"},
        "receipt records the author's latest-manuscript decision",
        checks,
    )
    require(artifact.is_file(), "latest manuscript PDF exists", checks)
    require(artifact.stat().st_size == receipt["size_bytes"], "PDF byte count matches", checks)
    require(sha256(artifact) == receipt["sha256"], "PDF SHA-256 matches", checks)

    info = run("pdfinfo", str(artifact))
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))
    require(pages == receipt["pages"], "PDF page count matches the receipt", checks)
    require("Page size:       " + receipt["page_size"] in info, "PDF uses the recorded page size", checks)
    require("Encrypted:       no" in info, "PDF is not encrypted", checks)

    text = re.sub(r"\s+", " ", run("pdftotext", "-layout", str(artifact), "-").replace("\u00ad", "-")).lower()
    required_text = {
        "title": "supervision-matched selection of paired rag repairs",
        "author surface": "qianxingji",
        "references": "references",
        "appendix start": "appendix a sensitivity to fixed action membership",
        "HGB appendix": "appendix e hgb-based pairwise preference scoring",
        "HGB estimator": "histgradientboostingclassifier",
        "HGB string feature": "sequencematcher",
        "final appendix": "appendix j scope of available replication materials",
        "public repository": "https://github.com/qianxingji/reliablerag-code",
        "public commit": receipt["public_repository"]["commit"].lower(),
    }
    for label, marker in required_text.items():
        require(marker in text, f"PDF contains {label}", checks)

    fonts = run("pdffonts", str(artifact)).splitlines()[2:]
    require(bool(fonts), "PDF contains font records", checks)
    require(all(" yes " in f" {row} " for row in fonts), "all PDF fonts are embedded", checks)
    require(all("Type 3" not in row for row in fonts), "PDF contains no Type 3 fonts", checks)

    result = {
        "decision": "PASS_LATEST_MANUSCRIPT_IDENTITY_AND_MECHANICAL_CHECKS",
        "check_count": len(checks),
        "artifact": receipt["authoritative_artifact"],
        "sha256": receipt["sha256"],
        "pages": pages,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
