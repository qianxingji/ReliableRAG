"""Strict IO adaptation from accepted C3 branches to unchanged native features."""
import hashlib
import math
import re

from scripts.empirical_runtime_contract import sha_json, trace_key

KEYS = {"dataset", "retriever", "sample_id"}
BRANCH = KEYS | {"question", "a0", "a1", "evidence0", "evidence1"}
EVIDENCE = {"rank", "document_id", "content_hash", "retrieval_score", "title", "text"}
PROVENANCE = KEYS | {"position", "original_top5_row_sha256", "e0", "e1", "question_sha256",
    "canonical_row_sha256", "runtime_config_sha256", "repair_binding_row_sha256", "pool_sha256"}
PREPARED = KEYS | {"position", "original_top5_ids", "original_top5_row_sha256"}
REPAIR = KEYS | {"position", "query_sha256", "ranking", "component_rankings", "dense_query_vector",
    "e0_ids", "e1_ids", "inserted_document_id", "inserted_candidate_rank", "replaced_document_id",
    "replacement_position_zero_based", "requested_depth", "repair_retrieval_calls", "pool_sha256", "fail_closed_reason"}


def require(value, message):
    if not value:
        raise ValueError(message)


def text_sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def restore_bound_trace(wrapper, branch, provenance, prepared, repair, *, pool_sha, runtime_config_sha):
    """Caller authenticates the complete C3 seal before supplying any fresh rows."""
    for row, schema in ((branch, BRANCH), (provenance, PROVENANCE), (prepared, PREPARED), (repair, REPAIR)):
        require(type(row) is dict and set(row) == schema, "Exact accepted C3 row schema")
        require(all(type(row[k]) is str and row[k] for k in KEYS), "Exact string trace key")
    key = trace_key(branch)
    require(key[0] in ("hotpotqa", "2wikimultihopqa", "musique") and key[1] in ("bm25", "dense", "hybrid"), "Trace stratum")
    require(all(trace_key(row) == key for row in (provenance, prepared, repair)), "C3 trace key alignment")
    require(type(prepared["position"]) is int and prepared["position"] >= 0 and
        all(type(row["position"]) is int and row["position"] == prepared["position"] for row in (provenance, repair)), "C3 exact positions")
    require(all(type(branch[k]) is str for k in ("question", "a0", "a1")), "Unmodified question/answer strings")
    require(provenance["canonical_row_sha256"] == sha_json(branch) and
        provenance["question_sha256"] == text_sha(branch["question"]), "Canonical branch/question hashes")
    require(provenance["repair_binding_row_sha256"] == sha_json(repair), "Repair receipt hash")
    require(all(re.fullmatch(r"[0-9a-f]{64}", str(value)) for value in (pool_sha, runtime_config_sha)), "Pinned context hashes")
    require(provenance["pool_sha256"] == repair["pool_sha256"] == pool_sha and
        provenance["runtime_config_sha256"] == runtime_config_sha, "Accepted pool/runtime configuration")
    require(provenance["original_top5_row_sha256"] == prepared["original_top5_row_sha256"], "Original retrieval row binding")
    projection = {name: branch[name] for name in KEYS}
    for state, field in (("e0", "evidence0"), ("e1", "evidence1")):
        rows, texts = provenance[state], branch[field]
        require(type(rows) is list and type(texts) is list and len(rows) == len(texts) == 5, "Five evidence positions")
        for rank, (row, text) in enumerate(zip(rows, texts, strict=True), 1):
            require(type(row) is dict and set(row) == EVIDENCE, "Exact full evidence schema")
            require(type(row["rank"]) is int and row["rank"] == rank, "Evidence rank order")
            require(all(type(row[k]) is str for k in ("document_id", "content_hash", "title", "text")), "Evidence string fields")
            require(row["document_id"] and re.fullmatch(r"[0-9a-f]{64}", row["content_hash"]), "Evidence ID/content identity")
            require(type(text) is str and row["text"] == text, "Evidence text binding")
            require(type(row["retrieval_score"]) in (int, float) and math.isfinite(row["retrieval_score"]), "Finite retrieval score")
        require(len({r["document_id"] for r in rows}) == 5, "Unique evidence documents")
        projection[state] = [{k: v for k, v in row.items() if k != "text"} for row in rows]
    e0, e1 = provenance["e0"], provenance["e1"]
    ids0, ids1 = [r["document_id"] for r in e0], [r["document_id"] for r in e1]
    require(ids0 == prepared["original_top5_ids"] == repair["e0_ids"] and ids1 == repair["e1_ids"], "All original/repair document IDs")
    require(prepared["original_top5_row_sha256"] == sha_json({**{k: branch[k] for k in KEYS}, "document_ids": ids0}), "Original Top-5 row digest")
    require(e0[:4] == e1[:4] and ids1[4] not in ids0, "Original first four and novel fifth passage")
    require(repair["inserted_document_id"] == ids1[4] and repair["replaced_document_id"] == ids0[4] and
        repair["replacement_position_zero_based"] == 4 and repair["requested_depth"] == 50 and
        repair["repair_retrieval_calls"] == 1 and repair["fail_closed_reason"] is None, "Accepted repair operation")
    return wrapper.restore_trace(branch, projection)
