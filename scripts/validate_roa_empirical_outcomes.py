"""Separate method-blind full outcome validation with independent EM/F1 math."""
import sys

from scripts.empirical_outcome_stage_io import arguments, selected_ids, rows, CANONICAL, STAGES, STATUSES
from scripts.empirical_outcome_stage_run import OutcomeRun
from scripts.empirical_outcome_native import canonical_answer_rows, selected_references
from scripts.empirical_outcome_independent import validate_numeric_rows
from scripts.empirical_pool_io import load, record, require
from scripts.empirical_runtime_contract import sha_json


def main():
    root, pins = arguments("outcome_validation")
    run = OutcomeRun(root, "outcome_validation", pins)
    accepted = None
    try:
        run.prepare()
        selected = selected_ids()
        run.phase["stage"] = "independent_method_blind_reference_reread"
        run.start_gold()
        refs, counts = selected_references(run.root, run.spec, selected, run.Cursor, run.readers, run.parquet)
        binding = sha_json([[ds, sid, refs[(ds, sid)]] for ds, sid in sorted(refs)])
        run.result.update(selected_question_labels_materialized=6000, raw_reference_strings_materialized=sum(map(len, refs.values())),
            selected_labels_reread_for_independent_validation=6000, source_counts=counts)
        mapping = load(STAGES["mapping"] / "BUILD_RECEIPT.json")
        numeric = STAGES["mapping"] / "numeric_outcomes.jsonl"
        require(binding == mapping["selected_reference_binding_sha256"] and counts == mapping["source_counts"] and
            record(numeric) == mapping["numeric_ledger"], "Independent exact selected-reference/source/numeric binding")
        run.phase["stage"] = "independent_all_outcome_metric_values"
        result = validate_numeric_rows(canonical_answer_rows(CANONICAL, run.Cursor), refs, rows(numeric))
        require(result["traces"] == 18000 and result["question_groups"] == 6000 and result["metric_values_checked"] == 72000, "All fresh numeric metrics independently checked")
        accepted = dict(status=STATUSES["outcome_validation"], cas_q2_status="NOT READY", **result,
            numeric_ledger=record(numeric), selected_reference_binding_sha256=binding, predecessor_manifests=pins,
            source_counts=counts, raw_reference_strings_written=False, method_inputs_decoded=0,
            selected_labels_reread_for_independent_validation=6000, quality_analysis_started=False,
            limitations="Independent metric formulas share the authenticated original selected-reference parser and original source bytes; no method selection occurs.")
        run.phase["completed_rows"] = 18000
        run.result.update(traces=18000, question_groups=6000, metric_values_checked=72000, method_inputs_decoded=0,
            numeric_outcome_rows_read=18000, unneeded_question_passage_strings_decoded=0, raw_reference_strings_written=False)
    except Exception as exc:
        run.error(exc)
    return run.finish(success=accepted is not None, independent=accepted)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
