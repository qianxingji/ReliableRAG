"""Independent no-model reconstruction of Mistral development repairs."""

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

from scripts.validate_mistral_development_a0_query import (
    canonical, load_original_native, object_sha, read_rows, require, sha256,
)


REPO = Path(__file__).resolve().parents[1]
EXPECTED_TRACES = 13_500
EXPECTED_DENSE_QUERIES = 9_000


def query_object(native, payload: dict):
    render = payload["render"]
    return native.GeneratedRepairQuery(
        payload["raw_text"], payload["parsed_text"], payload["parser_fallback"],
        payload["input_tokens"], payload["output_tokens"], render["context_truncated"],
        render["context_budget_characters"], tuple(render["ordered_passed_document_ids"]),
        tuple(render["per_document_truncated"]), 0.0, False, False, 1,
    )


def evidence_rows(evidence) -> list[dict]:
    return [row.as_private_dict() for row in evidence]


def validate_manifest(namespace: Path) -> None:
    manifest_path = namespace / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); members = set()
    for item in manifest["files"]:
        path = (namespace / item["path"]).resolve()
        require(path.is_relative_to(namespace) and path not in members, "MANIFEST_PATH")
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"], "MANIFEST_MEMBER")
        members.add(path)
    actual = {path.resolve() for path in namespace.rglob("*") if path.is_file()}
    require(actual == members | {manifest_path.resolve()}, "MANIFEST_COVERAGE")


