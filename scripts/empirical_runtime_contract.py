"""Pure trace construction and prespecified native runtime replay membership."""
import hashlib
import json

DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_json(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def trace_key(row):
    return row["dataset"], row["retriever"], row["sample_id"]


def make_traces(top5_by_dataset):
    if set(top5_by_dataset) != set(DATASETS): raise ValueError("Exact runtime datasets")
    traces = []
    for dataset in DATASETS:
        rows = top5_by_dataset[dataset]
        if len(rows) != 6000: raise ValueError("Complete per-dataset top5 ledger")
        for row in rows:
            if set(row) != {"dataset", "retriever", "sample_id", "document_ids"} or row["dataset"] != dataset:
                raise ValueError("Top5 source schema")
            if (row["retriever"] not in RETRIEVERS or type(row["sample_id"]) is not str or not row["sample_id"] or
                type(row["document_ids"]) is not list or any(type(x) is not str or not x for x in row["document_ids"])):
                raise ValueError("Top5 retrieval contract")
            if len(row["document_ids"]) != 5 or len(set(row["document_ids"])) != 5:
                raise ValueError("Five unique original evidence IDs")
            traces.append(dict(position=len(traces), dataset=dataset, retriever=row["retriever"], sample_id=row["sample_id"],
                original_top5_ids=list(row["document_ids"]), original_top5_row_sha256=sha_json(row)))
    keys = [trace_key(row) for row in traces]
    if len(keys) != 18000 or len(set(keys)) != 18000:
        raise ValueError("Complete unique trace set")
    groups = {(d, sid) for d, r, sid in keys}
    if len(groups) != 6000 or set(keys) != {(d, r, sid) for d, sid in groups for r in RETRIEVERS}:
        raise ValueError("All three retriever siblings required")
    return traces


def replay_subset(traces):
    wanted = set()
    for dataset in DATASETS:
        for retriever in RETRIEVERS:
            rows = [r for r in traces if (r["dataset"], r["retriever"]) == (dataset, retriever)]
            if len(rows) != 2000: raise ValueError("Replay source stratum count")
            ranked = sorted(rows, key=lambda row: (hashlib.sha256(("daa-v2-runtime-replay-v1|" + dataset + "|" + retriever + "|" + row["sample_id"]).encode("utf-8")).hexdigest(), row["sample_id"]))
            wanted.update(trace_key(row) for row in ranked[:20])
    if len(wanted) != 180: raise ValueError("Replay exact subset size")
    return [row for row in traces if trace_key(row) in wanted]
