"""Read-only verification of the private control namespace's pinned seal."""
import json
from pathlib import Path
from scripts.verify_roa_artifacts import digest,relative_path,safe_file

CONTROLS_MANIFEST_SHA256="80b65e2139e2e39909d8005465082b255d9c8494fc0861bfb866bce6a06adc01"


def verify_controls(root: Path):
    manifest=root/"SHA256_MANIFEST.json"
    if digest(manifest)!=CONTROLS_MANIFEST_SHA256:raise RuntimeError("CONTROL_MANIFEST_ANCHOR")
    data=json.loads(manifest.read_text());entries=data["files"]
    names=[e["path"] for e in entries]
    if len(set(n.casefold() for n in names))!=len(names):raise RuntimeError("CONTROL_DUPLICATE_PATH")
    for entry in entries:
        path=safe_file(root.resolve(),relative_path(entry["path"]))
        if path.stat().st_size!=entry["size_bytes"] or digest(path)!=entry["sha256"]:raise RuntimeError("CONTROL_PAYLOAD:"+entry["path"])
    if {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}!=set(names)|{"SHA256_MANIFEST.json"}:raise RuntimeError("CONTROL_EXACT_COVERAGE")
    if json.loads((root/"INDEPENDENT_VALIDATION.json").read_text())["status"]!="PASS":raise RuntimeError("CONTROL_INDEPENDENT")
    return dict(path=str(root),manifest_sha256=CONTROLS_MANIFEST_SHA256,payload_files=len(entries),status="PASS")
