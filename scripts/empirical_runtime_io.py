"""Authenticated reader assembly and restoration of already sealed retrieval arrays."""
import hashlib
import json
from pathlib import Path
import sys

from scripts.empirical_retrieval_io import (REPO, POOL, OUT as RETRIEVAL, GPU_OUT as BGE_GPU,
    inputs as acquisition_inputs, verify_namespace, load, record, require, import_file)
from scripts.empirical_runtime_contract import canonical, sha_json, trace_key
from scripts.verify_roa_artifacts import digest

OUT = REPO / "outputs/cas_q2/empirical_runtime_v1"
GPU_OUT = REPO / "outputs/cas_q2/empirical_runtime_gpu_preflight_v1"
PREPARATION = REPO / "outputs/cas_q2/empirical_runtime_preparation_v1"
CPU_TESTS = REPO / "outputs/cas_q2/empirical_runtime_native_tests_v1"
CPU_TEST_SHA = "cf861b1a90c3725e04878bc49892d609a27b12a1ba64fab9d6d712fe69e01410"
QREV = "aa8e72537993ba99e69dfaafa59ed015b17504d1"
BGE_REV = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"


def read_rows(path):
    with path.open(encoding="utf-8") as stream: return [json.loads(line) for line in stream]


def native_runtime(root):
    old = root / "outputs/daa_v2_fresh_v1/runtime_branch_freeze"
    import_file("runtime_support", old / "runtime_support.py")
    wrapper = import_file("empirical_authenticated_runtime", old / "native_runtime.py")
    native, nodes, generation_boundary = wrapper.accepted()
    expected = load(CPU_TESTS / "CPU_TEST_RESULT.json")
    require(nodes == expected["accepted_native_ast_nodes"] and generation_boundary == expected["generation_boundary"],
            "Runtime differs from original tested assembly")
    return wrapper, native, nodes, generation_boundary


def bound_inputs(root, preparation_sha):
    cfg, pre, paths = acquisition_inputs(root)
    paths += verify_namespace(CPU_TESTS, CPU_TEST_SHA)
    paths += verify_namespace(PREPARATION, preparation_sha)
    prepared = load(PREPARATION / "PREPARATION_RESULT.json")
    require(prepared["status"] == "PASS_RUNTIME_TRACE_PREPARATION_ONLY", "Runtime preparation status")
    freeze = load(PREPARATION / "TRACE_PREPARATION_FREEZE.json")
    for e in freeze["inputs"]:
        require(record(Path(e["path"])) == e, "Runtime preparation input changed")
        paths.append(Path(e["path"]))
    mp = root / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/SHA256_MANIFEST.json"
    item = next(e for e in load(mp)["files"] if e["path"].endswith("runtime_branch_freeze/independent_validate.py"))
    path = root / item["path"]
    require(digest(path) == item["sha256"] and path.stat().st_size == item["size_bytes"], "Original independent runtime source")
    paths.append(path)
    # All canonical retrieval payloads are directly covered by the preparation records.
    require(load(RETRIEVAL / "INDEPENDENT_VALIDATION.json")["status"] == "PASS_INDEPENDENT_ORIGINAL_RETRIEVAL", "Accepted original retrieval")
    return cfg, sorted(set(paths))


