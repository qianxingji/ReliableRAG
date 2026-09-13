"""Independent safe-projection/runtime/pool derivation; no native builder import."""
import hashlib
import json
from pathlib import Path
import re
import sys

from scripts.empirical_pool_io import DATASETS, SPLITS, OUT, REPO, COHORT_SHA, record, require, verify_namespace
from scripts.replay_roa_original import install_boundary, write_json
from scripts.verify_roa_artifacts import digest, safe_file, relative_path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def json_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def parse_json(payload):
    def pairs(entries):
        value = {}
        for key, item in entries:
            require(key not in value, "Duplicate JSON field")
            value[key] = item
        return value
    def reject(value):
        raise RuntimeError("Nonfinite JSON constant")
    return json.loads(payload, object_pairs_hook=pairs, parse_constant=reject)


def rows_from(path):
    result = []
    with path.open("rb") as stream:
        for line in stream:
            row = parse_json(line)
            require(line == canonical(row) + b"\n", "Noncanonical row bytes")
            result.append(row)
    return result


def runtime_from_projection(row, dataset):
    require(type(row) is dict, "Projection object")
    require(set(row) == ({"id", "question", "paragraphs"} if dataset == "musique" else
                         {"_id", "question", "context"}), "Projection field allowlist")
    identifier = row["id" if dataset == "musique" else "_id"]
    require(type(identifier) is str and bool(identifier.strip()), "Identifier type")
    require(type(row["question"]) is str and bool(row["question"].strip()), "Question type")
    documents = []
    if dataset == "musique":
        require(type(row["paragraphs"]) is list, "Paragraph array")
        indices = set()
        for paragraph in row["paragraphs"]:
            require(type(paragraph) is dict and set(paragraph) == {"idx", "title", "paragraph_text"}, "Paragraph allowlist")
            require(type(paragraph["idx"]) is int and paragraph["idx"] not in indices, "Paragraph index")
            indices.add(paragraph["idx"])
            require(all(type(paragraph[k]) is str and bool(paragraph[k].strip()) for k in ("title", "paragraph_text")), "Paragraph text")
            documents.append(dict(title=paragraph["title"], sentences=[paragraph["paragraph_text"]]))
    else:
        require(type(row["context"]) is list, "Context array")
        for paragraph in row["context"]:
            require(type(paragraph) is list and len(paragraph) == 2, "Context pair")
            title, sentences = paragraph
            require(type(title) is str and type(sentences) is list and all(type(s) is str for s in sentences), "Context text")
            documents.append(dict(title=title, sentences=sentences))
    require(bool(documents), "Empty runtime documents")
    return dict(id=identifier, dataset=dataset, split=SPLITS[dataset], question=row["question"], documents=documents)


def independent_pool(runtime, dataset):
    seen, ordered, pre_count = {}, [], 0
    for example in runtime:
        require(set(example) == {"id", "dataset", "split", "question", "documents"}, "Runtime allowlist")
        for document in example["documents"]:
            require(set(document) == {"title", "sentences"}, "Document allowlist")
            pre_count += 1
            content = json_sha(document["sentences"])
            normalized = re.sub(r"\s+", " ", document["title"].strip()).casefold()
            identity = json_sha(dict(title=normalized, content_hash=content))
            item = dict(id=dataset + ":" + identity[:24], dataset=dataset, title=document["title"],
                        sentences=document["sentences"], content_hash=content)
            if item["id"] in seen:
                require(item == seen[item["id"]], "Original-title identity collision")
            else:
                seen[item["id"]] = item
                ordered.append(item)
    fingerprint = json_sha([{k: item[k] for k in ("id", "title", "content_hash")} for item in ordered])
    return ordered, dict(questions=len(runtime), pre_dedup_documents=pre_count, documents=len(ordered),
                        duplicates_removed=pre_count-len(ordered), corpus_fingerprint=fingerprint)


