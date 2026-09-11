"""D prerequisite authentication and distinct decode permissions per process."""
from pathlib import Path
import re
import argparse
import json

from scripts.empirical_pool_io import REPO, checked, load, record, require, verify_namespace
from scripts.empirical_scoring_stage_io import STAGES as C4, stage_prerequisites as scoring_prerequisites

BASE = REPO / "outputs/cas_q2"
AUDIT = BASE / "empirical_outcome_input_audit_v1"
AUDIT_SHA = "13a9e14d8f58c737dd1aef2f8556bb9bf1a6d81a86acdd910acdeecde9732ef2"
COHORT = BASE / "empirical_fresh_cohort_v1"
COHORT_SHA = "6070c63b9cbf3277ef328d059dcaabc98480ba2bb60503b66ad2faa5e816b62a"
CANONICAL = BASE / "empirical_runtime_v1/canonical_branches.jsonl"
SELECTED = COHORT / "SELECTED_IDS_PRIVATE.jsonl"
STAGES = dict(mapping=BASE / "empirical_outcome_mapping_v1", outcome_validation=BASE / "empirical_outcome_validation_v1",
    analysis=BASE / "empirical_analysis_v1", analysis_validation=BASE / "empirical_analysis_validation_v1")
STATUSES = dict(mapping="PASS_METHOD_BLIND_NUMERIC_MAPPING_PENDING_VALIDATION", outcome_validation="PASS_INDEPENDENT_SELECTED_OUTCOMES",
    analysis="COMPLETED_FROZEN_ANALYSIS_PENDING_INDEPENDENT", analysis_validation="PASS_FROZEN_EMPIRICAL_ANALYSIS")


def pin(value):
    require(type(value) is str and re.fullmatch("[0-9a-f]{64}", value), "Explicit accepted D predecessor digest")
    return value


def arguments(stage):
    parser = argparse.ArgumentParser(description="Frozen D " + stage + " with explicit accepted predecessors")
    parser.add_argument("--project-root", type=Path, required=True)
    names = ["prelabel"]
    if stage != "mapping": names.append("mapping")
    if stage in {"analysis", "analysis_validation"}: names.append("outcome_validation")
    if stage == "analysis_validation": names.append("analysis")
    for name in names:
        parser.add_argument("--" + name.replace("_", "-") + "-manifest-sha256", required=True)
    args = parser.parse_args()
    return args.project_root, {name: getattr(args, name + "_manifest_sha256") for name in names}


def rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            require(bool(line.strip()) and line.endswith("\n"), "Complete nonblank numeric/identity ledger line")
            yield json.loads(line)


def selected_ids():
    values = list(rows(SELECTED))
    require(len(values) == 6000 and all(set(r) == {"dataset", "sample_id"} and
        all(type(v) is str and v for v in r.values()) for r in values), "Exact selected-only cohort schema/count")
    selected = {(r["dataset"], r["sample_id"]) for r in values}
    require(len(selected) == 6000 and all(sum(ds == d for ds, sid in selected) == 2000 for d in ("hotpotqa", "2wikimultihopqa", "musique")), "Complete balanced unique selected cohort")
    return selected


def unchanged_freeze(folder):
    paths = []
    for entry in load(folder / "EXECUTABLE_FREEZE.json")["inputs"]:
        require(record(Path(entry["path"])) == entry, "Unchanged predecessor source/input")
        paths.append(Path(entry["path"]))
    return paths


