"""One-time selected-reference mapping, with all method inputs undecodable."""
import math
import sys

from scripts.empirical_outcome_stage_io import arguments, selected_ids, CANONICAL
from scripts.empirical_outcome_stage_run import OutcomeRun
from scripts.empirical_outcome_native import canonical_answer_rows, selected_references
from scripts.empirical_scoring_journals import Ledger
from scripts.empirical_pool_io import record, require
from scripts.empirical_runtime_contract import sha_json


def main():
    root, pins = arguments("mapping")
    run = OutcomeRun(root, "mapping", pins)
    ledger, success = None, False
    try:
        run.prepare()
        selected = selected_ids()
        run.phase["stage"] = "method_blind_selected_reference_mapping"
        run.start_gold()
        references, counters = selected_references(run.root, run.spec, selected, run.Cursor, run.readers, run.parquet)
        run.result.update(selected_question_labels_materialized=len(references), raw_reference_strings_materialized=sum(map(len, references.values())),
            source_counts=counters, selected_reference_binding_sha256=sha_json([[ds, sid, references[(ds, sid)]] for ds, sid in sorted(references)]))
        expected = {(ds, r, sid) for ds, sid in selected for r in ("bm25", "dense", "hybrid")}
        seen = set()
        ledger = Ledger(run.out / "numeric_outcomes.jsonl")
        for branch in canonical_answer_rows(CANONICAL, run.Cursor):
            key = tuple(branch[k] for k in ("dataset", "retriever", "sample_id"))
            require(key in expected and key not in seen, "Exact unique selected canonical answer identity")
            seen.add(key)
            values = {k: branch[k] for k in ("dataset", "retriever", "sample_id")}
            for state in ("a0", "a1"):
                values[state+"_em"] = int(run.metric.exact_match(branch[state], references[(key[0], key[2])]))
                values[state+"_f1"] = float(run.metric.token_f1(branch[state], references[(key[0], key[2])]))
                require(values[state+"_em"] in (0, 1) and math.isfinite(values[state+"_f1"]) and 0 <= values[state+"_f1"] <= 1, "Finite native numeric outcome")
            ledger.append(values)
            run.phase["completed_rows"] = ledger.rows
        require(seen == expected and ledger.rows == 18000, "Complete selected numeric outcome ledger")
        run.result.update(traces=18000, question_groups=6000, numeric_ledger=record(run.out / "numeric_outcomes.jsonl"),
            canonical_answers_decoded=36000, unneeded_question_passage_strings_decoded=0, method_inputs_decoded=0,
            reference_policy=run.spec["reference_policy"], raw_reference_strings_written=False, quality_analysis_started=False)
        success = True
    except Exception as exc:
        run.error(exc)
    finally:
        if ledger is not None: ledger.close()
    return run.finish(success=success)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
