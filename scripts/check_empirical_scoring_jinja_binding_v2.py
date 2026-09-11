"""Single-use CPU gate for the prospective C4 Jinja execution binding V2."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
ROOT = Path(r"E:\paper\ReliableRAG")
RUNTIME_SHA256 = "dc2905224798b07302db8950f68db228de1faff9042c44dbaee7111ba107878f"
V1_SHA256 = "c03555a4a3562be34345bd79b35abb11c8b6bb913a4c812e24837cfb8c88f3b6"
AUDIT_SHA256 = "cbb9911c17c7c1b3f65f31d36b79814383bbba42a4cf4477b483ab1d9b2efc13"
INVENTORY_SHA256 = "a5b0adfe38b349de69afe422e5fb6731b88d2e213a80c7107c34d42e231c3146"


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


def verify(entry):
    path = Path(entry["path"]).resolve()
    require(record(path) == {**entry, "path": str(path)},
            "C4_V2_FIXTURE_INPUT_CHANGED")
    return path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def verify_namespace(root, expected):
    manifest = root / "SHA256_MANIFEST.json"
    require(sha(manifest) == expected, "C4_V2_FIXTURE_NAMESPACE_PIN")
    data = load(manifest)
    wanted = {"SHA256_MANIFEST.json"}
    for item in data["files"]:
        path = root / item["path"]
        verify({**item, "path": str(path)})
        wanted.add(item["path"])
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*")
              if path.is_file()}
    require(actual == wanted, "C4_V2_FIXTURE_NAMESPACE_CHANGED")
    return len(data["files"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args()
    out = args.config.resolve().parent
    require(not (out / "FIXTURE_RESULT.json").exists(), "C4_V2_SINGLE_USE_FIXTURE")
    raw = args.config.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == args.config_sha256,
            "C4_V2_FIXTURE_CONFIG_PIN")
    config = json.loads(raw)
    require(set(config) == {"version", "source_commit", "controls",
                            "environment_inventory", "failure_audit_manifest",
                            "command"} and config["version"] == 1,
            "C4_V2_FIXTURE_CONFIG_SCHEMA")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                     text=True).strip()
    require(commit == config["source_commit"] and not subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True).strip(),
        "C4_V2_FIXTURE_CLEAN_COMMIT")
    controls = [verify(item) for item in config["controls"]]
    inventory_path = verify(config["environment_inventory"])
    require(config["environment_inventory"]["sha256"] == INVENTORY_SHA256,
            "C4_V2_FIXTURE_INVENTORY_PIN")
    audit_manifest = verify(config["failure_audit_manifest"])
    require(config["failure_audit_manifest"]["sha256"] == AUDIT_SHA256,
            "C4_V2_FIXTURE_FAILURE_AUDIT_PIN")
    runtime_files = verify_namespace(REPO / "outputs/cas_q2/empirical_runtime_v1",
                                     RUNTIME_SHA256)
    v1_files = verify_namespace(REPO / "outputs/cas_q2/empirical_scoring_gpu_preflight_v1",
                                V1_SHA256)
    inventory = load(inventory_path)
    for item in inventory["files"]:
        verify(item)
    before = {str(path): record(path) for path in controls}
    command = [str(ROOT / ".venv/Scripts/python.exe"), "-B", "-X", "utf8",
               "-m", "unittest", "discover", "-s", "tests", "-p",
               "test_empirical*.py", "-v"]
    require(config["command"] == command, "C4_V2_FIXTURE_COMMAND")
    environment = os.environ.copy()
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
                       CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                       TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    run = subprocess.run(command, cwd=REPO, env=environment, capture_output=True)
    with (out / "UNITTEST_STDOUT.log").open("xb") as stream:
        stream.write(run.stdout)
    with (out / "UNITTEST_STDERR.log").open("xb") as stream:
        stream.write(run.stderr)
    stdout = run.stdout.decode("utf-8", errors="strict")
    stderr = run.stderr.decode("utf-8", errors="strict")
    require(run.returncode == 0 and stderr.rstrip().endswith("OK"),
            "C4_V2_FIXTURE_TESTS_FAILED\n" + stdout + "\n" + stderr)
    match = re.search(r"Ran (\d+) tests", stderr)
    require(match is not None, "C4_V2_FIXTURE_TEST_COUNT")
    after = {str(path): record(path) for path in controls}
    require(before == after, "C4_V2_FIXTURE_CONTROLS_CHANGED")
    for item in inventory["files"]:
        verify(item)
    require(sha(audit_manifest) == AUDIT_SHA256 and
            sha(REPO / "outputs/cas_q2/empirical_runtime_v1/SHA256_MANIFEST.json") == RUNTIME_SHA256 and
            sha(REPO / "outputs/cas_q2/empirical_scoring_gpu_preflight_v1/SHA256_MANIFEST.json") == V1_SHA256,
            "C4_V2_FIXTURE_PREDECESSOR_CHANGED")
    result = dict(
        status="PASS_C4_JINJA_EXECUTION_BINDING_V2_CPU_ONLY",
        cas_q2_status="NOT READY",
        source_commit=commit,
        unit_tests=int(match.group(1)),
        test_process_exit_code=run.returncode,
        test_stdout=stdout,
        test_stderr=stderr,
        raw_test_stdout=record(out / "UNITTEST_STDOUT.log"),
        raw_test_stderr=record(out / "UNITTEST_STDERR.log"),
        controls_unchanged=len(controls),
        environment_files_rehashed_before_and_after=len(inventory["files"]),
        c3_runtime_files_reverified=runtime_files,
        v1_failed_preflight_files_reverified=v1_files,
        v1_failure_manifest_sha256=V1_SHA256,
        v1_failure_audit_manifest_sha256=AUDIT_SHA256,
        exact_jinja_source_and_code_identity_checked=True,
        real_qwen_tokenizer_template_equivalence_checked=True,
        negative_cases_use_fresh_processes=True,
        model_weight_load_calls=0,
        model_forward_calls=0,
        scientific_fit_calls=0,
        current_benchmark_payload_reads=0,
        fresh_gold_values_materialized=0,
        v2_gpu_preflight_executed=False,
        limitation="CPU engineering/identity gate only; no neural scoring or fresh result acceptance.",
    )
    write(out / "FIXTURE_RESULT.json", result)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
