"""Independently reconstruct every row of the Mistral input freeze."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
PRODUCER = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
OUT = REPO / "outputs/cas_q3/mistral_reader_input_freeze_validation_v1"
DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
CONTEXT_BUDGET = 16000
TOKEN_GUARD = 8192
EXPECTED = {
    "development_runtime_config": "9eb8f1fd4e0d7a6549bd1a78adf92f96fb5ab12c64d3cdaaa6f2fa39029c40c9",
    "development_traces": "723cefe8817f5ff07fa81b06d71f59d9f28fe37d5e6b62ff94184e20bcdcf8e3",
    "test_preparation_manifest": "7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258",
    "test_trace": "87d5aff0bc77da76624b541326c523d41b00fa6c84ecefd4d6a050de66b25a29",
    "test_pool_manifest": "4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98",
    "roles": "40992a860943bc553fe9da6ad541181cb46958c56dc14a96621007449d0382ec",
    "asset_manifest": "0d52dd24d4f819af27b022877712a59ee07dab44e40a8e9c2586afa141b9fa18",
    "tokenizer_report": "47f3f2f04ed324e7be8051a594224bfdca8fc244133c14d5aeef028db24d1b5a",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            value.update(block)
    return value.hexdigest()


def object_sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def record(path: Path) -> dict[str, object]:
    path = path.resolve()
    return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": digest(path)}


def write_json(path: Path, value: object) -> None:
    require(not path.exists(), "REFUSE_OVERWRITE:" + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                indent=2, allow_nan=False).encode("utf-8") + b"\n")


def seal(output: Path) -> None:
    files = [record(path) for path in sorted(output.rglob("*")) if path.is_file()]
    for item in files:
        item["path"] = Path(str(item["path"])).relative_to(output).as_posix()
    write_json(output / "SHA256_MANIFEST.json", {
        "status": "PASS", "files": files, "excludes_only": "SHA256_MANIFEST.json",
        "exact_recursive_coverage": True,
    })


def verify_manifest(root: Path) -> None:
    manifest = load(root / "SHA256_MANIFEST.json")
    require(manifest["status"] == "PASS" and manifest["exact_recursive_coverage"] is True,
            "PRODUCER_MANIFEST_STATUS")
    expected = {
        row["path"]: {"size_bytes": row["size_bytes"], "sha256": row["sha256"]}
        for row in manifest["files"]
    }
    actual = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "SHA256_MANIFEST.json":
            actual[path.relative_to(root).as_posix()] = {
                "size_bytes": path.stat().st_size, "sha256": digest(path)
            }
    require(actual == expected, "PRODUCER_MANIFEST_EXACT_RECURSIVE_REHASH")


def render_evidence(evidence: list[dict]) -> tuple[str, bool, list[bool]]:
    require(len(evidence) == 5, "EXACT_FIVE_EVIDENCE")
    require([row["rank"] for row in evidence] == [1, 2, 3, 4, 5], "RANK_ORDER")
    headers = [
        f"[Evidence {row['rank']} | id={row['document_id']} | title={row['title']}]\n"
        for row in evidence
    ]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = CONTEXT_BUDGET - sum(
        len(separator) + len(header)
        for separator, header in zip(separators, headers, strict=True)
    )
    require(remaining >= 0, "HEADER_BUDGET")
    chunks, flags = [], []
    for separator, header, row in zip(separators, headers, evidence, strict=True):
        body = str(row["text"]).strip()
        included = body[:remaining]
        remaining -= len(included)
        chunks.append(separator + header + included)
        flags.append(len(included) < len(body))
    rendered = "".join(chunks)
    require(len(rendered) <= CONTEXT_BUDGET, "CONTEXT_BUDGET")
    return rendered, any(flags), flags


def metadata(tokenizer, template: str, question: str, evidence: list[dict]) -> dict[str, object]:
    rendered, truncated, flags = render_evidence(evidence)
    user = template.format(question=question, evidence=rendered)
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": user}], tokenize=False,
        add_generation_prompt=True,
    )
    token_ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
    require(0 < len(token_ids) <= TOKEN_GUARD, "TOKEN_GUARD")
    return {
        "prompt_sha256": text_sha(prompt),
        "input_token_ids_sha256": object_sha(token_ids),
        "input_tokens": len(token_ids),
        "rendered_context_characters": len(rendered),
        "context_truncated": truncated,
        "per_document_truncated": flags,
    }


def compact_document(row: dict, rank: int) -> dict[str, object]:
    return {
        "rank": rank,
        "document_id": row["id"],
        "title": row["title"],
        "text": row["title"] + "\n" + "".join(row["sentences"]),
        "content_hash": row["content_hash"],
    }


def load_assets(original: Path, cohort: str) -> dict[str, dict[str, object]]:
    if cohort == "development":
        base = original / "outputs/daa_v2_fresh_v1/pool_freeze"
        pool = lambda dataset: base / "pools" / f"{dataset}_documents.jsonl"
        runtime = lambda dataset: base / "runtime_projection" / f"{dataset}_selected_runtime.jsonl"
        bindings = load(
            original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json"
        )["parents"]["older_parents"]["datasets"]
    else:
        base = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
        pool = lambda dataset: base / "pools" / f"{dataset}.jsonl"
        runtime = lambda dataset: base / "runtime" / f"{dataset}.jsonl"
        manifest = {row["path"]: row for row in load(base / "SHA256_MANIFEST.json")["files"]}
    result = {}
    for dataset in DATASETS:
        pool_path, runtime_path = pool(dataset), runtime(dataset)
        if cohort == "development":
            require(digest(pool_path) == bindings[dataset]["pool_sha256"],
                    "DEV_POOL_PIN:" + dataset)
            require(digest(runtime_path) == bindings[dataset]["runtime_projection_sha256"],
                    "DEV_RUNTIME_PIN:" + dataset)
        else:
            for path in (pool_path, runtime_path):
                expected = manifest[path.relative_to(base).as_posix()]
                require(digest(path) == expected["sha256"] and
                        path.stat().st_size == expected["size_bytes"],
                        "TEST_ASSET_PIN:" + path.name)
        result[dataset] = {
            "documents": {row["id"]: row for row in rows(pool_path)},
            "questions": {row["id"]: row["question"] for row in rows(runtime_path)},
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    args = parser.parse_args()
    original = args.project_root.resolve()
    asset = args.asset.resolve()
    overlay = args.overlay.resolve()
    require(not OUT.exists(), "SINGLE_USE_VALIDATION_NAMESPACE")
    require(PRODUCER.is_dir(), "PRODUCER_NAMESPACE")
    verify_manifest(PRODUCER)
    receipt = load(PRODUCER / "BUILD_RECEIPT.json")
    freeze = load(PRODUCER / "EXECUTABLE_FREEZE.json")
    require(receipt["status"] == "PASS_VALUE_BLIND_MISTRAL_INPUT_FREEZE_PENDING_INDEPENDENT",
            "PRODUCER_PENDING_STATUS")
    require(receipt["source_commit"] == freeze["source_commit"], "SOURCE_COMMIT_BINDING")
    require(freeze["reader_revision"] == REVISION, "READER_REVISION")
    require(freeze["tokenizer_class"] == "LlamaTokenizerFast", "TOKENIZER_CLASS_FREEZE")
    require(freeze["maximum_generation_input_tokens"] == TOKEN_GUARD, "TOKEN_GUARD_FREEZE")
    require(freeze["dynamic_a1_admission_required_before_cuda"] is True,
            "DYNAMIC_A1_GUARD")
    for row in freeze["inputs"]:
        path = Path(row["path"])
        require(record(path) == row, "PRODUCER_INPUT_REHASH:" + path.name)

    require(digest(original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/RUNTIME_CONFIG_FREEZE.json") ==
            EXPECTED["development_runtime_config"], "DEVELOPMENT_CONFIG_PIN")
    development_trace_path = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/trace_manifest.jsonl"
    test_trace_path = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1/TRACE_MANIFEST_PRIVATE.jsonl"
    roles_path = REPO / "outputs/cas_q2/empirical_fixed_panel_v1/TRAINING_GROUPS_PRIVATE.jsonl"
    require(digest(development_trace_path) == EXPECTED["development_traces"], "DEV_TRACE_PIN")
    require(digest(REPO / "outputs/cas_q2/empirical_runtime_preparation_v1/SHA256_MANIFEST.json") ==
            EXPECTED["test_preparation_manifest"], "TEST_PREPARATION_PIN")
    require(digest(test_trace_path) == EXPECTED["test_trace"], "TEST_TRACE_PIN")
    require(digest(REPO / "outputs/cas_q2/empirical_candidate_pool_v2/SHA256_MANIFEST.json") ==
            EXPECTED["test_pool_manifest"], "TEST_POOL_PIN")
    require(digest(roles_path) == EXPECTED["roles"], "ROLE_PIN")
    require(digest(asset / "ASSET_MANIFEST.json") == EXPECTED["asset_manifest"],
            "ASSET_MANIFEST_PIN")
    require(digest(REPO / "docs/cas_q3/MISTRAL_TOKENIZER_PREFLIGHT_2026-09-17.json") ==
            EXPECTED["tokenizer_report"], "TOKENIZER_REPORT_PIN")

    sys.path.insert(0, str(overlay)) if str(overlay) not in sys.path else None
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        asset, use_fast=True, legacy=False, local_files_only=True,
        trust_remote_code=False,
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    require(type(tokenizer).__name__ == "LlamaTokenizerFast", "TOKENIZER_CLASS")
    answer_template = (original / "prompts/baseline_v1.txt").read_text(encoding="utf-8")
    repair_template = (original / "prompts/repair_missing_v1.txt").read_text(encoding="utf-8")
    roles = {(row["dataset"], row["sample_id"]): row["role"] for row in rows(roles_path)}
    require(collections.Counter(roles.values()) == {"fit": 3600, "cal": 900},
            "ROLE_COUNTS")
    development_assets = load_assets(original, "development")
    test_assets = load_assets(original, "test")
    traces_by_cohort = (
        ("development", list(rows(development_trace_path)), development_assets),
        ("test", list(rows(test_trace_path)), test_assets),
    )
    ledger = rows(PRODUCER / "INPUT_LENGTHS_PRIVATE.jsonl")
    aggregates = collections.defaultdict(
        lambda: {"rows": 0, "answer_max": 0, "repair_query_max": 0,
                 "context_truncated": 0}
    )
    maximum: dict[str, object] = {"input_tokens": -1}
    checked_rows = 0
    checked_tokenizations = 0
    for cohort, traces, assets in traces_by_cohort:
        expected_trace_count = 13500 if cohort == "development" else 18000
        require(len(traces) == expected_trace_count, "TRACE_COUNT:" + cohort)
        require([row["position"] for row in traces] == list(range(expected_trace_count)),
                "TRACE_POSITIONS:" + cohort)
        for trace in traces:
            dataset, retriever, sample_id = (
                trace["dataset"], trace["retriever"], trace["sample_id"]
            )
            asset_rows = assets[dataset]
            evidence = [
                compact_document(asset_rows["documents"][document_id], rank)
                for rank, document_id in enumerate(trace["original_top5_ids"], 1)
            ]
            answer = metadata(
                tokenizer, answer_template, asset_rows["questions"][sample_id], evidence
            )
            repair = metadata(
                tokenizer, repair_template, asset_rows["questions"][sample_id], evidence
            )
            role = roles[(dataset, sample_id)] if cohort == "development" else "test"
            reconstructed = {
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
            try:
                saved = next(ledger)
            except StopIteration as error:
                raise RuntimeError("PRODUCER_LEDGER_ENDED_EARLY") from error
            require(saved == reconstructed, "LEDGER_ROW:" + str(checked_rows))
            group = aggregates[(cohort, dataset, retriever)]
            group["rows"] += 1
            group["answer_max"] = max(group["answer_max"], answer["input_tokens"])
            group["repair_query_max"] = max(group["repair_query_max"], repair["input_tokens"])
            group["context_truncated"] += int(answer["context_truncated"])
            for stage, value in (("a0", answer), ("repair_query", repair)):
                if value["input_tokens"] > maximum["input_tokens"]:
                    maximum = {
                        "cohort": cohort, "dataset": dataset, "retriever": retriever,
                        "sample_id": sample_id, "position": trace["position"],
                        "stage": stage, "input_tokens": value["input_tokens"],
                        "prompt_sha256": value["prompt_sha256"],
                        "input_token_ids_sha256": value["input_token_ids_sha256"],
                    }
            checked_rows += 1
            checked_tokenizations += 2
    try:
        next(ledger)
    except StopIteration:
        pass
    else:
        raise RuntimeError("PRODUCER_LEDGER_HAS_EXTRA_ROWS")
    aggregate_rows = [
        dict(cohort=key[0], dataset=key[1], retriever=key[2], **value)
        for key, value in sorted(aggregates.items())
    ]
    require(checked_rows == receipt["deterministic_prompt_rows"] == 31500,
            "DETERMINISTIC_ROW_COUNT")
    require(checked_tokenizations == receipt["prompt_tokenizations"] == 63000,
            "TOKENIZATION_COUNT")
    require(maximum == receipt["maximum"], "MAXIMUM_RECONSTRUCTION")
    require(aggregate_rows == receipt["aggregates"], "AGGREGATE_RECONSTRUCTION")
    require(sum(row["context_truncated"] for row in aggregate_rows) == 0,
            "NO_CONTEXT_TRUNCATION")

    validation = {
        "schema_version": 1,
        "status": "PASS_INDEPENDENT_VALUE_BLIND_MISTRAL_INPUT_RECONSTRUCTION",
        "cas_q3_status": "NOT READY",
        "producer_manifest_sha256": digest(PRODUCER / "SHA256_MANIFEST.json"),
        "producer_source_commit": receipt["source_commit"],
        "validator_source_sha256": digest(Path(__file__).resolve()),
        "checked_rows": checked_rows,
        "checked_prompt_tokenizations": checked_tokenizations,
        "maximum": maximum,
        "aggregates": aggregate_rows,
        "model_loads": 0,
        "model_forward_calls": 0,
        "generation_calls": 0,
        "scientific_fit_calls": 0,
        "gold_reads": 0,
        "existing_answer_strings_read": 0,
        "source_chain": "DIRECT_ACCEPTED_QWEN_DEVELOPMENT_AND_TEST_INPUTS_NO_PHI_ARTIFACTS",
    }
    OUT.mkdir(parents=True, exist_ok=False)
    write_json(OUT / "VALIDATION.json", validation)
    seal(OUT)
    print(json.dumps({"status": validation["status"], "maximum": maximum,
                      "checked_rows": checked_rows}))
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
