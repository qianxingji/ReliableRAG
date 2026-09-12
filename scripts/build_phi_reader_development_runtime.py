"""Run or resume one frozen Phi development pass or its fixed 180-trace replay."""
from __future__ import annotations

import argparse
import collections
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import types

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.phi_reader_development_runtime_common import (
    DurableCallEvents, DurableJsonl, GuardedGenerationTokenizer, event_id,
    object_sha, validate_call_events, validate_frozen_generation_capture, validate_generation_receipt,
    validate_completed_trace_rows, validate_output_name, validate_repair_receipt, validate_resume_prefix, validate_trace_input_binding,
    verify_manifest_members, verify_recorded_tree, verify_selected_manifest_members,
)
from scripts.phi_reader_development_runtime_guard import compact as compact_boundary
from scripts.phi_reader_development_runtime_guard import install as install_boundary
from scripts.phi_reader_input_freeze_common import canonical, digest, load, record, require, rows, text_sha
from scripts.phi_reader_preflight_common import configure_environment, configure_torch


REPO = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = REPO / "outputs/cas_q2"
OLD_RUNTIME_RELATIVE = Path("outputs/daa_v2_fresh_v1/runtime_branch_freeze")
LEDGER_FILES = {
    "generation_receipts": "generation_receipts.jsonl",
    "repair_bindings": "repair_bindings.jsonl",
    "branch_provenance": "branch_provenance.jsonl",
    "canonical_branches": "canonical_branches.jsonl",
}
PHI_REVISION = "2fe192450127e6a83f7441aef6e3ca586c338b77"
BGE_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
PINNED_MANIFESTS = {
    "phi_input_freeze": ("outputs/cas_q2/phi_reader_input_freeze_v2/SHA256_MANIFEST.json", "17cb0c29e4d4a5b98991bbebf1368bdff0ebece6221ca163c73327bcf4bcedd9"),
    "phi_input_validation": ("outputs/cas_q2/phi_reader_input_freeze_validation_v1/SHA256_MANIFEST.json", "3d0488e18ff5433abc721230763aa82d57452a13a66322040904392a1ff0ccd0"),
    "phi_joint_preflight": ("outputs/cas_q2/phi_bge_joint_gpu_preflight_v2/SHA256_MANIFEST.json", "ecf17a8af6c21fe2887700993bafe53c4aa8ae3c5419112737049db5c91ef2bf"),
    "phi_joint_validation": ("outputs/cas_q2/phi_bge_joint_gpu_preflight_validation_v1/SHA256_MANIFEST.json", "931391743a6ce4c64164973801eeffde0476545552c79d6b150458cd1b7d417d"),
}
ORIGINAL_MANIFEST_PINS = {
    "runtime": (OLD_RUNTIME_RELATIVE / "SHA256_MANIFEST.json", "0e831d2807ee48197029f03f8ed1e18381a60bc5fc25327edccc8d8486b6cefb"),
    "pool": (Path("outputs/daa_v2_fresh_v1/pool_freeze/SHA256_MANIFEST.json"), "f53575bc7b9514f33a235f8380520b99c2faac4cb8b6d78533fc42cb08f377b8"),
    "retrieval": (Path("outputs/daa_v2_fresh_v1/retrieval_freeze/SHA256_MANIFEST.json"), "15a18dc5c2a61a83171add05be2cb989813ab023ffea8a035cb1ba42dacdf651"),
}


def _import_file(name: str, path: Path):
    # Compile the authenticated source bytes directly.  Importlib may silently
    # prefer an old __pycache__ file, which is outside the executable freeze.
    module = types.ModuleType(name); module.__file__ = str(path); module.__package__ = ""
    sys.modules[name] = module
    payload = Path(path).read_bytes()
    exec(compile(payload.decode("utf-8-sig"), str(path), "exec"), module.__dict__)
    return module


def write_json_durable(path: Path, value: object) -> None:
    path = Path(path); require(not path.exists(), f"refuse overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n")
        stream.flush(); os.fsync(stream.fileno())


def seal_output(output: Path) -> None:
    files = [record(path) for path in sorted(output.rglob("*")) if path.is_file()]
    for row in files: row["path"] = Path(row["path"]).relative_to(output).as_posix()
    write_json_durable(output / "SHA256_MANIFEST.json", {"status": "PASS", "files": files,
        "excludes_only": "SHA256_MANIFEST.json", "exact_recursive_coverage": True})


def load_original_native(original: Path):
    frozen = original / OLD_RUNTIME_RELATIVE
    support = _import_file("runtime_support", frozen / "runtime_support.py")
    require(support.ROOT == original, "original runtime root binding")
    _import_file("retrieval_support", original / "outputs/daa_v2_fresh_v1/retrieval_freeze/retrieval_support.py")
    loader = _import_file("phi_development_original_native_runtime", frozen / "native_runtime.py")
    loader.import_file = _import_file
    native, nodes, boundary = loader.accepted()
    tested = load(frozen / "SYNTHETIC_TEST_RESULT_V2.json")
    require(tested["status"] == "PASS" and tested["tests_run"] == 22 and not tested["errors"] and not tested["failures"],
            "original native runtime tests")
    require(nodes == tested["accepted_ast_nodes"] and boundary == tested["boundary"], "tested native assembly")
    return loader, native, nodes, boundary


