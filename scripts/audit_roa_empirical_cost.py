"""Reconcile accepted fresh inference costs without decoding any answer text."""
import argparse
from pathlib import Path
import subprocess
import sys
import time

from scripts.empirical_cost_accounting import generation_projection, generation_cost, retrieval_cost, scoring_cost, timing
from scripts.empirical_cost_guard import guard
from scripts.empirical_outcome_stage_io import prerequisites, unchanged_freeze, C4
from scripts.empirical_outcome_native import definitions, PARSER_SHA
from scripts.empirical_pool_io import REPO, checked, load, record, require, verify_namespace
from scripts.empirical_retrieval_io import boundary_record, seal
from scripts.replay_roa_original import write_json

BASE = REPO / "outputs/cas_q2"
OUT = BASE / "empirical_inference_cost_v1"
D_ENGINEERING = BASE / "empirical_outcome_engineering_v1"
D_ENGINEERING_SHA = "9461d2d4dd54c6935eb9dac949b381c6bd3489857b8b4a6ddbb1e2864e34e0c8"
RUNTIME = BASE / "empirical_runtime_v1"
RETRIEVAL = BASE / "empirical_retrieval_v1"


def source_paths():
    return [REPO / name for name in ("scripts/empirical_cost_accounting.py", "scripts/empirical_cost_guard.py",
        "scripts/audit_roa_empirical_cost.py", "tests/test_empirical_cost.py", "docs/cas_q2/EMPIRICAL_COST_AUDIT_CONTRACT.md")]


def authorized_inputs(root, prelabel):
    paths = prerequisites("mapping", {"prelabel":prelabel})
    paths += verify_namespace(D_ENGINEERING, D_ENGINEERING_SHA) + unchanged_freeze(D_ENGINEERING)
    require(load(D_ENGINEERING / "CPU_ENGINEERING_TESTS.json")["status"] == "PASS_CPU_D_ENGINEERING_ONLY", "Accepted byte-cursor boundary engineering")
    parser_path = checked(root / "src/phase10/source_projection_v2r1.py", PARSER_SHA)
    paths += source_paths() + [parser_path, Path(sys.executable)]
    metadata = [BASE / "empirical_candidate_pool_v2/BUILD_RECEIPT.json", RETRIEVAL / "BUILD_RECEIPT.json",
        RUNTIME / "BUILD_RECEIPT.json", RUNTIME / "replay/BUILD_RECEIPT.json", RUNTIME / "INDEPENDENT_VALIDATION.json",
        BASE / "empirical_retrieval_gpu_preflight_v1/GPU_PREFLIGHT.json", BASE / "empirical_runtime_gpu_preflight_v1/GPU_PREFLIGHT.json",
        C4["independent"] / "INDEPENDENT_VALIDATION.json"] + [folder / "BUILD_RECEIPT.json" for folder in C4.values()]
    decoded = metadata + [RUNTIME / "generation_receipts.jsonl", RUNTIME / "replay/generation_receipts.jsonl"] + source_paths() + [parser_path]
    require({p.resolve() for p in decoded} <= {p.resolve() for p in paths}, "Every decoded cost file bound by complete prelabel graph")
    return sorted(set(paths)), sorted(set(decoded)), parser_path


