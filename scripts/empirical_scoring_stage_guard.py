"""Stage-specific restrictions added to the unchanged C4 write/import boundary."""
import os
from pathlib import Path
import sys

from scripts.empirical_scoring_guard import guard as original_guard
from scripts.empirical_pool_io import REPO


def guard(root, output, paths, *, stage):
    if stage not in {"gpu_preflight", "base", "gbv", "policies", "independent"}:
        raise ValueError("Fixed scoring execution stage")
    # Fresh CPU policy/validation inputs require their own stage rules. The old
    # cpu_models mode was explicitly invented-only and is not silently widened.
    receipt = original_guard(root, output, paths, mode="neural")
    receipt["stage"] = stage
    receipt["top_level_forward_calls"] = {}
    prior_profile = sys.getprofile()
    root, output = Path(root).resolve(), Path(output).resolve()
    projects = REPO / "outputs/cas_q2"
    bge = root / "data/models/huggingface/models--BAAI--bge-base-en-v1.5"
    qwen = root / "data/models/huggingface/models--Qwen--Qwen2.5-3B-Instruct"
    nli = root / "outputs/published_baseline_gbv_nli_v1/infrastructure/model_snapshot"
    def opaque():
        frame = sys._getframe(2)
        while frame:
            if frame.f_code.co_name == "digest" and Path(frame.f_code.co_filename).resolve() == REPO / "scripts/verify_roa_artifacts.py":
                return True
            frame = frame.f_back
        return False
    def deny(message):
        receipt["denied"].append(message)
        raise RuntimeError("C4 stage boundary: " + message)
    def audit(event, args):
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = isinstance(mode, str) and any(c in mode for c in "wax+") or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing or opaque():
            return
        if stage == "gpu_preflight" and path.is_relative_to(projects) and not path.is_relative_to(output) and path.suffix in {".jsonl", ".npy"}:
            deny("benchmark/private ledger decoding in GPU preflight")
        if path.suffix == ".safetensors" or path.name == "pytorch_model.bin":
            permitted = ((stage == "gpu_preflight" and (path.is_relative_to(bge) or path.is_relative_to(qwen) or path.is_relative_to(nli) or path.is_relative_to(output / "cache/hf")))
                or (stage == "base" and (path.is_relative_to(bge) or path.is_relative_to(qwen)))
                or (stage == "gbv" and (path.is_relative_to(nli) or path.is_relative_to(output / "cache/hf"))))
            if not permitted:
                deny("neural weight loading outside stage")
        if stage == "gbv" and path.suffix in {".joblib", ".pkl"}:
            deny("unneeded learned estimator loading in GbV stage")
    sys.addaudithook(audit)
    def profile(frame, event, arg):
        prior_profile(frame, event, arg)
        if event != "call":
            return
        name = frame.f_code.co_name
        if name in {"retrieve", "search", "rank", "encode_queries"} and Path(frame.f_code.co_filename).is_relative_to(root / "src/retrieval"):
            deny("new retrieval/query embedding in scoring")
        model = frame.f_locals.get("self")
        if name == "forward" and hasattr(model, "parameters"):
            if stage in {"policies", "independent"}:
                deny("neural forward in CPU policy/independent stage")
            cls = type(model).__name__
            if cls in {"BertModel", "Qwen2ForCausalLM", "DebertaV2ForSequenceClassification"}:
                allowed = {"BertModel", "Qwen2ForCausalLM"} if stage == "base" else {"DebertaV2ForSequenceClassification"} if stage == "gbv" else {"BertModel", "Qwen2ForCausalLM", "DebertaV2ForSequenceClassification"}
                if cls not in allowed:
                    deny("wrong top-level neural model for stage")
                receipt["top_level_forward_calls"][cls] = receipt["top_level_forward_calls"].get(cls, 0) + 1
    sys.setprofile(profile)
    return receipt
