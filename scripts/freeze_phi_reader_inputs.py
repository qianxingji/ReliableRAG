"""Create the tokenizer-only Phi development/test input and runtime guard freeze."""
from __future__ import annotations

import argparse
import collections
import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.phi_reader_input_freeze_common import (
    CONTEXT_BUDGET_CHARACTERS, DATASETS, MAXIMUM_GENERATION_INPUT_TOKENS, OUT,
    PHI_RELATIVE, PHI_REVISION, REPO, RETRIEVERS, canonical, compact_document,
    configure_tokenizer_environment, digest, load, object_sha, prompt_ids, record,
    require, require_generation_admission, rows, seal, write_json,
)


EXPECTED = {
    "development_runtime_config": "9eb8f1fd4e0d7a6549bd1a78adf92f96fb5ab12c64d3cdaaa6f2fa39029c40c9",
    "development_traces": "723cefe8817f5ff07fa81b06d71f59d9f28fe37d5e6b62ff94184e20bcdcf8e3",
    "test_preparation_manifest": "7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258",
    "test_pool_manifest": "4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98",
    "roles": "40992a860943bc553fe9da6ad541181cb46958c56dc14a96621007449d0382ec",
    "preflight_manifest": "cfebd83ce688479af922e884ea0df6034af6e32fc2175c3fd3b5e69266e58d30",
    "preflight_validation_manifest": "ef11925bb631e47c22fd47ba0579edf138e708b4a1ee78bbe4527cb1f7fe291a",
}


def install_boundary(allowed: set[Path], snapshot: Path, output: Path) -> dict:
    receipt = {"denied": [], "weight_reads_denied": 0, "outside_reads_denied": 0, "outside_writes_denied": 0}
    allowed = {path.resolve() for path in allowed}
    snapshot, output = snapshot.resolve(), output.resolve()

    def hook(event, args):
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request", "subprocess.Popen", "os.system"}:
            raise RuntimeError("Phi input freeze network/process boundary")
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output):
                receipt["outside_writes_denied"] += 1; receipt["denied"].append(str(path)); raise RuntimeError("write outside input-freeze output")
            return
        if path.is_relative_to(snapshot) and path.suffix in {".safetensors", ".bin"}:
            receipt["weight_reads_denied"] += 1; receipt["denied"].append(str(path)); raise RuntimeError("model weight read forbidden")
        if path not in allowed and not path.is_relative_to(snapshot) and not path.is_relative_to(output):
            receipt["outside_reads_denied"] += 1; receipt["denied"].append(str(path)); raise RuntimeError(f"non-allowlisted input read: {path}")

    sys.addaudithook(hook)
    return receipt


def input_paths(original: Path) -> list[Path]:
    dev = original / "outputs/daa_v2_fresh_v1"
    test = REPO / "outputs/cas_q2"
    paths = [dev / "runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json", dev / "runtime_branch_freeze/trace_manifest.jsonl",
        test / "empirical_runtime_preparation_v1/TRACE_MANIFEST_PRIVATE.jsonl",
        test / "empirical_fixed_panel_v1/TRAINING_GROUPS_PRIVATE.jsonl",
        test / "empirical_runtime_preparation_v1/SHA256_MANIFEST.json", test / "empirical_candidate_pool_v2/SHA256_MANIFEST.json",
        test / "phi_reader_gpu_preflight_v1/SHA256_MANIFEST.json", test / "phi_reader_gpu_preflight_validation_v2/SHA256_MANIFEST.json",
        original / "prompts/baseline_v1.txt", original / "prompts/repair_missing_v1.txt",
        REPO / "scripts/phi_reader_input_freeze_common.py", REPO / "scripts/freeze_phi_reader_inputs.py",
        REPO / "tests/test_phi_reader_input_freeze.py", REPO / "docs/cas_q2/PHI_READER_INPUT_FREEZE_CONTRACT.md",
        REPO / "docs/cas_q2/PHI_READER_PREFLIGHT_RESULTS.json", Path(sys.executable)]
    for dataset in DATASETS:
        paths += [dev / "pool_freeze/pools" / f"{dataset}_documents.jsonl",
            dev / "pool_freeze/runtime_projection" / f"{dataset}_selected_runtime.jsonl",
            test / "empirical_candidate_pool_v2/pools" / f"{dataset}.jsonl",
            test / "empirical_candidate_pool_v2/runtime" / f"{dataset}.jsonl"]
    return paths


