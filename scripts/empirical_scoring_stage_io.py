"""C4 stage prerequisites, immutable inputs and explicit private artifact IO."""
import json
from pathlib import Path
import re

from scripts.empirical_scoring_io import REPO, inputs, record, require
from scripts.empirical_pool_io import load, verify_namespace

BASE = REPO / "outputs/cas_q2"
RUNTIME = BASE / "empirical_runtime_v1"
PREPARATION = BASE / "empirical_runtime_preparation_v1"
PREPARATION_SHA = "7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258"
CPU = BASE / "empirical_neural_engineering_tests_v1"
CPU_SHA = "cc322f1456cfe6c3c3190c98c5b03f305c2d4846cd6062bb68417bae47efcfbf"
STAGES = dict(gpu_preflight=BASE / "empirical_scoring_gpu_preflight_v1", base=BASE / "empirical_base_scoring_v1",
    gbv=BASE / "empirical_gbv_scoring_v1", policies=BASE / "empirical_prelabel_policies_v1",
    independent=BASE / "empirical_scoring_validation_v1")
EXPECTED_STATUS = dict(gpu_preflight="PASS_NATIVE_SCORING_GPU_INVENTED_ONLY", base="COMPLETED_NATIVE_BASE_PENDING_INDEPENDENT",
    gbv="COMPLETED_NATIVE_GBV_PENDING_INDEPENDENT", policies="COMPLETED_PRELABEL_POLICIES_PENDING_INDEPENDENT",
    independent="PASS_COMPLETE_FROZEN_PRELABEL_ONLY")
DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")


def read_rows(path):
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            require(bool(line.strip()), "No blank private ledger row")
            yield json.loads(line)


def pin(value, name):
    require(type(value) is str and re.fullmatch("[0-9a-f]{64}", value), "Explicit accepted manifest hash: " + name)
    return value


def stage_prerequisites(mode, pins):
    """No output mutation or model load; called before creating a run directory."""
    require(mode in STAGES, "Fixed C4 stage")
    wanted = ["runtime"] + (["gpu_preflight"] if mode != "gpu_preflight" else [])
    if mode in {"gbv", "policies", "independent"}:
        wanted.append("base")
    if mode in {"policies", "independent"}:
        wanted.append("gbv")
    if mode == "independent":
        wanted.append("policies")
    require(set(pins) == set(wanted), "Exact predecessor manifest argument set")
    paths = verify_namespace(RUNTIME, pin(pins["runtime"], "runtime"))
    validation = load(RUNTIME / "INDEPENDENT_VALIDATION.json")
    seal = load(RUNTIME / "SEAL.json")
    require(validation["status"] == "PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY" and
        seal["status"] == "PASS_CANDIDATE_PAIR_ACQUISITION_ONLY" and
        seal["independent_sha256"] == record(RUNTIME / "INDEPENDENT_VALIDATION.json")["sha256"], "Complete accepted C3 before C4")
    require(validation["canonical_traces"] == 18000 and validation["questions"] == 6000 and
        validation["replay_traces"] == 180 and validation["exact_replay_match"] is True and
        validation["model_forward_calls"] == validation["scientific_fit_calls"] == validation["fresh_gold_values_materialized"] == 0,
        "Complete C3 validation scope and zero Gold access")
    for entry in load(RUNTIME / "EXECUTABLE_FREEZE.json")["inputs"]:
        require(record(Path(entry["path"])) == entry, "Unchanged accepted C3 executable/input")
        paths.append(Path(entry["path"]))
    for name in wanted[1:]:
        folder = STAGES[name]
        paths += verify_namespace(folder, pin(pins[name], name))
        receipt = load(folder / "BUILD_RECEIPT.json")
        require(receipt["status"] == EXPECTED_STATUS[name] and receipt["source_inputs_unchanged"], "Completed C4 predecessor: " + name)
        require(load(folder / "EXECUTABLE_FREEZE.json")["predecessor_manifests"]["runtime"] == pins["runtime"], "Single common accepted C3 cohort")
        require(all(pins.get(ancestor) == value for ancestor, value in
            load(folder / "EXECUTABLE_FREEZE.json")["predecessor_manifests"].items()), "Exact C4 predecessor chain")
        for entry in load(folder / "EXECUTABLE_FREEZE.json")["inputs"]:
            require(record(Path(entry["path"])) == entry, "Unchanged predecessor executable/input")
            paths.append(Path(entry["path"]))
    return paths


