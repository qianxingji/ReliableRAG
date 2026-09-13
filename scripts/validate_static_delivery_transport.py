"""Independently restore an authenticated static graph; all payloads are opaque."""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import stat
import sys
import traceback
import zipfile

GRAPH_PIN = "aa5c3da7ed764405e92602b64303984931a798abf2aee3e64c5d56ae34e892ea"
ASSET_PIN = "741b30828503c481cbdc712295c9ab12f52a1c3de183c17bc572a11436762fa9"
LOCK_PIN = "53fc72dd7e85dfd6dab703531cdf2599b029e2adec8430610c688ab8a4a1a12c"
ROLES = {"original", "engineering", "task"}


def safe_parts(name):
    assert isinstance(name, str) and name and "\\" not in name and ":" not in name
    parts = name.split("/")
    assert all(p and p not in {".", ".."} and p == p.rstrip(" .")
               and not PureWindowsPath(p).is_reserved() for p in parts), "UNSAFE_PATH"
    return parts


def digest(stream):
    h, size = hashlib.sha256(), 0
    for block in iter(lambda: stream.read(2 * 1024 * 1024), b""):
        h.update(block); size += len(block)
    return h.hexdigest(), size


def file_digest(path):
    with path.open("rb") as stream:
        return digest(stream)


def no_links(path):
    for p in (path, *path.parents):
        if p.exists() or p.is_symlink():
            s = p.lstat()
            assert not stat.S_ISLNK(s.st_mode) and not getattr(s, "st_file_attributes", 0) & 0x400, "REPARSE_PATH"
            if p.is_file():
                assert s.st_nlink == 1, "HARDLINK_FILE"


def checked_zip(z):
    rows = z.infolist(); names = [i.filename for i in rows]
    assert len(names) == len({n.casefold() for n in names}), "ARCHIVE_ALIAS"
    for i in rows:
        safe_parts(i.filename)
        assert not i.is_dir() and not i.flag_bits & 1
        assert stat.S_IFMT(i.external_attr >> 16) in {0, stat.S_IFREG}
    return set(names)


def restore(z, member, destination, wanted):
    info = z.getinfo(member); assert info.file_size == wanted[1]
    destination.parent.mkdir(parents=True, exist_ok=True); no_links(destination)
    h, size = hashlib.sha256(), 0
    with z.open(info) as source, destination.open("xb") as target:
        for block in iter(lambda: source.read(2 * 1024 * 1024), b""):
            target.write(block); h.update(block); size += len(block)
    assert (h.hexdigest(), size) == wanted, "EXTRACTION_DIGEST_MISMATCH"


