"""Run the single invented-only concurrent Phi/BGE CUDA memory preflight."""
from __future__ import annotations

import argparse
import copy
import math
from pathlib import Path
import subprocess
import sys

from scripts.empirical_runtime_io import native_runtime
from scripts.phi_bge_joint_preflight_guard import compact, install
from scripts.phi_reader_development_runtime_common import GuardedGenerationTokenizer
from scripts.phi_reader_preflight_common import (
    PHI_RELATIVE, PHI_REVISION, REPO, configure_environment, configure_torch,
    invented_evidence, record, require, seal, write_json,
)


OUT = REPO / "outputs/cas_q2/phi_bge_joint_gpu_preflight_v2"
BGE_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
INPUT_FREEZE_MANIFEST = "17cb0c29e4d4a5b98991bbebf1368bdff0ebece6221ca163c73327bcf4bcedd9"
INPUT_VALIDATION_MANIFEST = "3d0488e18ff5433abc721230763aa82d57452a13a66322040904392a1ff0ccd0"
V1_FAILURE_MANIFEST = "692c75ac0a625bc3c5aec37562b0be5e73832d7b315df399b044a1b9600464c1"


def source_paths(original: Path) -> list[Path]:
    paths = [REPO / value for value in (
        "scripts/preflight_phi_bge_joint_gpu_v2.py", "scripts/phi_bge_joint_preflight_guard.py",
        "scripts/phi_reader_development_runtime_common.py", "scripts/phi_reader_input_freeze_common.py",
        "scripts/empirical_runtime_io.py", "docs/cas_q2/PHI_BGE_JOINT_PREFLIGHT_CONTRACT.md",
        "docs/cas_q2/PHI_READER_DEVELOPMENT_RUNTIME_CONTRACT.md", "docs/cas_q2/PHI_BGE_JOINT_PREFLIGHT_V2_AMENDMENT.md",
        "outputs/cas_q2/phi_reader_input_freeze_v2/SHA256_MANIFEST.json",
        "outputs/cas_q2/phi_reader_input_freeze_validation_v1/SHA256_MANIFEST.json",
        "outputs/cas_q2/phi_reader_gpu_preflight_v1/SHA256_MANIFEST.json",
        "outputs/cas_q2/phi_bge_joint_gpu_preflight_v1/SHA256_MANIFEST.json")]
    paths += [original / value for value in (
        "src/phase10/adapters.py", "src/phase10/contracts.py", "src/generation/parsing.py",
        "prompts/baseline_v1.txt", "prompts/repair_missing_v1.txt",
        "outputs/daa_v2_fresh_v1/runtime_branch_freeze/native_runtime.py",
        "outputs/daa_v2_fresh_v1/runtime_branch_freeze/runtime_support.py")]
    for relative in (PHI_RELATIVE, Path("data/models/huggingface/models--BAAI--bge-base-en-v1.5/snapshots") / BGE_REVISION):
        paths.extend(path for path in (original / relative).iterdir() if path.is_file())
    return sorted(set(path.resolve() for path in paths))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-root", type=Path, required=True); args = parser.parse_args()
    original = args.project_root.resolve(); require(not OUT.exists(), "single-use joint Phi/BGE preflight")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "commit joint preflight first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    OUT.mkdir(parents=True, exist_ok=False); configure_environment(OUT)
    result = {"status": "FAIL", "cas_q2_status": "NOT READY", "source_commit": commit, "model_loads": 0,
        "phi_logical_generations": 0, "phi_forward_calls": 0, "bge_forward_calls": 0,
        "benchmark_rows_read": 0, "generation_calls_on_benchmark": 0, "scientific_fit_calls": 0,
        "gold_reads": 0, "existing_answer_strings_read": 0}
    reader = bge = boundary = None
    try:
        import torch
        import transformers
        configure_torch(torch)
        require(record(REPO / "outputs/cas_q2/phi_reader_input_freeze_v2/SHA256_MANIFEST.json")["sha256"] == INPUT_FREEZE_MANIFEST, "input freeze pin")
        require(record(REPO / "outputs/cas_q2/phi_reader_input_freeze_validation_v1/SHA256_MANIFEST.json")["sha256"] == INPUT_VALIDATION_MANIFEST, "input validation pin")
        require(record(REPO / "outputs/cas_q2/phi_bge_joint_gpu_preflight_v1/SHA256_MANIFEST.json")["sha256"] == V1_FAILURE_MANIFEST, "V1 failure pin")
        wrapper, native, nodes, generation_boundary = native_runtime(original)
        paths = source_paths(original) + [Path(sys.executable)]
        inputs = [record(path) for path in sorted(set(paths))]
        write_json(OUT / "EXECUTABLE_FREEZE.json", {"source_commit": commit, "inputs": inputs,
            "native_ast_nodes": nodes, "generation_boundary": generation_boundary,
            "scope": "Two invented Phi generations and one invented BGE query forward with both models resident"})
        boundary = install(original, OUT, paths)
        bge = native.ExactLocalBGEBackend(model_cache_dir=original / "data/models/huggingface"); bge._ensure_loaded(); result["model_loads"] += 1
        reader = native.HFProspectiveReaderAdapter(reader="phi", model_cache_dir=original / "data/models/huggingface",
            answer_prompt_path=original / "prompts/baseline_v1.txt", repair_prompt_path=original / "prompts/repair_missing_v1.txt",
            max_answer_tokens=48, max_query_tokens=64, context_budget_characters=16000)
        reader._ensure_loaded(); result["model_loads"] += 1
        require(reader.model.config._commit_hash == PHI_REVISION and bge.model.config._commit_hash == BGE_REVISION, "joint model revisions")
        require(str(next(reader.model.parameters()).dtype) == str(next(bge.model.parameters()).dtype) == "torch.bfloat16", "joint BF16")
        require(not reader.model.training and not bge.model.training, "joint eval mode")
        phase = {"stage": None, "position": 0}; admissions = []
        reader.tokenizer = GuardedGenerationTokenizer(reader.tokenizer, phase, admissions)
        def phi_forward(model, args, kwargs):
            require(torch.is_inference_mode_enabled() and not torch.is_grad_enabled(), "Phi inference mode"); result["phi_forward_calls"] += 1
        def bge_forward(model, args, kwargs):
            require(torch.is_inference_mode_enabled() and not torch.is_grad_enabled(), "BGE inference mode"); result["bge_forward_calls"] += 1
        qhook = reader.model.register_forward_pre_hook(phi_forward, with_kwargs=True)
        bhook = bge.model.register_forward_pre_hook(bge_forward, with_kwargs=True)
        key = native.TraceKey("phi", "hotpotqa", "invented-joint-memory", "dense")
        invented_question = "In the invented toy scene, what color is the paper cog?"
        phase["stage"] = "repair_query"
        query = reader.generate_repair_query(key=key, question=invented_question,
            evidence=invented_evidence(native)); result["phi_logical_generations"] += 1
        short_capture = copy.deepcopy(reader._generation_capture)
        vector = bge.encode_queries([query.search_query]); require(vector.shape == (1, 768), "invented BGE vector")
        vector_norm = float((vector[0].astype("float64") ** 2).sum() ** 0.5); require(math.isfinite(vector_norm), "finite BGE norm")
        phase["stage"] = "a1"
        answer = reader.generate_answer(key=key, question=invented_question,
            evidence=invented_evidence(native, long=True), state="e1"); result["phi_logical_generations"] += 1
        long_capture = copy.deepcopy(reader._generation_capture)
        result.update(admissions=admissions, short_generation={"capture": short_capture,
            "result": {"search_query": query.search_query, "parser_fallback": query.parser_fallback}},
            long_generation={"capture": long_capture, "result": {"parsed_text": answer.parsed_text}})
        require(len(admissions) == 2 and admissions[0]["input_tokens"] == short_capture["input_tokens"] and
            admissions[1]["input_tokens"] == long_capture["input_tokens"] == 9472, "exact joint token admissions")
        qhook.remove(); bhook.remove()
        peak_allocated = int(torch.cuda.max_memory_allocated()); peak_reserved = int(torch.cuda.max_memory_reserved())
        result.update(status="PASS_PHI_BGE_JOINT_GPU_INVENTED_ONLY",
            bge={"revision": BGE_REVISION, "embedding_shape": list(vector.shape), "embedding_norm": vector_norm},
            phi_revision=PHI_REVISION, peak_allocated_cuda_bytes=peak_allocated, peak_reserved_cuda_bytes=peak_reserved,
            nominal_cuda_total_bytes=int(torch.cuda.get_device_properties(0).total_memory), execution_boundary=compact(boundary))
        reader.close(); bge.close(); reader = bge = None
        for row in inputs: require(record(Path(row["path"])) == row, "joint preflight input changed")
        require(not boundary["denied"], "joint preflight boundary")
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
        if boundary is not None: result["execution_boundary"] = compact(boundary)
    finally:
        if reader is not None: reader.close()
        if bge is not None: bge.close()
    write_json(OUT / "BUILD_RECEIPT.json", result); seal(OUT)
    print(result["status"], result.get("diagnostic", ""), flush=True); return 0 if result["status"].startswith("PASS_") else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
