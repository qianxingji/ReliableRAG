"""Authenticate a declared static file graph; scientific payloads stay opaque."""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import sys
import traceback

FREEZES = {"EXECUTABLE_FREEZE.json", "EXECUTABLE_PREFLIGHT_FREEZE.json", "PRESELECTION_FREEZE.json",
           "PROTOCOL_FREEZE.json", "TRACE_PREPARATION_FREEZE.json", "CPU_TEST_FREEZE.json"}
AUDITS = {"ACQUISITION_INPUT_AUDIT.json", "SCORING_INPUT_AUDIT.json", "OUTCOME_INPUT_AUDIT.json"}
NATIVE = {"RUNTIME_CONFIG_FREEZE.json", "PREFLIGHT_INPUT_VERIFICATION.json", "ACCEPTED_IMPLEMENTATION_PROVENANCE.json", "COHORT_FREEZE.json"}


def safe_relative(value):
    assert isinstance(value, str) and value
    parts = re.split(r"[/\\]", value)
    assert all(p and p not in {".", ".."} and ":" not in p and p == p.rstrip(" .") and not PureWindowsPath(p).is_reserved() for p in parts)
    return parts


def full_path(value, base):
    assert isinstance(value, str)
    if re.match(r"^[A-Za-z]:[/\\]", value):
        safe_relative(value[3:]); return Path(value).absolute()
    return base.joinpath(*safe_relative(value)).absolute()


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for b in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2); stream.write("\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task-root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--source-commit", required=True)
    a = p.parse_args()
    roots = dict(original=Path("E:/paper/ReliableRAG"), engineering=Path(__file__).resolve().parents[1], task=a.task_root.resolve())
    out = a.output.resolve(); assert not out.exists()
    assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
    seeds_path = roots["engineering"] / "docs/cas_q2/STATIC_DELIVERY_SEEDS.json"
    contract = roots["engineering"] / "docs/cas_q2/STATIC_DELIVERY_CLOSURE_CONTRACT.md"
    asset_lock = roots["engineering"] / "docs/cas_q2/PRETRAINED_ASSET_LOCK.json"
    assert sha(asset_lock) == "53fc72dd7e85dfd6dab703531cdf2599b029e2adec8430610c688ab8a4a1a12c"
    external = json.loads(asset_lock.read_text(encoding="utf-8"))
    seeds = json.loads(seeds_path.read_text(encoding="utf-8"))["seeds"]
    out.mkdir(exist_ok=False)
    control_paths = [Path(__file__).resolve(), seeds_path, contract, asset_lock]
    controls = [dict(path=str(p), sha256=sha(p), size_bytes=p.stat().st_size) for p in control_paths]
    write(out / "AUDIT_FREEZE.json", dict(source_commit=a.source_commit, inputs=controls, seeds=seeds, roots={k: str(v) for k, v in roots.items()},
                                        scope="Authenticated declared static metadata only; no live ledgers or scientific payload decoding"))
    nodes, edges, queue, issues, metadata, namespace_checks = {}, [], collections.deque(), [], [], []
    allowed = set(control_paths); libraries = (Path(sys.base_prefix).resolve(), Path(os.environ["SystemRoot"]).resolve())
    blocked = []; opened = set(); active = roots["engineering"] / "outputs/cas_q2/empirical_runtime_v1"

    def audit(event, args):
        if event == "import" and args[0].split(".")[0] in {"numpy", "torch", "transformers", "sklearn", "datasets", "pyarrow", "safetensors", "sentencepiece", "joblib", "pickle", "_pickle"}:
            blocked.append(dict(event=event, module=args[0])); raise RuntimeError("SCIENTIFIC_IMPORT_FORBIDDEN")
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "socket.sendto", "subprocess.Popen", "os.system", "urllib.Request"}:
            blocked.append(dict(event=event)); raise RuntimeError("NETWORK_OR_PROCESS_FORBIDDEN")
        if event == "open" and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if (writing and not path.is_relative_to(out)) or (not writing and path not in allowed and not path.is_relative_to(out) and not any(path.is_relative_to(r) for r in libraries)):
                blocked.append(dict(event=event, path=str(path), writing=bool(writing))); raise RuntimeError("UNDECLARED_FILE_ACCESS")
            opened.add(str(path))
        if event in {"os.remove", "os.rmdir", "os.mkdir", "os.rename", "os.replace", "os.truncate", "os.symlink", "os.link"}:
            for v in args[:2] if event in {"os.rename", "os.replace", "os.symlink", "os.link"} else args[:1]:
                if isinstance(v, (str, bytes, os.PathLike)) and not Path(os.fsdecode(v)).resolve().is_relative_to(out):
                    blocked.append(dict(event=event, path=os.fsdecode(v))); raise RuntimeError("ORIGINAL_MUTATION_FORBIDDEN")
    sys.addaudithook(audit)

    def add(entry, base, parent, selector):
        try:
            assert isinstance(entry, dict) and "path" in entry and re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
            path = full_path(entry["path"], base)
            owners = [k for k, v in roots.items() if path.is_relative_to(v)]; assert len(owners) == 1, "UNRECOGNIZED_LOGICAL_ROOT"
            assert not path.is_relative_to(active) or path.name == "EXECUTABLE_FREEZE.json", "LIVE_C3_PAYLOAD_EXCLUDED"
            size = entry.get("size_bytes"); assert size is None or type(size) is int and size >= 0
            key = str(path).casefold()
            edge = dict(parent=parent, selector=selector, child=key, declared_path=entry["path"], sha256=entry["sha256"], size_bytes=size, relative_base=str(base))
            edges.append(edge)
            if key in nodes:
                row = nodes[key]
                if (row["sha256"] != entry["sha256"]
                        or size is not None and row["declared_size_bytes"] is not None and row["declared_size_bytes"] != size
                        or size is not None and row.get("size_bytes") is not None and row["size_bytes"] != size):
                    issues.append(dict(kind="CONFLICTING_DECLARATIONS", path=str(path), previous=dict(row), incoming=edge))
                elif row["declared_size_bytes"] is None and size is not None:
                    row["declared_size_bytes"] = size
                return key
            role = owners[0]
            nodes[key] = dict(root=role, relative_path=path.relative_to(roots[role]).as_posix(), logical_path=str(path), sha256=entry["sha256"],
                              declared_size_bytes=size, status="PENDING", metadata_schema=None)
            allowed.add(path.resolve()); queue.append(key); return key
        except Exception as exc:
            issues.append(dict(kind="UNRESOLVED_RECORD", parent=parent, selector=selector, entry=entry, error=repr(exc)))
            return None

    def records(value, base, parent, selector):
        if value is None: return
        if isinstance(value, list):
            for i, e in enumerate(value): add(e, base, parent, f"{selector}/{i}")
        elif isinstance(value, dict) and "path" in value:
            add(value, base, parent, selector)
        elif isinstance(value, dict):
            for name, e in value.items(): add(e, base, parent, f"{selector}/{name}")
        else: issues.append(dict(kind="UNSUPPORTED_RECORD_CONTAINER", parent=parent, selector=selector, value_type=type(value).__name__))

    result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=a.source_commit,
                  started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), scientific_fits=0, model_loads=0, neural_forwards=0, fresh_gold_values_decoded=0)
    try:
        for i, seed in enumerate(seeds): add(seed, roots[seed["root"]], "SEEDS", str(i))
        visited = 0
        while queue:
            key = queue.popleft(); row = nodes[key]; path = Path(row["logical_path"])
            try:
                assert path.is_file(), "MISSING_STATIC_FILE"
                for part in (path, *path.parents):
                    info = part.lstat(); assert not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400, "REPARSE_POINT"
                size = path.stat().st_size; observed = sha(path)
                assert observed == row["sha256"], "STATIC_DIGEST_MISMATCH"
                assert row["declared_size_bytes"] is None or size == row["declared_size_bytes"], "STATIC_SIZE_MISMATCH"
                row.update(status="PASS_BYTES", size_bytes=size)
                name = path.name; owner_root = roots[row["root"]]
                is_metadata = name in FREEZES | AUDITS | NATIVE | {"SHA256_MANIFEST.json", "EXECUTION_MANIFEST.json", "UPSTREAM_PROVENANCE.json"}
                if is_metadata:
                    assert row["relative_path"].startswith("outputs/"), "METADATA_SCHEMA_OUTSIDE_DECLARED_OUTPUTS"
                    obj = json.loads(path.read_text(encoding="utf-8-sig")); assert isinstance(obj, dict)
                    row["metadata_schema"] = name; metadata.append(dict(path=str(path), sha256=observed, schema=name))
                    if name in {"SHA256_MANIFEST.json", "EXECUTION_MANIFEST.json"}:
                        base = roots["original"] if row["root"] == "original" else path.parent
                        values = obj.get("files"); assert isinstance(values, list), "MANIFEST_FILE_LIST_SCHEMA"
                        records(values, base, key, "files")
                        declared = {full_path(e["path"], base) for e in values}
                        assert len(declared) == len(values), "DUPLICATE_NAMESPACE_MEMBER"
                        if name == "SHA256_MANIFEST.json" and all(p.is_relative_to(path.parent) for p in declared):
                            actual = {p.absolute() for p in path.parent.rglob("*") if p.is_file() or p.is_symlink()}
                            ok = actual == declared | {path}
                            namespace_checks.append(dict(manifest=str(path), exact_fileset=ok, declared_files=len(declared), actual_files=len(actual),
                                                         unexpected=[str(x) for x in sorted(actual - declared - {path})], missing=[str(x) for x in sorted(declared - actual)]))
                            assert ok, "SEALED_NAMESPACE_FILESET_MISMATCH"
                    elif name in FREEZES:
                        for field in ("inputs", "input_files", "source_files"):
                            records(obj.get(field), owner_root, key, field)
                        if name == "PROTOCOL_FREEZE.json": records(obj.get("files"), owner_root, key, "files")
                        if isinstance(obj.get("executable"), dict): records(obj["executable"], owner_root, key, "executable")
                        if path.parent == active:
                            assert obj["mode"] == "canonical" and obj["expected_traces"] == 18000 and obj["source_commit"].startswith("cc304ee")
                            assert obj["preparation_manifest_sha256"] == "7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258"
                            assert obj["gpu_manifest_sha256"] == "050efac3a47c4c5cc8a9ffb82284dc8a60b8b480cf4561e6aa8788db504ab5f8"
                    elif name in AUDITS:
                        records(obj.get("checked_files"), owner_root, key, "checked_files")
                    elif name == "UPSTREAM_PROVENANCE.json":
                        assert path == roots["task"] / "outputs/p0_1_upstream_v2/UPSTREAM_PROVENANCE.json"
                        for i, value in enumerate(obj["manifests"]): records(value["manifest"], roots["original"], key, f"manifests/{i}/manifest")
                    elif name == "RUNTIME_CONFIG_FREEZE.json":
                        for field in ("accepted_sources", "preflight_sources"): records(obj.get(field), owner_root, key, field)
                    elif name == "PREFLIGHT_INPUT_VERIFICATION.json":
                        for field in ("accepted_source_files", "source_byte_inputs"): records(obj.get(field), owner_root, key, field)
                        records(obj.get("historical_source_authentication", {}).get("sources"), owner_root, key, "historical_source_authentication/sources")
                    elif name == "ACCEPTED_IMPLEMENTATION_PROVENANCE.json":
                        for field in ("sources", "evidence_controls"): records(obj.get(field), owner_root, key, field)
                    elif name == "COHORT_FREEZE.json":
                        for field in ("source_id_ledgers", "selected_id_ledger"): records(obj.get(field), owner_root, key, field)
            except Exception as exc:
                row["status"] = "FAIL"; issues.append(dict(kind="NODE_AUTHENTICATION_OR_SCHEMA_FAILURE", path=str(path), error=repr(exc)))
            visited += 1
            if visited % 2000 == 0: print("STATIC_FILES_AUTHENTICATED", visited, "discovered", len(nodes), flush=True)
        external_rows = {e["path"]: e for e in external["files"]}
        external_used = set()
        for key, row in nodes.items():
            row["delivery_route"] = "new_static_package"
            if row["root"] == "original" and row["relative_path"] in external_rows:
                e = external_rows[row["relative_path"]]
                assert row["sha256"] == e["sha256"] and row.get("size_bytes") == e["size_bytes"]
                row["delivery_route"] = "accepted_pretrained_archive"; external_used.add(row["relative_path"])
        assert len(external_used) == 22
        for row in nodes.values():
            if row["status"] == "PASS_BYTES":
                p = Path(row["logical_path"]); assert sha(p) == row["sha256"] and p.stat().st_size == row["size_bytes"], "POST_AUDIT_INPUT_CHANGE"
        for e in controls: assert sha(Path(e["path"])) == e["sha256"]
        assert not blocked
        result.update(status="PASS_DECLARED_STATIC_GRAPH_ONLY" if not issues else "FAIL_DECLARED_STATIC_GRAPH_ISSUES",
                      nodes=len(nodes), edges=len(edges), decoded_metadata_files=len(metadata), opaque_files=sum(r["metadata_schema"] is None for r in nodes.values()),
                      bytes=sum(r.get("size_bytes", 0) for r in nodes.values()), issue_count=len(issues), namespace_checks=len(namespace_checks),
                      external_pretrained_files=22, external_pretrained_bytes=sum(e["size_bytes"] for e in external_rows.values()),
                      remaining_package_files=sum(r["delivery_route"] == "new_static_package" for r in nodes.values()),
                      remaining_package_bytes=sum(r.get("size_bytes", 0) for r in nodes.values() if r["delivery_route"] == "new_static_package"),
                      metadata_schema_counts=dict(collections.Counter(r["schema"] for r in metadata)),
                      full_pipeline_closure=False, static_launch_freeze_only=True, live_c3_ledgers_opened=False,
                      pending_stages=["C3 canonical completion, 180-trace replay and independent seal", "Actual C4/prelabel", "Cost and D outcomes/analysis", "Complete relocated execution"])
    except Exception as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc(), failed_outputs_retained=True)
    write(out / "NODES_PRIVATE.json", dict(roots={k: str(v) for k, v in roots.items()}, files=[nodes[k] for k in sorted(nodes)]))
    write(out / "EDGES_PRIVATE.json", dict(edges=edges)); write(out / "ISSUES.json", dict(issues=issues))
    write(out / "METADATA_DECODE_AUDIT.json", dict(decoded_metadata=metadata, opaque_payload_decode_calls=0))
    write(out / "NAMESPACE_CHECKS.json", dict(checks=namespace_checks))
    result.update(blocked_events=blocked, opened_paths_count=len(opened), finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write(out / "RESULT.json", result)
    manifest = out / ("SHA256_MANIFEST.json" if result["status"] == "PASS_DECLARED_STATIC_GRAPH_ONLY" else "FAILURE_MANIFEST.json")
    write(manifest, dict(files=[dict(path=p.name, sha256=sha(p), size_bytes=p.stat().st_size) for p in sorted(out.iterdir()) if p.is_file()]))
    print(json.dumps(result, indent=2)); print("MANIFEST_SHA256", sha(manifest))
    return 0 if result["status"] == "PASS_DECLARED_STATIC_GRAPH_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
