"""Freeze exact label-free development/test prompts for the Mistral reader."""

from __future__ import annotations

import argparse
import collections
import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.mistral_reader_input_freeze_common import (
    CONTEXT_BUDGET_CHARACTERS,
    DATASETS,
    MAXIMUM_GENERATION_INPUT_TOKENS,
    OUT,
    REPO,
    RETRIEVERS,
    REVISION,
    canonical,
    compact_document,
    configure_tokenizer_environment,
    digest,
    load,
    object_sha,
    prompt_metadata,
    record,
    require,
    require_generation_admission,
    rows,
    seal,
    write_json,
)


EXPECTED = {
    "development_runtime_config": "9eb8f1fd4e0d7a6549bd1a78adf92f96fb5ab12c64d3cdaaa6f2fa39029c40c9",
    "development_traces": "723cefe8817f5ff07fa81b06d71f59d9f28fe37d5e6b62ff94184e20bcdcf8e3",
    "test_preparation_manifest": "7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258",
    "test_trace": "87d5aff0bc77da76624b541326c523d41b00fa6c84ecefd4d6a050de66b25a29",
    "test_pool_manifest": "4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98",
    "roles": "40992a860943bc553fe9da6ad541181cb46958c56dc14a96621007449d0382ec",
    "asset_manifest": "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18",
    "tokenizer_report": "47f3f2f04ed324e7be8051a594224bfdca8fc244133c14d5aeef028db24d1b5a",
    "tokenizer_json": "e553af6fff7d7ad76e830608b218c5c0b0822998d5a1a96099a74cd3c1cb1a49",
    "tokenizer_config": "0533dec9cfe319163801b6618d0f3ec9cfa126b6288e3df5deca6e32acb09cd2",
}


def install_boundary(
    allowed: set[Path], output: Path, environment_roots: tuple[Path, ...],
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "denied": [],
        "environment_reads": set(),
        "weight_reads_denied": 0,
        "outside_reads_denied": 0,
        "outside_writes_denied": 0,
        "network_or_process_denied": 0,
    }
    allowed = {path.resolve() for path in allowed}
    output = output.resolve()
    environment_roots = tuple(path.resolve() for path in environment_roots)

    def hook(event, args):
        if event in {
            "socket.connect", "socket.bind", "socket.getaddrinfo",
            "urllib.Request", "subprocess.Popen", "os.system",
        }:
            receipt["network_or_process_denied"] += 1
            raise RuntimeError("MISTRAL_INPUT_FREEZE_NETWORK_PROCESS_BOUNDARY")
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode = args[1] if len(args) > 1 else "r"
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        writing = (
            isinstance(mode, str) and any(character in mode for character in "wax+")
        ) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output):
                receipt["outside_writes_denied"] += 1
                receipt["denied"].append(str(path))
                raise RuntimeError("MISTRAL_INPUT_FREEZE_WRITE_OUTSIDE_OUTPUT")
            return
        if path.suffix.casefold() in {".safetensors", ".bin", ".pt", ".pth", ".ckpt"}:
            receipt["weight_reads_denied"] += 1
            receipt["denied"].append(str(path))
            raise RuntimeError("MISTRAL_INPUT_FREEZE_MODEL_WEIGHT_READ")
        if any(path.is_relative_to(root) for root in environment_roots):
            receipt["environment_reads"].add(str(path))
            return
        if path not in allowed and not path.is_relative_to(output):
            receipt["outside_reads_denied"] += 1
            receipt["denied"].append(str(path))
            raise RuntimeError("MISTRAL_INPUT_FREEZE_NON_ALLOWLISTED_READ:" + str(path))

    sys.addaudithook(hook)
    return receipt


