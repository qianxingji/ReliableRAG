"""Pinned native scoring constructors with explicit new-cache IO adaptation."""
from pathlib import Path
import shutil

from scripts.empirical_scoring_io import require, record
from scripts.empirical_scoring_import_v2 import source_only_import

BGE_REV = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
QWEN_REV = "aa8e72537993ba99e69dfaafa59ed015b17504d1"
NLI_REV = "5a4338ab2151dc8db04ad53b42b6153382bf4f99"
NLI_ID = "MoritzLaurer/deberta-v3-large-zeroshot-v2.0"
NLI_FILES = {"config.json", "tokenizer_config.json", "special_tokens_map.json", "added_tokens.json", "spm.model", "README.md", "model.safetensors"}


def fixed_configs(root, output, pre):
    """All scientific values must match the accepted historical config exactly."""
    root, output = Path(root).resolve(), Path(output).resolve()
    require(not output.is_relative_to(root), "New scoring output must be outside the original checkout")
    dense = dict(pre["phase3_config"]["dense"])
    wanted_dense = dict(batch_size=16, cache_dir="data/indexes/phase3", code_version="phase3-dense-batched-v1",
        dtype="bfloat16", index_backend="numpy_exact", max_length=512, model_cache_dir="data/models/huggingface",
        model_name="BAAI/bge-base-en-v1.5", normalize=True, pooling="cls",
        query_prefix="Represent this sentence for searching relevant passages: ", require_cuda=True, revision=BGE_REV)
    require(dense == wanted_dense, "Original answer-embedding configuration")
    dense.pop("cache_dir")
    dense.pop("model_cache_dir")
    dense.pop("require_cuda")
    reader = dict(pre["historical_config"]["reader_scorer"])
    wanted_reader = dict(model_name="Qwen/Qwen2.5-3B-Instruct", revision=QWEN_REV, dtype="bfloat16", batch_size=1,
        max_length=8192, require_cuda=True, model_cache_dir="data/models/huggingface",
        cache_dir="data/cache/mars_full/reader_likelihood", answer_prompt_path="prompts/baseline_v1.txt", context_budget_characters=16000)
    require(reader == wanted_reader, "Original likelihood scorer configuration")
    reader.update(model_cache_dir=str(root / "data/models/huggingface"),
        cache_dir=str(output / "cache/reader_likelihood"), answer_prompt_path=str(root / "prompts/baseline_v1.txt"))
    return dict(dense=dense, bge_cache_dir=root / "data/models/huggingface", reader=reader)


def nli_copy_plan(root, output, pre):
    """Authenticate every source before copying; no inherited cache or overwrite."""
    root, output = Path(root).resolve(), Path(output).resolve()
    require(not output.is_relative_to(root), "NLI cache outside original checkout")
    source = root / "outputs/published_baseline_gbv_nli_v1/infrastructure/model_snapshot"
    destination = output / "cache/hf/hub/models--MoritzLaurer--deberta-v3-large-zeroshot-v2.0/snapshots" / NLI_REV
    require(not destination.exists(), "New empty pinned NLI snapshot namespace")
    plan, names = [], set()
    for entry in pre["gbv"]["files"]:
        path = (root / entry["path"]).resolve()
        require(path.parent == source and path.name in NLI_FILES and path.name not in names, "Exact original snapshot member")
        names.add(path.name)
        actual = record(path)
        require(actual["sha256"] == entry["sha256"] and actual["size_bytes"] == entry["size_bytes"], "Pinned NLI snapshot source unchanged")
        target = destination / path.name
        require(target.resolve().is_relative_to(output) and not target.exists(), "Exclusive NLI cache destination")
        plan.append(dict(source=actual, target=str(target)))
    require(names == NLI_FILES, "Complete seven-file original NLI snapshot")
    return plan


def stage_nli_cache(root, output, pre):
    """Byte copies into the new HF_HOME; retain original model ID/revision loading."""
    plan = nli_copy_plan(root, output, pre)
    for item in plan:
        target = Path(item["target"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with Path(item["source"]["path"]).open("rb") as source, target.open("xb") as dest:
            shutil.copyfileobj(source, dest, 1024 * 1024)
        actual = record(target)
        require(actual["sha256"] == item["source"]["sha256"] and actual["size_bytes"] == item["source"]["size_bytes"], "Copied NLI snapshot bytes")
        item["copied"] = actual
    return plan


def make_bge(native, root, output, pre):
    cfg = fixed_configs(root, output, pre)
    model = native.HFEmbeddingBackend(native.DenseConfig(**cfg["dense"]), cache_dir=cfg["bge_cache_dir"], require_cuda=True)
    require(model.model.__class__.__name__ == "BertModel" and model.metadata["resolved_revision"] == BGE_REV and
        model.metadata["actual_dtype"] == "torch.bfloat16" and model.metadata["device"].startswith("cuda") and
        not model.model.training and model.dimension == 768, "Pinned native answer embedding backend")
    return model


def make_likelihood(native, root, output, pre):
    cfg = fixed_configs(root, output, pre)
    cache = Path(cfg["reader"]["cache_dir"])
    require(not cache.exists(), "Initially empty native likelihood cache")
    model = native.likelihood.ReaderLikelihoodScorer(cfg["reader"])
    require(model.model.__class__.__name__ == "Qwen2ForCausalLM" and model.metadata["resolved_revision"] == QWEN_REV and
        model.metadata["dtype"] == "torch.bfloat16" and model.metadata["device"].startswith("cuda") and not model.model.training,
        "Pinned native teacher-forced reader")
    return model


def make_gbv(root, output):
    """Caller stages/authenticates local assets and sets HF_HOME before HF imports."""
    import os
    root, output = Path(root).resolve(), Path(output).resolve()
    require(Path(os.environ.get("HF_HOME", "")).resolve() == output / "cache/hf", "Per-execution NLI HF_HOME")
    require(os.environ.get("HF_HUB_OFFLINE") == os.environ.get("TRANSFORMERS_OFFLINE") == "1", "Local-only scoring environment")
    # HF constants must have resolved only after this execution's environment.
    from huggingface_hub.constants import HF_HUB_CACHE
    require(Path(HF_HUB_CACHE).resolve() == output / "cache/hf/hub", "No stale global HF cache binding")
    native = source_only_import("src.verification.gbv_nli", root / "src/verification/gbv_nli.py")
    scorer = native.GBVPostAnsweringNLI(model_id=NLI_ID, revision=NLI_REV, device="cuda:0", batch_size=8,
        torch_dtype="float32", local_files_only=True)
    require(scorer.model.__class__.__name__ == "DebertaV2ForSequenceClassification" and
        scorer.model.config._commit_hash == NLI_REV and scorer.resolved_dtype == "torch.float32" and
        not scorer.model.training and not scorer.tokenizer.is_fast and scorer.entailment_index == 0 and scorer.max_length == 512,
        "Pinned native slow-tokenizer binary FP32 GbV")
    return native, scorer