def main():
    p = argparse.ArgumentParser()
    for option in ("archive", "asset-archive", "freeze", "destination", "receipt"):
        p.add_argument("--" + option, required=True, type=Path)
    p.add_argument("--archive-sha256", required=True)
    p.add_argument("--freeze-sha256", required=True)
    a = p.parse_args()
    assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
    for path in (a.archive, a.asset_archive, a.freeze, a.destination, a.receipt):
        assert path.is_absolute(); no_links(path)
    assert not a.destination.exists() and not a.receipt.exists()
    assert file_digest(a.freeze)[0] == a.freeze_sha256
    freeze = json.loads(a.freeze.read_text(encoding="utf-8"))
    this = Path(__file__).resolve()
    support = {e["archive_path"]: (e["sha256"], e["size_bytes"]) for e in freeze["support_files"]}
    assert len(support) == len(freeze["support_files"])
    assert file_digest(this) == support["control/validator.py"]
    assert freeze["graph_manifest_sha256"] == GRAPH_PIN and freeze["asset_archive_sha256"] == ASSET_PIN
    assert freeze["asset_lock_sha256"] == LOCK_PIN
    libraries = [Path(sys.base_prefix).resolve(), Path(os.environ["SystemRoot"]).resolve()]
    named = {this, a.archive.resolve(), a.asset_archive.resolve(), a.freeze.resolve()}
    blocked, opened = [], set()

    def guard(event, args):
        if event == "import" and args[0].split(".")[0] in {"numpy", "scipy", "torch", "transformers", "sklearn", "datasets", "pyarrow", "safetensors", "sentencepiece", "joblib", "pickle", "_pickle"}:
            blocked.append(dict(event=event, module=args[0])); raise RuntimeError("SCIENTIFIC_IMPORT_FORBIDDEN")
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "socket.gethostbyname", "socket.sendto", "subprocess.Popen", "os.system", "urllib.Request"}:
            blocked.append(dict(event=event)); raise RuntimeError("NETWORK_OR_PROCESS_FORBIDDEN")
        if event == "open" and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            permitted = (path == a.receipt or path.is_relative_to(a.destination)) if writing else (path in named or path.is_relative_to(a.destination) or any(path.is_relative_to(r) for r in libraries))
            if not permitted:
                blocked.append(dict(event=event, path=str(path), writing=bool(writing))); raise RuntimeError("UNDECLARED_FILE_ACCESS")
            opened.add(str(path))
        if event in {"os.remove", "os.rmdir", "os.mkdir", "os.rename", "os.replace", "os.truncate", "os.symlink", "os.link"}:
            for v in args[:2] if event in {"os.rename", "os.replace", "os.symlink", "os.link"} else args[:1]:
                if isinstance(v, (str, bytes, os.PathLike)) and not Path(os.fsdecode(v)).resolve().is_relative_to(a.destination):
                    blocked.append(dict(event=event, path=os.fsdecode(v))); raise RuntimeError("OUTSIDE_RESTORATION_MUTATION")
    sys.addaudithook(guard)
    result = dict(status="FAIL", started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  scientific_fits=0, model_loads=0, neural_forwards=0, fresh_gold_values_decoded=0,
                  payload_json_decodes=0, original_project_content_reads=0, full_pipeline_replay=False)
    try:
        assert file_digest(a.archive)[0] == a.archive_sha256
        assert file_digest(a.asset_archive)[0] == ASSET_PIN
        with zipfile.ZipFile(a.archive) as z, zipfile.ZipFile(a.asset_archive) as assets:
            names = checked_zip(z); asset_names = checked_zip(assets)
            assert len(asset_names) == 30
            for name, wanted in support.items():
                safe_parts(name)
                assert name.startswith(("audit/", "control/")) and z.getinfo(name).file_size == wanted[1]
                with z.open(name) as stream:
                    assert digest(stream) == wanted, "SUPPORT_DIGEST_MISMATCH"
            def metadata(name):
                assert name in support
                return json.loads(z.read(name))
            assert support["audit/SHA256_MANIFEST.json"][0] == GRAPH_PIN
            manifest = metadata("audit/SHA256_MANIFEST.json")
            expected_audit = {"audit/SHA256_MANIFEST.json"}
            for e in manifest["files"]:
                assert len(safe_parts(e["path"])) == 1
                key = "audit/" + e["path"]; expected_audit.add(key)
                assert support[key] == (e["sha256"], e["size_bytes"])
            assert expected_audit == {k for k in support if k.startswith("audit/")}
            assert len(expected_audit) == 8
            graph = metadata("audit/NODES_PRIVATE.json"); audit_freeze = metadata("audit/AUDIT_FREEZE.json")
            audit_result = metadata("audit/RESULT.json")
            assert audit_result["status"] == "PASS_DECLARED_STATIC_GRAPH_ONLY" and audit_result["issue_count"] == 0
            assert metadata("audit/ISSUES.json") == {"issues": []}
            checks = metadata("audit/NAMESPACE_CHECKS.json")["checks"]
            assert len(checks) == 36 and all(e["exact_fileset"] and not e["unexpected"] and not e["missing"] for e in checks)
            assert graph["roots"] == audit_freeze["roots"] and set(graph["roots"]) == ROLES
            control_mapping = {"audit_static_delivery_closure.py": "control/auditor.py",
                               "STATIC_DELIVERY_SEEDS.json": "control/seeds.json",
                               "STATIC_DELIVERY_CLOSURE_CONTRACT.md": "control/closure_contract.md",
                               "PRETRAINED_ASSET_LOCK.json": "control/asset_lock.json"}
            assert len(audit_freeze["inputs"]) == 4
            for e in audit_freeze["inputs"]:
                assert support[control_mapping[PureWindowsPath(e["path"]).name]] == (e["sha256"], e["size_bytes"])
            assert audit_freeze["seeds"] == metadata("control/seeds.json")["seeds"]
            assert support["control/asset_lock.json"][0] == LOCK_PIN
            lock = metadata("control/asset_lock.json")
            assert hashlib.sha256(assets.read("ASSET_LOCK.json")).hexdigest() == LOCK_PIN
            external = {e["path"]: e for e in lock["files"]}; assert len(external) == 22
            nodes, by_key, internal, routed = graph["files"], {}, {}, {}
            for e in nodes:
                assert e["root"] in ROLES and e["status"] == "PASS_BYTES"
                safe_parts(e["relative_path"])
                logical = str(PureWindowsPath(graph["roots"][e["root"]]) / PureWindowsPath(e["relative_path"]))
                assert logical == e["logical_path"]
                key = logical.casefold(); assert key not in by_key; by_key[key] = e
                assert type(e["size_bytes"]) is int and e["size_bytes"] >= 0
                assert e["declared_size_bytes"] is None or e["declared_size_bytes"] == e["size_bytes"]
                target = e["root"] + "/" + e["relative_path"]
                if e["root"] == "original" and e["relative_path"] in external:
                    x = external[e["relative_path"]]
                    assert (e["sha256"], e["size_bytes"]) == (x["sha256"], x["size_bytes"])
                    assert e["delivery_route"] == "accepted_pretrained_archive"; routed[target] = e
                else:
                    assert e["delivery_route"] == "new_static_package"; internal["roots/" + target] = e
            assert len(nodes) == 17617 and len(internal) == 17595 and len(routed) == 22
            assert sum(e["size_bytes"] for e in nodes) == 11840356271 == audit_result["bytes"]
            assert sum(e["size_bytes"] for e in internal.values()) == 4345359738
            edges = metadata("audit/EDGES_PRIVATE.json")["edges"]; assert len(edges) == 21118
            adjacency = collections.defaultdict(set); seed_edges = []
            for edge in edges:
                child = by_key[edge["child"]]
                assert child["sha256"] == edge["sha256"]
                assert edge["size_bytes"] is None or child["size_bytes"] == edge["size_bytes"]
                assert edge["parent"] == "SEEDS" or edge["parent"] in by_key
                bound = PureWindowsPath(edge["declared_path"])
                resolved = bound if bound.is_absolute() else PureWindowsPath(edge["relative_base"]) / bound
                assert str(resolved).casefold() == edge["child"]
                adjacency[edge["parent"]].add(edge["child"])
                if edge["parent"] == "SEEDS": seed_edges.append(edge)
            assert len(seed_edges) == len(audit_freeze["seeds"]) == 21
            for i, seed in enumerate(audit_freeze["seeds"]):
                edge = next(e for e in seed_edges if e["selector"] == str(i))
                expected_key = str(PureWindowsPath(graph["roots"][seed["root"]]) / seed["path"]).casefold()
                assert (edge["child"], edge["sha256"], edge["size_bytes"]) == (expected_key, seed["sha256"], seed["size_bytes"])
            seen, pending = set(), list(adjacency["SEEDS"])
            while pending:
                key = pending.pop()
                if key not in seen:
                    seen.add(key); pending.extend(adjacency[key])
            assert seen == set(by_key), "UNREACHABLE_GRAPH_MEMBER"
            assert names == set(support) | set(internal), "ARCHIVE_FILESET_MISMATCH"
            a.destination.mkdir(exist_ok=False)
            for i, (member, e) in enumerate(internal.items(), 1):
                destination = a.destination.joinpath(*safe_parts(member[len("roots/"):]))
                restore(z, member, destination, (e["sha256"], e["size_bytes"]))
                if i % 2000 == 0: print("STATIC_RESTORED", i, len(internal), flush=True)
            for target, e in routed.items():
                restore(assets, "assets/" + e["relative_path"], a.destination.joinpath(*safe_parts(target)), (e["sha256"], e["size_bytes"]))
            actual = {p.relative_to(a.destination).as_posix() for p in a.destination.rglob("*") if p.is_file() or p.is_symlink()}
            assert actual == {e["root"] + "/" + e["relative_path"] for e in nodes}
            for e in nodes:
                path = a.destination / e["root"] / e["relative_path"]; no_links(path)
                assert file_digest(path) == (e["sha256"], e["size_bytes"]), "RESTORED_REHASH_MISMATCH"
            assert not blocked
            result.update(status="PASS_INDEPENDENT_STATIC_THREE_ROOT_RESTORATION_ONLY", graph_manifest_sha256=GRAPH_PIN,
                          archive_sha256=a.archive_sha256, asset_archive_sha256=ASSET_PIN, archive_members=len(names),
                          restored_files=len(nodes), restored_bytes=sum(e["size_bytes"] for e in nodes),
                          per_root_files=dict(collections.Counter(e["root"] for e in nodes)),
                          dependency_edges_checked=len(edges), seed_reachable_nodes=len(seen),
                          internal_files=len(internal), external_pretrained_files=len(routed),
                          destination=str(a.destination), exact_restored_fileset=True,
                          live_c3_ledgers_restored=False, absolute_metadata_rewritten=False)
    except Exception as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc(), failed_outputs_retained=True)
    result.update(blocked_events=blocked, opened_paths=sorted(opened), finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with a.receipt.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2); stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "opened_paths"}, indent=2))
    return 0 if result["status"] == "PASS_INDEPENDENT_STATIC_THREE_ROOT_RESTORATION_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