def source_paths(original: Path, canonical_reference: Path | None) -> list[Path]:
    paths = [REPO / value for value in (
        "scripts/build_phi_reader_development_runtime.py",
        "scripts/phi_reader_development_runtime_common.py",
        "scripts/phi_reader_development_runtime_guard.py",
        "scripts/phi_reader_input_freeze_common.py",
        "scripts/phi_reader_preflight_common.py",
        "tests/test_phi_reader_development_runtime.py",
        "docs/cas_q2/PHI_READER_DEVELOPMENT_RUNTIME_CONTRACT.md",
        "docs/cas_q2/PHI_READER_REPLICATION_PROTOCOL_V1.md",
        "docs/cas_q2/PHI_BGE_JOINT_PREFLIGHT_ACCEPTANCE.md",
        "docs/cas_q2/PHI_READER_INPUT_FREEZE_ACCEPTANCE.md",
    )]
    for relative, expected in PINNED_MANIFESTS.values():
        manifest = REPO / relative
        paths += verify_manifest_members(namespace=manifest.parent, manifest_path=manifest,
            expected_manifest_sha256=expected)
    runtime_manifest_relative, runtime_manifest_sha = ORIGINAL_MANIFEST_PINS["runtime"]
    runtime_manifest = original / runtime_manifest_relative
    runtime_required = [original / OLD_RUNTIME_RELATIVE / value for value in (
        "runtime_support.py", "native_runtime.py", "RUNTIME_CONFIG_FREEZE.json",
        "SYNTHETIC_TEST_RESULT_V2.json", "trace_manifest.jsonl", "replay_subset.jsonl",
    )]
    paths += verify_selected_manifest_members(namespace=runtime_manifest.parent, manifest_path=runtime_manifest,
        expected_manifest_sha256=runtime_manifest_sha, record_base=original, required_paths=runtime_required)
    for name in ("pool", "retrieval"):
        relative, expected = ORIGINAL_MANIFEST_PINS[name]
        manifest = original / relative
        paths += verify_manifest_members(namespace=manifest.parent, manifest_path=manifest,
            expected_manifest_sha256=expected, record_base=original, allow_only_extra_pycache=True)
    paths += [original / value for value in (
        "prompts/baseline_v1.txt", "prompts/repair_missing_v1.txt",
        "src/datasets/schema.py", "src/retrieval/corpus.py", "src/retrieval/base.py",
        "src/retrieval/bm25.py", "src/retrieval/hybrid.py", "src/phase3/retrieval.py",
        "src/phase10/contracts.py", "src/phase10/adapters.py", "src/phase10/validation.py",
        "src/phase10/runner.py", "src/phase10/pipeline_v2r3.py", "src/generation/parsing.py",
        "src/evaluation/fresh_schema.py",
        "outputs/phase10_extension_private_v2r3/inputs/runtime_config.yaml",
        "outputs/phase10_extension_private_v2r3/inputs/executable_input_allowlist.json",
        "outputs/phase10_extension_private_v2r3/inputs/environment_model_preflight.json",
        "outputs/phase10_extension_private_v2r3/inputs/candidate_pool_manifest.json",
    )]
    joint_freeze = load(REPO / "outputs/cas_q2/phi_bge_joint_gpu_preflight_v2/EXECUTABLE_FREEZE.json")
    joint_records = {Path(row["path"]).resolve(): row for row in joint_freeze["inputs"]}
    snapshot_roots = [
        (original / f"data/models/huggingface/models--microsoft--Phi-3.5-mini-instruct/snapshots/{PHI_REVISION}").resolve(),
        (original / f"data/models/huggingface/models--BAAI--bge-base-en-v1.5/snapshots/{BGE_REVISION}").resolve(),
    ]
    for snapshot in snapshot_roots:
        accepted = [row for path, row in joint_records.items() if path.is_relative_to(snapshot)]
        require(accepted, "joint preflight model snapshot records")
        paths += verify_recorded_tree(snapshot, accepted)
    joint_required = [Path(sys.executable).resolve(),
        (original / OLD_RUNTIME_RELATIVE / "native_runtime.py").resolve(),
        (original / OLD_RUNTIME_RELATIVE / "runtime_support.py").resolve(),
        (original / "prompts/baseline_v1.txt").resolve(), (original / "prompts/repair_missing_v1.txt").resolve()]
    for path in joint_required:
        require(path in joint_records and record(path) == joint_records[path], "joint preflight executable input binding")
    if canonical_reference is not None:
        paths += verify_sealed_namespace(canonical_reference)
    paths.append(Path(sys.executable))
    result = sorted(set(path.resolve() for path in paths))
    require(all(path.is_file() for path in result), "executable input missing")
    verify_applicable_joint_bindings(result, joint_records, original=original, interpreter=Path(sys.executable))
    return result


def verify_pins(original: Path) -> dict:
    pins = {}
    for name, (relative, expected) in PINNED_MANIFESTS.items():
        path = REPO / relative
        require(digest(path) == expected, f"{name} manifest pin")
        pins[name] = record(path)
    for name, (relative, expected) in ORIGINAL_MANIFEST_PINS.items():
        path = original / relative
        require(digest(path) == expected, f"original {name} manifest pin")
        pins["original_" + name] = record(path)
    return pins


def verify_applicable_joint_bindings(paths: list[Path], joint_records: dict[Path, dict], *,
                                     original: Path, interpreter: Path) -> None:
    """Bind accepted external inputs, excluding this prospective implementation."""
    original, interpreter = Path(original).resolve(), Path(interpreter).resolve()
    for path in paths:
        path = Path(path).resolve()
        if path in joint_records and (path == interpreter or path.is_relative_to(original)):
            require(record(path) == joint_records[path], "joint preflight applicable input binding")


def verify_sealed_namespace(path: Path) -> list[Path]:
    manifest = load(path / "SHA256_MANIFEST.json")
    expected = {row["path"] for row in manifest["files"]} | {"SHA256_MANIFEST.json"}
    actual = {item.relative_to(path).as_posix() for item in path.rglob("*") if item.is_file()}
    require(expected == actual and manifest.get("exact_recursive_coverage") is True, "canonical namespace seal coverage")
    members = [path / "SHA256_MANIFEST.json"]
    for row in manifest["files"]:
        item = path / row["path"]
        require(item.resolve().is_relative_to(path.resolve()), "canonical seal member path")
        require(item.stat().st_size == row["size_bytes"] and digest(item) == row["sha256"], "canonical namespace seal hash")
        members.append(item)
    return members


