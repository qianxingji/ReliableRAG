"""Count remaining question IDs from authenticated ledgers; select none."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
from scripts.select_v2_fresh_ids import read_id_ledger
from scripts.verify_roa_artifacts import digest
from scripts.replay_roa_original import write_json

DATASETS=("hotpotqa","2wikimultihopqa","musique")


def inventory(sources,forbidden):
    if set(sources)!=set(DATASETS):raise ValueError("All three datasets must be declared")
    union=set(forbidden)
    return {d:dict(source=len(sources[d]),excluded=sum(k in union for k in sources[d]),available=sum(k not in union for k in sources[d])) for d in DATASETS}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();root=args.project_root.resolve()
    if args.output.exists():p.error("Never overwrite an inventory")
    cohort=json.loads((root/"outputs/daa_v2_fresh_v1/cohort_freeze/COHORT_FREEZE.json").read_text())
    records=list(cohort["source_id_ledgers"].values())+[cohort["selected_id_ledger"]]
    # The original ROA source manifest binds the current question set separately.
    source={}
    for ds,item in cohort["source_id_ledgers"].items():
        path=root/item["path"]
        if digest(path)!=item["sha256"] or path.stat().st_size!=item["size_bytes"]:raise RuntimeError("SOURCE_HASH")
        rows=read_id_ledger(path)
        if any(d!=ds for d,_ in rows):raise RuntimeError("DATASET_BINDING")
        source[ds]=set(rows)
    oldpath=root/"outputs/daa_v2_fresh_v1/audit/all_forbidden_ids.jsonl"
    if digest(oldpath)!=cohort["frozen_forbidden_union_sha256"]:raise RuntimeError("EXCLUSION_HASH")
    selected=root/cohort["selected_id_ledger"]["path"]
    if digest(selected)!=cohort["selected_id_ledger"]["sha256"]:raise RuntimeError("OPENED_COHORT_HASH")
    old=set(read_id_ledger(oldpath));opened=set(read_id_ledger(selected));forbidden=old|opened
    if old&opened:raise RuntimeError("ORIGINAL_FRESH_COHORT_OVERLAP")
    result=dict(status="ID_ONLY_AVAILABILITY_INVENTORY_NO_SELECTION",cas_q2_status="NOT READY",available_after_exclusion=inventory(source,forbidden),
                original_forbidden_questions=len(old),newly_developmentized_questions=len(opened),total_forbidden_questions=len(forbidden),
                source_ledgers=cohort["source_id_ledgers"],exclusion_ledgers=[dict(path=str(oldpath),sha256=digest(oldpath)),cohort["selected_id_ledger"]],
                question_ids_selected=0,new_raw_benchmark_or_gold_access=False,scientific_fit_calls=0,
                limitation="Authenticated existing source ledgers only; not a claim that every public split or all unlogged historical uses have been inventoried.")
    write_json(args.output,result);print(json.dumps(result["available_after_exclusion"]))


if __name__=="__main__":main()