def source_paths():
    names = ("empirical_scoring_stage_io", "empirical_scoring_stage_guard", "empirical_scoring_journals", "empirical_scoring_stage_run",
        "preflight_roa_empirical_scoring_gpu", "build_roa_empirical_scoring", "validate_roa_empirical_scoring",
        "empirical_scoring_io", "empirical_scoring_import_v2", "empirical_scoring_bindings", "empirical_scoring_pipeline",
        "empirical_scoring_models", "empirical_scoring_guard", "empirical_semantic_witness", "empirical_likelihood_witness",
        "empirical_gbv_witness", "empirical_neural_checks", "empirical_likelihood_independent", "empirical_gbv_independent",
        "empirical_semantic_independent", "empirical_feature_independent", "empirical_policy_independent", "empirical_policy_actions",
        "empirical_scoring_gpu_fixtures", "empirical_scoring_stage_independent")
    return [REPO / "scripts" / (name + ".py") for name in names] + [REPO / "tests/test_empirical_scoring_stages.py"] + [REPO / "docs/cas_q2" / name for name in
        ("EMPIRICAL_C4_SCORING_CONTRACT.md", "EMPIRICAL_C4_NEURAL_VALIDATION_CONTRACT.md", "EMPIRICAL_C4_EXECUTION_CONTRACT.md")]


def bound_inputs(root, mode, pins, predecessor_paths):
    audit, pre, paths = inputs(root, neural=True)
    paths += predecessor_paths + verify_namespace(CPU, CPU_SHA) + verify_namespace(PREPARATION, PREPARATION_SHA)
    require(load(CPU / "CPU_ENGINEERING_TESTS.json")["status"] == "PASS_CPU_ENGINEERING_TESTS_ONLY", "Accepted neural CPU engineering")
    for entry in load(CPU / "EXECUTABLE_FREEZE.json")["inputs"]:
        require(record(Path(entry["path"])) == entry, "CPU-tested source/input remains unchanged")
        paths.append(Path(entry["path"]))
    paths += source_paths()
    freeze = load(RUNTIME / "EXECUTABLE_FREEZE.json")
    pools = {}
    for dataset in DATASETS:
        path = (BASE / "empirical_candidate_pool_v2/pools" / (dataset + ".jsonl")).resolve()
        matches = [e for e in freeze["inputs"] if Path(e["path"]).resolve() == path]
        require(len(matches) == 1, "C3 accepted pool identity")
        pools[dataset] = matches[0]["sha256"]
    return audit, pre, sorted(set(paths)), dict(pool_sha=pools, runtime_config_sha=freeze["runtime_config_sha256"])


def restore_traces(wrapper, context):
    """Execution-side adapter only; the independent validator has a separate path."""
    from scripts.empirical_scoring_bindings import restore_bound_trace
    from scripts.empirical_runtime_contract import trace_key
    prepared = list(read_rows(PREPARATION / "TRACE_MANIFEST_PRIVATE.jsonl"))
    require(len(prepared) == 18000, "Full frozen empirical trace manifest")
    streams = [read_rows(RUNTIME / name) for name in ("canonical_branches.jsonl", "branch_provenance.jsonl", "repair_bindings.jsonl")]
    traces = []
    for index, (branch, provenance, repair, binding) in enumerate(zip(*streams, prepared, strict=True)):
        require(binding["position"] == index, "Canonical C3 trace position")
        traces.append(restore_bound_trace(wrapper, branch, provenance, binding, repair,
            pool_sha=context["pool_sha"][branch["dataset"]], runtime_config_sha=context["runtime_config_sha"]))
    keys = [trace_key(t) for t in traces]
    require(len(keys) == len(set(keys)) == 18000 and all(sum(t["dataset"] == d for t in traces) == 6000 for d in DATASETS), "Complete unique native scoring traces")
    return traces


def serialize_allocation(value):
    return {**value, "selected": {name: [list(k) for k in sorted(keys)] for name, keys in value["selected"].items()}}


def restore_allocation(value):
    return {**value, "selected": {name: {tuple(k) for k in keys} for name, keys in value["selected"].items()}}
