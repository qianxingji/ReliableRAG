"""Run authenticated original reader/repair CPU fixtures without its old writer."""
import argparse
from pathlib import Path
import platform
import subprocess
import sys
import unittest

from scripts.empirical_retrieval_io import REPO, AUDIT, AUDIT_SHA, verify_namespace, configure_environment, import_file, seal
from scripts.empirical_pool_io import checked, load, record, require
from scripts.replay_roa_original import install_boundary, write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    root = p.parse_args().project_root.resolve()
    out = REPO / "outputs/cas_q2/empirical_runtime_native_tests_v1"
    require(not out.exists(), "Single-use native CPU fixture run")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    out.mkdir(parents=True, exist_ok=False)
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit, pretrained_model_load_calls=0,
                  pretrained_model_forward_calls=0, scientific_fit_calls=0, fresh_gold_values_materialized=0)
    try:
        configure_environment(out); platform.uname()._asdict()
        import torch
        import numpy
        paths = verify_namespace(AUDIT, AUDIT_SHA)
        audit = load(AUDIT / "ACQUISITION_INPUT_AUDIT.json")
        for e in audit["checked_files"]:
            path = Path(e["path"])
            if path.suffix in {".py", ".txt", ".json", ".yaml"}:
                paths.append(checked(path, e["sha256"], e["size_bytes"]))
        old = root / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
        mp = old / "SHA256_MANIFEST.json"
        entry = next(e for e in audit["checked_files"] if Path(e["path"]) == mp)
        checked(mp, entry["sha256"], entry["size_bytes"])
        item = next(e for e in load(mp)["files"] if e["path"].endswith("runtime_branch_freeze/test_runtime_v2.py"))
        test_source = checked(root / item["path"], item["sha256"], item["size_bytes"])
        paths += [test_source, Path(__file__), REPO / "docs/cas_q2/EMPIRICAL_C3_RUNTIME_CONTRACT.md"]
        bound = [record(p) for p in sorted(set(paths))]
        write_json(out / "CPU_TEST_FREEZE.json", dict(source_commit=commit, inputs=bound,
            scope="Original 22 invented CPU fixtures; original main/output writer never executed"))
        boundary = install_boundary(out)
        def no_benchmark_or_model(event, args):
            if event == "import" and (args[0] == "src" or args[0].startswith("src.")):
                raise RuntimeError("Original pipeline package import forbidden")
            if event == "open" and isinstance(args[0], (str, bytes)):
                path = Path(args[0]).resolve()
                if path.is_relative_to(root / "data") or (path.is_relative_to(root / "outputs") and path.suffix == ".jsonl"):
                    raise RuntimeError("Benchmark or model file forbidden in CPU fixtures")
        sys.addaudithook(no_benchmark_or_model)
        import_file("runtime_support", old / "runtime_support.py")
        import_file("native_runtime", old / "native_runtime.py")
        tests = import_file("empirical_original_runtime_cpu_fixtures", test_source)
        with (out / "CPU_TESTS.log").open("x", encoding="utf-8", newline="\n") as stream:
            run = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(tests.RuntimeTests))
        require(run.testsRun == 22 and run.wasSuccessful(), "Original runtime CPU fixtures failed")
        # No package/full-pipeline executors or old __main__ writers were run.
        require(not boundary["blocked"], "Native CPU fixture write boundary")
        result.update(status="PASS_ORIGINAL_RUNTIME_CPU_FIXTURES", tests_run=run.testsRun, errors=len(run.errors), failures=len(run.failures),
            accepted_native_ast_nodes=tests.RuntimeTests.nodes, generation_boundary=tests.RuntimeTests.boundary,
            fixture_scope="Invented CPU tensors and dummy model/tokenizer only; old 1500-ID replay fixture preserved, new 2000-ID rule tested separately",
            original_output_writers_executed=False, parser_behavior="Original cross-line whitespace regex preserved; no cleaner replacement parser")
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    write_json(out / "CPU_TEST_RESULT.json", result); seal(out)
    print(result["status"], result.get("diagnostic", "")); return 2 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
