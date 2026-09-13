"""Prespecified common-eligibility nine-policy batch allocation; no labels or fitting."""
import math

SCORED_POLICIES=("HGB","GbV","ROA-FULL","ROA-NOGBV","HGB_GBV_R","HGB_ONLY_R","GBV_ONLY_R","V2")
POLICIES=("Keep",)+SCORED_POLICIES


def allocate(keys, eligible, scores):
    """All rows remain in the denominator; the caller must reconcile one shared mask."""
    keys=list(keys);universe=set(keys);eligible=set(eligible)
    if len(keys)!=len(universe) or not eligible<=universe: raise ValueError("Unique keys and common eligibility subset required")
    if any(len(k)!=3 or not all(type(x) is str and x for x in k) or
           k[0] not in ("hotpotqa","2wikimultihopqa","musique") or k[1] not in ("bm25","dense","hybrid") for k in keys):
        raise ValueError("Canonical dataset/retriever/sample_id keys required")
    if set(scores)!=set(SCORED_POLICIES): raise ValueError("Exact eight scored policies required")
    cap=round(.05*len(keys));selected={"Keep":set()}
    for policy in SCORED_POLICIES:
        values=scores[policy]
        if set(values)!=universe: raise ValueError("Every policy must retain all rows")
        for key,value in values.items():
            if key in eligible:
                if type(value) not in (int,float) or not math.isfinite(value): raise ValueError("Common eligible row has invalid score")
            elif value is not None: raise ValueError("Ineligible scores must be reconciled to common null mask")
        selected[policy]=set(sorted(eligible,key=lambda k:(-values[k],k))[:cap])
    expected=min(cap,len(eligible))
    if any(len(selected[p])!=expected for p in SCORED_POLICIES): raise AssertionError("Common budget accounting")
    ledger=[dict(dataset=k[0],retriever=k[1],sample_id=k[2],eligible=k in eligible,
                 scores={p:scores[p][k] for p in SCORED_POLICIES},
                 actions={p:"REPLACE" if k in selected[p] else "KEEP" for p in POLICIES})
            for k in sorted(universe)]
    return dict(N_all=len(keys),N_eligible=len(eligible),cap=cap,
                replacement_counts={p:len(selected[p]) for p in POLICIES},selected=selected,ledger=ledger)