def input_paths(original: Path, asset: Path) -> list[Path]:
    development = original / "outputs/daa_v2_fresh_v1"
    test = REPO / "outputs/cas_q2"
    paths = [
        development / "runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json",
        development / "runtime_branch_freeze/trace_manifest.jsonl",
        test / "empirical_runtime_preparation_v1/TRACE_MANIFEST_PRIVATE.jsonl",
        test / "empirical_runtime_preparation_v1/SHA256_MANIFEST.json",
        test / "empirical_fixed_panel_v1/TRAINING_GROUPS_PRIVATE.jsonl",
        test / "empirical_candidate_pool_v2/SHA256_MANIFEST.json",
        original / "prompts/baseline_v1.txt",
        original / "prompts/repair_missing_v1.txt",
        asset / "ASSET_MANIFEST.json",
        asset / "config.json",
        asset / "special_tokens_map.json",
        asset / "tokenizer.json",
        asset / "tokenizer.model",
        asset / "tokenizer.model.v3",
        asset / "tokenizer_config.json",
        REPO / "docs/cas_q3/MISTRAL_TOKENIZER_PREFLIGHT_2026-09-17.json",
        REPO / "docs/cas_q3/MISTRAL_READER_INPUT_FREEZE_PROTOCOL_2026-09-17.md",
        REPO / "scripts/mistral_reader_input_freeze_common.py",
        REPO / "scripts/freeze_mistral_reader_inputs.py",
        REPO / "scripts/validate_mistral_reader_inputs.py",
        REPO / "tests/test_mistral_reader_input_freeze.py",
        Path(sys.executable),
    ]
    for dataset in DATASETS:
        paths.extend([
            development / "pool_freeze/pools" / f"{dataset}_documents.jsonl",
            development / "pool_freeze/runtime_projection" / f"{dataset}_selected_runtime.jsonl",
            test / "empirical_candidate_pool_v2/pools" / f"{dataset}.jsonl",
            test / "empirical_candidate_pool_v2/runtime" / f"{dataset}.jsonl",
        ])
    return paths


def load_sources(original: Path) -> tuple[list[dict], list[dict], dict[tuple[str, str], str]]:
    development = original / "outputs/daa_v2_fresh_v1"
    test = REPO / "outputs/cas_q2"
    development_config = development / "runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json"
    development_traces = development / "runtime_branch_freeze/trace_manifest.jsonl"
    test_traces = test / "empirical_runtime_preparation_v1/TRACE_MANIFEST_PRIVATE.jsonl"
    roles_path = test / "empirical_fixed_panel_v1/TRAINING_GROUPS_PRIVATE.jsonl"
    require(digest(development_config) == EXPECTED["development_runtime_config"],
            "DEVELOPMENT_CONFIG_PIN")
    require(digest(development_traces) == EXPECTED["development_traces"],
            "DEVELOPMENT_TRACE_PIN")
    require(digest(test / "empirical_runtime_preparation_v1/SHA256_MANIFEST.json") ==
            EXPECTED["test_preparation_manifest"], "TEST_PREPARATION_MANIFEST_PIN")
    require(digest(test_traces) == EXPECTED["test_trace"], "TEST_TRACE_PIN")
    require(digest(test / "empirical_candidate_pool_v2/SHA256_MANIFEST.json") ==
            EXPECTED["test_pool_manifest"], "TEST_POOL_MANIFEST_PIN")
    require(digest(roles_path) == EXPECTED["roles"], "ROLE_PIN")
    development_rows = list(rows(development_traces))
    test_rows = list(rows(test_traces))
    roles = {
        (row["dataset"], row["sample_id"]): row["role"] for row in rows(roles_path)
    }
    require(len(roles) == 4500, "DEVELOPMENT_ROLE_GROUP_COUNT")
    require(collections.Counter(roles.values()) == {"fit": 3600, "cal": 900},
            "DEVELOPMENT_ROLE_COUNTS")
    return development_rows, test_rows, roles


