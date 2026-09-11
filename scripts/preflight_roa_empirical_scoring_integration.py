"""Guarded invented-only C4 downstream integration with authenticated saved models."""
import argparse
import importlib.metadata
from pathlib import Path
import platform
import subprocess
import sys

from scripts.empirical_scoring_io import REPO, inputs, saved_models, record, require
from scripts.empirical_scoring_import_v2 import native_scoring
from scripts.empirical_pool_io import verify_namespace, load
from scripts.empirical_scoring_guard import guard
from scripts.empirical_scoring_binding_fixtures import invented_bound_rows, InventedLikelihood, InventedGbV, POOL_SHA, CONFIG_SHA
from scripts.empirical_scoring_bindings import restore_bound_trace
from scripts.empirical_scoring_pipeline import score_likelihood_trace, score_gbv_trace, common_policy_ledger
from scripts.empirical_policy_independent import validate_policies
from scripts.empirical_retrieval_io import configure_environment, boundary_record, seal
from scripts.replay_roa_original import write_json
from scripts.empirical_runtime_contract import canonical, trace_key

PREVIOUS_SHA = "65bfe79a80974c67204eb1dd792d420ffc974b4e9e6be95d3496ae2b86aa0ceb"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    out = REPO / "outputs/cas_q2/empirical_scoring_integration_cpu_v1"
    require(not out.exists(), "Single-use invented integration namespace")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit integration first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    out.mkdir(parents=True, exist_ok=False)
    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=commit,
        scientific_fit_calls=0, pretrained_neural_model_loads=0, neural_forward_calls=0,
        fresh_branch_rows_read=0, fresh_gold_values_materialized=0)
    boundary = None
    try:
        environment = configure_environment(out)
        metadata = platform.uname()._asdict()
        import joblib
        import sklearn.ensemble, sklearn.linear_model, sklearn.pipeline, sklearn.preprocessing
        from threadpoolctl import threadpool_info, threadpool_limits
        threadpool_info()
        joblib.cpu_count(only_physical_cores=True)
        audit, pre, paths = inputs(root)
        prior = REPO / "outputs/cas_q2/empirical_saved_scoring_preflight_v2"
        paths += verify_namespace(prior, PREVIOUS_SHA)
        previous = load(prior / "CPU_PREFLIGHT.json")
        require(previous["status"] == "PASS_SAVED_SCORING_CPU_INVENTED_ONLY", "Accepted native compatibility")
        for entry in load(prior / "EXECUTABLE_FREEZE.json")["inputs"]:
            require(record(Path(entry["path"])) == entry, "Prior CPU freeze unchanged")
            paths.append(Path(entry["path"]))
        names = ("scripts/preflight_roa_empirical_scoring_integration.py", "scripts/empirical_scoring_bindings.py",
            "scripts/empirical_semantic_witness.py", "scripts/empirical_scoring_binding_fixtures.py",
            "scripts/empirical_scoring_pipeline.py", "scripts/empirical_feature_independent.py",
            "scripts/empirical_policy_independent.py", "scripts/empirical_policy_actions.py",
            "scripts/empirical_likelihood_witness.py", "scripts/empirical_gbv_witness.py",
            "scripts/empirical_runtime_contract.py", "docs/cas_q2/EMPIRICAL_C4_BINDING_NOTE.md",
            "tests/test_empirical_scoring_integration.py", "tests/test_empirical_likelihood_witness.py",
            "tests/test_empirical_gbv_witness.py", "tests/test_empirical_policy_actions.py")
        paths += [REPO / name for name in names] + [Path(sys.executable)]
        records = [record(path) for path in sorted(set(paths))]
        versions = {name: importlib.metadata.version(name) for name in pre["environment"]["versions"]}
        require(versions == pre["environment"]["versions"], "Original scoring environment")
        write_json(out / "EXECUTABLE_FREEZE.json", dict(source_commit=commit, command=sys.argv, inputs=records,
            environment=environment, versions=versions, platform_metadata=metadata,
            previous_cpu_manifest_sha256=PREVIOUS_SHA,
            scope="36 invented traces with static semantic/likelihood/NLI values; real saved downstream estimators only"))
        boundary = guard(root, out, paths, mode="cpu_models")
        wrapper, native, v2, eligibility, schema, nodes = native_scoring(root)
        require(nodes == previous["native_ast_nodes"], "Accepted original scientific definitions")
        models, bundle, panel = saved_models(root, native, v2)
        traces, bindings, base, gbv = [], [], [], []
        answers = (("silver", "blue"), ("The cog", "cog!"), ("", "blue"), ("the", "blue"))
        with threadpool_limits(limits=1):
            for dataset in ("hotpotqa", "2wikimultihopqa", "musique"):
                for retriever in ("bm25", "dense", "hybrid"):
                    for pair in answers:
                        index = len(traces)
                        rows = invented_bound_rows(index, retriever, dataset, pair)
                        trace = restore_bound_trace(wrapper, *rows, pool_sha=POOL_SHA, runtime_config_sha=CONFIG_SHA)
                        trace["answer_semantic_agreement"] = .125 + index * .001
                        traces.append(trace)
                        bindings.append(dict(branch=rows[0], provenance=rows[1], prepared=rows[2], repair=rows[3]))
                        base.append(score_likelihood_trace(wrapper, native, models, eligibility, trace, InventedLikelihood(native, index)))
                        gbv.append(score_gbv_trace(eligibility, trace, InventedGbV(fail_second=index == 0)))
            allocation = common_policy_ledger(traces, base, gbv, eligibility, v2, bundle, panel)
            independent = validate_policies(traces, base, gbv, allocation, models, native.ordinary.ORDINARY_NAMES, bundle, panel)
        require(len(traces) == 36 and allocation["N_eligible"] == 17 and allocation["cap"] == 2, "Fixed invented fixture accounting")
        selected = allocation.pop("selected")
        allocation["selected"] = {name: [list(k) for k in sorted(keys)] for name, keys in selected.items()}
        for name, rows in (("INVENTED_BINDINGS.jsonl", bindings), ("INVENTED_TRACES.jsonl", traces),
                ("INVENTED_BASE.jsonl", base), ("INVENTED_GBV.jsonl", gbv)):
            with (out / name).open("xb") as stream:
                for row in rows:
                    stream.write(canonical(row) + b"\n")
        write_json(out / "INVENTED_POLICIES.json", allocation)
        write_json(out / "INDEPENDENT_DOWNSTREAM.json", independent)
        # Check the serialized objects too: a successful in-memory calculation is
        # not sufficient if storage loses a field, row or action membership.
        def read_rows(name):
            import json
            with (out / name).open(encoding="utf-8") as stream:
                return [json.loads(line) for line in stream]
        reopened = load(out / "INVENTED_POLICIES.json")
        reopened["selected"] = {name: {tuple(k) for k in values} for name, values in reopened["selected"].items()}
        with threadpool_limits(limits=1):
            roundtrip = validate_policies(read_rows("INVENTED_TRACES.jsonl"), read_rows("INVENTED_BASE.jsonl"),
                read_rows("INVENTED_GBV.jsonl"), reopened, models, native.ordinary.ORDINARY_NAMES, bundle, panel)
        require(roundtrip == independent, "Exact round-trip independent validation report")
        for entry in records:
            require(record(Path(entry["path"])) == entry, "Integration inputs unchanged")
        require(not boundary["denied"] and not boundary["call_counts"], "No forbidden or neural call in CPU integration")
        result.update(status="PASS_SAVED_SCORING_INTEGRATION_INVENTED_ONLY", invented_traces=36,
            invented_native_eligible=18, invented_common_eligible=17,
            saved_upstream_estimators_loaded=7, saved_v2_ensemble_bundles_loaded=1, fixed_parameter_heads=5,
            numeric_checks=independent["numeric_checks"], max_numeric_error=independent["max_numeric_error"],
            unchanged_numeric_tolerance=1e-10, native_ast_nodes=nodes, roundtrip_independent_equal=True,
            source_inputs_unchanged=True, replacement_counts=independent["replacement_counts"],
            limitation="Invented binding and downstream policy integration only; no neural scoring or fresh performance. Full neural witness validators and GPU preflights are still required.")
    except Exception as exc:
        frames = []
        tb = exc.__traceback__
        while tb:
            frames.append(dict(file=tb.tb_frame.f_code.co_filename, line=tb.tb_lineno, function=tb.tb_frame.f_code.co_name))
            tb = tb.tb_next
        result.update(error_type=type(exc).__name__, diagnostic=str(exc), code_locations=frames)
    finally:
        sys.setprofile(None)
    if boundary is not None:
        result["execution_boundary"] = boundary_record(boundary)
    write_json(out / "CPU_INTEGRATION.json", result)
    seal(out)
    print(result["status"], result.get("diagnostic", ""))
    return 2 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
