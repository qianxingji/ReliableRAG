"""Joint pinned Qwen/BGE load and exactly two invented answer generations."""
import argparse
import copy
from pathlib import Path
import platform
import subprocess
import sys

from scripts.empirical_runtime_io import (REPO, GPU_OUT, bound_inputs, native_runtime, make_reader,
    check_models, source_paths, record, require, BGE_REV)
from scripts.empirical_runtime_guard import guard
from scripts.empirical_retrieval_io import configure_environment, boundary_record, seal
from scripts.replay_roa_original import write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    p.add_argument("--preparation-manifest-sha256", required=True)
    args = p.parse_args(); root = args.project_root.resolve()
    require(not GPU_OUT.exists(), "Single-use joint GPU preflight")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    GPU_OUT.mkdir(parents=True, exist_ok=False)
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit,
        synthetic_reader_generation_calls=0, synthetic_qwen_forward_calls=0, synthetic_bge_forward_calls=0,
        benchmark_generation_calls=0, scientific_fit_calls=0, fresh_gold_values_materialized=0)
    reader = bge = boundary = None
    try:
        environment = configure_environment(GPU_OUT); platform_metadata = platform.uname()._asdict()
        import torch
        import transformers
        cfg, paths = bound_inputs(root, args.preparation_manifest_sha256)
        wrapper, native, nodes, prefix = native_runtime(root)
        paths += source_paths() + [Path(sys.executable)]
        records = [record(p) for p in sorted(set(paths))]
        write_json(GPU_OUT / "EXECUTABLE_FREEZE.json", dict(source_commit=commit, command=sys.argv,
            inputs=records, environment=environment, platform_metadata=platform_metadata,
            native_ast_nodes=nodes, generation_boundary=prefix, runtime_config_sha256=cfg["runtime_config_sha256"],
            scope="Exactly two identical invented answers; both pinned models loaded, no benchmark text"))
        boundary = guard(root, GPU_OUT, paths, gpu_only=True)
        bge = native.ExactLocalBGEBackend(model_cache_dir=root / "data/models/huggingface"); bge._ensure_loaded()
        reader = make_reader(native, root); reader._ensure_loaded()
        actual = check_models(reader, bge, cfg)
        def count(model, args):
            require(torch.is_inference_mode_enabled() and not torch.is_grad_enabled() and not model.training, "Reader inference-only")
            result["synthetic_qwen_forward_calls"] += 1
        def no_bge_forward(model, args):
            result["synthetic_bge_forward_calls"] += 1
            raise RuntimeError("No BGE forward in joint load preflight")
        qhook = reader.model.register_forward_pre_hook(count); bhook = bge.model.register_forward_pre_hook(no_bge_forward)
        evidence = tuple(native.RankedDocument(i+1, "invented-doc-"+str(i), "0"*64, float(5-i),
            "Invented "+str(i), "In this invented toy scene, the paper cog is silver.") for i in range(5))
        key = native.TraceKey("qwen", "hotpotqa", "invented-joint-preflight", "bm25")
        captures = []
        for _ in range(2):
            answer = reader.generate_answer(key=key, question="In the invented toy scene, what color is the paper cog?", evidence=evidence, state="e0")
            result["synthetic_reader_generation_calls"] += 1
            captures.append(dict(capture=copy.deepcopy(reader._generation_capture), parsed_text=answer.parsed_text))
        require(captures[0] == captures[1], "Exact invented token/receipt replay")
        require(result["synthetic_qwen_forward_calls"] > 0 and result["synthetic_bge_forward_calls"] == 0, "Preflight forward scope")
        qhook.remove(); bhook.remove()
        actual["peak_allocated_cuda_bytes"] = torch.cuda.max_memory_allocated()
        reader.close(); bge.close(); reader = bge = None
        for e in records: require(record(Path(e["path"])) == e, "Joint preflight input changed")
        require(not boundary["denied"], "Joint preflight boundary")
        result.update(status="PASS_JOINT_READER_GPU_SYNTHETIC_ONLY", actual_backend=actual, exact_synthetic_token_replay=True,
            synthetic_receipt=captures[0], limitation="Short invented context checks compatibility; it does not guarantee peak memory or token determinism for every benchmark trace")
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    finally:
        if reader is not None: reader.close()
        if bge is not None: bge.close()
    if boundary is not None: result["execution_boundary"] = boundary_record(boundary)
    write_json(GPU_OUT / "GPU_PREFLIGHT.json", result); seal(GPU_OUT)
    print(result["status"], result.get("diagnostic", "")); return 2 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
