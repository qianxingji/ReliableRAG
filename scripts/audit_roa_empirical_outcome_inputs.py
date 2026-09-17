"""Authenticate D sources and dependencies using metadata/opaque hashes only."""
import argparse
from pathlib import Path
import subprocess
import sys

from scripts.empirical_outcome_native import authenticate, native
from scripts.empirical_outcome_guard import guard
from scripts.empirical_pool_io import REPO, record, require
from scripts.empirical_retrieval_io import boundary_record, seal
from scripts.replay_roa_original import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = REPO / "outputs/cas_q2/empirical_outcome_input_audit_v1"
    require(not output.exists(), "Single-use outcome inventory")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit D inventory first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    source = [Path(__file__), REPO / "scripts/empirical_outcome_native.py", REPO / "scripts/empirical_outcome_guard.py",
        REPO / "docs/cas_q2/EMPIRICAL_D_EXECUTION_CONTRACT.md", Path(sys.executable)]
    initial = [record(p) for p in source]
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "EXECUTABLE_FREEZE.json", dict(source_commit=commit, command=sys.argv, inputs=initial,
        scope="D source inventory only; no selected answers or numeric outcomes decoded"))
    boundary = guard(root, output, source, mode="audit")
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit, scientific_fit_calls=0,
        neural_model_loads=0, model_forward_calls=0, fresh_gold_values_materialized=0, canonical_answers_decoded=0)
    try:
        spec, pre, paths, packages = authenticate(root)
        _, _, _, hashes = native(root, spec)
        records = [record(path) for path in paths]
        for entry in initial + records:
            require(record(Path(entry["path"])) == entry, "Unchanged outcome source inventory")
        require(not boundary["denied"] and boundary["forbidden_calls"] == 0, "Clean metadata-only inventory boundary")
        result.update(status="PASS_OUTCOME_SOURCE_INVENTORY_ONLY", checked_files=records, source_file_count=len(records),
            source_size_bytes=sum(e["size_bytes"] for e in records), arrow_package_files=packages,
            original_sources=spec["sources"], reference_policy=spec["reference_policy"], original_environment=pre["environment"],
            original_ast_definitions=hashes, all_source_bytes_unchanged=True,
            limitation="Does not execute Gold mapping, validate selected answers or authorize outcome analysis. Complete C4 prelabel acceptance is still required.")
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    finally:
        sys.setprofile(None)
    result["boundary"] = boundary_record(boundary)
    write_json(output / "OUTCOME_INPUT_AUDIT.json", result)
    seal(output)
    print(result["status"], result.get("diagnostic", ""), flush=True)
    return 2 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
