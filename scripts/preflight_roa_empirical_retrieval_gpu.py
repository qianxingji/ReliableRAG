"""Pinned BGE GPU compatibility: exactly two invented-query forwards, no benchmark."""
import argparse
import importlib.metadata
from pathlib import Path
import platform
import subprocess
import sys

from scripts.empirical_retrieval_io import (REPO, GPU_OUT, REV, inputs, native_retrieval,
    configure_environment, guard, boundary_record, source_paths, seal, record, require)
from scripts.replay_roa_original import write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, required=True)
    args = p.parse_args(); root = args.project_root.resolve()
    require(not GPU_OUT.exists(), "Single-use GPU preflight")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    GPU_OUT.mkdir(parents=True, exist_ok=False)
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit, model_load_calls=0,
                  synthetic_embedding_forward_calls=0, benchmark_embedding_forward_calls=0,
                  scientific_fit_calls=0, fresh_gold_values_materialized=0)
    backend = None; boundary = None
    try:
        environment = configure_environment(GPU_OUT)
        # Standard library/package initialization only; no model or benchmark data.
        platform_metadata = platform.uname()._asdict()
        import numpy as np
        import torch
        import transformers
        cfg, pre, paths = inputs(root)
        packages = {k: importlib.metadata.version(k) for k in cfg["environment"]["packages"]}
        require(packages == cfg["environment"]["packages"], "Package versions")
        wrapper, native, nodes = native_retrieval(root)
        paths += source_paths() + [Path(sys.executable)]
        bound = [record(q) for q in sorted(set(paths))]
        write_json(GPU_OUT / "EXECUTABLE_FREEZE.json", dict(source_commit=commit, command=sys.argv,
            inputs=bound, environment=environment, platform_metadata=platform_metadata, packages=packages,
            native_ast_nodes=nodes, retrieval_config=pre["retriever_config"],
            scope="Two identical invented queries only; no benchmark text decode"))
        boundary = guard(root, GPU_OUT, paths, gpu_only=True)
        backend = native.ExactLocalBGEBackend(model_cache_dir=root / "data/models/huggingface")
        backend._ensure_loaded(); result["model_load_calls"] += 1
        require(backend.revision == REV and backend.dimension == 768, "Resolved model")
        require(str(next(backend.model.parameters()).dtype) == "torch.bfloat16", "BF16")
        def count(model, args):
            require(torch.is_inference_mode_enabled() and not torch.is_grad_enabled() and not model.training, "Inference mode")
            result["synthetic_embedding_forward_calls"] += 1
        handle = backend.model.register_forward_pre_hook(count)
        query = ["Invented fixture: where does the paper cog turn?"]
        first = backend.encode_queries(query); second = backend.encode_queries(query)
        handle.remove()
        require(np.array_equal(first, second) and first.shape == (1, 768) and first.dtype == np.float32, "Synthetic exact replay")
        require(np.isfinite(first).all() and result["synthetic_embedding_forward_calls"] == 2, "Synthetic count")
        actual = dict(device=str(backend.device), gpu=torch.cuda.get_device_name(0), model_class=backend.model.__class__.__name__,
            revision=backend.model.config._commit_hash, dtype=str(next(backend.model.parameters()).dtype),
            deterministic=torch.are_deterministic_algorithms_enabled(), tf32=torch.backends.cuda.matmul.allow_tf32,
            cudnn_tf32=torch.backends.cudnn.allow_tf32, cudnn_deterministic=torch.backends.cudnn.deterministic,
            cudnn_benchmark=torch.backends.cudnn.benchmark, attention=getattr(backend.model.config, "_attn_implementation", None))
        backend.close(); backend = None
        for e in bound: require(record(Path(e["path"])) == e, "Preflight frozen input changed")
        require(not boundary["denied"], "Preflight boundary denial")
        result.update(status="PASS_BGE_GPU_SYNTHETIC_ONLY", actual_backend=actual, exact_synthetic_embedding_replay=True)
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    finally:
        if backend is not None: backend.close()
    if boundary is not None: result["execution_boundary"] = boundary_record(boundary)
    write_json(GPU_OUT / "GPU_PREFLIGHT.json", result); seal(GPU_OUT)
    print(result["status"], result.get("diagnostic", ""), flush=True)
    return 0 if result["status"] == "PASS_BGE_GPU_SYNTHETIC_ONLY" else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