def acquire_gpu_mutex():
    """Exclude another instance of this benchmark executor on the Windows host."""
    require(os.name == "nt", "Phi development runtime is bound to the accepted Windows host")
    import ctypes
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, "Local\\ReliableRAG_Phi_Development_Runtime_GPU")
    require(handle, "cannot create Phi development GPU mutex")
    if kernel32.GetLastError() == 183:
        kernel32.CloseHandle(handle)
        raise RuntimeError("another Phi development runtime holds the GPU mutex")
    return handle


def runtime_config(reader, bge, native) -> dict:
    import torch
    import numpy
    import transformers
    protocol = native.FrozenProtocol()
    require(protocol.context_top_k == 5 and protocol.repair_candidate_depth == 50 and
            protocol.replacement_position_zero_based == 4 and protocol.context_budget_characters == 16_000 and
            protocol.answer_max_new_tokens == 48 and protocol.repair_query_max_new_tokens == 64,
            "native frozen protocol values")
    require(reader.reader == "phi" and reader.revision == PHI_REVISION and reader.model.config._commit_hash == PHI_REVISION,
            "pinned Phi revision")
    require(bge.model.config._commit_hash == BGE_REVISION and bge.dimension == 768, "pinned BGE revision")
    require(reader.model.__class__.__name__ == "Phi3ForCausalLM" and bge.model.__class__.__name__ == "BertModel",
            "accepted Phi/BGE model classes")
    require(str(next(reader.model.parameters()).dtype) == str(next(bge.model.parameters()).dtype) == "torch.bfloat16",
            "joint BF16")
    require(not reader.model.training and not bge.model.training and torch.are_deterministic_algorithms_enabled(),
            "single-process inference determinism")
    require(not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32 and
            not torch.backends.cudnn.benchmark and torch.backends.cudnn.deterministic, "CUDA deterministic flags")
    versions = {"torch": torch.__version__, "transformers": transformers.__version__, "numpy": numpy.__version__}
    require(versions == {"torch": "2.7.1+cu128", "transformers": "4.53.2", "numpy": "2.2.6"},
            "accepted runtime library versions")
    generations = {}
    for stage, maximum in (("a0", 48), ("repair_query", 64), ("a1", 48)):
        effective = reader.model.generation_config.to_dict()
        effective.update(do_sample=False, max_new_tokens=maximum, pad_token_id=reader.tokenizer.pad_token_id,
            eos_token_id=reader.tokenizer.eos_token_id, use_cache=True, return_dict_in_generate=True, output_scores=True)
        generations[stage] = effective
    return {
        "reader": "microsoft/Phi-3.5-mini-instruct", "reader_revision": PHI_REVISION,
        "bge": "BAAI/bge-base-en-v1.5", "bge_revision": BGE_REVISION, "dtype": "torch.bfloat16",
        "device": str(reader.device), "batch_size": 1, "active_reader_instances": 1,
        "answer_max_new_tokens": 48, "repair_query_max_new_tokens": 64,
        "context_budget_characters": 16_000, "maximum_generation_input_tokens": 9_472,
        "original_evidence_top_k": 5, "original_question_retrieval_calls": 0,
        "repair_candidate_depth": 50, "replacement_position_zero_based": 4,
        "same_retriever_repair": True, "do_sample": False, "runtime_seed": 20260830,
        "tokenizer_class": reader.tokenizer.__class__.__name__,
        "tokenizer_chat_template_sha256": text_sha(reader.tokenizer.chat_template),
        "reader_model_class": reader.model.__class__.__name__, "bge_model_class": bge.model.__class__.__name__,
        "reader_attention": reader.model.config._attn_implementation, "bge_attention": bge.model.config._attn_implementation,
        "versions": versions,
        "effective_generation_configs": generations,
    }


def read_runtime_inputs(original: Path):
    frozen = original / OLD_RUNTIME_RELATIVE
    traces = list(rows(frozen / "trace_manifest.jsonl"))
    frozen_rows = list(rows(REPO / "outputs/cas_q2/phi_reader_input_freeze_v2/INPUT_LENGTHS_PRIVATE.jsonl"))
    frozen_index = validate_trace_input_binding(traces, frozen_rows)
    replay = list(rows(frozen / "replay_subset.jsonl"))
    require(len(replay) == 180, "fixed replay count")
    by_position = {trace["position"]: trace for trace in traces}
    require(len(by_position) == len(traces) and all(by_position[row["position"]] == row for row in replay),
            "replay rows are exact canonical trace members")
    strata = collections.Counter((row["dataset"], row["retriever"]) for row in replay)
    require(set(strata.values()) == {20} and len(strata) == 9, "replay 20-per-cell contract")
    return traces, replay, frozen_index


def _row_lookup(rows_: list[dict], *, stages: bool = False) -> dict:
    result = {}
    for row in rows_:
        key = (row["dataset"], row["retriever"], row["sample_id"])
        if stages: key = (*key, row["stage"])
        require(key not in result, "duplicate ledger row")
        result[key] = row
    return result


def _answer(native, row: dict):
    render = row["render"]
    return native.GeneratedAnswer(row["raw_text"], row["parsed_text"], row["input_tokens"], row["output_tokens"],
        None, None, render["context_truncated"], render["context_budget_characters"],
        tuple(render["ordered_passed_document_ids"]), tuple(render["per_document_truncated"]), 0.0, False, False, 1)


def _query(native, row: dict):
    render = row["render"]
    return native.GeneratedRepairQuery(row["raw_text"], row["parsed_text"], row["parser_fallback"],
        row["input_tokens"], row["output_tokens"], render["context_truncated"], render["context_budget_characters"],
        tuple(render["ordered_passed_document_ids"]), tuple(render["per_document_truncated"]), 0.0, False, False, 1)


