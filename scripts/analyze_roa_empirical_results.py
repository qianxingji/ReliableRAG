"""Execute all frozen D point/cell/paired-bootstrap analyses exactly once."""
import sys

from scripts.empirical_outcome_stage_io import arguments, rows, STAGES, C4
from scripts.empirical_outcome_stage_run import OutcomeRun
from scripts.empirical_analysis_math import Panel, point_estimates, question_weights, draw_record, intervals, SEED, DRAWS
from scripts.empirical_analysis_storage import BootstrapWriter
from scripts.empirical_scoring_journals import Ledger
from scripts.empirical_pool_io import load, record, require
from scripts.replay_roa_original import write_json


def main():
    from threadpoolctl import threadpool_limits
    root, pins = arguments("analysis")
    run = OutcomeRun(root, "analysis", pins)
    writer, group_ledger, success = None, None, False
    try:
        run.prepare()
        run.phase["stage"] = "numeric_only_fixed_policy_point_estimates"
        allocation = load(C4["policies"] / "POLICIES.json")
        actions = list(rows(C4["policies"] / "actions.jsonl"))
        require(actions == allocation["ledger"] and allocation["N_all"] == 18000 and allocation["cap"] == 900, "Accepted duplicate prelabel actions and budget")
        run.result["numeric_outcome_rows_read"] = None
        outcomes = list(rows(STAGES["mapping"] / "numeric_outcomes.jsonl"))
        run.result["numeric_outcome_rows_read"] = len(outcomes)
        panel = Panel(actions, outcomes)
        require(panel.n == 18000 and len(panel.groups) == 6000 and panel.cap == 900, "Complete actual empirical analysis population")
        with threadpool_limits(limits=1):
            point = point_estimates(panel)
            write_json(run.out / "POINT_ESTIMATES.json", point)
            group_ledger = Ledger(run.out / "GROUP_ORDER_PRIVATE.jsonl")
            for dataset, sample_id in panel.groups:
                group_ledger.append(dict(dataset=dataset, sample_id=sample_id))
            group_ledger.close()
            writer = BootstrapWriter(run.out, groups=6000, draws=DRAWS, questions_per_dataset=2000)
            run.phase["stage"] = "all_frozen_reallocated_and_fixed_action_bootstrap_draws"
            records = []
            for index, counts in enumerate(question_weights(panel)):
                draw = draw_record(panel, counts, index)
                writer.append(counts, draw)
                records.append(draw)
                run.phase["completed_rows"] = index + 1
                if (index + 1) % 100 == 0:
                    print("D_BOOTSTRAP_DRAWS", index + 1, DRAWS, flush=True)
            require(writer.completed == len(records) == DRAWS == 20000, "Every frozen bootstrap draw completed")
            writer.close()
            storage = writer.summary()
            require((run.out / "BOOTSTRAP_QUESTION_WEIGHTS.u16le").stat().st_size == storage["expected_complete_weight_bytes"] == 240000000, "Exact complete bootstrap count storage")
            write_json(run.out / "BOOTSTRAP_STORAGE.json", dict(**storage, seed=SEED, generator="numpy.default_rng",
                group_order=record(run.out / "GROUP_ORDER_PRIVATE.jsonl"), dataset_order=["2wikimultihopqa", "hotpotqa", "musique"],
                question_draws_per_dataset=2000, three_siblings_together=True, models_and_realized_pool_fixed=True))
            write_json(run.out / "INTERVALS.json", intervals(panel, records))
        run.result.update(traces=18000, question_groups=6000, completed_draws=20000, bootstrap_seed=SEED,
            action_modifications=0, fixed_models_and_candidate_pools=True, all_nine_policies_retained=True,
            primary_comparisons=3, primary_endpoints=6, report_scope="Frozen conditional empirical analysis pending separate independent validation",
            limitations="Bonferroni-adjusted bootstrap coverage is approximate and conditional on fixed models/pools; no equivalence, novel-method or Submission Ready claim.")
        success = True
    except Exception as exc:
        run.error(exc)
    finally:
        if writer is not None:
            run.result["partial_or_complete_bootstrap_storage"] = writer.summary()
            writer.close()
        if group_ledger is not None: group_ledger.close()
    return run.finish(success=success)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