def main():
    require(not (OUT / "INDEPENDENT_VALIDATION.json").exists(), "Already validated")
    boundary = install_boundary(OUT)
    result = dict(status="FAIL", cas_q2_status="NOT READY", checks=0, scientific_fit_calls=0,
                  model_calls=0, fresh_gold_values_materialized=0, datasets={})
    def eq(left, right):
        result["checks"] += 1
        require(left == right, "Independent C1 mismatch")
    try:
        manifest = parse_json((OUT / "EXECUTION_MANIFEST.json").read_bytes())
        expected_files = {"EXECUTABLE_FREEZE.json", "BUILD_RECEIPT.json"} | {
            category + "/" + d + ".jsonl" for category in ("projected", "runtime", "pools") for d in DATASETS}
        eq({e["path"] for e in manifest["files"]}, expected_files)
        eq({p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()},
           expected_files | {"EXECUTION_MANIFEST.json"})
        for e in manifest["files"]:
            q = safe_file(OUT, relative_path(e["path"]))
            eq(digest(q), e["sha256"]); eq(q.stat().st_size, e["size_bytes"])
        freeze = parse_json((OUT / "EXECUTABLE_FREEZE.json").read_bytes())
        eq(freeze["status"], "FROZEN_BEFORE_PROJECTION")
        for e in freeze["inputs"]:
            eq(record(Path(e["path"])), e)
        cohort = REPO / "outputs/cas_q2/empirical_fresh_cohort_v1"
        verify_namespace(cohort, COHORT_SHA)
        ids = [parse_json(line) for line in (cohort / "SELECTED_IDS_PRIVATE.jsonl").read_bytes().splitlines()]
        receipt = parse_json((OUT / "BUILD_RECEIPT.json").read_bytes())
        eq(receipt["status"], "BUILT_PENDING_INDEPENDENT")
        eq(receipt["source_commit"], freeze["commit"])
        for key in ("scientific_fit_calls", "retrieval_calls", "model_calls", "fresh_gold_values_materialized"):
            eq(receipt[key], 0)
        eq(receipt["projected_questions"], 6000)
        eq(receipt["materialization_gate"]["denied_materialization_attempts"], 0)
        eq(receipt["materialization_gate"]["gold_outcome_values_materialized"], 0)
        eq(receipt["sources_unchanged"], True)
        for d in DATASETS:
            projected = rows_from(OUT / "projected" / (d + ".jsonl"))
            runtime = rows_from(OUT / "runtime" / (d + ".jsonl"))
            actual_pool = rows_from(OUT / "pools" / (d + ".jsonl"))
            eq(len(projected), 2000); eq(len(runtime), 2000)
            eq([r["id"] for r in runtime], [r["sample_id"] for r in ids if r["dataset"] == d])
            for projected_row, runtime_row in zip(projected, runtime):
                eq(runtime_from_projection(projected_row, d), runtime_row)
            pool, counts = independent_pool(runtime, d)
            eq(len(pool), len(actual_pool))
            for expected, actual in zip(pool, actual_pool):
                eq(expected, actual)
            eq(counts, receipt["datasets"][d])
            eq(len({r["id"] for r in actual_pool}), len(actual_pool))
            result["datasets"][d] = counts
        require(not boundary["blocked"], "Validation boundary violation")
        result.update(status="PASS_INDEPENDENT_EMPIRICAL_POOL", projected_questions=6000,
            no_native_projector_or_builder_import=True, exact_runtime_and_pool_derivation=True,
            limitations="Native raw projection authenticated and guarded; independent derivation starts at safe projected source rows. No separate raw-source parser, model inference or outcome evidence.")
    except Exception as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    write_json(OUT / "INDEPENDENT_VALIDATION.json", result)
    if result["status"] == "FAIL":
        print(json.dumps(result)); return 2
    write_json(OUT / "SEAL.json", dict(status="PASS_C1_POOL_ONLY", independent_sha256=digest(OUT / "INDEPENDENT_VALIDATION.json"),
                                     cas_q2_status="NOT READY", fresh_gold_values_materialized=0))
    write_json(OUT / "SHA256_MANIFEST.json", dict(files=[dict(path=p.relative_to(OUT).as_posix(),
        sha256=digest(p), size_bytes=p.stat().st_size) for p in sorted(OUT.rglob("*")) if p.is_file()]))
    print(json.dumps(result)); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