def _string_field_count(value) -> int:
    if isinstance(value, str): return 1
    if isinstance(value, list): return sum(_string_field_count(item) for item in value)
    if isinstance(value, dict): return sum(_string_field_count(item) for item in value.values())
    return 0


def selected_reference_bytes(canonical_output: Path, traces: list[dict], *, canonical_trace_count: int = 13_500):
    maps, signatures = {}, {}; audit = {"rows_decoded": 0, "string_fields_decoded": 0, "answer_fields_decoded": 0,
        "raw_lines_scanned": 0, "raw_bytes_scanned": 0}
    for ledger, filename in LEDGER_FILES.items():
        mapping = {}; multiplier = 3 if ledger == "generation_receipts" else 1
        target_lines = ({3 * row["position"] + offset for row in traces for offset in range(3)}
                        if multiplier == 3 else {row["position"] for row in traces})
        total_lines = 0
        with (canonical_output / filename).open("rb") as stream:
            for line_index, raw in enumerate(stream):
                total_lines += 1; audit["raw_lines_scanned"] += 1; audit["raw_bytes_scanned"] += len(raw)
                if line_index not in target_lines: continue
                require(raw.endswith(b"\n"), "canonical reference partial row")
                row = json.loads(raw)
                require(raw == canonical(row) + b"\n", "canonical reference noncanonical row")
                key = (row["dataset"], row["retriever"], row["sample_id"])
                if ledger == "generation_receipts": key = (*key, row["stage"])
                require(key not in mapping, "duplicate replay reference")
                mapping[key] = raw; audit["rows_decoded"] += 1; audit["string_fields_decoded"] += _string_field_count(row)
                if ledger == "generation_receipts" and row["stage"] in {"a0", "a1"}: audit["answer_fields_decoded"] += 2
                if ledger == "canonical_branches": audit["answer_fields_decoded"] += 2
        require(total_lines == canonical_trace_count * multiplier, "canonical reference ledger line count")
        maps[ledger] = mapping
        ordered = []
        for trace in traces:
            key = (trace["dataset"], trace["retriever"], trace["sample_id"])
            if ledger == "generation_receipts":
                ordered.extend(mapping[(*key, stage)] for stage in ("a0", "repair_query", "a1"))
            else: ordered.append(mapping[key])
        payload = b"".join(ordered)
        signatures[ledger] = (hashlib.sha256(payload).hexdigest(), len(payload))
    require(audit["rows_decoded"] == len(traces) * 6 and audit["answer_fields_decoded"] == len(traces) * 6,
            "replay reference decode accounting")
    return maps, signatures, audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True, help="Original E:/paper/ReliableRAG checkout")
    parser.add_argument("--output-name", required=True, help="Explicit new single-component namespace under outputs/cas_q2")
    parser.add_argument("--mode", choices=("canonical", "replay"), required=True)
    parser.add_argument("--canonical-output-name", help="Completed canonical namespace, required only for replay")
    parser.add_argument("--resume", action="store_true", help="Resume only from a fully paired durable call boundary")
    args = parser.parse_args()
    validate_output_name(args.output_name)
    require((args.mode == "replay") == bool(args.canonical_output_name), "canonical-output-name is required only for replay")
    if args.canonical_output_name: validate_output_name(args.canonical_output_name)
    original = args.project_root.resolve(); require(original == Path("E:/paper/ReliableRAG").resolve(), "fixed original project root")
    output = (OUTPUT_PARENT / args.output_name).resolve(); require(output.parent == OUTPUT_PARENT.resolve(), "output namespace containment")
    canonical_output = None if args.mode == "canonical" else (OUTPUT_PARENT / args.canonical_output_name).resolve()
    require(not args.resume or output.is_dir(), "resume namespace missing")
    require(args.resume or not output.exists(), "single-use output namespace exists; use --resume only after interruption")
    require(not (output / "BUILD_RECEIPT.json").exists() and not (output / "RUNTIME_FAILURE.json").exists() and
            not (output / "SHA256_MANIFEST.json").exists(), "completed or failed namespace is immutable")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "commit runtime implementation before execution")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    started = time.perf_counter(); phase = {"stage": "freeze", "position": None}; boundary = None
    environment = {}
    reader = bge = None; hooks = []; streams = {}; events = None; gpu_mutex = None
    counters = collections.Counter(); failclosed = collections.Counter(); completed_traces = 0
    row_counts = collections.Counter(); guard_admission_max_tokens = 0
    result = {"status": "FAIL", "mode": args.mode, "cas_q2_status": "NOT READY", "source_commit": commit,
        "output_name": args.output_name, "resume_requested": args.resume, "phase": phase,
        "fresh_gold_values_materialized": 0, "historical_qwen_answer_strings_read": 0, "scientific_fit_calls": 0,
        "replay_canonical_reference_rows_decoded": 0, "replay_canonical_string_fields_decoded": 0,
        "replay_canonical_answer_fields_decoded": 0, "replay_canonical_reference_raw_lines_scanned": 0,
        "replay_canonical_reference_raw_bytes_scanned": 0,
        "original_question_retrieval_calls": 0, "document_embedding_calls": 0, "bm25_structure_rebuild_calls": 0,
        "automatic_retry_allowed": False}
    try:
        if not args.resume: output.mkdir(parents=True, exist_ok=False)
        environment = configure_environment(output)
        gpu_mutex = acquire_gpu_mutex()
        result["gpu_mutex"] = "Local\\ReliableRAG_Phi_Development_Runtime_GPU"
        input_paths = source_paths(original, canonical_output)
        boundary = install_boundary(repository=REPO, original=original, output=output,
            allowed_reads=input_paths, canonical_reference=canonical_output)
        input_records = [record(path) for path in input_paths]
        pins = verify_pins(original)
        if canonical_output is not None:
            require(canonical_output != output and canonical_output.is_dir(), "canonical replay reference namespace")
            verify_sealed_namespace(canonical_output)
            canonical_receipt = load(canonical_output / "BUILD_RECEIPT.json")
            require(canonical_receipt.get("status") == "PASS_PHI_DEVELOPMENT_RUNTIME" and canonical_receipt.get("mode") == "canonical",
                    "canonical replay reference status")
        import torch
        configure_torch(torch)
        start_free, start_total = (int(value) for value in torch.cuda.mem_get_info())
        loader, native, nodes, generation_boundary = load_original_native(original)
        bge = native.ExactLocalBGEBackend(model_cache_dir=original / "data/models/huggingface"); bge._ensure_loaded()
        reader = native.HFProspectiveReaderAdapter(reader="phi", model_cache_dir=original / "data/models/huggingface",
            answer_prompt_path=original / "prompts/baseline_v1.txt", repair_prompt_path=original / "prompts/repair_missing_v1.txt",
            max_answer_tokens=48, max_query_tokens=64, context_budget_characters=16_000)
        reader._ensure_loaded()
        config = runtime_config(reader, bge, native); config_sha = object_sha(config)
        device_index = int(reader.device.index or 0); properties = torch.cuda.get_device_properties(device_index)
        device = {"index": device_index, "name": properties.name, "capability": list(torch.cuda.get_device_capability(device_index)),
            "nominal_total_bytes": int(properties.total_memory), "start_free_bytes": start_free, "start_total_bytes": start_total,
            "torch_cuda_version": torch.version.cuda, "platform": platform.platform(),
            "allocator_backend": torch.cuda.memory.get_allocator_backend(),
            "pytorch_cuda_alloc_conf": os.environ.get("PYTORCH_CUDA_ALLOC_CONF")}
        freeze = {"status": "FROZEN_BEFORE_BENCHMARK_EXECUTION", "source_commit": commit, "mode": args.mode,
            "output_name": args.output_name, "canonical_output_name": args.canonical_output_name,
            "command_contract": {"entrypoint": str(Path(__file__).resolve()), "project_root": str(original),
                "mode": args.mode, "output_name": args.output_name, "canonical_output_name": args.canonical_output_name},
            "inputs": input_records, "predecessor_manifests": pins, "runtime_config": config,
            "runtime_config_sha256": config_sha, "native_ast_nodes": nodes, "generation_boundary": generation_boundary,
            "environment": environment, "device_at_start": device,
            "trace_source": record(original / OLD_RUNTIME_RELATIVE / "trace_manifest.jsonl"),
            "replay_source": record(original / OLD_RUNTIME_RELATIVE / "replay_subset.jsonl"),
            "call_durability": "fsync intent; execute one call; fsync main ledger row; fsync completion; unmatched intent forbids resume",
            "scope": "Phi development generation only; no Gold, scoring, fitting, test runtime, or outcome analysis"}
        freeze_path = output / "EXECUTABLE_FREEZE.json"
        if args.resume:
            saved_freeze = load(freeze_path)
            actual_launch_device = dict(device)
            frozen_device = saved_freeze.get("device_at_start", {})
            for field in ("index", "name", "capability", "nominal_total_bytes", "start_total_bytes", "torch_cuda_version",
                          "platform", "allocator_backend", "pytorch_cuda_alloc_conf"):
                require(actual_launch_device.get(field) == frozen_device.get(field), "resume GPU/device/allocator mismatch")
            freeze["device_at_start"] = frozen_device
            require(saved_freeze == freeze, "resume executable freeze mismatch")
        else:
            write_json_durable(freeze_path, freeze)
        result["launch_device"] = device
        traces, replay, frozen_index = read_runtime_inputs(original)
        selected = traces if args.mode == "canonical" else replay
        expected = 13_500 if args.mode == "canonical" else 180
        require(len(selected) == expected, "selected trace count")
        reference_maps = reference_signatures = None
        if canonical_output is not None:
            reference_maps, reference_signatures, reference_audit = selected_reference_bytes(canonical_output, selected)
            result.update(replay_canonical_reference_rows_decoded=reference_audit["rows_decoded"],
                replay_canonical_string_fields_decoded=reference_audit["string_fields_decoded"],
                replay_canonical_answer_fields_decoded=reference_audit["answer_fields_decoded"],
                replay_canonical_reference_raw_lines_scanned=reference_audit["raw_lines_scanned"],
                replay_canonical_reference_raw_bytes_scanned=reference_audit["raw_bytes_scanned"])
        for name, filename in LEDGER_FILES.items():
            streams[name] = DurableJsonl(output / filename, resume=args.resume, retain_rows=args.resume)
        events = DurableCallEvents(output / "call_events.jsonl", resume=args.resume, retain_rows=args.resume)
        generation_lookup = {}; repair_lookup = {}; provenance_lookup = {}; branch_lookup = {}; partial = None
        if args.resume:
            ledger_rows = {name: stream.rows for name, stream in streams.items()}
            validate_call_events(events.rows, ledger_rows)
            completed_traces, partial = validate_resume_prefix(selected, ledger_rows)
            validate_completed_trace_rows(selected, ledger_rows, config_sha)
            require(all(row["intent"].get("runtime_config_sha256") == config_sha for row in events.completed.values()),
                    "call event runtime config binding")
            partial_key = None if partial is None else partial["key"]
            for row in ledger_rows["generation_receipts"]:
                validate_generation_receipt(row, config_sha)
                if row["stage"] in {"a0", "repair_query"}:
                    validate_frozen_generation_capture(row, frozen_index[(row["dataset"], row["retriever"], row["sample_id"])],
                        row["stage"], row["guard_input_tokens"])
                counters[row["stage"] + "_generation_calls"] += 1
                counters[row["stage"] + "_generation_completed"] += 1
                counters["phi_forward_calls"] += row["phi_forward_calls"]
                counters[row["stage"] + "_forward_calls"] += row["phi_forward_calls"]
                guard_admission_max_tokens = max(guard_admission_max_tokens, row["guard_input_tokens"])
                if row["stage"] in {"a0", "a1"} and not row["parsed_text"]:
                    failclosed["empty_" + row["stage"] + "_retained"] += 1
                if row["stage"] == "repair_query" and row["parser_fallback"]:
                    failclosed["native_repair_parser_fallback_retained"] += 1
                key = (row["dataset"], row["retriever"], row["sample_id"])
                if key == partial_key: generation_lookup[(*key, row["stage"])] = row
            counters["repair_retrieval_completed"] = len(ledger_rows["repair_bindings"])
            counters["repair_retrieval_calls"] = len(ledger_rows["repair_bindings"])
            for row in ledger_rows["repair_bindings"]:
                counters["repair_" + row["retriever"] + "_calls"] += 1
                key = (row["dataset"], row["retriever"], row["sample_id"])
                if key == partial_key: repair_lookup[key] = row
            counters["repair_query_embedding_calls"] = sum(row["retriever"] in {"dense", "hybrid"} for row in ledger_rows["repair_bindings"])
            counters["bge_query_forward_calls"] = counters["repair_query_embedding_calls"]
            for name, target in (("branch_provenance", provenance_lookup), ("canonical_branches", branch_lookup)):
                for row in ledger_rows[name]:
                    key = (row["dataset"], row["retriever"], row["sample_id"])
                    if key == partial_key: target[key] = row
            if reference_maps is not None:
                for name, rows_ in ledger_rows.items():
                    for row in rows_:
                        key = (row["dataset"], row["retriever"], row["sample_id"])
                        if name == "generation_receipts": key = (*key, row["stage"])
                        require(reference_maps[name].get(key) == canonical(row) + b"\n", "resumed replay row differs byte-for-byte")
            row_counts.update({name: len(rows_) for name, rows_ in ledger_rows.items()})
            for stream in streams.values(): stream.release_rows()
            events.release_history(); del ledger_rows
            # Python loop variables retain their final value.  Drop the last
            # potentially large scientific row once the partial-trace copies
            # above are the only history needed for continuation.
            row = None; rows_ = None
        else:
            completed_traces = 0
        admissions = []
        phase.update(stage="ready", position=None)
        reader.tokenizer = GuardedGenerationTokenizer(reader.tokenizer, phase, admissions)

        def phi_forward(model, hook_args, hook_kwargs):
            require(phase["stage"] in {"a0", "repair_query", "a1"} and torch.is_inference_mode_enabled() and
                    not torch.is_grad_enabled() and not model.training, "Phi inference call boundary")
            counters["phi_forward_calls"] += 1; counters[phase["stage"] + "_forward_calls"] += 1

        def bge_forward(model, hook_args, hook_kwargs):
            require(phase["stage"] == "repair_retrieval" and torch.is_inference_mode_enabled() and
                    not torch.is_grad_enabled() and not model.training, "BGE repair-query boundary")
            counters["bge_query_forward_calls"] += 1

        hooks = [reader.model.register_forward_pre_hook(phi_forward, with_kwargs=True),
                 bge.model.register_forward_pre_hook(bge_forward, with_kwargs=True)]

        class QueryOnlyBackend:
            dimension = 768
            def __init__(self): self.last = None
            def encode_queries(self, texts):
                require(phase["stage"] == "repair_retrieval" and type(texts) is list and len(texts) == 1,
                        "single repair query embedding only")
                counters["repair_query_embedding_calls"] += 1
                self.last = bge.encode_queries(texts); return self.last
            def encode_documents(self, *unused_args, **unused_kwargs):
                raise RuntimeError("document re-embedding forbidden")

        backend = QueryOnlyBackend(); runner = native.ProspectiveRunner(); runner.protocol = native.FrozenProtocol()

        def append(name: str, row: dict) -> None:
            streams[name].append(row)
            row_counts[name] += 1
            if reference_maps is not None:
                key = (row["dataset"], row["retriever"], row["sample_id"])
                if name == "generation_receipts": key = (*key, row["stage"])
                require(reference_maps[name].get(key) == canonical(row) + b"\n", "replay row differs byte-for-byte from canonical")

        def complete_call(trace: dict, operation: str, ledger: str, row: dict) -> None:
            events.completion({"event": "completion", "event_id": event_id(trace, operation), "operation": operation,
                "ledger": ledger, "ledger_row_sha256": object_sha(row)})

        def generate(trace: dict, question: str, evidence, stage: str):
            nonlocal guard_admission_max_tokens
            lookup_key = (trace["dataset"], trace["retriever"], trace["sample_id"], stage)
            if lookup_key in generation_lookup:
                saved = generation_lookup[lookup_key]
                require(saved["question_sha256"] == text_sha(question) and
                        saved["evidence_sha256"] == object_sha([row.as_private_dict() for row in evidence]),
                        "resumed generation call input mismatch")
                value = _query(native, saved) if stage == "repair_query" else _answer(native, saved)
                return value, saved
            phase.update(stage=stage, position=trace["position"]); before_forwards = counters["phi_forward_calls"]
            counters[stage + "_generation_calls"] += 1
            intent = {"event": "intent", "event_id": event_id(trace, stage), "operation": stage,
                "dataset": trace["dataset"], "retriever": trace["retriever"], "sample_id": trace["sample_id"],
                "position": trace["position"], "runtime_config_sha256": config_sha,
                "question_sha256": text_sha(question), "evidence_sha256": object_sha([row.as_private_dict() for row in evidence])}
            events.intent(intent); admission_index = len(admissions)
            key = native.TraceKey("phi", trace["dataset"], trace["sample_id"], trace["retriever"])
            value = (reader.generate_repair_query(key=key, question=question, evidence=evidence) if stage == "repair_query" else
                reader.generate_answer(key=key, question=question, evidence=evidence, state="e0" if stage == "a0" else "e1"))
            require(len(admissions) == admission_index + 1, "exactly one pre-CUDA admission per generation")
            admission = admissions.pop(); capture = copy.deepcopy(reader._generation_capture)
            require(len(admissions) == admission_index, "generation admission released after capture")
            require(admission == {"stage": stage, "position": trace["position"], "input_tokens": capture["input_tokens"]},
                    "guard/native generation capture mismatch")
            if stage in {"a0", "repair_query"}:
                validate_frozen_generation_capture(capture, frozen_index[(trace["dataset"], trace["retriever"], trace["sample_id"])],
                    stage, admission["input_tokens"])
            row = {"dataset": trace["dataset"], "retriever": trace["retriever"], "sample_id": trace["sample_id"],
                "position": trace["position"], "stage": stage, **capture,
                "question_sha256": intent["question_sha256"], "evidence_sha256": intent["evidence_sha256"],
                "parsed_text": value.search_query if stage == "repair_query" else value.parsed_text,
                "parser_fallback": value.parser_fallback if stage == "repair_query" else None,
                "logical_generation_calls": 1, "phi_forward_calls": counters["phi_forward_calls"] - before_forwards,
                "reader": "phi", "guard_input_tokens": admission["input_tokens"], "runtime_config_sha256": config_sha}
            validate_generation_receipt(row, config_sha)
            append("generation_receipts", row); complete_call(trace, stage, "generation_receipts", row)
            guard_admission_max_tokens = max(guard_admission_max_tokens, row["guard_input_tokens"])
            counters[stage + "_generation_completed"] += 1
            if stage != "repair_query":
                runner._validate_generation(value, stage, evidence)
                if not value.parsed_text: failclosed["empty_" + stage + "_retained"] += 1
            elif value.parser_fallback: failclosed["native_repair_parser_fallback_retained"] += 1
            return value, row

        current_dataset = None; data = None
        start_index = completed_traces if partial is None else partial["index"]
        for trace in selected[start_index:]:
            phase["position"] = trace["position"]; dataset, retriever, sample_id = trace["dataset"], trace["retriever"], trace["sample_id"]
            if dataset != current_dataset:
                data = loader.restore_dataset(dataset, native, backend); current_dataset = dataset
            question = data["questions"][sample_id]; e0 = loader.original_evidence(trace, data, native)
            a0, a0_row = generate(trace, question, e0, "a0")
            query, query_row = generate(trace, question, e0, "repair_query")
            trace_key = (dataset, retriever, sample_id)
            if trace_key in repair_lookup:
                repair = repair_lookup[trace_key]
                validate_repair_receipt(repair, trace)
                require(repair["query_sha256"] == text_sha(query.search_query) and repair["requested_depth"] == 50,
                        "saved repair binding")
                inserted_id = repair["inserted_document_id"]
                inserted_doc = data["documents"][inserted_id]
                inserted_score = next(row["score"] for row in repair["ranking"] if row["document_id"] == inserted_id)
                e1 = tuple((*e0[:4], native.RankedDocument(5, inserted_id, inserted_doc.content_hash,
                    inserted_score, inserted_doc.title, inserted_doc.text)))
                require([row.document_id for row in e1] == repair["e1_ids"], "resumed repair evidence identity")
            else:
                phase.update(stage="repair_retrieval", position=trace["position"]); data["components"].clear(); backend.last = None
                events.intent({"event": "intent", "event_id": event_id(trace, "repair_retrieval"), "operation": "repair_retrieval",
                    "dataset": dataset, "retriever": retriever, "sample_id": sample_id, "position": trace["position"],
                    "runtime_config_sha256": config_sha, "query_sha256": text_sha(query.search_query), "requested_depth": 50})
                counters["repair_retrieval_calls"] += 1; counters["repair_" + retriever + "_calls"] += 1; ranking = []
                def rank(query_text, method, depth):
                    require(method == retriever and depth == 50, "same-retriever depth-50 repair")
                    value = data["router"].rank(query_text, method, depth); ranking.extend(value); return value
                e1, inserted, diagnostics = runner._repair(types.SimpleNamespace(rank=rank), query, retriever, e0)
                components = data["components"]
                require(len(components) == (2 if retriever == "hybrid" else 1), "repair component count")
                repair = {"dataset": dataset, "retriever": retriever, "sample_id": sample_id, "position": trace["position"],
                    "query_sha256": text_sha(query.search_query), "runtime_config_sha256": config_sha,
                    "ranking": [{"document_id": row.document_id, "rank": row.rank, "score": float(row.score)} for row in ranking],
                    "component_rankings": {"bm25": components[0], "dense": components[1]} if retriever == "hybrid" else {retriever: components[0]},
                    "dense_query_vector": None if backend.last is None else backend.last[0].tolist(),
                    "e0_ids": [row.document_id for row in e0], "e1_ids": [row.document_id for row in e1],
                    "inserted_document_id": inserted.document_id, "inserted_candidate_rank": inserted.rank,
                    "replaced_document_id": e0[4].document_id, "replacement_position_zero_based": 4,
                    "requested_depth": 50, "repair_retrieval_calls": 1, "pool_sha256": data["binding"]["pool_sha256"],
                    "fail_closed_reason": None}
                validate_repair_receipt(repair, trace)
                append("repair_bindings", repair); complete_call(trace, "repair_retrieval", "repair_bindings", repair)
                counters["repair_retrieval_completed"] += 1
            a1, a1_row = generate(trace, question, e1, "a1")
            branch = {"dataset": dataset, "retriever": retriever, "sample_id": sample_id, "question": question,
                "a0": a0.parsed_text, "a1": a1.parsed_text, "evidence0": [row.text for row in e0], "evidence1": [row.text for row in e1]}
            require(set(branch) == loader.BRANCH_FIELDS, "canonical branch schema")
            provenance = {"dataset": dataset, "retriever": retriever, "sample_id": sample_id, "position": trace["position"],
                "original_top5_row_sha256": trace["original_top5_row_sha256"], "e0": [row.as_private_dict() for row in e0],
                "e1": [row.as_private_dict() for row in e1], "question_sha256": text_sha(question),
                "canonical_row_sha256": object_sha(branch), "runtime_config_sha256": config_sha,
                "repair_binding_row_sha256": object_sha(repair), "pool_sha256": data["binding"]["pool_sha256"]}
            validate_completed_trace_rows([trace], {"generation_receipts": [a0_row, query_row, a1_row],
                "repair_bindings": [repair], "branch_provenance": [provenance], "canonical_branches": [branch]}, config_sha)
            if trace_key not in provenance_lookup:
                append("branch_provenance", provenance)
            else: require(provenance_lookup[trace_key] == provenance, "resumed provenance mismatch")
            if trace_key not in branch_lookup:
                append("canonical_branches", branch)
            else: require(branch_lookup[trace_key] == branch, "resumed canonical branch mismatch")
            generation_lookup.clear(); repair_lookup.clear(); provenance_lookup.clear(); branch_lookup.clear()
            completed_traces += 1
            if completed_traces % 10 == 0:
                print(json.dumps({"stage": "phi_development", "mode": args.mode, "completed_traces": completed_traces,
                    "expected_traces": expected}, sort_keys=True), flush=True)
        require(completed_traces == expected and row_counts == collections.Counter({
            "generation_receipts": expected * 3, "repair_bindings": expected,
            "branch_provenance": expected, "canonical_branches": expected}), "complete streamed ledger counts")
        require(events.paired and events.completed_count == expected * 4 and events.ledger.row_count == expected * 8,
                "complete durable call-event counts")
        require(all(counters[stage + "_generation_completed"] == expected for stage in ("a0", "repair_query", "a1")),
                "complete Phi generation counts")
        dense_expected = sum(row["retriever"] in {"dense", "hybrid"} for row in selected)
        require(counters["repair_retrieval_completed"] == expected and counters["repair_query_embedding_calls"] ==
                counters["bge_query_forward_calls"] == dense_expected, "complete repair/BGE counts")
        for stream in streams.values(): stream.close()
        events.close()
        if reference_signatures is not None:
            for name, filename in LEDGER_FILES.items():
                require((digest(output / filename), (output / filename).stat().st_size) == reference_signatures[name],
                        "complete replay ledger differs byte-for-byte from canonical selection")
        for before in input_records: require(record(Path(before["path"])) == before, "executable input changed during runtime")
        require(not boundary["denied"], "runtime IO boundary denial")
        result.update(status="PASS_PHI_DEVELOPMENT_RUNTIME" if args.mode == "canonical" else "PASS_PHI_DEVELOPMENT_REPLAY",
            completed_traces=completed_traces, expected_traces=expected,
            question_clusters=len({(row["dataset"], row["sample_id"]) for row in selected}),
            stratum_counts={f"{dataset}/{retriever}": sum((row["dataset"], row["retriever"]) == (dataset, retriever) for row in selected)
                for dataset in ("hotpotqa", "2wikimultihopqa", "musique") for retriever in ("bm25", "dense", "hybrid")},
            counters=dict(counters), fail_closed_counts=dict(failclosed), guard_admission_count=row_counts["generation_receipts"],
            guard_admission_max_tokens=guard_admission_max_tokens,
            replay_exact_match=True if args.mode == "replay" else None, runtime_config_sha256=config_sha,
            executable_freeze=record(freeze_path), artifacts=[record(output / filename) for filename in (*LEDGER_FILES.values(), "call_events.jsonl")],
            generation_failure_count=0, repair_failure_count=0, source_inputs_unchanged=True)
    except Exception as exc:
        is_oom = "torch" in locals() and isinstance(exc, torch.OutOfMemoryError)
        result.update(status="FAIL_CUDA_OOM" if is_oom else "FAIL", error_type=type(exc).__name__, diagnostic=str(exc),
            stderr_traceback=traceback.format_exc(), completed_traces=completed_traces, counters=dict(counters),
            failure_sealed=True, configuration_changed_after_failure=False)
    finally:
        for hook in hooks:
            try: hook.remove()
            except Exception: pass
        for stream in streams.values():
            try: stream.close()
            except Exception: pass
        if events is not None:
            try: events.close()
            except Exception: pass
        if reader is not None:
            try: reader.close()
            except Exception: pass
        if bge is not None:
            try: bge.close()
            except Exception: pass
        if gpu_mutex is not None:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(gpu_mutex)
            except Exception: pass
    if "torch" in locals() and torch.cuda.is_available():
        result.update(peak_allocated_cuda_bytes=int(torch.cuda.max_memory_allocated()),
            peak_reserved_cuda_bytes=int(torch.cuda.max_memory_reserved()))
    result.update(phase=dict(phase), elapsed_seconds=time.perf_counter() - started,
        execution_boundary=None if boundary is None else compact_boundary(boundary), finished_at_utc=datetime.now(timezone.utc).isoformat())
    receipt_name = "BUILD_RECEIPT.json" if result["status"].startswith("PASS_") else "RUNTIME_FAILURE.json"
    write_json_durable(output / receipt_name, result)
    seal_output(output)
    print(result["status"], result.get("diagnostic", ""), flush=True)
    return 0 if result["status"].startswith("PASS_") else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