def validate_journal(rows: list[dict], events: list[dict]) -> int:
    row_map = {row["operation_key"]: row for row in rows}
    require(len(row_map) == len(rows), "UNIQUE_ROWS")
    pending = None; completed = {}; recoveries = 0
    for event in events:
        if event["event"] == "intent":
            require(pending is None, "OVERLAPPING_INTENT"); pending = event
        elif event["event"] == "resume_pending":
            require(pending is not None and event["operation_key"] == pending["operation_key"], "RESUME_EVENT")
            recoveries += 1
        else:
            require(event["event"] == "result" and pending is not None
                    and event["operation_key"] == pending["operation_key"], "RESULT_EVENT")
            require(event["result_sha256"] == object_sha(row_map[event["operation_key"]]), "RESULT_HASH")
            completed[event["operation_key"]] = event; pending = None
    require(pending is None and set(completed) == set(row_map), "COMPLETE_EVENTS")
    return recoveries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    original, root, output = args.project_root.resolve(), args.root.resolve(), args.output.resolve()
    require(original == Path("E:/paper/ReliableRAG").resolve() and not output.exists(), "FIXED_ROOT_OR_OUTPUT")
    namespace = root / "repair"; validate_manifest(namespace)
    stage = json.loads((namespace / "STAGE_RECEIPT.json").read_text(encoding="utf-8"))
    require(stage["status"] == "PASS_MISTRAL_DEVELOPMENT_REPAIR_PENDING_INDEPENDENT"
            and stage["completed_traces"] == EXPECTED_TRACES, "PRODUCER_STATUS")
    freeze = json.loads((namespace / "EXECUTABLE_FREEZE.json").read_text(encoding="utf-8"))
    for item in freeze["inputs"]:
        path = Path(item["path"])
        require(path.stat().st_size == item["size_bytes"] and sha256(path) == item["sha256"], "FROZEN_INPUT")
    repair_rows = read_rows(namespace / "REPAIR_BINDINGS.jsonl")
    events = read_rows(namespace / "CALL_JOURNAL.jsonl")
    require(len(repair_rows) == EXPECTED_TRACES, "REPAIR_ROW_COUNT")
    recovery_count = validate_journal(repair_rows, events)
    a0_stage = root / "a0_query"; validate_manifest(a0_stage)
    a0_validation = json.loads((root / "a0_query_validation/VALIDATION.json").read_text(encoding="utf-8"))
    require(a0_validation["status"] == "PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_DEVELOPMENT_A0_QUERY"
            and a0_validation["producer_receipt_sha256"] == sha256(a0_stage / "STAGE_RECEIPT.json")
            and a0_validation["generation_receipts_sha256"] == sha256(a0_stage / "GENERATION_RECEIPTS.jsonl")
            and a0_validation["call_journal_sha256"] == sha256(a0_stage / "CALL_JOURNAL.jsonl"),
            "A0_VALIDATION_BINDING")
    query_rows = [row for row in read_rows(a0_stage / "GENERATION_RECEIPTS.jsonl")
                  if row["operation"] == "repair_query"]
    require(len(query_rows) == EXPECTED_TRACES, "QUERY_ROW_COUNT")
    query_by_position = {row["payload"]["position"]: row["payload"] for row in query_rows}
    runtime_root = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    traces = read_rows(runtime_root / "trace_manifest.jsonl")
    frozen_rows = [row for row in read_rows(REPO / "outputs/cas_q3/mistral_reader_input_freeze_v1/INPUT_LENGTHS_PRIVATE.jsonl")
                   if row.get("cohort") == "development"]
    require(len(traces) == len(frozen_rows) == EXPECTED_TRACES, "SOURCE_COUNTS")
    loader, native = load_original_native(original)

    class SavedVectorBackend:
        dimension = 768
        def __init__(self): self.vector = None; self.calls = 0
        def encode_queries(self, texts):
            require(type(texts) is list and len(texts) == 1 and self.vector is not None, "SAVED_VECTOR_QUERY")
            self.calls += 1; return np.asarray([self.vector], dtype=np.float32)
        def encode_documents(self, *_args, **_kwargs): raise RuntimeError("DOCUMENT_REEMBEDDING_FORBIDDEN")

    backend = SavedVectorBackend(); runner = native.ProspectiveRunner(); runner.protocol = native.FrozenProtocol()
    current_dataset = None; data = None; checks = 0
    for position, (trace, frozen, row) in enumerate(zip(traces, frozen_rows, repair_rows, strict=True)):
        payload = row["payload"]; dataset, retriever, sample_id = trace["dataset"], trace["retriever"], trace["sample_id"]
        require(trace["position"] == frozen["position"] == payload["position"] == position, "POSITION")
        require((dataset, retriever, sample_id) == (payload["dataset"], payload["retriever"], payload["sample_id"]),
                "IDENTITY")
        require(row["sequence"] == position and row["operation_key"] == f"{position:05d}:repair_retrieval"
                and row["operation"] == "repair_retrieval", "ROW_ORDER")
        if dataset != current_dataset:
            data = loader.restore_dataset(dataset, native, backend); current_dataset = dataset
        e0 = loader.original_evidence(trace, data, native); query_payload = query_by_position[position]
        query = query_object(native, query_payload)
        backend.vector = payload["dense_query_vector"]
        before_calls = backend.calls; data["components"].clear(); ranking = []
        def rank(query_text, method, depth):
            require(method == retriever and depth == 50 and query_text == query.search_query, "RANK_CALL")
            value = data["router"].rank(query_text, method, depth); ranking.extend(value); return value
        e1, inserted, _diagnostics = runner._repair(types.SimpleNamespace(rank=rank), query, retriever, e0)
        require(backend.calls - before_calls == (0 if retriever == "bm25" else 1), "QUERY_FORWARD_COUNT")
        components = data["components"]
        expected_ranking = [{"document_id": item.document_id, "rank": item.rank, "score": float(item.score)} for item in ranking]
        expected_components = ({"bm25": components[0], "dense": components[1]}
                               if retriever == "hybrid" else {retriever: components[0]})
        require(payload["ranking"] == expected_ranking and payload["component_rankings"] == expected_components,
                "RANKING_RECONSTRUCTION")
        require(payload["e0_ids"] == [item.document_id for item in e0]
                and payload["e1_ids"] == [item.document_id for item in e1]
                and payload["inserted_document_id"] == inserted.document_id
                and payload["inserted_candidate_rank"] == inserted.rank
                and payload["replaced_document_id"] == e0[4].document_id
                and payload["replacement_position_zero_based"] == 4, "REPAIR_RECONSTRUCTION")
        inserted_rows = [item for item in ranking if item.document_id == inserted.document_id]
        require(len(inserted_rows) == 1 and inserted_rows[0].rank == inserted.rank,
                "INSERTED_RANK_RECONSTRUCTION")
        require(payload["query_sha256"] == hashlib.sha256(query.search_query.encode("utf-8")).hexdigest(), "QUERY_HASH")
        input_value = {"dataset": dataset, "retriever": retriever, "sample_id": sample_id,
                       "position": position, "query": query.search_query, "e0": evidence_rows(e0),
                       "depth": 50, "replacement_position_zero_based": 4}
        require(row["input_sha256"] == object_sha(input_value), "OPERATION_INPUT_HASH")
        if payload["dense_query_vector"] is not None:
            vector = np.asarray(payload["dense_query_vector"], dtype=np.float64)
            require(vector.shape == (768,) and np.isfinite(vector).all(), "FINITE_VECTOR")
        require(payload["role"] == frozen["role"] and payload["pool_sha256"] == data["binding"]["pool_sha256"],
                "ROLE_POOL_BINDING")
        checks += 32
    require(backend.calls == EXPECTED_DENSE_QUERIES, "TOTAL_DENSE_QUERY_COUNT")
    require(stage["gold_values_read"] == stage["scientific_fits"] == stage["test_rows_read"] == 0
            and stage["mistral_model_loads"] == stage["nli_model_loads"] == 0, "ZERO_FORBIDDEN_ACCESS")
    result = {
        "status": "PASS_INDEPENDENT_NO_MODEL_MISTRAL_DEVELOPMENT_REPAIR",
        "cas_q3_status": "NOT READY", "checks": checks,
        "producer_receipt_sha256": sha256(namespace / "STAGE_RECEIPT.json"),
        "repair_bindings_sha256": sha256(namespace / "REPAIR_BINDINGS.jsonl"),
        "call_journal_sha256": sha256(namespace / "CALL_JOURNAL.jsonl"),
        "recovery_events": recovery_count, "reconstructed_dense_queries": backend.calls,
        "model_loads": 0, "model_forwards": 0, "gold_values_read": 0,
        "scientific_fits": 0, "test_rows_read": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(result, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    print(result["status"], checks, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