def load_label_free_assets(original: Path, cohort: str) -> dict[str, dict[str, object]]:
    if cohort == "development":
        base = original / "outputs/daa_v2_fresh_v1/pool_freeze"
        pool_path = lambda dataset: base / "pools" / f"{dataset}_documents.jsonl"
        runtime_path = lambda dataset: base / "runtime_projection" / f"{dataset}_selected_runtime.jsonl"
        bindings = load(
            original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json"
        )["parents"]["older_parents"]["datasets"]
    else:
        base = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
        pool_path = lambda dataset: base / "pools" / f"{dataset}.jsonl"
        runtime_path = lambda dataset: base / "runtime" / f"{dataset}.jsonl"
        manifest = {row["path"]: row for row in load(base / "SHA256_MANIFEST.json")["files"]}
    result: dict[str, dict[str, object]] = {}
    for dataset in DATASETS:
        pool = pool_path(dataset)
        runtime = runtime_path(dataset)
        if cohort == "development":
            require(digest(pool) == bindings[dataset]["pool_sha256"],
                    "DEVELOPMENT_POOL_PIN:" + dataset)
            require(digest(runtime) == bindings[dataset]["runtime_projection_sha256"],
                    "DEVELOPMENT_RUNTIME_PIN:" + dataset)
        else:
            for path in (pool, runtime):
                relative = path.relative_to(base).as_posix()
                expected = manifest[relative]
                actual = record(path)
                require(actual["size_bytes"] == expected["size_bytes"] and
                        actual["sha256"] == expected["sha256"],
                        "TEST_LABEL_FREE_ASSET_PIN:" + relative)
        documents = {row["id"]: row for row in rows(pool)}
        questions = {row["id"]: row["question"] for row in rows(runtime)}
        require(len(documents) == len(set(documents)), "UNIQUE_DOCUMENTS:" + dataset)
        require(len(questions) == len(set(questions)), "UNIQUE_QUESTIONS:" + dataset)
        result[dataset] = {"documents": documents, "questions": questions}
    return result