def sources(original: Path) -> tuple[list[dict], list[dict], dict]:
    dev = original / "outputs/daa_v2_fresh_v1"
    test = REPO / "outputs/cas_q2"
    dev_cfg_path = dev / "runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json"
    dev_trace_path = dev / "runtime_branch_freeze/trace_manifest.jsonl"
    test_trace_path = test / "empirical_runtime_preparation_v1/TRACE_MANIFEST_PRIVATE.jsonl"
    roles_path = test / "empirical_fixed_panel_v1/TRAINING_GROUPS_PRIVATE.jsonl"
    require(digest(dev_cfg_path) == EXPECTED["development_runtime_config"], "development config pin")
    require(digest(dev_trace_path) == EXPECTED["development_traces"], "development trace pin")
    require(digest(test / "empirical_runtime_preparation_v1/SHA256_MANIFEST.json") == EXPECTED["test_preparation_manifest"], "test preparation pin")
    require(digest(test / "empirical_candidate_pool_v2/SHA256_MANIFEST.json") == EXPECTED["test_pool_manifest"], "test pool pin")
    require(digest(roles_path) == EXPECTED["roles"], "development role pin")
    require(digest(test / "phi_reader_gpu_preflight_v1/SHA256_MANIFEST.json") == EXPECTED["preflight_manifest"], "Phi preflight pin")
    require(digest(test / "phi_reader_gpu_preflight_validation_v2/SHA256_MANIFEST.json") == EXPECTED["preflight_validation_manifest"], "Phi preflight validator pin")
    dev_traces, test_traces = list(rows(dev_trace_path)), list(rows(test_trace_path))
    roles = {(row["dataset"], row["sample_id"]): row["role"] for row in rows(roles_path)}
    require(len(roles) == 4500 and collections.Counter(roles.values()) == {"fit": 3600, "cal": 900}, "fixed development roles")
    return dev_traces, test_traces, roles


