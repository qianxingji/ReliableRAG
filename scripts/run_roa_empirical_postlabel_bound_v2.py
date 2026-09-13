"""Versioned postlabel entry binding accepted C4 V2 preflight into cost/D."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
PROJECT = Path(r"E:\paper\ReliableRAG")
PRELABEL_SHA256 = "046009231ff834f667f469386c9617f121c4341d39310dbeddf86d5bfedf97b2"
V1_SHA256 = "c03555a4a3562be34345bd79b35abb11c8b6bb913a4c812e24837cfb8c88f3b6"
V2_SHA256 = "1aabac381c8a5e5381f46729f49e9afcaae915c1fa84cd375141486e513b530a"
ENTRIES = {
    "cost": "scripts.audit_roa_empirical_cost",
    "mapping": "scripts.map_roa_empirical_outcomes",
    "outcome_validation": "scripts.validate_roa_empirical_outcomes",
    "analysis": "scripts.analyze_roa_empirical_results",
    "analysis_validation": "scripts.validate_roa_empirical_analysis",
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def record(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": sha(path),
            "size_bytes": path.stat().st_size}


def verify_record(entry):
    require(set(entry) == {"path", "sha256", "size_bytes"},
            "POSTLABEL_V2_CONTROL_SCHEMA")
    path = Path(entry["path"]).resolve()
    require(path.is_file() and record(path) == {**entry, "path": str(path)},
            "POSTLABEL_V2_CONTROL_CHANGED")
    return path


def fixed_stage_maps():
    base = REPO / "outputs/cas_q2"
    before = {
        "gpu_preflight": str((base / "empirical_scoring_gpu_preflight_v1").resolve()),
        "base": str((base / "empirical_base_scoring_v1").resolve()),
        "gbv": str((base / "empirical_gbv_scoring_v1").resolve()),
        "policies": str((base / "empirical_prelabel_policies_v1").resolve()),
        "independent": str((base / "empirical_scoring_validation_v1").resolve()),
    }
    return before, {**before, "gpu_preflight":
                    str((base / "empirical_scoring_gpu_preflight_v2").resolve())}


def parse_binding(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("original_arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    require(args.original_arguments and args.original_arguments[0] == "--",
            "POSTLABEL_V2_ARGUMENT_DELIMITER")
    args.original_arguments = args.original_arguments[1:]
    raw = args.config.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == args.config_sha256,
            "POSTLABEL_V2_CONFIG_PIN")
    config = json.loads(raw)
    exact = {"version", "stage", "project_root", "engineering_root",
             "source_commit", "entry_module", "original_arguments",
             "stage_paths_before", "stage_paths_after",
             "prelabel_manifest_sha256", "v1_manifest_sha256",
             "v2_manifest_sha256", "controls"}
    require(set(config) == exact and config["version"] == 2,
            "POSTLABEL_V2_CONFIG_SCHEMA")
    require(config["stage"] in ENTRIES and
            config["entry_module"] == ENTRIES[config["stage"]],
            "POSTLABEL_V2_FIXED_ENTRY")
    require(config["original_arguments"] == args.original_arguments,
            "POSTLABEL_V2_ORIGINAL_ARGUMENTS")
    require(Path(config["project_root"]).resolve() == PROJECT.resolve() and
            Path(config["engineering_root"]).resolve() == REPO.resolve(),
            "POSTLABEL_V2_FIXED_ROOTS")
    require(config["prelabel_manifest_sha256"] == PRELABEL_SHA256 and
            config["v1_manifest_sha256"] == V1_SHA256 and
            config["v2_manifest_sha256"] == V2_SHA256,
            "POSTLABEL_V2_EVIDENCE_PINS")
    require(config["source_commit"] == subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "POSTLABEL_V2_SOURCE_COMMIT")
    require(not subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True).strip(),
        "POSTLABEL_V2_CLEAN_COMMITTED_CHECKOUT")
    controls = [verify_record(entry) for entry in config["controls"]]
    return args, config, controls


def apply_c4_path_binding(config):
    from scripts import empirical_scoring_stage_io as scoring_io

    before, after = fixed_stage_maps()
    observed = {key: str(value.resolve()) for key, value in scoring_io.STAGES.items()}
    require(config["stage_paths_before"] == before and
            config["stage_paths_after"] == after,
            "POSTLABEL_V2_STAGE_CONFIG")
    require(observed == before, "POSTLABEL_V2_ORIGINAL_STAGE_PATHS")
    require(Path(before["gpu_preflight"]).is_dir() and
            sha(Path(before["gpu_preflight"]) / "SHA256_MANIFEST.json") == V1_SHA256,
            "POSTLABEL_V2_PRESERVED_V1")
    require(Path(after["gpu_preflight"]).is_dir() and
            sha(Path(after["gpu_preflight"]) / "SHA256_MANIFEST.json") == V2_SHA256,
            "POSTLABEL_V2_ACCEPTED_V2")
    require(Path(after["independent"]).is_dir() and
            sha(Path(after["independent"]) / "SHA256_MANIFEST.json") == PRELABEL_SHA256,
            "POSTLABEL_V2_ACCEPTED_PRELABEL")
    scoring_io.STAGES["gpu_preflight"] = Path(after["gpu_preflight"])
    require({key: str(value.resolve()) for key, value in scoring_io.STAGES.items()} == after,
            "POSTLABEL_V2_BOUND_STAGE_PATHS")


def add_binding_inputs(stage, controls, config_path):
    """Include the wrapper/config in each newly created scientific freeze."""
    extras = [Path(config_path).resolve(), *controls]
    if stage == "cost":
        from scripts import audit_roa_empirical_cost as target
        original = target.source_paths

        def source_paths():
            return sorted(set(original() + extras))

        target.source_paths = source_paths
        return target
    from scripts import empirical_outcome_stage_io as outcome_io
    original = outcome_io.source_paths

    def source_paths():
        return sorted(set(original() + extras))

    outcome_io.source_paths = source_paths
    return __import__(ENTRIES[stage], fromlist=["main"])


def main(argv=None):
    args, config, controls = parse_binding(argv)
    apply_c4_path_binding(config)
    module = add_binding_inputs(config["stage"], controls, args.config)
    require(module.__name__ == config["entry_module"],
            "POSTLABEL_V2_IMPORTED_ENTRY")
    sys.argv = [str(Path(module.__file__).resolve()), *args.original_arguments]
    return module.main()


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
