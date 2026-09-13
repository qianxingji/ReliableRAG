"""Versioned C4 entry with exact Jinja identity and fixed V2 preflight path."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
PROJECT = Path(r"E:\paper\ReliableRAG")
RUNTIME_SHA256 = "dc2905224798b07302db8950f68db228de1faff9042c44dbaee7111ba107878f"
V1_FAILURE_SHA256 = "c03555a4a3562be34345bd79b35abb11c8b6bb913a4c812e24837cfb8c88f3b6"
V1_AUDIT_SHA256 = "cbb9911c17c7c1b3f65f31d36b79814383bbba42a4cf4477b483ab1d9b2efc13"
STAGE_MODULES = {
    "gpu_preflight": "scripts.preflight_roa_empirical_scoring_gpu",
    "base": "scripts.build_roa_empirical_scoring",
    "gbv": "scripts.build_roa_empirical_scoring",
    "policies": "scripts.build_roa_empirical_scoring",
    "independent": "scripts.validate_roa_empirical_scoring",
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
    return dict(path=str(path), sha256=sha(path), size_bytes=path.stat().st_size)


def verify_record(entry):
    require(set(entry) == {"path", "sha256", "size_bytes"}, "C4_V2_CONTROL_RECORD_SCHEMA")
    path = Path(entry["path"]).resolve()
    require(path.is_file() and record(path) == {**entry, "path": str(path)},
            "C4_V2_CONTROL_RECORD_CHANGED")
    return path


def canonical_hash(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_binding(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("original_arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    require(args.original_arguments and args.original_arguments[0] == "--",
            "C4_V2_ORIGINAL_ARGUMENT_DELIMITER")
    args.original_arguments = args.original_arguments[1:]
    raw = args.config.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == args.config_sha256,
            "C4_V2_BINDING_CONFIG_PIN")
    config = json.loads(raw)
    exact = {"version", "stage", "project_root", "engineering_root",
             "source_commit", "entry_module", "original_arguments",
             "stage_paths_before", "stage_paths_after", "runtime_manifest_sha256",
             "v1_failure_manifest_sha256", "v1_failure_audit_manifest_sha256",
             "controls"}
    require(set(config) == exact and config["version"] == 2,
            "C4_V2_BINDING_CONFIG_SCHEMA")
    require(config["stage"] in STAGE_MODULES and
            config["entry_module"] == STAGE_MODULES[config["stage"]],
            "C4_V2_FIXED_ENTRY")
    require(config["original_arguments"] == args.original_arguments,
            "C4_V2_ORIGINAL_ARGUMENTS")
    require(Path(config["project_root"]).resolve() == PROJECT and
            Path(config["engineering_root"]).resolve() == REPO,
            "C4_V2_FIXED_ROOTS")
    require(config["runtime_manifest_sha256"] == RUNTIME_SHA256 and
            config["v1_failure_manifest_sha256"] == V1_FAILURE_SHA256 and
            config["v1_failure_audit_manifest_sha256"] == V1_AUDIT_SHA256,
            "C4_V2_EVIDENCE_PINS")
    require(config["source_commit"] ==
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                    text=True).strip(), "C4_V2_SOURCE_COMMIT")
    require(not subprocess.check_output(["git", "status", "--porcelain"],
                                        cwd=REPO, text=True).strip(),
            "C4_V2_CLEAN_COMMITTED_CHECKOUT")
    for entry in config["controls"]:
        verify_record(entry)
    return args, config


def fixed_stage_maps():
    base = REPO / "outputs/cas_q2"
    before = dict(
        gpu_preflight=str((base / "empirical_scoring_gpu_preflight_v1").resolve()),
        base=str((base / "empirical_base_scoring_v1").resolve()),
        gbv=str((base / "empirical_gbv_scoring_v1").resolve()),
        policies=str((base / "empirical_prelabel_policies_v1").resolve()),
        independent=str((base / "empirical_scoring_validation_v1").resolve()),
    )
    return before, {**before, "gpu_preflight":
                    str((base / "empirical_scoring_gpu_preflight_v2").resolve())}


def prebinding_input_checks(root):
    """Authenticate accepted C4/C3/CPU inputs before mutating shared path globals."""
    from scripts.empirical_pool_io import load, verify_namespace
    from scripts.empirical_scoring_io import inputs
    from scripts.empirical_scoring_stage_io import CPU, CPU_SHA, PREPARATION, PREPARATION_SHA

    paths = inputs(root, neural=True)[2]
    paths += verify_namespace(CPU, CPU_SHA)
    paths += verify_namespace(PREPARATION, PREPARATION_SHA)
    for entry in load(CPU / "EXECUTABLE_FREEZE.json")["inputs"]:
        paths.append(verify_record(entry))
    require(sha(REPO / "outputs/cas_q2/empirical_runtime_v1/SHA256_MANIFEST.json") ==
            RUNTIME_SHA256, "C4_V2_ACCEPTED_C3_PIN")
    return sorted(set(Path(path).resolve() for path in paths))


def apply_stage_paths(config):
    from scripts import empirical_scoring_stage_io as stage_io

    before, after = fixed_stage_maps()
    require(config["stage_paths_before"] == before and
            config["stage_paths_after"] == after, "C4_V2_FIXED_STAGE_PATH_CONFIG")
    require({key: str(value.resolve()) for key, value in stage_io.STAGES.items()} == before,
            "C4_V2_ORIGINAL_STAGE_PATHS")
    if config["stage"] == "gpu_preflight":
        require(not Path(after["gpu_preflight"]).exists(),
                "C4_V2_PREFLIGHT_NAMESPACE_MUST_START_ABSENT")
    else:
        require(Path(after["gpu_preflight"]).is_dir(),
                "C4_V2_ACCEPTED_PREFLIGHT_NAMESPACE_REQUIRED")
    stage_io.STAGES["gpu_preflight"] = Path(after["gpu_preflight"])
    require({key: str(value.resolve()) for key, value in stage_io.STAGES.items()} == after,
            "C4_V2_BOUND_STAGE_PATHS")
    return before, after


def bound_stage_run(config, config_path, config_sha256, prebinding_paths):
    from scripts import empirical_scoring_stage_run as stage_run
    from scripts.empirical_scoring_jinja_binding_v2 import (
        active_binding, guard as jinja_guard, release_binding)
    from scripts.replay_roa_original import write_json

    original_class = stage_run.StageRun
    original_guard = stage_run.guard
    require(original_guard.__module__ == "scripts.empirical_scoring_stage_guard" and
            original_guard.__name__ == "guard", "C4_V2_ORIGINAL_GUARD_ALIAS")
    stage_run.guard = jinja_guard
    extra_paths = [Path(config_path).resolve(), *[verify_record(entry)
                   for entry in config["controls"]]]

    class V2StageRun(original_class):
        def __init__(self, root, stage, pins):
            require(stage == config["stage"], "C4_V2_STAGE_MATCH")
            super().__init__(root, stage, pins)
            self.paths = sorted(set(self.paths + extra_paths))
            self.c4_v2_prebinding_paths = len(prebinding_paths)
            self.c4_v2_original_guard = original_guard

        def finish(self, success_status=None, *, acceptance=None):
            binding = active_binding(self.boundary) if self.boundary is not None else None
            profile_active = bool(binding is not None and sys.getprofile() is binding.profile)
            if success_status is not None:
                require(profile_active, "C4_V2_PROFILE_ACTIVE_BEFORE_SUCCESS_FINALIZATION")
            before = copy.deepcopy(self.result)
            receipt = dict(
                status="PASS_DECLARED_C4_JINJA_EXECUTION_BINDING_V2" if
                    success_status is not None else "BOUND_C4_JINJA_EXECUTION_V2_WITH_STAGE_FAILURE",
                binding_config_sha256=config_sha256,
                stage=config["stage"],
                stage_paths_before=config["stage_paths_before"],
                stage_paths_after=config["stage_paths_after"],
                changed_globals=[
                    "scripts.empirical_scoring_stage_io.STAGES[gpu_preflight]",
                    "scripts.empirical_scoring_stage_run.guard",
                    config["entry_module"] + ".StageRun",
                ],
                original_scientific_entry_source_unchanged=True,
                original_stage_run_source_unchanged=True,
                original_guard_sources_unchanged=True,
                original_result_before_binding_sha256=canonical_hash(before),
                original_result_fields=list(before),
                active_profile_before_finalization=profile_active,
                prebinding_authenticated_paths=self.c4_v2_prebinding_paths,
                controls_added=[record(path) for path in extra_paths],
                jinja_execution_binding_v2=(copy.deepcopy(binding.stats)
                                            if binding is not None else None),
                fresh_outcome_access_authorized=False,
            )
            self.result["execution_binding_v2"] = receipt
            if self.out.exists():
                write_json(self.out / "EXECUTION_BINDING_V2.json", receipt)
            try:
                return super().finish(success_status, acceptance=acceptance)
            finally:
                if self.boundary is not None:
                    release_binding(self.boundary)

    return V2StageRun


def main(argv=None):
    args, config = parse_binding(argv)
    prebinding_paths = prebinding_input_checks(Path(config["project_root"]).resolve())
    apply_stage_paths(config)
    stage_class = bound_stage_run(config, args.config, args.config_sha256,
                                  prebinding_paths)
    module = __import__(config["entry_module"], fromlist=["main"])
    require(module.StageRun.__module__ == "scripts.empirical_scoring_stage_run" and
            module.StageRun.__name__ == "StageRun", "C4_V2_ORIGINAL_ENTRY_STAGE_RUN_ALIAS")
    module.StageRun = stage_class
    sys.argv = [str(Path(module.__file__).resolve()), *args.original_arguments]
    return module.main()


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