def load_label_free_assets(original: Path, cohort: str) -> dict:
    if cohort == "development":
        base = original / "outputs/daa_v2_fresh_v1/pool_freeze"
        pool_name = lambda d: base / "pools" / f"{d}_documents.jsonl"
        runtime_name = lambda d: base / "runtime_projection" / f"{d}_selected_runtime.jsonl"
        bindings = load(original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json")["parents"]["older_parents"]["datasets"]
    else:
        base = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
        pool_name = lambda d: base / "pools" / f"{d}.jsonl"
        runtime_name = lambda d: base / "runtime" / f"{d}.jsonl"
        entries = {row["path"]: row for row in load(base / "SHA256_MANIFEST.json")["files"]}
    result = {}
    for dataset in DATASETS:
        pp, rp = pool_name(dataset), runtime_name(dataset)
        if cohort == "development":
            require(digest(pp) == bindings[dataset]["pool_sha256"] and digest(rp) == bindings[dataset]["runtime_projection_sha256"],
                "accepted development label-free assets")
        else:
            for path in (pp, rp):
                relative = path.relative_to(base).as_posix(); expected = entries[relative]
                require(record(path) == {"path": str(path.resolve()), "size_bytes": expected["size_bytes"], "sha256": expected["sha256"]},
                    "accepted test label-free assets")
        documents = {row["id"]: row for row in rows(pp)}
        questions = {row["id"]: row["question"] for row in rows(rp)}
        require(len(documents) == len(set(documents)) and len(questions) == len(set(questions)), "unique label-free assets")
        result[dataset] = {"documents": documents, "questions": questions}
    return result


def validate_trace_set(traces: list[dict], expected: int, groups: int) -> None:
    keys = [(row["dataset"], row["retriever"], row["sample_id"]) for row in traces]
    require(len(traces) == expected == len(set(keys)), "trace count/uniqueness")
    require([row["position"] for row in traces] == list(range(expected)), "canonical trace positions")
    require(set(row["dataset"] for row in traces) == set(DATASETS) and set(row["retriever"] for row in traces) == set(RETRIEVERS), "trace strata")
    require(len({(row["dataset"], row["sample_id"]) for row in traces}) == groups, "question groups")
    counts = collections.Counter((row["dataset"], row["retriever"]) for row in traces)
    require(set(counts.values()) == {groups // 3}, "balanced trace strata")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-root", type=Path, required=True); args = parser.parse_args()
    original = args.project_root.resolve()
    require(not OUT.exists(), "single-use Phi input-freeze namespace")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "commit Phi input freeze first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    OUT.mkdir(parents=True, exist_ok=False); configure_tokenizer_environment(OUT)
    from transformers import AutoTokenizer

    result = {"status": "FAIL", "cas_q2_status": "NOT READY", "source_commit": commit, "model_loads": 0,
        "model_forward_calls": 0, "generation_calls": 0, "scientific_fit_calls": 0, "gold_reads": 0,
        "existing_answer_strings_read": 0, "prompt_tokenizations": 0}
    boundary = None
    try:
        paths = input_paths(original)
        snapshot = original / PHI_RELATIVE
        allowed = set(path.resolve() for path in paths)
        allowed.update(path.resolve() for path in snapshot.iterdir() if path.is_file() and path.suffix not in {".safetensors", ".bin"})
        boundary = install_boundary(allowed, snapshot, OUT)
        input_records = [record(path) for path in sorted(allowed)]
        dev_traces, test_traces, roles = sources(original)
        validate_trace_set(dev_traces, 13500, 4500); validate_trace_set(test_traces, 18000, 6000)
        development = load_label_free_assets(original, "development")
        test = load_label_free_assets(original, "test")
        answer_path, repair_path = original / "prompts/baseline_v1.txt", original / "prompts/repair_missing_v1.txt"
        tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True, trust_remote_code=False)
        answer_template = answer_path.read_text(encoding="utf-8"); repair_template = repair_path.read_text(encoding="utf-8")
        ledger = OUT / "INPUT_LENGTHS_PRIVATE.jsonl"
        aggregates = collections.defaultdict(lambda: {"rows": 0, "answer_max": 0, "repair_query_max": 0, "context_truncated": 0})
        maximum = {"input_tokens": -1}
        with ledger.open("xb") as stream:
            for cohort, traces, assets in (("development", dev_traces, development), ("test", test_traces, test)):
                for trace in traces:
                    dataset, retriever, sid = trace["dataset"], trace["retriever"], trace["sample_id"]
                    asset = assets[dataset]; require(sid in asset["questions"], "question membership")
                    evidence = [compact_document(asset["documents"][doc_id], rank) for rank, doc_id in enumerate(trace["original_top5_ids"], 1)]
                    answer_ids, answer = prompt_ids(tokenizer, answer_template, asset["questions"][sid], evidence)
                    repair_ids, repair = prompt_ids(tokenizer, repair_template, asset["questions"][sid], evidence)
                    require_generation_admission(stage="a0", input_ids=[answer_ids], attention_mask=[[1] * len(answer_ids)])
                    require_generation_admission(stage="repair_query", input_ids=[repair_ids], attention_mask=[[1] * len(repair_ids)])
                    role = roles[(dataset, sid)] if cohort == "development" else "test"
                    row = {"cohort": cohort, "dataset": dataset, "retriever": retriever, "sample_id": sid,
                        "position": trace["position"], "role": role, "original_top5_ids_sha256": object_sha(trace["original_top5_ids"]),
                        "answer": answer, "repair_query": repair}
                    stream.write(canonical(row) + b"\n")
                    group = aggregates[(cohort, dataset, retriever)]; group["rows"] += 1
                    group["answer_max"] = max(group["answer_max"], answer["input_tokens"])
                    group["repair_query_max"] = max(group["repair_query_max"], repair["input_tokens"])
                    group["context_truncated"] += int(answer["context_truncated"])
                    for stage, metadata in (("a0", answer), ("repair_query", repair)):
                        if metadata["input_tokens"] > maximum["input_tokens"]:
                            maximum = {"cohort": cohort, "dataset": dataset, "retriever": retriever, "sample_id": sid,
                                "position": trace["position"], "stage": stage, "input_tokens": metadata["input_tokens"],
                                "prompt_sha256": metadata["prompt_sha256"]}
                    result["prompt_tokenizations"] += 2
        require(result["prompt_tokenizations"] == 63000 and maximum["input_tokens"] <= MAXIMUM_GENERATION_INPUT_TOKENS, "complete safe deterministic prompts")
        require(not boundary["denied"], "input-freeze boundary denial")
        aggregate_rows = [dict(cohort=k[0], dataset=k[1], retriever=k[2], **v) for k, v in sorted(aggregates.items())]
        write_json(OUT / "EXECUTABLE_FREEZE.json", {"source_commit": commit, "inputs": input_records,
            "reader_revision": PHI_REVISION, "context_budget_characters": CONTEXT_BUDGET_CHARACTERS,
            "maximum_generation_input_tokens": MAXIMUM_GENERATION_INPUT_TOKENS, "batch_size": 1,
            "concurrent_reader_instances": 1, "dynamic_a1_admission_required_before_cuda": True,
            "development_traces": 13500, "test_traces": 18000, "planned_logical_generations": 94500})
        result.update(status="PASS_VALUE_BLIND_PHI_INPUT_FREEZE_PENDING_INDEPENDENT", deterministic_prompt_rows=31500,
            development_traces=13500, test_traces=18000, development_fit_questions=3600,
            development_calibration_questions=900, test_questions=6000, maximum=maximum, aggregates=aggregate_rows,
            dynamic_a1_pretoken_guard_frozen=True, maximum_generation_input_tokens=MAXIMUM_GENERATION_INPUT_TOKENS,
            batch_size=1, concurrent_reader_instances=1, execution_boundary=boundary)
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
        if boundary is not None: result["execution_boundary"] = boundary
    write_json(OUT / "BUILD_RECEIPT.json", result); seal(OUT)
    print(result["status"], result.get("maximum"), flush=True)
    return 0 if result["status"].startswith("PASS_") else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
