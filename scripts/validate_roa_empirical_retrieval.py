"""Independent complete saved-array retrieval arithmetic; no model or native router."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

from scripts.empirical_retrieval_io import (REPO, OUT, POOL, DATASETS, RETRIEVERS, inputs,
    independent_arithmetic, seal, record, require, load)
from scripts.replay_roa_original import install_boundary, write_json
from scripts.verify_roa_artifacts import digest, relative_path, safe_file


def read_rows(path):
    with path.open(encoding="utf-8") as stream: return [json.loads(line) for line in stream]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    root = p.parse_args().project_root.resolve()
    require(not (OUT / "INDEPENDENT_VALIDATION.json").exists(), "Single-use independent validation")
    boundary = install_boundary(OUT)
    result = dict(status="FAIL", cas_q2_status="NOT READY", checks=0, scientific_fit_calls=0,
                  model_forward_calls=0, fresh_gold_values_materialized=0, datasets={})
    def eq(left, right):
        result["checks"] += 1
        require(left == right, "Independent retrieval mismatch")
    try:
        cfg, pre, paths = inputs(root)
        independent = independent_arithmetic(root)
        execution = load(OUT / "EXECUTION_MANIFEST.json")
        listed = {e["path"] for e in execution["files"]}
        eq({p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()}, listed | {"EXECUTION_MANIFEST.json"})
        expected_science = {"indexes/" + d + "/" + name for d in DATASETS for name in
            ("bm25_structure.json", "document_embeddings.npy", "query_embeddings_dense.npy", "query_embeddings_hybrid.npy")} | {
            "rankings/" + d + "_" + r + ".jsonl" for d in DATASETS for r in RETRIEVERS} | {
            "top5/" + d + ".jsonl" for d in DATASETS}
        eq({x for x in listed if not x.startswith("cache/")}, expected_science | {"EXECUTABLE_FREEZE.json", "BUILD_RECEIPT.json"})
        for e in execution["files"]:
            path = safe_file(OUT, relative_path(e["path"]))
            eq(digest(path), e["sha256"]); eq(path.stat().st_size, e["size_bytes"])
        freeze = load(OUT / "EXECUTABLE_FREEZE.json")
        for e in freeze["inputs"]: eq(record(Path(e["path"])), e)
        eq(freeze["config"], pre["retriever_config"])
        receipt = load(OUT / "BUILD_RECEIPT.json")
        eq(receipt["status"], "RETRIEVED_PENDING_INDEPENDENT")
        eq(receipt["source_commit"], freeze["source_commit"])
        eq(receipt["execution_boundary"]["denied"], [])
        eq(receipt["source_inputs_unchanged"], True)
        for key in ("scientific_fit_calls", "reader_generation_calls", "fresh_gold_values_materialized"): eq(receipt[key], 0)
        eq(receipt["execution_counters"], dict(bm25_structure_builds=3, embedding_document_rows=54716,
            embedding_forward_documents=3422, embedding_query_rows=12000, embedding_forward_queries=12000,
            embedding_forward_calls=15422, original_retrieval_calls=18000, original_bm25_calls=6000,
            original_dense_calls=6000, original_hybrid_calls=6000))
        actual = receipt["actual_backend"]
        eq(actual["dtype"], "torch.bfloat16"); eq(actual["model_class"], "BertModel")
        eq(actual["deterministic"], True); eq(actual["tf32"], False); eq(actual["eval_mode"], True)
        eq(actual["document_batch_size"], 16); eq(actual["query_batch_size"], 1); eq(actual["dimension"], 768)
        all_keys = []
        for dataset in DATASETS:
            docs = read_rows(POOL / "pools" / (dataset + ".jsonl"))
            runtime = read_rows(POOL / "runtime" / (dataset + ".jsonl"))
            eq(len(runtime), 2000)
            index = OUT / "indexes" / dataset
            structure = independent.independent_structure(docs)
            eq(load(index / "bm25_structure.json"), structure)
            lookup = {x["term"]: x for x in structure["terms"]}
            arrays = {name: np.load(index / (name + ".npy"), allow_pickle=False) for name in
                      ("document_embeddings", "query_embeddings_dense", "query_embeddings_hybrid")}
            for name, matrix in arrays.items(): independent.validate_array(matrix, len(docs) if name == "document_embeddings" else 2000)
            eq(bool(np.array_equal(arrays["query_embeddings_dense"], arrays["query_embeddings_hybrid"])), True)
            ranked = {r: read_rows(OUT / "rankings" / (dataset + "_" + r + ".jsonl")) for r in RETRIEVERS}
            top = read_rows(OUT / "top5" / (dataset + ".jsonl"))
            eq(len(top), 6000)
            for rows in ranked.values(): eq(len(rows), 2000)
            ids = [d["id"] for d in docs]; valid = set(ids)
            for i, row in enumerate(runtime):
                for r in RETRIEVERS: independent.validate_rank(ranked[r][i], dataset, row["id"], r, valid)
                bm = independent.ordered_entries(independent.bm_scores(row["question"], structure, lookup), ids, 100)
                dense = independent.ordered_entries(arrays["document_embeddings"] @ arrays["query_embeddings_dense"][i], ids, 100)
                eq(ranked["bm25"][i]["ranking"], bm)
                eq(ranked["dense"][i]["ranking"], dense)
                eq(ranked["hybrid"][i]["ranking"], independent.independent_rrf(bm, dense))
                for j, r in enumerate(RETRIEVERS):
                    independent.validate_top(top[i*3+j], ranked[r][i]); all_keys.append((dataset, row["id"], r))
                if (i+1) % 200 == 0: print("INDEPENDENT_QUESTIONS", dataset, i+1, flush=True)
            result["datasets"][dataset] = dict(questions=2000, traces=6000, pool_documents=len(docs), exact_numeric_rankings=True)
            del arrays, structure, lookup, docs, runtime, ranked, top
        eq(len(all_keys), 18000); eq(len(set(all_keys)), 18000)
        eq(any(name in sys.modules for name in ("torch", "transformers", "empirical_authenticated_retrieval")), False)
        eq(boundary["blocked"], [])
        result.update(status="PASS_INDEPENDENT_ORIGINAL_RETRIEVAL", questions=6000, traces=18000,
            independent_score_vectors=12000, independent_fusions=6000, exact_bm25_dense_rrf_top5=True,
            scope="Saved-array retrieval arithmetic and complete trace binding; no second full encoder replay or reader outcome evidence")
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    write_json(OUT / "INDEPENDENT_VALIDATION.json", result)
    if result["status"] == "FAIL": print(json.dumps(result)); return 2
    write_json(OUT / "SEAL.json", dict(status="PASS_ORIGINAL_RETRIEVAL_ONLY", independent_sha256=digest(OUT / "INDEPENDENT_VALIDATION.json"), cas_q2_status="NOT READY"))
    seal(OUT); print(json.dumps(result)); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