def prerequisites(stage, pins):
    require(stage in STAGES, "Fixed D stage")
    wanted = ["prelabel"]
    if stage != "mapping": wanted.append("mapping")
    if stage in {"analysis", "analysis_validation"}: wanted.append("outcome_validation")
    if stage == "analysis_validation": wanted.append("analysis")
    require(set(pins) == set(wanted), "Exact D predecessor argument set")
    folder = C4["independent"]
    paths = verify_namespace(folder, pin(pins["prelabel"]))
    seal, independent, build = [load(folder / n) for n in ("SEAL.json", "INDEPENDENT_VALIDATION.json", "BUILD_RECEIPT.json")]
    require(seal["status"] == independent["status"] == build["status"] == "PASS_COMPLETE_FROZEN_PRELABEL_ONLY", "Complete C4 independent prelabel acceptance before D")
    require(seal["independent_sha256"] == record(folder / "INDEPENDENT_VALIDATION.json")["sha256"] and build["source_inputs_unchanged"] is True,
        "Independent prelabel seal/report binding")
    require(independent["traces"] == 18000 and independent["questions"] == 6000 and independent["cap"] == 900 and
        independent["model_forward_calls"] == independent["scientific_fit_calls"] == independent["fresh_gold_values_materialized"] == 0,
        "Complete label-free C4 validation scope")
    prior_pins = load(folder / "EXECUTABLE_FREEZE.json")["predecessor_manifests"]
    require(seal["predecessor_manifests"] == independent["predecessor_manifests"] == prior_pins, "Exact C4 final predecessor chain")
    paths += scoring_prerequisites("independent", prior_pins) + unchanged_freeze(folder)
    for name in wanted[1:]:
        folder = STAGES[name]
        paths += verify_namespace(folder, pin(pins[name]))
        build = load(folder / "BUILD_RECEIPT.json")
        require(build["status"] == STATUSES[name] and build["source_inputs_unchanged"] is True, "Complete D predecessor")
        previous = load(folder / "EXECUTABLE_FREEZE.json")["predecessor_manifests"]
        require(all(pins.get(k) == value for k, value in previous.items()) and previous["prelabel"] == pins["prelabel"], "Exact same D cohort and predecessor chain")
        if name == "outcome_validation":
            report, seal = load(folder / "INDEPENDENT_VALIDATION.json"), load(folder / "SEAL.json")
            require(report["status"] == seal["status"] == STATUSES[name] and report["metric_values_checked"] == 72000 and
                report["traces"] == 18000 and report["question_groups"] == 6000 and report["all_numeric_outcomes_match"] is True and
                seal["independent_sha256"] == record(folder / "INDEPENDENT_VALIDATION.json")["sha256"], "Complete independent numeric outcome seal")
        paths += unchanged_freeze(folder)
    return paths


def source_paths():
    names = ("empirical_outcome_stage_io", "empirical_outcome_stage_run", "map_roa_empirical_outcomes", "validate_roa_empirical_outcomes",
        "analyze_roa_empirical_results", "validate_roa_empirical_analysis", "empirical_outcome_native", "empirical_outcome_independent",
        "empirical_outcome_guard", "empirical_outcome_guard_v2", "empirical_analysis_math", "empirical_analysis_independent", "empirical_analysis_storage")
    return [REPO / "scripts" / (name + ".py") for name in names] + [REPO / p for p in (
        "src/evaluation/batch_allocation.py", "tests/test_empirical_analysis.py", "tests/test_empirical_outcomes.py", "tests/test_empirical_outcome_stages.py",
        "docs/cas_q2/EMPIRICAL_D_EXECUTION_CONTRACT.md", "docs/cas_q2/EMPIRICAL_D_DECODE_BOUNDARY_REFINEMENT.md")]


def inputs(root, stage, predecessor_paths):
    audit_paths = verify_namespace(AUDIT, AUDIT_SHA)
    audit = load(AUDIT / "OUTCOME_INPUT_AUDIT.json")
    require(audit["status"] == "PASS_OUTCOME_SOURCE_INVENTORY_ONLY" and audit["all_source_bytes_unchanged"] is True and
        audit["fresh_gold_values_materialized"] == audit["canonical_answers_decoded"] == 0, "Accepted value-blind D source audit")
    original = [checked(Path(e["path"]), e["sha256"], e["size_bytes"]) for e in audit["checked_files"]]
    paths = predecessor_paths + audit_paths + unchanged_freeze(AUDIT) + original + verify_namespace(COHORT, COHORT_SHA) + source_paths()
    # Canonical and policy payloads already belong to authenticated C4 inputs.
    require(CANONICAL.resolve() in {p.resolve() for p in paths} and SELECTED.resolve() in {p.resolve() for p in paths}, "Complete actual branch/cohort input binding")
    readable = source_paths() + audit_paths
    if stage in {"mapping", "outcome_validation"}:
        readable += original + [CANONICAL, SELECTED]
        if stage == "outcome_validation":
            readable += [STAGES["mapping"] / "numeric_outcomes.jsonl", STAGES["mapping"] / "BUILD_RECEIPT.json"]
    else:
        readable += [C4["policies"] / "POLICIES.json", C4["policies"] / "actions.jsonl", STAGES["mapping"] / "numeric_outcomes.jsonl"]
        if stage == "analysis_validation":
            readable += [p for p in STAGES["analysis"].rglob("*") if p.is_file()]
    return audit, sorted(set(paths)), sorted(set(readable))
