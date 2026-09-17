"""Independently reconstruct Mistral test repairs without loading a model."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import types

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.empirical_runtime_io import CPU_TEST_SHA, native_runtime, restore_dataset
from scripts.mistral_development_acquisition_common import read_jsonl, sha256
from scripts.validate_mistral_test_a0_query import (
    EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
    EXPECTED_TEST_POOL_MANIFEST_SHA256,
    EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
    EXPECTED_TEST_TRACE_SHA256,
    object_sha,
    read_rows,
    require,
    validate_selected_manifest,
    validate_manifest,
    validate_test_binding,
)


REPO = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = Path("E:/paper/ReliableRAG")
TEST_ROOT = REPO / "outputs/cas_q3/mistral_test_confirmation_v1"
EXPECTED_TRACES = 18_000
EXPECTED_DENSE_QUERIES = 12_000
EXPECTED_RETRIEVAL_MANIFEST_SHA256 = (
    "81b9c7163adf669a828bd2ef772e14fecbda727cf596bced45856a1e699a354d"
)
EXPECTED_BGE_PREFLIGHT_MANIFEST_SHA256 = (
    "3861f34c6add005baa1889d36679b740c90677d0fbbbc04ea85ab8b5cc6a2b3d"
)
BGE_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")


def current_manifest_member_paths(
    namespace: Path, expected_manifest_sha256: str,
) -> set[Path]:
    namespace = namespace.resolve(); manifest_path = namespace / "SHA256_MANIFEST.json"
    require(sha256(manifest_path) == expected_manifest_sha256,
            "CURRENT_MANIFEST_PIN")
    value = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    for item in value["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members
                and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "CURRENT_MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()},
            "CURRENT_MANIFEST_COVERAGE")
    return {manifest_path.resolve(), *members}


def bge_asset_paths(preflight: Path, original: Path) -> set[Path]:
    receipt = json.loads((preflight / "GPU_PREFLIGHT.json").read_text(
        encoding="utf-8"
    ))
    require(receipt.get("status") == "PASS_BGE_GPU_SYNTHETIC_ONLY"
            and receipt.get("actual_backend", {}).get("revision") == BGE_REVISION
            and receipt.get("benchmark_embedding_forward_calls") == 0
            and receipt.get("fresh_gold_values_materialized") == 0,
            "BGE_PREFLIGHT_STATUS")
    freeze = json.loads((preflight / "EXECUTABLE_FREEZE.json").read_text(
        encoding="utf-8"
    ))
    model_root = (original / "data/models/huggingface"
                  / "models--BAAI--bge-base-en-v1.5"
                  / "snapshots" / BGE_REVISION).resolve()
    selected = set()
    for item in freeze["inputs"]:
        path = Path(item["path"]).resolve()
        if path.is_relative_to(model_root):
            require(path not in selected and path.is_file()
                    and path.stat().st_size == item["size_bytes"]
                    and sha256(path) == item["sha256"], "BGE_ASSET_MEMBER")
            selected.add(path)
    require(len(selected) == 6, "BGE_ASSET_FILE_COUNT")
    return selected


def query_object(native, payload: dict):
    render = payload["render"]
    return native.GeneratedRepairQuery(
        payload["raw_text"], payload["parsed_text"],
        payload["parser_fallback"], payload["input_tokens"],
        payload["output_tokens"], render["context_truncated"],
        render["context_budget_characters"],
        tuple(render["ordered_passed_document_ids"]),
        tuple(render["per_document_truncated"]), 0.0, False, False, 1,
    )


def evidence_rows(evidence) -> list[dict]:
    return [row.as_private_dict() for row in evidence]


def validate_journal(rows: list[dict], events: list[dict]) -> int:
    row_map = {row["operation_key"]: row for row in rows}
    require(len(row_map) == len(rows), "UNIQUE_ROWS")
    pending = None
    completed = {}
    recoveries = 0
    for event in events:
        if event["event"] == "intent":
            require(pending is None, "OVERLAPPING_INTENT")
            pending = event
        elif event["event"] == "resume_pending":
            require(pending is not None
                    and event["operation_key"] == pending["operation_key"]
                    and event["input_sha256"] == pending["input_sha256"],
                    "RESUME_EVENT")
            recoveries += 1
        else:
            require(event["event"] == "result" and pending is not None
                    and event["operation_key"] == pending["operation_key"],
                    "RESULT_EVENT")
            require(event["result_sha256"]
                    == object_sha(row_map[event["operation_key"]]),
                    "RESULT_HASH")
            completed[event["operation_key"]] = event
            pending = None
    require(pending is None and set(completed) == set(row_map),
            "COMPLETE_EVENTS")
    return recoveries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ORIGINAL_ROOT)
    parser.add_argument("--test-root", type=Path, default=TEST_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    original, root = args.project_root.resolve(), args.test_root.resolve()
    output = (args.output.resolve() if args.output else
              (root / "repair_validation/VALIDATION.json").resolve())
    require(original == ORIGINAL_ROOT.resolve() and root == TEST_ROOT.resolve()
            and output == (root / "repair_validation/VALIDATION.json").resolve()
            and not output.exists(), "FIXED_ROOTS_OR_OUTPUT")
    namespace = root / "repair"
    validate_manifest(namespace)
    receipt = json.loads((namespace / "STAGE_RECEIPT.json").read_text(
        encoding="utf-8"
    ))
    require(receipt.get("status")
            == "PASS_MISTRAL_TEST_REPAIR_PENDING_INDEPENDENT"
            and receipt.get("completed_traces") == EXPECTED_TRACES
            and receipt.get("logical_dense_query_forwards")
            == EXPECTED_DENSE_QUERIES
            and receipt.get("gold_values_read") == 0
            and receipt.get("test_gold_values_read") == 0
            and receipt.get("scientific_fits") == 0
            and receipt.get("test_input_rows_read") == EXPECTED_TRACES
            and receipt.get("mistral_model_loads") == 0
            and receipt.get("nli_model_loads") == 0,
            "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(
        encoding="utf-8"
    ))
    require(freeze.get("source_commit") == receipt.get("source_commit")
            and freeze.get("status")
            == "FROZEN_BEFORE_FORMAL_MISTRAL_TEST_REPAIR"
            and freeze.get("expected_traces") == EXPECTED_TRACES
            and freeze.get("expected_dense_query_forwards")
            == EXPECTED_DENSE_QUERIES
            and freeze.get("retrieval_depth") == 50
            and freeze.get("replacement_position_zero_based") == 4
            and freeze.get("test_gold_access") == "FORBIDDEN",
            "EXECUTABLE_FREEZE")
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.is_file() and path.stat().st_size == item["size_bytes"]
                and sha256(path) == item["sha256"], "FROZEN_INPUT")
    frozen_paths = {Path(item["path"]).resolve() for item in freeze["inputs"]}
    require(len(frozen_paths) == len(freeze["inputs"]), "UNIQUE_FROZEN_INPUTS")
    repair_rows = read_rows(namespace / "REPAIR_BINDINGS.jsonl")
    events = read_rows(namespace / "CALL_JOURNAL.jsonl")
    require(len(repair_rows) == EXPECTED_TRACES, "REPAIR_ROW_COUNT")
    recoveries = validate_journal(repair_rows, events)

    a0_stage = root / "a0_query"
    validate_manifest(a0_stage)
    a0_receipt = json.loads((a0_stage / "STAGE_RECEIPT.json").read_text(
        encoding="utf-8"
    ))
    a0_validation_path = root / "a0_query_validation/VALIDATION.json"
    a0_validation = json.loads(a0_validation_path.read_text(encoding="utf-8"))
    require(a0_receipt.get("status")
            == "PASS_MISTRAL_TEST_A0_QUERY_PENDING_INDEPENDENT"
            and a0_validation.get("status")
            == "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY"
            and a0_validation.get("producer_receipt_sha256")
            == sha256(a0_stage / "STAGE_RECEIPT.json")
            and a0_validation.get("generation_receipts_sha256")
            == sha256(a0_stage / "GENERATION_RECEIPTS.jsonl")
            and a0_validation.get("call_journal_sha256")
            == sha256(a0_stage / "CALL_JOURNAL.jsonl"),
            "A0_VALIDATION_BINDING")
    preparation = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
    pool_root = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
    retrieval = REPO / "outputs/cas_q2/empirical_retrieval_v1"
    preflight = REPO / "outputs/cas_q2/empirical_retrieval_gpu_preflight_v1"
    cpu_tests = REPO / "outputs/cas_q2/empirical_runtime_native_tests_v1"
    input_freeze = REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1"
    pool_relatives = tuple(
        f"{folder}/{dataset}.jsonl"
        for folder in ("pools", "runtime") for dataset in DATASETS
    ) + ("INDEPENDENT_VALIDATION.json",)
    required_inputs = {
        *{path.resolve() for path in validate_selected_manifest(
            preparation, EXPECTED_TEST_PREPARATION_MANIFEST_SHA256,
            ("TRACE_MANIFEST_PRIVATE.jsonl",),
        )},
        *{path.resolve() for path in validate_selected_manifest(
            pool_root, EXPECTED_TEST_POOL_MANIFEST_SHA256, pool_relatives,
        )},
        *current_manifest_member_paths(
            retrieval, EXPECTED_RETRIEVAL_MANIFEST_SHA256,
        ),
        *current_manifest_member_paths(
            preflight, EXPECTED_BGE_PREFLIGHT_MANIFEST_SHA256,
        ),
        *current_manifest_member_paths(cpu_tests, CPU_TEST_SHA),
        *current_manifest_member_paths(
            input_freeze, EXPECTED_INPUT_FREEZE_MANIFEST_SHA256,
        ),
        *current_manifest_member_paths(
            a0_stage, sha256(a0_stage / "SHA256_MANIFEST.json"),
        ),
        *bge_asset_paths(preflight, original),
        a0_validation_path.resolve(),
        (root / "EXECUTABLE_FREEZE.json").resolve(),
        (REPO / "scripts/run_mistral_test_repair.py").resolve(),
        Path(__file__).resolve(),
        (REPO / "scripts/validate_mistral_test_a0_query.py").resolve(),
        (REPO / "scripts/empirical_runtime_io.py").resolve(),
        (REPO / "scripts/empirical_retrieval_io.py").resolve(),
        (REPO / "scripts/empirical_pool_io.py").resolve(),
        (REPO / "scripts/empirical_runtime_contract.py").resolve(),
        (REPO / "scripts/replay_roa_original.py").resolve(),
        (REPO / "scripts/verify_roa_artifacts.py").resolve(),
        (REPO / "scripts/mistral_development_acquisition_common.py").resolve(),
        (REPO / "scripts/mistral_reader_input_freeze_common.py").resolve(),
        (REPO / "scripts/run_mistral_test_a0_query.py").resolve(),
        (REPO / "src/arbitration/mistral_reader_runtime.py").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_EXECUTION_PROTOCOL_2026-09-17.md").resolve(),
        (REPO / "docs/cas_q3/MISTRAL_TEST_REPAIR_INPUT_GRAPH_AMENDMENT_2026-09-17.md").resolve(),
        (original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/SHA256_MANIFEST.json").resolve(),
        (original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/runtime_support.py").resolve(),
        (original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/native_runtime.py").resolve(),
        Path(sys.executable).resolve(),
    }
    require(required_inputs == frozen_paths, "NONEXACT_FROZEN_INPUT_GRAPH")
    query_rows = [row for row in read_rows(
        a0_stage / "GENERATION_RECEIPTS.jsonl"
    ) if row["operation"] == "repair_query"]
    require(len(query_rows) == EXPECTED_TRACES, "QUERY_ROW_COUNT")
    query_by_position = {row["payload"]["position"]: row["payload"]
                         for row in query_rows}
    require(len(query_by_position) == EXPECTED_TRACES,
            "UNIQUE_QUERY_POSITIONS")
    traces = read_rows(
        preparation / "TRACE_MANIFEST_PRIVATE.jsonl"
    )
    frozen_rows = validate_test_binding(
        traces,
        read_jsonl(input_freeze / "INPUT_LENGTHS_PRIVATE.jsonl"),
    )
    wrapper, native, nodes, boundary = native_runtime(original)
    require(receipt.get("native_ast_nodes") == nodes
            and receipt.get("generation_boundary") == boundary,
            "NATIVE_RUNTIME_BINDING")

    class SavedVectorBackend:
        dimension = 768

        def __init__(self):
            self.vector = None
            self.calls = 0

        def encode_queries(self, texts):
            require(type(texts) is list and len(texts) == 1
                    and self.vector is not None, "SAVED_VECTOR_QUERY")
            self.calls += 1
            return np.asarray([self.vector], dtype=np.float32)

        def encode_documents(self, *_args, **_kwargs):
            raise RuntimeError("DOCUMENT_REEMBEDDING_FORBIDDEN")

    backend = SavedVectorBackend()
    runner = native.ProspectiveRunner()
    runner.protocol = native.FrozenProtocol()
    current_dataset = None
    data = None
    checks = 0
    for position, (trace, frozen_row, row) in enumerate(zip(
            traces, frozen_rows, repair_rows, strict=True)):
        payload = row["payload"]
        dataset, retriever, sample_id = (
            trace["dataset"], trace["retriever"], trace["sample_id"]
        )
        require(trace["position"] == frozen_row["position"]
                == payload["position"] == position, "POSITION")
        require((dataset, retriever, sample_id)
                == (payload["dataset"], payload["retriever"],
                    payload["sample_id"])
                and payload["role"] == frozen_row["role"] == "test",
                "IDENTITY")
        require(row["sequence"] == position
                and row["operation_key"]
                == f"{position:05d}:repair_retrieval"
                and row["operation"] == "repair_retrieval", "ROW_ORDER")
        if dataset != current_dataset:
            data = restore_dataset(dataset, native, backend)
            current_dataset = dataset
        e0 = wrapper.original_evidence(trace, data, native)
        query = query_object(native, query_by_position[position])
        backend.vector = payload["dense_query_vector"]
        before = backend.calls
        data["components"].clear()
        ranking = []

        def rank(query_text, method, depth):
            require(method == retriever and depth == 50
                    and query_text == query.search_query, "RANK_CALL")
            value = data["router"].rank(query_text, method, depth)
            ranking.extend(value)
            return value

        e1, inserted, _diagnostics = runner._repair(
            types.SimpleNamespace(rank=rank), query, retriever, e0
        )
        require(backend.calls - before == (0 if retriever == "bm25" else 1),
                "QUERY_FORWARD_COUNT")
        components = data["components"]
        expected_ranking = [
            {"document_id": item.document_id, "rank": item.rank,
             "score": float(item.score)} for item in ranking
        ]
        expected_components = (
            {"bm25": components[0], "dense": components[1]}
            if retriever == "hybrid" else {retriever: components[0]}
        )
        require(payload["ranking"] == expected_ranking
                and payload["component_rankings"] == expected_components,
                "RANKING_RECONSTRUCTION")
        require(payload["e0_ids"] == [item.document_id for item in e0]
                and payload["e1_ids"] == [item.document_id for item in e1]
                and payload["inserted_document_id"] == inserted.document_id
                and payload["inserted_candidate_rank"] == inserted.rank
                and payload["replaced_document_id"] == e0[4].document_id
                and payload["replacement_position_zero_based"] == 4,
                "REPAIR_RECONSTRUCTION")
        inserted_rows = [item for item in ranking
                         if item.document_id == inserted.document_id]
        require(len(inserted_rows) == 1
                and inserted_rows[0].rank == inserted.rank,
                "INSERTED_RANK_RECONSTRUCTION")
        require(payload["query_sha256"]
                == hashlib.sha256(query.search_query.encode("utf-8")).hexdigest(),
                "QUERY_HASH")
        input_value = {
            "dataset": dataset, "retriever": retriever,
            "sample_id": sample_id, "position": position,
            "query": query.search_query, "e0": evidence_rows(e0),
            "depth": 50, "replacement_position_zero_based": 4,
        }
        require(row["input_sha256"] == object_sha(input_value),
                "OPERATION_INPUT_HASH")
        if payload["dense_query_vector"] is not None:
            vector = np.asarray(payload["dense_query_vector"], dtype=np.float64)
            require(vector.shape == (768,) and np.isfinite(vector).all(),
                    "FINITE_VECTOR")
        require(payload["pool_sha256"] == data["binding"]["pool_sha256"]
                and payload["requested_depth"] == 50
                and payload["repair_retrieval_calls"] == 1
                and payload["fail_closed_reason"] is None,
                "CONTROL_BINDING")
        require(all(math.isfinite(item["score"])
                    for item in payload["ranking"]), "FINITE_RANKING")
        checks += 34
    require(backend.calls == EXPECTED_DENSE_QUERIES,
            "TOTAL_DENSE_QUERY_COUNT")
    repair_path = namespace / "REPAIR_BINDINGS.jsonl"
    require(receipt.get("repair_bindings") == {
        "path": str(repair_path.resolve()),
        "size_bytes": repair_path.stat().st_size,
        "sha256": sha256(repair_path),
    }, "REPAIR_FILE_BINDING")
    result = {
        "status": "PASS_INDEPENDENT_NO_MODEL_MISTRAL_TEST_REPAIR",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "repair_bindings_sha256": sha256(repair_path),
        "call_journal_sha256": sha256(namespace / "CALL_JOURNAL.jsonl"),
        "validated_traces": EXPECTED_TRACES,
        "recovery_events": recoveries,
        "reconstructed_dense_queries": backend.calls,
        "model_loads": 0, "model_forwards": 0,
        "gold_values_read": 0, "test_gold_values_read": 0,
        "scientific_fits": 0, "test_input_rows_read": EXPECTED_TRACES,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2,
                                  allow_nan=False).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True)
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
