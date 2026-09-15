"""One guarded native runtime projection and pool build; no models or labels."""
import argparse
import ast
from pathlib import Path
import subprocess
import sys
import time

from scripts.empirical_pool_io import (DATASETS, SPLITS, OUT, REPO, load, record,
    require, authenticate, load_native, restrict_reads, seal_execution)
from scripts.replay_roa_original import install_boundary, write_json


OUT = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"


def native_census_check(native, path):
    # Execute the original function's AST unchanged, without its executor/imports.
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_census"]
    require(len(nodes) == 1, "Native census check definition")
    scope = {"require": native.require}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), scope)
    return scope["validate_census"]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", required=True, type=Path)
    p.add_argument("--replay-root", required=True, type=Path)
    args = p.parse_args()
    root = args.project_root.resolve()
    require(not OUT.exists(), "Single-use namespace already exists")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit sources first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    OUT.mkdir(parents=True, exist_ok=False)
    boundary = install_boundary(OUT)
    result = dict(status="FAIL", source_commit=commit, cas_q2_status="NOT READY",
        scientific_fit_calls=0, retrieval_calls=0, model_calls=0, fresh_gold_values_materialized=0, datasets={})
    started = time.monotonic()
    try:
        helper, sources, ids, paths, preflight = authenticate(root, args.replay_root)
        native = load_native(helper, root)
        accepted, nodes = native.load_accepted()
        check_census = native_census_check(native, helper.parent / "construct_pools.py")
        for d in ("2wikimultihopqa", "musique"):
            check_census(load(preflight / (d + "_CENSUS.json")), d)
        source_files = [REPO / name for name in (
            "scripts/build_roa_empirical_pool.py", "scripts/build_roa_empirical_pool_v2.py",
            "scripts/validate_roa_empirical_pool.py", "scripts/validate_roa_empirical_pool_v2.py",
            "docs/cas_q2/EMPIRICAL_C1_WINDOWS_CORRECTION.md",
            "scripts/empirical_pool_io.py", "scripts/replay_roa_original.py", "scripts/verify_roa_artifacts.py",
            "tests/test_empirical_pool.py", "docs/cas_q2/EMPIRICAL_C1_EXECUTION_CONTRACT.md",
            "docs/cas_q2/EMPIRICAL_REPLICATION_PROTOCOL_V1.md", "docs/cas_q2/EMPIRICAL_SAMPLE_SIZE_CORRIGENDUM.md",
            "docs/cas_q2/EMPIRICAL_AB_ACCEPTANCE.md")]
        paths.extend(source_files + [Path(sys.executable)])
        input_records = [record(q) for q in sorted(set(paths))]
        write_json(OUT / "EXECUTABLE_FREEZE.json", dict(status="FROZEN_BEFORE_PROJECTION", commit=commit,
            command=sys.argv, python=sys.version, platform=dict(sys_platform=sys.platform, windows=str(sys.getwindowsversion()) if sys.platform == "win32" else None), inputs=input_records,
            native_ast_nodes=nodes, scientific_parameters="Unchanged; C1 staging amendment only",
            scope="6000 selected runtime questions and three native candidate pools; zero downstream calls"))
        reads = restrict_reads(paths, OUT)
        gate = native.MaterializationGate(accepted)
        # Native writers now target only the NEW output namespace, after original AST authentication.
        native.OUT = OUT
        for d in DATASETS:
            selected = [r for r in ids if r["dataset"] == d]
            wanted = {r["sample_id"] for r in selected}
            print("PROJECTING", d, len(wanted), flush=True)
            if d == "hotpotqa":
                projected = native.selected_hotpot_safe(accepted, sources[d], wanted, gate)
            else:
                rows = accepted.project_selected_file(sources[d], dataset=d, wanted=wanted, observer=gate.observer)
                key = "id" if d == "musique" else "_id"
                projected = {r[key]: r for r in rows}
                require(len(rows) == len(projected), "Duplicate projected identity")
            require(set(projected) == wanted, "Exact projected cohort")
            safe_rows = [projected[r["sample_id"]] for r in selected]
            examples = [(accepted._musique_runtime(r, split=SPLITS[d]) if d == "musique" else
                accepted._hotpot_or_2wiki_runtime(r, dataset=d, split=SPLITS[d])) for r in safe_rows]
            require([e.id for e in examples] == [r["sample_id"] for r in selected], "Runtime order")
            corpus = accepted.build_pooled_corpus(examples)
            pool_rows = [dict(id=e.id, dataset=e.dataset, title=e.title, sentences=list(e.sentences), content_hash=e.content_hash)
                         for e in corpus.documents]
            # Round-trip validators see only these explicitly gold-free projection structures.
            def check_projection(row):
                require(set(row) == ({"id", "question", "paragraphs"} if d == "musique" else
                                     {"_id", "question", "context"}), "Projected source field contract")
                if d == "musique":
                    require(all(set(x) == {"idx", "title", "paragraph_text"} for x in row["paragraphs"]), "Paragraph fields")
            native.write_rows(OUT / "projected" / (d + ".jsonl"), safe_rows, check_projection)
            native.write_rows(OUT / "runtime" / (d + ".jsonl"), [e.to_dict() for e in examples], native.check_runtime)
            native.write_rows(OUT / "pools" / (d + ".jsonl"), pool_rows, native.check_pool)
            pre = sum(len(e.documents) for e in examples)
            result["datasets"][d] = dict(questions=len(examples), pre_dedup_documents=pre,
                documents=len(pool_rows), duplicates_removed=pre-len(pool_rows), corpus_fingerprint=corpus.fingerprint)
            print("POOL_BUILT", d, result["datasets"][d], flush=True)
        require(gate.denied == 0 and not boundary["blocked"], "Execution boundary event")
        for e in input_records:
            require(record(Path(e["path"])) == e, "Input changed during C1")
        require(not any(x in sys.modules for x in ("torch", "transformers", "sklearn", "numpy", "faiss")), "Model module imported")
        result.update(status="BUILT_PENDING_INDEPENDENT", projected_questions=6000,
            materialization_gate=gate.report(), sources_unchanged=True, read_paths=sorted(reads),
            write_paths=sorted(boundary["write_paths"]), scope="No retrieval, generation, scores, actions or outcomes")
    except Exception as exc:
        # No raw row or question values in diagnostics.
        result.update(error_type=type(exc).__name__, diagnostic=str(exc))
    result["elapsed_seconds"] = time.monotonic() - started
    write_json(OUT / "BUILD_RECEIPT.json", result)
    seal_execution(OUT)
    print(result["status"], flush=True)
    return 0 if result["status"] == "BUILT_PENDING_INDEPENDENT" else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
