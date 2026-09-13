"""Independent complete fixed-policy analysis and every explicit-copy draw."""
import sys

from scripts.empirical_outcome_stage_io import arguments, rows, STAGES, STATUSES, C4
from scripts.empirical_outcome_stage_run import OutcomeRun
from scripts.empirical_analysis_independent import IndependentPanel, compare_report, independent_intervals, validate_draw_files
from scripts.empirical_pool_io import load, record, require
from scripts.empirical_neural_checks import Checks


def main():
    from threadpoolctl import threadpool_limits
    root, pins = arguments("analysis_validation")
    run = OutcomeRun(root, "analysis_validation", pins)
    accepted = None
    try:
        run.prepare()
        run.phase["stage"] = "independent_numeric_population_and_point_reports"
        actions = list(rows(C4["policies"] / "actions.jsonl"))
        require(actions == load(C4["policies"] / "POLICIES.json")["ledger"], "Complete frozen prelabel row binding")
        run.result["numeric_outcome_rows_read"] = None
        numeric = list(rows(STAGES["mapping"] / "numeric_outcomes.jsonl"))
        run.result["numeric_outcome_rows_read"] = len(numeric)
        panel = IndependentPanel(actions, numeric)
        folder = STAGES["analysis"]
        a = panel.audit
        with threadpool_limits(limits=1):
            point = load(folder / "POINT_ESTIMATES.json")
            compare_report(point, panel.point(), a)
            a.exact(list(rows(folder / "GROUP_ORDER_PRIVATE.jsonl")), [dict(dataset=d, sample_id=sid) for d, sid in panel.groups], "exact frozen bootstrap group order")
            expected_storage = dict(dtype="little-endian uint16", shape=[20000, 6000], completed_draws=20000,
                completed_weight_bytes=240000000, expected_complete_weight_bytes=240000000, maximum_count=2000,
                arithmetic_dtype="int64", no_header=True, seed=20260926, generator="numpy.default_rng",
                group_order=record(folder / "GROUP_ORDER_PRIVATE.jsonl"), dataset_order=["2wikimultihopqa", "hotpotqa", "musique"],
                question_draws_per_dataset=2000, three_siblings_together=True, models_and_realized_pool_fixed=True)
            a.exact(load(folder / "BOOTSTRAP_STORAGE.json"), expected_storage, "complete prospective draw storage contract")
            run.phase["stage"] = "independent_every_RNG_draw_and_explicit_policy_copy_allocation"
            def progress(count):
                run.phase["completed_rows"] = count
                if count % 100 == 0: print("D_INDEPENDENT_DRAWS", count, 20000, flush=True)
            draws = validate_draw_files(panel, folder / "BOOTSTRAP_QUESTION_WEIGHTS.u16le", folder / "BOOTSTRAP_DRAWS.jsonl", progress=progress)
            a.exact(len(draws), 20000, "all primary and sensitivity draws")
            observed_intervals = load(folder / "INTERVALS.json")
            compare_report(observed_intervals, independent_intervals(panel, draws), a)
        build = load(folder / "BUILD_RECEIPT.json")
        for field, value in dict(traces=18000, question_groups=6000, completed_draws=20000, bootstrap_seed=20260926,
            action_modifications=0, primary_comparisons=3, primary_endpoints=6, scientific_fit_calls=0,
            neural_model_loads=0, model_forward_calls=0, new_retrieval_calls=0, new_generation_calls=0,
            raw_reference_strings_materialized=0, numeric_outcome_rows_read=18000).items():
            a.exact(build[field], value, "complete frozen analysis execution receipt")
        a.exact(build["boundary"]["denied"], [], "no analysis boundary denials")
        a.exact(build["boundary"]["forbidden_calls"], 0, "no forbidden analysis computation")
        accepted = dict(status=STATUSES["analysis_validation"], cas_q2_status="NOT READY", checks=a.count,
            traces=18000, question_groups=6000, validated_draws=20000, explicit_policy_allocations_checked=180000,
            same_draw_fixed_action_sensitivities_checked=180000, exact_integer_action_event_counts=True,
            exact_RNG_multiplicities=True, complete_point_and_cell_reports_match=True, all_six_adjusted_intervals_match=True,
            all_source_inputs_bound=True, predecessor_manifests=pins, scientific_fit_calls=0, model_forward_calls=0,
            raw_reference_strings_materialized=0, action_modifications=0,
            limitations=["Shared pinned NumPy RNG and quantile implementation; independent allocation expands and sorts row copies.",
                "All intervals condition on fixed trained models and realized bounded pools.",
                "No equivalence or Submission Ready claim follows from this computational PASS."])
        run.result.update(traces=18000, question_groups=6000, completed_draws=20000, independent_checks=a.count,
            action_modifications=0, quality_claims_require_separate_lead_review=True)
    except Exception as exc:
        run.error(exc)
    return run.finish(success=accepted is not None, independent=accepted)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