def validate_trace_set(traces: list[dict], expected: int, groups: int) -> None:
    keys = [(row["dataset"], row["retriever"], row["sample_id"]) for row in traces]
    require(len(traces) == expected == len(set(keys)), "TRACE_COUNT_AND_UNIQUENESS")
    require([row["position"] for row in traces] == list(range(expected)),
            "CANONICAL_TRACE_POSITIONS")
    require(set(row["dataset"] for row in traces) == set(DATASETS), "TRACE_DATASETS")
    require(set(row["retriever"] for row in traces) == set(RETRIEVERS), "TRACE_RETRIEVERS")
    require(len({(row["dataset"], row["sample_id"]) for row in traces}) == groups,
            "TRACE_GROUP_COUNT")
    counts = collections.Counter((row["dataset"], row["retriever"]) for row in traces)
    require(set(counts.values()) == {groups // 3}, "BALANCED_TRACE_STRATA")


def compact_boundary(boundary: dict[str, object]) -> dict[str, object]:
    return {
        key: (len(value) if key == "environment_reads" else value)
        for key, value in boundary.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    args = parser.parse_args()
    original = args.project_root.resolve()
    asset = args.asset.resolve()
    overlay = args.overlay.resolve()
    require(not OUT.exists(), "SINGLE_USE_MISTRAL_INPUT_FREEZE_NAMESPACE")
    require(not subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True
    ).strip(), "COMMIT_MISTRAL_INPUT_FREEZE_BEFORE_RUN")
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    require(asset.is_dir() and overlay.is_dir(), "ASSET_AND_OVERLAY_ROOTS")
    require(digest(asset / "ASSET_MANIFEST.json") == EXPECTED["asset_manifest"],
            "ASSET_MANIFEST_PIN")
    require(digest(REPO / "docs/cas_q3/MISTRAL_TOKENIZER_PREFLIGHT_2026-09-17.json") ==
            EXPECTED["tokenizer_report"], "TOKENIZER_REPORT_PIN")
    require(digest(asset / "tokenizer.json") == EXPECTED["tokenizer_json"],
            "TOKENIZER_JSON_PIN")
    require(digest(asset / "tokenizer_config.json") == EXPECTED["tokenizer_config"],
            "TOKENIZER_CONFIG_PIN")

    OUT.mkdir(parents=True, exist_ok=False)
    configure_tokenizer_environment(OUT)
    from transformers import AutoTokenizer

    result: dict[str, object] = {
        "status": "FAIL",
        "cas_q3_status": "NOT READY",
        "source_commit": source_commit,
        "model_loads": 0,
        "model_forward_calls": 0,
        "generation_calls": 0,
        "scientific_fit_calls": 0,
        "gold_reads": 0,
        "existing_answer_strings_read": 0,
        "prompt_tokenizations": 0,
    }
    boundary = None
    try:
        paths = input_paths(original, asset)
        require(all(path.is_file() for path in paths), "ALL_ALLOWLISTED_INPUTS_EXIST")
        allowed = {path.resolve() for path in paths}
        boundary = install_boundary(
            allowed,
            OUT,
            (Path(sys.prefix), Path(sys.base_prefix), overlay),
        )
        input_records = [record(path) for path in sorted(allowed)]
        development_traces, test_traces, roles = load_sources(original)
        validate_trace_set(development_traces, 13500, 4500)
        validate_trace_set(test_traces, 18000, 6000)
        development_assets = load_label_free_assets(original, "development")
        test_assets = load_label_free_assets(original, "test")
        answer_path = original / "prompts/baseline_v1.txt"
        repair_path = original / "prompts/repair_missing_v1.txt"
        tokenizer = AutoTokenizer.from_pretrained(
            asset, use_fast=True, legacy=False, local_files_only=True,
            trust_remote_code=False,
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        require(type(tokenizer).__name__ == "LlamaTokenizerFast", "TOKENIZER_CLASS")
        require(tokenizer.pad_token_id == tokenizer.eos_token_id == 2, "TOKENIZER_PAD_EOS")
        answer_template = answer_path.read_text(encoding="utf-8")
        repair_template = repair_path.read_text(encoding="utf-8")
        aggregates = collections.defaultdict(
            lambda: {"rows": 0, "answer_max": 0, "repair_query_max": 0,
                     "context_truncated": 0}
        )
        maximum: dict[str, object] = {"input_tokens": -1}
        ledger = OUT / "INPUT_LENGTHS_PRIVATE.jsonl"
        with ledger.open("xb") as handle:
            for cohort, traces, assets in (
                ("development", development_traces, development_assets),
                ("test", test_traces, test_assets),
            ):
                for trace in traces:
                    dataset = trace["dataset"]
                    retriever = trace["retriever"]
                    sample_id = trace["sample_id"]
                    asset_rows = assets[dataset]
                    require(sample_id in asset_rows["questions"], "QUESTION_MEMBERSHIP")
                    evidence = [
                        compact_document(asset_rows["documents"][document_id], rank)
                        for rank, document_id in enumerate(trace["original_top5_ids"], 1)
                    ]
                    answer = prompt_metadata(
                        tokenizer, answer_template, asset_rows["questions"][sample_id], evidence
                    )
                    repair = prompt_metadata(
                        tokenizer, repair_template, asset_rows["questions"][sample_id], evidence
                    )
                    require_generation_admission(
                        stage="a0",
                        input_ids=[[1] * int(answer["input_tokens"])],
                        attention_mask=[[1] * int(answer["input_tokens"])],
                    )
                    require_generation_admission(
                        stage="repair_query",
                        input_ids=[[1] * int(repair["input_tokens"])],
                        attention_mask=[[1] * int(repair["input_tokens"])],
                    )
                    role = roles[(dataset, sample_id)] if cohort == "development" else "test"
                    row = {
                        "cohort": cohort,
                        "dataset": dataset,
                        "retriever": retriever,
                        "sample_id": sample_id,
                        "position": trace["position"],
                        "role": role,
                        "original_top5_ids_sha256": object_sha(trace["original_top5_ids"]),
                        "answer": answer,
                        "repair_query": repair,
                    }
                    handle.write(canonical(row) + b"\n")
                    group = aggregates[(cohort, dataset, retriever)]
                    group["rows"] += 1
                    group["answer_max"] = max(group["answer_max"], answer["input_tokens"])
                    group["repair_query_max"] = max(
                        group["repair_query_max"], repair["input_tokens"]
                    )
                    group["context_truncated"] += int(answer["context_truncated"])
                    require(answer["context_truncated"] == repair["context_truncated"],
                            "TEMPLATE_CONTEXT_TRUNCATION_MATCH")
                    for stage, metadata in (("a0", answer), ("repair_query", repair)):
                        if metadata["input_tokens"] > maximum["input_tokens"]:
                            maximum = {
                                "cohort": cohort,
                                "dataset": dataset,
                                "retriever": retriever,
                                "sample_id": sample_id,
                                "position": trace["position"],
                                "stage": stage,
                                "input_tokens": metadata["input_tokens"],
                                "prompt_sha256": metadata["prompt_sha256"],
                                "input_token_ids_sha256": metadata["input_token_ids_sha256"],
                            }
                    result["prompt_tokenizations"] += 2
        require(result["prompt_tokenizations"] == 63000,
                "COMPLETE_DETERMINISTIC_PROMPT_TOKENIZATIONS")
        require(maximum["input_tokens"] <= MAXIMUM_GENERATION_INPUT_TOKENS,
                "MAXIMUM_WITHIN_GENERATION_GUARD")
        require(sum(group["context_truncated"] for group in aggregates.values()) == 0,
                "NO_CONTEXT_TRUNCATION")
        require(not boundary["denied"], "NO_BOUNDARY_DENIALS")
        environment_records = [
            record(Path(path)) for path in sorted(boundary["environment_reads"])
            if Path(path).is_file()
        ]
        aggregate_rows = [
            dict(cohort=key[0], dataset=key[1], retriever=key[2], **value)
            for key, value in sorted(aggregates.items())
        ]
        write_json(OUT / "EXECUTABLE_FREEZE.json", {
            "source_commit": source_commit,
            "inputs": input_records,
            "reader_repo_id": "mistralai/Mistral-7B-Instruct-v0.3",
            "reader_revision": REVISION,
            "tokenizer_class": type(tokenizer).__name__,
            "use_fast": True,
            "legacy": False,
            "add_special_tokens_after_chat_template": False,
            "context_budget_characters": CONTEXT_BUDGET_CHARACTERS,
            "maximum_generation_input_tokens": MAXIMUM_GENERATION_INPUT_TOKENS,
            "batch_size": 1,
            "concurrent_reader_instances": 1,
            "dynamic_a1_admission_required_before_cuda": True,
            "development_traces": 13500,
            "test_traces": 18000,
            "planned_logical_generations": 94500,
            "environment_inputs_actually_read": environment_records,
        })
        result.update({
            "status": "PASS_VALUE_BLIND_MISTRAL_INPUT_FREEZE_PENDING_INDEPENDENT",
            "deterministic_prompt_rows": 31500,
            "development_traces": 13500,
            "test_traces": 18000,
            "development_fit_questions": 3600,
            "development_calibration_questions": 900,
            "test_questions": 6000,
            "maximum": maximum,
            "aggregates": aggregate_rows,
            "dynamic_a1_pretoken_guard_frozen": True,
            "maximum_generation_input_tokens": MAXIMUM_GENERATION_INPUT_TOKENS,
            "batch_size": 1,
            "concurrent_reader_instances": 1,
            "execution_boundary": compact_boundary(boundary),
            "environment_files_actually_read": len(environment_records),
            "source_chain": "DIRECT_ACCEPTED_QWEN_DEVELOPMENT_AND_TEST_INPUTS_NO_PHI_ARTIFACTS",
        })
    except Exception as error:
        result.update({"error_type": type(error).__name__, "diagnostic": str(error)})
        if boundary is not None:
            result["execution_boundary"] = compact_boundary(boundary)
    write_json(OUT / "BUILD_RECEIPT.json", result)
    seal(OUT)
    print(json.dumps({"status": result["status"], "maximum": result.get("maximum")}))
    return 0 if str(result["status"]).startswith("PASS_") else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
