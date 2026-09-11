"""Authenticated original selected-reference readers and unchanged answer metrics.

Only explicit functions are assembled. No old controller/main or Gold read runs
on import. Actual source reading requires a separate accepted-prelabel process.
"""
import ast
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import string
import types
from collections.abc import Sequence

from scripts.empirical_pool_io import checked, load, record, require
from scripts.verify_roa_artifacts import safe_file, relative_path

FINAL_SHA = "6a13d70133669c56d2a0c03829ea55267f4bc87108f767e6f80c4b6c1170512a"
METRIC_SHA = "d6de10b0d44bf32c5aa3727c4d2b4b3dc2556b3e4f791cc1fc4f08ad957dd182"
PARSER_SHA = "4ecb9dad8bf88a80b99dfb97df4bc36de4bfa95feb3a9d5645e850fa08362472"


def authenticate(root):
    """Metadata and opaque file hashes only; does not deserialize source datasets."""
    paths = []
    def check(path, sha, size=None):
        actual = checked(path, sha, size)
        paths.append(actual)
        return actual
    def old(entry):
        return check(safe_file(root, relative_path(entry["path"])), entry["sha256"], entry["size_bytes"])
    parent = root / "outputs/daa_v2_fresh_v1/final_evaluation"
    manifest = check(parent / "SHA256_MANIFEST.json", FINAL_SHA)
    entries = load(manifest)["files"]
    require(len(entries) == len({e["path"].casefold() for e in entries}) == 55, "Original outcome namespace manifest uniqueness")
    byname = {e["path"]: e for e in entries}
    def parent_file(name):
        relative = (parent / name).relative_to(root).as_posix()
        return old(byname[relative])
    spec = load(parent_file("preflight/MAPPING_INPUT_SPEC.json"))
    pre = load(parent_file("preflight/PRE_GOLD_AUTHENTICATION.json"))
    parent_file("selected_gold.py")
    require(spec["status"] == "PASS" and spec["pre_gold_authentication"]["sha256"] == record(parent / "preflight/PRE_GOLD_AUTHENTICATION.json")["sha256"], "Original method-blind outcome input specification")
    require(set(spec["sources"]) == {"hotpotqa", "2wikimultihopqa", "musique"}, "Original three reference sources")
    for entry in spec["metric_files"]:
        old(entry)
    check(root / "src/evaluation/answers.py", METRIC_SHA)
    check(root / "src/phase10/source_projection_v2r1.py", PARSER_SHA)
    for entry in spec["sources"].values():
        old(entry)
    arrow = load(old(pre["arrow_environment_control"]))
    package = root / "tmp/daa_v2_hotpot_full_column_reader"
    package_paths = set()
    for entry in arrow["files"]:
        path = Path(entry["path"]).resolve()
        require(path.is_relative_to(package) and path not in package_paths, "Original Arrow package input identity")
        package_paths.add(path)
        check(path, entry["sha256"], entry["size_bytes"])
    require(arrow["exit_code"] == arrow["import_verification"]["exit_code"] == 0 and
        arrow["import_verification"]["stdout"].strip() == pre["environment"]["pyarrow"] == "20.0.0", "Authenticated original Arrow version")
    old(pre["environment"]["executable"])
    return spec, pre, sorted(set(paths)), len(package_paths)


def definitions(path, names, values):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    require({n.name for n in nodes} == set(names), "Exact original outcome AST selection")
    module = types.ModuleType("authenticated_outcome_definitions")
    module.__dict__.update(values)
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[])), str(path), "exec"), module.__dict__)
    hashes = {n.name: hashlib.sha256(ast.dump(n, include_attributes=False).encode()).hexdigest() for n in nodes}
    return module, hashes


def native(root, spec):
    metric, hashes = definitions(root / "src/evaluation/answers.py",
        ("normalize_answer", "_answers", "exact_match", "_single_f1", "token_f1"),
        dict(re=re, string=string, Counter=Counter, Sequence=Sequence, _SPECIAL_ANSWERS={"yes", "no", "noanswer"}))
    require(hashes == spec["metric_ast_hashes"], "Original historical metric AST identities")
    parser, parser_hashes = definitions(root / "src/phase10/source_projection_v2r1.py", ("_JSONByteCursor",),
        dict(json=json, Phase10FailClosed=RuntimeError))
    readers, reader_hashes = definitions(root / "outputs/daa_v2_fresh_v1/final_evaluation/selected_gold.py",
        ("read_object", "json_references", "parquet_references"), dict(require=require, io=io, json=json, Path=Path))
    return metric, parser._JSONByteCursor, readers, dict(metrics=hashes, parser=parser_hashes, readers=reader_hashes)


def canonical_answer_rows(path, Cursor):
    """Materialize identities and a0/a1 only; skip question and passage strings."""
    allowed = {"dataset", "retriever", "sample_id", "a0", "a1"}
    schema = allowed | {"question", "evidence0", "evidence1"}
    with path.open("rb") as stream:
        cursor = Cursor(stream)
        while True:
            cursor.skip_whitespace()
            if cursor.peek() is None:
                return
            cursor.expect(ord("{"), path="branch")
            seen, row = set(), {}
            while True:
                cursor.skip_whitespace()
                field = cursor.read_string(path="branch_key")
                require(field in schema and field not in seen, "Exact unique canonical branch fields")
                seen.add(field)
                cursor.expect(ord(":"), path="branch_value")
                if field in allowed:
                    row[field] = cursor.read_string(path="bound_answer_or_identity")
                else:
                    cursor.skip_value(path="unneeded_runtime_text")
                cursor.skip_whitespace()
                if cursor.peek() == ord("}"):
                    cursor.take()
                    break
                cursor.expect(ord(","), path="branch_separator")
            require(seen == schema, "Complete eight-field canonical source row")
            require(all(row[k] for k in ("dataset", "retriever", "sample_id")), "Nonempty canonical answer identities")
            yield row


def selected_references(root, spec, selected, Cursor, readers, parquet):
    """Only the cohort size/path orchestration changes from original readers."""
    require(len(selected) == 6000, "Exactly 6000 prelabel-sealed reference IDs")
    references, counters = {}, {}
    for dataset in sorted(spec["sources"]):
        source = spec["sources"][dataset]
        wanted = {sid for ds, sid in selected if ds == dataset}
        require(len(wanted) == 2000, "Exact balanced selected reference population")
        path = checked(safe_file(root, relative_path(source["path"])), source["sha256"], source["size_bytes"])
        if source["format"] == "parquet":
            values, receipt = readers.parquet_references(path, wanted, parquet)
        else:
            require(source["format"] in {"json", "jsonl"}, "Original reference serialization")
            values, receipt = readers.json_references(lambda: path.open("rb"), wanted, id_field=source["id_field"],
                json_lines=source["format"] == "jsonl", aliases=source["aliases"], Cursor=Cursor)
        require(receipt["source_rows"] == source["row_count"] and len(values) == 2000 and set(values) == wanted, "Complete selected source reference count")
        checked(path, source["sha256"], source["size_bytes"])
        references.update({(dataset, sid): values[sid] for sid in values})
        counters[dataset] = receipt
    require(set(references) == set(selected), "Exact prelabel reference identities")
    return references, counters