def reconcile(Cursor):
    runtime_independent = load(RUNTIME / "INDEPENDENT_VALIDATION.json")
    modes, runtime_builds = {}, {}
    for mode, folder, size in (("canonical", RUNTIME, 2000), ("bounded_replay", RUNTIME / "replay", 20)):
        build = load(folder / "BUILD_RECEIPT.json")
        accepted_mode = "canonical" if mode == "canonical" else "replay"
        runtime_builds[mode] = build
        modes[mode] = generation_cost(generation_projection(folder / "generation_receipts.jsonl", Cursor), build,
            runtime_independent["canonical_and_replay"][accepted_mode], questions_per_stratum=size)
    c2 = load(RETRIEVAL / "BUILD_RECEIPT.json")
    builds = {name:load(folder / "BUILD_RECEIPT.json") for name, folder in C4.items()}
    scored = scoring_cost(builds["base"], builds["gbv"], builds["policies"], load(C4["independent"] / "INDEPENDENT_VALIDATION.json"))
    projection = load(BASE / "empirical_candidate_pool_v2/BUILD_RECEIPT.json")
    c2_preflight = load(BASE / "empirical_retrieval_gpu_preflight_v1/GPU_PREFLIGHT.json")
    c3_preflight = load(BASE / "empirical_runtime_gpu_preflight_v1/GPU_PREFLIGHT.json")
    return dict(canonical_shared_execution=dict(pool_projection=timing(projection, boundary="C1 original saved construction timer"),
        original_retrieval=retrieval_cost(c2), candidate_acquisition=modes["canonical"], scoring=scored),
        stage_measurements=dict(original_retrieval=timing(c2, boundary="C2 executor includes model setup, IO, hooks and final input rehash"),
            canonical_runtime=timing(runtime_builds["canonical"], boundary="C3 executor includes setup, generation, repair, durable journals and rehash"),
            **{name:timing(builds[name], boundary="C4 stage starts after prerequisite authentication; includes preparation, model/IO/witness work and final rehash", peak=name in {"base","gbv"}) for name in ("base","gbv","policies")}),
        verification_overhead=dict(bounded_replay=modes["bounded_replay"],
            bounded_replay_measurement=timing(runtime_builds["bounded_replay"], boundary="C3 bounded replay including reference binding and byte comparison"),
            c2_gpu_preflight=dict(embedding_forwards=c2_preflight["synthetic_embedding_forward_calls"], generation_calls=0),
            c3_gpu_preflight=dict(generation_calls=c3_preflight["synthetic_reader_generation_calls"], qwen_forwards=c3_preflight["synthetic_qwen_forward_calls"],
                bge_forwards=c3_preflight["synthetic_bge_forward_calls"], synthetic_only_cuda_allocator_peak_bytes=c3_preflight["actual_backend"]["peak_allocated_cuda_bytes"]),
            c4_gpu_preflight=dict(measurement=timing(builds["gpu_preflight"], boundary="Invented-only C4 scoring preflight", peak=True),
                actual={name:builds["gpu_preflight"][name]["actual"] for name in ("bge","qwen","gbv")}),
            c4_independent=timing(builds["independent"], boundary="Tokenizers and saved CPU heads; complete saved-witness checks, zero new neural forwards")),
        cache_scope=dict(weights="Existing pinned model bytes; each neural stage constructs models", documents="C2 vectors reused by canonical C3 and its bounded replay without re-embedding",
            generation="Native autoregressive KV cache; every canonical generation actually executed", likelihood="Initially empty per-pass result cache with complete current-pass witness binding",
            nli="No result cache; all completed branch chunks included"),
        missing_measurements=["Canonical C2/C3 CUDA allocator peaks", "Per-generation latency and separately timed policy deployments",
            "C2/C3 BGE token totals and generation per-forward input-token touches", "Uniform end-to-end wall-time boundary or FLOPs"],
        interpretation_limits=["Shared acquisition/scoring is reported once, not multiplied by nine policies.",
            "A 5% action cap is not a 5% generation or scoring budget; candidate generation precedes pair eligibility.",
            "Stage timers have different boundaries and instrumented IO; do not sum them into measured end-to-end or standalone policy latency.",
            "Reported input tokens are prompt totals, not repeated KV-cache token touches or FLOPs.",
            "C4 reconciliation relies on its independently validated complete witness summaries; this audit performs no neural replay.",
            "CUDA allocator peaks exclude other GPU processes and are not total device memory; synthetic peaks do not substitute for canonical peaks.",
            "Historical fits, CPU engineering and later D statistics are separate work; no standalone deployment cost experiment was run."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--prelabel-manifest-sha256", required=True)
    args = parser.parse_args(); root = args.project_root.resolve()
    require(not OUT.exists(), "Single-use complete cost audit namespace")
    require(not subprocess.check_output(["git","status","--porcelain"],cwd=REPO,text=True).strip(), "Commit cost executable first")
    commit = subprocess.check_output(["git","rev-parse","HEAD"],cwd=REPO,text=True).strip()
    paths, decoded, parser_path = authorized_inputs(root, args.prelabel_manifest_sha256)
    import json
    module, hashes = definitions(parser_path, ("_JSONByteCursor",), dict(json=json, Phase10FailClosed=RuntimeError))
    records = [record(p) for p in paths]
    OUT.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    write_json(OUT / "EXECUTABLE_FREEZE.json", dict(source_commit=commit, inputs=records, decoded_input_paths=[str(p) for p in decoded],
        command=sys.argv, prelabel_manifest_sha256=args.prelabel_manifest_sha256, byte_cursor_ast_hash=hashes))
    boundary = guard(root, OUT, paths, decoded)
    report = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit, prelabel_manifest_sha256=args.prelabel_manifest_sha256,
        scientific_fit_calls=0, new_inference_calls=0, fresh_gold_values_materialized=0, raw_or_parsed_answer_strings_decoded=0)
    try:
        report.update(reconcile(module._JSONByteCursor))
        for entry in records:
            require(record(Path(entry["path"])) == entry, "Cost input/source changed")
        require(not boundary["denied"] and boundary["forbidden_calls"] == 0, "Clean complete cost boundary")
        report.update(status="PASS_ACCEPTED_PRELABEL_COST_RECONCILIATION_WITH_LIMITS", source_inputs_unchanged=True)
    except Exception as exc:
        frames, tb = [], exc.__traceback__
        while tb:
            frames.append(dict(file=tb.tb_frame.f_code.co_filename, line=tb.tb_lineno, function=tb.tb_frame.f_code.co_name)); tb=tb.tb_next
        report.update(error_type=type(exc).__name__, code_locations=frames, diagnostic="NO_TEXT_VALUES_LOGGED")
    finally:
        sys.setprofile(None)
    report.update(audit_elapsed_seconds=time.perf_counter()-started, execution_boundary=boundary_record(boundary))
    write_json(OUT / "INFERENCE_COST_AUDIT.json", report)
    seal(OUT)
    print(report["status"], flush=True)
    return 2 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