def restore_dataset(dataset, native, backend):
    """Path adaptation of native restore_dataset; no index construction or re-embedding."""
    import numpy as np
    pool_path = POOL / "pools" / (dataset + ".jsonl")
    runtime_path = POOL / "runtime" / (dataset + ".jsonl")
    docs = read_rows(pool_path); runtime = read_rows(runtime_path)
    summary = load(POOL / "INDEPENDENT_VALIDATION.json")["datasets"][dataset]
    corpus = native.Corpus(tuple(native.IndexedDocument(d["id"], dataset, d["title"], tuple(d["sentences"]), d["content_hash"])
                                 for d in docs), summary["corpus_fingerprint"])
    index = RETRIEVAL / "indexes" / dataset
    payload = load(index / "bm25_structure.json")
    require(payload["document_ids"] == [d.id for d in corpus.documents], "Stored BM25 order")
    bm = native.FastBM25Index.__new__(native.FastBM25Index)
    bm.corpus = corpus; bm.config = native.BM25Config()
    bm.lengths = np.asarray(payload["lengths"], dtype=np.float64); bm.average_length = payload["average_length"]
    bm.postings = {x["term"]: [tuple(p) for p in x["postings"]] for x in payload["terms"]}
    bm.idf = {x["term"]: x["idf"] for x in payload["terms"]}
    matrix = np.load(index / "document_embeddings.npy", allow_pickle=False)
    require(matrix.dtype == np.float32 and matrix.shape == (len(docs), 768), "Frozen document matrix")
    router = native.SharedCorpusRetriever()
    router.dataset = dataset; router.corpus = corpus; router.corpus_fingerprint = corpus.fingerprint
    router.bm25 = bm; router.document_embeddings = matrix; router.dense_backend = backend
    router.hybrid_rrf_k = 60; router.hybrid_component_depth = 100
    original_scores = router._from_scores; components = []
    def capture_scores(scores, depth):
        ranked = original_scores(scores, depth)
        components.append([dict(document_id=r.document.id, rank=r.rank, score=float(r.score)) for r in ranked])
        return ranked
    router._from_scores = capture_scores
    ranks = {r: {x["sample_id"]: x["ranking"] for x in read_rows(RETRIEVAL / "rankings" / (dataset + "_" + r + ".jsonl"))}
             for r in ("bm25", "dense", "hybrid")}
    return dict(router=router, corpus=corpus, documents={d.id: d for d in corpus.documents},
        questions={r["id"]: r["question"] for r in runtime}, original_rankings=ranks, components=components,
        binding=dict(pool_sha256=digest(pool_path), runtime_projection_sha256=digest(runtime_path),
                     corpus_fingerprint=corpus.fingerprint, canonical_document_id_sequence_sha256=sha_json([d.id for d in corpus.documents])))


def make_reader(native, root):
    return native.HFProspectiveReaderAdapter(reader="qwen", model_cache_dir=root / "data/models/huggingface",
        answer_prompt_path=root / "prompts/baseline_v1.txt", repair_prompt_path=root / "prompts/repair_missing_v1.txt",
        max_answer_tokens=48, max_query_tokens=64, context_budget_characters=16000)


def check_models(reader, bge, cfg):
    import torch
    require(reader.model.__class__.__name__ == "Qwen2ForCausalLM" and reader.model.config._commit_hash == QREV, "Pinned Qwen")
    require(bge.model.__class__.__name__ == "BertModel" and bge.model.config._commit_hash == BGE_REV and bge.dimension == 768, "Pinned BGE")
    require(str(next(reader.model.parameters()).dtype) == str(next(bge.model.parameters()).dtype) == "torch.bfloat16", "Joint BF16")
    require(not reader.model.training and not bge.model.training and torch.are_deterministic_algorithms_enabled(), "Inference determinism")
    require(not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32 and
            not torch.backends.cudnn.benchmark and torch.backends.cudnn.deterministic, "CUDA flags")
    for stage, budget in (("a0",48), ("repair_query",64), ("a1",48)):
        effective = reader.model.generation_config.to_dict()
        effective.update(do_sample=False, max_new_tokens=budget, pad_token_id=reader.tokenizer.pad_token_id,
            eos_token_id=reader.tokenizer.eos_token_id, use_cache=True, return_dict_in_generate=True, output_scores=True)
        require(effective == cfg["runtime_config"]["effective_generation_configs"][stage], "Original inherited generation config")
    template = hashlib.sha256(reader.tokenizer.chat_template.encode("utf-8")).hexdigest()
    require(template == cfg["runtime_config"]["tokenizer_chat_template_sha256"], "Original tokenizer chat template")
    return dict(qwen_revision=QREV, bge_revision=BGE_REV, device=str(reader.device), dtype="torch.bfloat16",
        qwen_attention=reader.model.config._attn_implementation, bge_attention=bge.model.config._attn_implementation,
        tokenizer_chat_template_sha256=template, runtime_config_sha256=cfg["runtime_config_sha256"],
        deterministic_algorithms=True, tf32=False, runtime_seed=20260828)


def source_paths():
    return [REPO / name for name in (
        "scripts/empirical_runtime_io.py", "scripts/empirical_runtime_guard.py", "scripts/empirical_runtime_contract.py",
        "scripts/preflight_roa_empirical_runtime_gpu.py", "scripts/build_roa_empirical_runtime.py",
        "scripts/validate_roa_empirical_runtime.py", "scripts/prepare_roa_empirical_runtime.py",
        "scripts/check_roa_empirical_runtime_native.py", "scripts/empirical_retrieval_io.py",
        "scripts/empirical_pool_io.py", "scripts/replay_roa_original.py", "scripts/verify_roa_artifacts.py",
        "tests/test_empirical_runtime_contract.py", "tests/test_empirical_runtime_guard.py",
        "tests/test_empirical_runtime_validation.py", "docs/cas_q2/EMPIRICAL_C3_RUNTIME_CONTRACT.md")]
