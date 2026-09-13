"""Exhaustive, non-neural C3 repair-arithmetic observer for one BLAS mode.

This program is diagnostic only.  It never calls the original validator, never
loads an encoder or Gold data, and writes only into a new caller-supplied
directory.  Run it in two separate processes as frozen by the research contract.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
from typing import Any, Iterable


DATASETS = ("hotpotqa", "2wikimultihopqa", "musique")
RETRIEVERS = ("bm25", "dense", "hybrid")
HELPERS = {"bm25_scores", "rank_entries", "rrf", "validate_rank", "replacement"}
REPAIR_FIELDS = {"dataset", "retriever", "sample_id", "position", "query_sha256", "ranking",
    "component_rankings", "dense_query_vector", "e0_ids", "e1_ids", "inserted_document_id",
    "inserted_candidate_rank", "replaced_document_id", "replacement_position_zero_based",
    "requested_depth", "repair_retrieval_calls", "pool_sha256", "fail_closed_reason"}
EXPECTED_HELPER_ASTS = {
    "bm25_scores": "36675e616bc325d7a3572f151107615ed7e0a549cfc6d517cea9e761f47ae5b6",
    "rank_entries": "db176001b96d49a4fcd7fd2577456a2414d75720ee8afbb60c171cd90cd2fe1c",
    "rrf": "0c76abd9e31b1c26e3492d7214996407d8809d4d35e4d8a6efe59d9173e82205",
    "validate_rank": "558d6a73192c42e7e8ff54cd1adf3cebf01c6161b5bd444f34539626db907653",
    "replacement": "48e2dcbee6f9965a70b919b4fb432944ebe94b3cc63ca75a1ab8acaba4208096",
}


def require(value: Any, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(2 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def record(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "sha256": sha(path), "size_bytes": path.stat().st_size}


def ast_hash(node: ast.AST) -> str:
    return sha_bytes(ast.dump(node, annotate_fields=True, include_attributes=False).encode("utf-8"))


def load_helpers(path: Path, np: Any) -> tuple[dict[str, Any], dict[str, str]]:
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in HELPERS]
    require({node.name for node in nodes} == HELPERS, "exact original helper set")
    hashes = {node.name: ast_hash(node) for node in nodes}
    require(hashes == EXPECTED_HELPER_ASTS, "original helper AST hashes")
    scope = {"np": np, "re": re, "math": math, "require": require}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), scope)
    return {name: scope[name] for name in HELPERS}, hashes


def ordered_bits(value: float, bits: int) -> int:
    if bits == 32:
        raw = struct.unpack(">I", struct.pack(">f", value))[0]
        sign = 1 << 31
        return sign - raw if raw & sign else sign + raw
    raw = struct.unpack(">Q", struct.pack(">d", value))[0]
    sign = 1 << 63
    return sign - raw if raw & sign else sign + raw


def ulp_distance(left: float, right: float, bits: int) -> int:
    return abs(ordered_bits(left, bits) - ordered_bits(right, bits))


def compare_ranking(saved: list[dict[str, Any]], computed: list[dict[str, Any]], *,
                    kind: str, component: str | None, trace: dict[str, Any], pass_name: str,
                    ledger: Any, counters: collections.Counter) -> dict[str, Any]:
    require(len(saved) == len(computed), f"{kind} depth changed")
    exact = saved == computed
    ids_equal = [x["document_id"] for x in saved] == [x["document_id"] for x in computed]
    ranks_equal = [x["rank"] for x in saved] == [x["rank"] for x in computed]
    score_diffs = 0
    max_abs = 0.0
    max_ulp = 0
    bits = 32 if (component == "dense" and kind == "component") or (kind == "final_ranking" and trace["retriever"] == "dense") else 64
    for index, (old, new) in enumerate(zip(saved, computed)):
        if old != new:
            score_changed = old.get("score") != new.get("score")
            if score_changed:
                score_diffs += 1
                max_abs = max(max_abs, abs(float(old["score"]) - float(new["score"])))
                max_ulp = max(max_ulp, ulp_distance(float(old["score"]), float(new["score"]), bits))
            item = {"pass": pass_name, "dataset": trace["dataset"], "retriever": trace["retriever"],
                "sample_id": trace["sample_id"], "position": trace["position"], "kind": kind,
                "component": component, "index_zero_based": index, "saved": old, "computed": new,
                "document_id_changed": old.get("document_id") != new.get("document_id"),
                "rank_changed": old.get("rank") != new.get("rank"), "score_changed": score_changed,
                "absolute_score_difference": abs(float(old["score"]) - float(new["score"])) if score_changed else 0.0,
                "ulp_distance": ulp_distance(float(old["score"]), float(new["score"]), bits) if score_changed else 0,
                "score_format_bits": bits}
            ledger.write(canonical(item) + b"\n")
            counters[f"{kind}_ledger_entries"] += 1
    return {"exact": exact, "ordered_ids_equal": ids_equal, "ranks_equal": ranks_equal,
        "score_difference_count": score_diffs, "differing_entry_count": sum(a != b for a, b in zip(saved, computed)),
        "max_absolute_score_difference": max_abs, "max_ulp_distance": max_ulp}


def install_guard(project_root: Path, engineering_root: Path, output: Path, allowed: Iterable[Path]) -> dict[str, Any]:
    allowed_set = {Path(p).resolve() for p in allowed}
    receipt: dict[str, Any] = {"reads": set(), "writes": set(), "denied": []}
    def deny(reason: str) -> None:
        receipt["denied"].append(reason)
        raise RuntimeError("C3 census boundary: " + reason)
    def hook(event: str, args: tuple[Any, ...]) -> None:
        if event == "import" and (args[0] in {"torch", "transformers", "sklearn", "joblib", "src"} or
                                  args[0].startswith(("torch.", "transformers.", "sklearn.", "src."))):
            deny("forbidden package import " + args[0])
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request"}:
            deny(event)
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output):
                deny("write outside census output")
            receipt["writes"].add(str(path)); return
        if path.is_relative_to(project_root / "data/raw"):
            deny("raw benchmark read")
        if path.is_relative_to(project_root / "data/models"):
            deny("model asset read")
        if (path.is_relative_to(project_root) or path.is_relative_to(engineering_root)) and path not in allowed_set and not path.is_relative_to(output):
            deny("unlisted project read: " + str(path))
        receipt["reads"].add(str(path))
    sys.addaudithook(hook)
    return receipt


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_record(entry: dict[str, Any]) -> Path:
    path = Path(entry["path"])
    require(path.is_file() and not path.is_symlink(), "regular authenticated input: " + str(path))
    require(path.stat().st_size == entry["size_bytes"] and sha(path) == entry["sha256"], "input record changed: " + str(path))
    return path.resolve()


def verify_runtime(base: Path, manifest_sha: str) -> list[Path]:
    manifest_path = base / "EXECUTION_MANIFEST.json"
    require(sha(manifest_path) == manifest_sha, "runtime execution manifest")
    manifest = load_json(manifest_path)
    paths = [manifest_path.resolve()]
    for entry in manifest["files"]:
        path = base / entry["path"]
        require(record(path)["sha256"] == entry["sha256"] and path.stat().st_size == entry["size_bytes"], "runtime payload changed")
        paths.append(path.resolve())
    return paths


def verify_task_manifest(manifest_path: Path) -> list[Path]:
    manifest = load_json(manifest_path)
    paths = [manifest_path.resolve()]
    for entry in manifest["files"]:
        path = manifest_path.parent / entry["path"]
        require(path.is_file() and path.stat().st_size == entry["size_bytes"] and sha(path) == entry["sha256"],
                "sealed task payload changed: " + str(path))
        paths.append(path.resolve())
    return paths


def restore_state(dataset: str, index_root: Path, np: Any) -> dict[str, Any]:
    index = index_root / dataset
    structure = load_json(index / "bm25_structure.json")
    ids = structure["document_ids"]
    matrix = np.load(index / "document_embeddings.npy", allow_pickle=False)
    require(matrix.dtype == np.float32 and matrix.shape == (len(ids), 768), "frozen dense matrix schema")
    return {"ids": ids, "terms": {x["term"]: x for x in structure["terms"]},
        "lengths": np.asarray(structure["lengths"], dtype=np.float64),
        "average_length": structure["average_length"], "matrix": matrix}


def rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def expected_pool(config: dict[str, Any], pools: list[dict[str, Any]], mode: str) -> None:
    require(len(pools) == 1, "one NumPy BLAS pool")
    pool = pools[0]
    expected = config["blas"]
    require(pool["internal_api"] == "openblas" and pool["version"] == expected["version"] and
            pool["architecture"] == expected["architecture"] and pool["threading_layer"] == expected["threading_layer"],
            "pinned OpenBLAS identity")
    require(Path(pool["filepath"]).resolve() == Path(expected["filepath"]).resolve(), "pinned OpenBLAS DLL path")
    require(sha(Path(pool["filepath"])) == expected["sha256"], "pinned OpenBLAS DLL bytes")
    require(pool["num_threads"] == (1 if mode == "single" else 12), "required BLAS thread count")


def process_pass(pass_name: str, base: Path, traces: list[dict[str, Any]], state_root: Path,
                 np: Any, helper: dict[str, Any], observations: Any, discrepancies: Any,
                 counters: collections.Counter, strata: collections.Counter,
                 pool_sha256: dict[str, str]) -> None:
    repair_path = base / "repair_bindings.jsonl"
    generation_path = base / "generation_receipts.jsonl"
    state = None; current_dataset = None
    with repair_path.open("rb") as repair_stream, generation_path.open("rb") as generation_stream:
        for trace_number, trace in enumerate(traces):
            repair_line = repair_stream.readline(); require(repair_line, "missing repair row")
            repair = json.loads(repair_line)
            a0_line = generation_stream.readline(); query_line = generation_stream.readline(); a1_line = generation_stream.readline()
            require(a0_line and query_line and a1_line, "missing three generation rows")
            query_receipt = json.loads(query_line)
            key = (trace["dataset"], trace["retriever"], trace["sample_id"])
            require((repair["dataset"], repair["retriever"], repair["sample_id"]) == key, "repair trace alignment")
            require((query_receipt["dataset"], query_receipt["retriever"], query_receipt["sample_id"]) == key and
                    query_receipt["stage"] == "repair_query", "repair-query receipt alignment")
            require(set(repair) == REPAIR_FIELDS and repair["position"] == trace["position"] and
                    query_receipt["position"] == trace["position"], "repair schema/position")
            require(repair["pool_sha256"] == pool_sha256[trace["dataset"]], "original pool-hash binding")
            require(repair["e0_ids"] == trace["original_top5_ids"] and repair["requested_depth"] == 50 and
                    repair["repair_retrieval_calls"] == 1 and repair["replacement_position_zero_based"] == 4 and
                    repair["replaced_document_id"] == trace["original_top5_ids"][4] and repair["fail_closed_reason"] is None,
                    "stored repair controls")
            query = query_receipt["parsed_text"]
            require(type(query) is str and sha_bytes(query.encode("utf-8")) == repair["query_sha256"], "repair query hash")
            dataset, retriever, _ = key
            if dataset != current_dataset:
                state = restore_state(dataset, state_root, np); current_dataset = dataset
            valid = set(state["ids"]); depth = 100 if retriever == "hybrid" else 50
            components: dict[str, list[dict[str, Any]]] = {}
            score_hashes: dict[str, str] = {}
            component_results: dict[str, Any] = {}
            if retriever in {"bm25", "hybrid"}:
                score_vector = helper["bm25_scores"](query, state)
                require(score_vector.dtype == np.float64, "original BM25 float64")
                components["bm25"] = helper["rank_entries"](score_vector, state["ids"], depth)
                score_hashes["bm25"] = sha_bytes(score_vector.tobytes())
            if retriever in {"dense", "hybrid"}:
                raw_vector = repair["dense_query_vector"]
                require(type(raw_vector) is list and len(raw_vector) == 768 and all(type(v) is float for v in raw_vector), "saved dense vector schema")
                vector = np.asarray(raw_vector, dtype=np.float32)
                require(all(float(np.float32(v)) == v for v in raw_vector), "dense JSON scalars round-trip exactly to float32")
                score_vector = state["matrix"] @ vector
                require(score_vector.dtype == np.float32, "original dense float32 product")
                components["dense"] = helper["rank_entries"](score_vector, state["ids"], depth)
                score_hashes["dense"] = sha_bytes(score_vector.tobytes())
            else:
                require(repair["dense_query_vector"] is None, "BM25 dense vector must be null")
            require(set(repair["component_rankings"]) == set(components), "component key schema")
            for component, computed in components.items():
                helper["validate_rank"](repair["component_rankings"][component], valid, depth)
                component_results[component] = compare_ranking(repair["component_rankings"][component], computed,
                    kind="component", component=component, trace=trace, pass_name=pass_name,
                    ledger=discrepancies, counters=counters)
                counters["component_lists"] += 1; counters["component_entries"] += depth
            computed_ranking = helper["rrf"](components["bm25"], components["dense"]) if retriever == "hybrid" else components[retriever]
            helper["validate_rank"](repair["ranking"], valid, 50)
            ranking_result = compare_ranking(repair["ranking"], computed_ranking, kind="final_ranking", component=None,
                trace=trace, pass_name=pass_name, ledger=discrepancies, counters=counters)
            computed_e1, inserted = helper["replacement"](computed_ranking, trace["original_top5_ids"])
            replacement_fields = {"e1_ids": computed_e1, "inserted_document_id": inserted["document_id"],
                "inserted_candidate_rank": inserted["rank"], "replaced_document_id": trace["original_top5_ids"][4],
                "replacement_position_zero_based": 4, "requested_depth": 50, "repair_retrieval_calls": 1,
                "fail_closed_reason": None}
            replacement_equal = all(repair[name] == value for name, value in replacement_fields.items())
            if not replacement_equal:
                item = {"pass": pass_name, "dataset": dataset, "retriever": retriever, "sample_id": trace["sample_id"],
                    "position": trace["position"], "kind": "replacement", "saved": {k: repair[k] for k in replacement_fields},
                    "computed": replacement_fields}
                discrepancies.write(canonical(item) + b"\n"); counters["replacement_ledger_entries"] += 1
            component_exact = all(x["exact"] for x in component_results.values())
            if replacement_equal and ranking_result["exact"] and component_exact:
                classification = "exact"
            elif not replacement_equal:
                classification = "replacement_change"
            elif not ranking_result["ordered_ids_equal"]:
                classification = "final_ranking_membership_or_order"
            elif any(not x["ordered_ids_equal"] for x in component_results.values()):
                classification = "component_membership_or_order"
            else:
                classification = "score_only"
            counters["traces"] += 1; counters["final_rankings"] += 1; counters["replacements"] += 1
            counters["classification_" + classification] += 1; strata[(pass_name, dataset, retriever)] += 1
            vector_hash = None if repair["dense_query_vector"] is None else sha_bytes(np.asarray(repair["dense_query_vector"], dtype=np.float32).tobytes())
            observation = {"pass": pass_name, "dataset": dataset, "retriever": retriever, "sample_id": trace["sample_id"],
                "position": trace["position"], "trace_key_sha256": sha_bytes(canonical(list(key))),
                "repair_record_sha256": sha_bytes(repair_line), "repair_query_record_sha256": sha_bytes(query_line),
                "repair_query_sha256": repair["query_sha256"], "dense_query_vector_bytes_sha256": vector_hash,
                "recomputed_score_vector_sha256": score_hashes, "component_comparisons": component_results,
                "final_ranking_comparison": ranking_result, "replacement_equal": replacement_equal,
                "classification": classification}
            observations.write(canonical(observation) + b"\n")
            if counters["traces"] % 100 == 0:
                observations.flush(); discrepancies.flush()
                print(json.dumps({"mode_progress": counters["traces"], "of": 18180}), flush=True)
        require(not repair_stream.readline(), "extra repair rows")
        require(not generation_stream.readline(), "extra generation rows")


def manifest(directory: Path, names: list[str]) -> dict[str, Any]:
    return {"files": [{"path": name, "sha256": sha(directory / name), "size_bytes": (directory / name).stat().st_size} for name in names]}


def self_test() -> None:
    assert ulp_distance(0.5, struct.unpack(">f", struct.pack(">I", struct.unpack(">I", struct.pack(">f", 0.5))[0] + 2))[0], 32) == 2
    assert canonical({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--config-sha256")
    parser.add_argument("--mode", choices=("single", "default"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test(); print("PASS_C3_CENSUS_SELF_TEST"); return 0
    require(args.config and args.config_sha256 and args.mode and args.output, "complete arguments")
    config_path = args.config.resolve(); output = args.output.resolve()
    require(sha(config_path) == args.config_sha256, "frozen config bytes")
    config = load_json(config_path)
    require(not output.exists(), "single-use mode output")
    output.mkdir(parents=True)
    require(sys.flags.isolated and sys.dont_write_bytecode, "isolated no-bytecode interpreter")
    thread_values = {name: os.environ.get(name) for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")}
    require(thread_values == ({name: "1" for name in thread_values} if args.mode == "single" else {name: None for name in thread_values}), "exact thread environment")
    project_root = Path(config["project_root"]).resolve(); engineering_root = Path(config["engineering_root"]).resolve()
    runtime_root = Path(config["runtime_root"]).resolve(); preparation = Path(config["preparation_root"]).resolve()
    helper_path = Path(config["helper_source"]["path"]).resolve(); inventory_path = Path(config["environment_inventory"]["path"]).resolve()
    digest_source = verify_record(config["digest_source"])
    digest_spec = importlib.util.spec_from_file_location("authenticated_c3_digest", digest_source)
    require(digest_spec is not None and digest_spec.loader is not None, "authenticated digest loader")
    digest_module = importlib.util.module_from_spec(digest_spec); digest_spec.loader.exec_module(digest_module)
    opaque_digest = digest_module.digest
    authenticated = [verify_record(config["helper_source"]), verify_record(config["environment_inventory"]), digest_source,
        verify_record(config["failed_report"]), verify_record(config["contract"])]
    v2_manifest = verify_record(config["v2_failure_manifest"])
    v1_manifest = verify_record(config["v1_sibling_manifest"])
    authenticated.extend(verify_task_manifest(v2_manifest))
    authenticated.extend(verify_task_manifest(v1_manifest))
    preparation_manifest = verify_record(config["preparation_manifest"])
    authenticated.extend(verify_task_manifest(preparation_manifest))
    runtime_paths = verify_runtime(runtime_root, config["runtime_manifests"]["canonical"])
    runtime_paths += verify_runtime(runtime_root / "replay", config["runtime_manifests"]["replay"])
    expected_runtime_files = {str(path.resolve()) for path in runtime_paths} | {str(Path(config["failed_report"]["path"]).resolve())}
    require({str(path.resolve()) for path in runtime_root.rglob("*") if path.is_file()} == expected_runtime_files,
            "exact original runtime namespace including retained V2 failed report")
    traces_path = preparation / "TRACE_MANIFEST_PRIVATE.jsonl"; replay_path = preparation / "REPLAY_SUBSET_PRIVATE.jsonl"
    authenticated.extend([traces_path.resolve(), replay_path.resolve()]); authenticated.extend(runtime_paths)
    freeze_inputs = {entry["path"]: entry for entry in load_json(runtime_root / "EXECUTABLE_FREEZE.json")["inputs"]}
    index_root = Path(config["index_root"]).resolve()
    for dataset in DATASETS:
        for filename in ("bm25_structure.json", "document_embeddings.npy"):
            path = index_root / dataset / filename
            authenticated.append(verify_record(freeze_inputs[str(path)]))
    inventory = load_json(inventory_path)["files"]
    env_records = [entry for entry in inventory if Path(entry["path"]).is_relative_to(project_root / ".venv") and
                   any(part in entry["path"] for part in ("\\numpy\\", "\\numpy.libs\\", "\\threadpoolctl.py"))]
    require(len(env_records) == 1544, "exact NumPy/threadpool environment subset")
    for entry in env_records:
        path = Path(entry["path"]).resolve()
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == entry["size_bytes"] and
                opaque_digest(path) == entry["sha256"], "opaque environment input changed: " + str(path))
        authenticated.append(path)
    authenticated = sorted(set(authenticated))
    environment_paths = {str(Path(entry["path"]).resolve()): entry for entry in env_records}
    initial_records = {str(path): record(path) for path in authenticated if str(path) not in environment_paths}
    sys.path.insert(0, str(engineering_root))
    import numpy as np
    import threadpoolctl
    require(np.__version__ == "2.2.6", "pinned NumPy version")
    pools_start = threadpoolctl.threadpool_info(); expected_pool(config, pools_start, args.mode)
    guard = install_guard(project_root, engineering_root, output, authenticated + [config_path])
    helpers, helper_asts = load_helpers(helper_path, np)
    traces = rows(traces_path); replay = rows(replay_path)
    require(len(traces) == 18000 and [x["position"] for x in traces] == list(range(18000)), "canonical trace sequence")
    require(len(replay) == 180 and replay == [x for x in traces if (x["dataset"], x["retriever"], x["sample_id"]) in
            {(y["dataset"], y["retriever"], y["sample_id"]) for y in replay}], "fixed replay sequence")
    counters: collections.Counter = collections.Counter(); strata: collections.Counter = collections.Counter()
    observation_path = output / "OBSERVATIONS.jsonl"; discrepancy_path = output / "DISCREPANCIES.jsonl"
    result: dict[str, Any]
    try:
        with observation_path.open("xb") as observations, discrepancy_path.open("xb") as discrepancies:
            process_pass("canonical", runtime_root, traces, index_root, np, helpers, observations, discrepancies, counters, strata,
                         config["pool_sha256"])
            process_pass("replay", runtime_root / "replay", replay, index_root, np, helpers, observations, discrepancies, counters, strata,
                         config["pool_sha256"])
        require(counters["traces"] == 18180 and counters["component_lists"] == 24240 and
                counters["component_entries"] == 1818000 and counters["final_rankings"] == 18180 and
                counters["replacements"] == 18180, "complete required census totals")
        expected_strata = {(p, d, r): (2000 if p == "canonical" else 20) for p in ("canonical", "replay") for d in DATASETS for r in RETRIEVERS}
        require(dict(strata) == expected_strata, "exact census strata")
        pools_end = threadpoolctl.threadpool_info(); expected_pool(config, pools_end, args.mode)
        for path in authenticated:
            if str(path) in environment_paths:
                entry = environment_paths[str(path)]
                require(path.stat().st_size == entry["size_bytes"] and opaque_digest(path) == entry["sha256"],
                        "opaque environment input changed during census: " + str(path))
            else:
                require(record(path) == initial_records[str(path)], "authenticated input changed during census: " + str(path))
        require(not guard["denied"], "empty denied-access ledger")
        result = {"status": "COMPLETE_DIAGNOSTIC_CENSUS_MODE", "cas_q2_status": "NOT READY", "mode": args.mode,
            "thread_environment": thread_values, "numpy_version": np.__version__, "threadpools_start": pools_start,
            "threadpools_end": pools_end, "original_helper_ast_sha256": helper_asts,
            "counts": dict(counters), "stratum_counts": {"|".join(k): v for k, v in sorted(strata.items())},
            "numpy_and_threadpool_input_files_verified_before_and_after": len(env_records),
            "execution_boundary": {"reads": sorted(guard["reads"]), "writes": sorted(guard["writes"]), "denied": guard["denied"]},
            "neural_forwards": 0, "scientific_fits": 0, "fresh_gold_values_materialized": 0,
            "original_validator_invocations": 0, "a0_a1_json_decodes": 0}
    except Exception as exc:
        result = {"status": "FAIL_PRESERVED_CENSUS_MODE", "cas_q2_status": "NOT READY", "mode": args.mode,
            "error_type": type(exc).__name__, "diagnostic": str(exc), "counts_before_failure": dict(counters),
            "neural_forwards": 0, "scientific_fits": 0, "fresh_gold_values_materialized": 0,
            "original_validator_invocations": 0, "a0_a1_json_decodes": 0}
    write_json(output / "RESULT.json", result)
    write_json(output / "SHA256_MANIFEST.json", manifest(output, ["OBSERVATIONS.jsonl", "DISCREPANCIES.jsonl", "RESULT.json"]))
    print(json.dumps({"status": result["status"], "mode": args.mode, "counts": result.get("counts", result.get("counts_before_failure"))}), flush=True)
    return 0 if result["status"] == "COMPLETE_DIAGNOSTIC_CENSUS_MODE" else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    try:
        raise SystemExit(main())
    except Exception as exc:
        output = None
        if "--output" in sys.argv:
            output = Path(sys.argv[sys.argv.index("--output") + 1]).resolve()
            output.mkdir(parents=True, exist_ok=True)
            report = output / "RESULT.json"
            if not report.exists():
                write_json(report, {"status": "FAIL_PRESERVED_CENSUS_MODE", "cas_q2_status": "NOT READY",
                    "error_type": type(exc).__name__, "diagnostic": str(exc), "neural_forwards": 0,
                    "scientific_fits": 0, "fresh_gold_values_materialized": 0,
                    "original_validator_invocations": 0, "a0_a1_json_decodes": 0})
        print(json.dumps({"status": "FAIL_PRESERVED_CENSUS_MODE", "error_type": type(exc).__name__,
                          "diagnostic": str(exc), "output": str(output) if output else None}), flush=True)
        raise SystemExit(2)
