"""Independent opaque-byte asset extraction; imports no scientific packages."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import sys
import traceback
import zipfile

ORIGINAL = PureWindowsPath("E:/paper/ReliableRAG")
SPECS = {
    "bge": ("BAAI/bge-base-en-v1.5", "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a", 6, 438899684),
    "qwen": ("Qwen/Qwen2.5-3B-Instruct", "aa8e72537993ba99e69dfaafa59ed015b17504d1", 9, 6183451098),
    "gbv_nli": ("MoritzLaurer/deberta-v3-large-zeroshot-v2.0", "5a4338ab2151dc8db04ad53b42b6153382bf4f99", 7, 872645751),
}
PINS = {"acquisition": "6e441f8f9fef2b000ba2b39dcfd7b40f74dd4f779568d885584bb7da10b7d518",
        "scoring": "1027d9e0c062c11bca3c6427d2c2db6403b42e25880d34777d5e32b6adae8ebc"}


def safe_member(name):
    assert isinstance(name, str) and name and "\\" not in name and ":" not in name
    pieces = name.split("/")
    assert all(p and p not in {".", ".."} and p == p.rstrip(" .") and not PureWindowsPath(p).is_reserved() for p in pieces)
    assert not PurePosixPath(name).is_absolute()
    return pieces


def stream_hash(stream):
    h, size = hashlib.sha256(), 0
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(block); size += len(block)
    return h.hexdigest(), size


def file_hash(path):
    with path.open("rb") as stream:
        return stream_hash(stream)


def no_reparse(path):
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            assert not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--archive-sha256", required=True)
    p.add_argument("--freeze", required=True, type=Path)
    p.add_argument("--freeze-sha256", required=True)
    p.add_argument("--destination", required=True, type=Path)
    p.add_argument("--receipt", required=True, type=Path)
    a = p.parse_args()
    assert all(x.is_absolute() for x in (a.archive, a.freeze, a.destination, a.receipt))
    assert not a.destination.exists() and not a.receipt.exists()
    no_reparse(a.destination); no_reparse(a.archive); no_reparse(a.freeze)
    assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
    assert file_hash(a.freeze)[0] == a.freeze_sha256
    freeze = json.loads(a.freeze.read_text(encoding="utf-8"))
    this = Path(__file__).resolve()
    expected_self = next(e for e in freeze["controls"] if e["archive_path"] == "control/validator.py")
    assert file_hash(this) == (expected_self["sha256"], expected_self["size_bytes"])
    libraries = [Path(sys.base_prefix).resolve(), Path(os.environ["SystemRoot"]).resolve()]
    named = {this, a.archive.resolve(), a.freeze.resolve()}
    blocked, opened = [], set()

    def audit(event, args):
        if event == "import" and args[0].split(".")[0] in {"torch", "transformers", "numpy", "sklearn", "datasets", "pyarrow", "safetensors", "sentencepiece", "joblib", "pickle", "_pickle"}:
            blocked.append(dict(event=event, module=args[0])); raise RuntimeError("SCIENTIFIC_IMPORT_FORBIDDEN")
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "socket.gethostbyname", "socket.sendto", "subprocess.Popen", "os.system", "urllib.Request"}:
            blocked.append(dict(event=event)); raise RuntimeError("NETWORK_OR_PROCESS_FORBIDDEN")
        if event == "open" and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
            write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            accepted_write = path == a.receipt or path.is_relative_to(a.destination)
            accepted_read = path in named or path.is_relative_to(a.destination) or any(path.is_relative_to(root) for root in libraries)
            if (write and not accepted_write) or (not write and not accepted_read):
                blocked.append(dict(event=event, path=str(path), writing=bool(write))); raise RuntimeError("UNDECLARED_FILE_ACCESS")
            opened.add(str(path))
        if event in {"os.remove", "os.rmdir", "os.mkdir", "os.rename", "os.replace", "os.truncate", "os.symlink", "os.link"}:
            for value in args[:2] if event in {"os.rename", "os.replace", "os.symlink", "os.link"} else args[:1]:
                if isinstance(value, (str, bytes, os.PathLike)):
                    path = Path(os.fsdecode(value)).resolve()
                    if path != a.destination and not path.is_relative_to(a.destination):
                        blocked.append(dict(event=event, path=str(path))); raise RuntimeError("OUTSIDE_RESTORATION_MUTATION")
    sys.addaudithook(audit)
    result = dict(status="FAIL", started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), model_loads=0, neural_forwards=0, scientific_fits=0, fresh_gold_values=0)
    try:
        assert file_hash(a.archive)[0] == a.archive_sha256
        with zipfile.ZipFile(a.archive) as z:
            infos = z.infolist(); names = [i.filename for i in infos]
            assert len(names) == len(set(n.casefold() for n in names))
            for info in infos:
                safe_member(info.filename)
                assert not info.is_dir() and not info.flag_bits & 1
                assert stat.S_IFMT(info.external_attr >> 16) in {0, stat.S_IFREG}
            reports = {}
            expected = {}
            for role, pin in PINS.items():
                member = f"provenance/{role}/SHA256_MANIFEST.json"
                data = z.read(member); assert hashlib.sha256(data).hexdigest() == pin
                expected[member] = (pin, len(data))
                manifest = json.loads(data)
                report_name = {"acquisition": "ACQUISITION_INPUT_AUDIT.json", "scoring": "SCORING_INPUT_AUDIT.json"}[role]
                assert len(manifest["files"]) == 1 and manifest["files"][0]["path"] == report_name
                record = manifest["files"][0]; member = f"provenance/{role}/{report_name}"
                data = z.read(member); assert (hashlib.sha256(data).hexdigest(), len(data)) == (record["sha256"], record["size_bytes"])
                expected[member] = (record["sha256"], record["size_bytes"]); reports[role] = json.loads(data)
            roots = {
                "bge": ORIGINAL / "data/models/huggingface/models--BAAI--bge-base-en-v1.5/snapshots" / SPECS["bge"][1],
                "qwen": ORIGINAL / "data/models/huggingface/models--Qwen--Qwen2.5-3B-Instruct/snapshots" / SPECS["qwen"][1],
                "gbv_nli": ORIGINAL / "outputs/published_baseline_gbv_nli_v1/infrastructure/model_snapshot",
            }
            derived = []
            for role, root in roots.items():
                report = reports["scoring" if role == "gbv_nli" else "acquisition"]
                binding = report["gbv"] if role == "gbv_nli" else report["models"][{"bge": "bge_dense_encoder", "qwen": "qwen_reader"}[role]]
                assert (binding["model_id"], binding["revision"]) == SPECS[role][:2]
                selected = [e for e in report["checked_files"] if PureWindowsPath(e["path"]).is_relative_to(root)]
                assert len(selected) == SPECS[role][2] and sum(e["size_bytes"] for e in selected) == SPECS[role][3]
                for e in selected:
                    relative = PureWindowsPath(e["path"]).relative_to(ORIGINAL).as_posix(); safe_member(relative)
                    derived.append(dict(model=role, path=relative, sha256=e["sha256"], size_bytes=e["size_bytes"]))
            derived.sort(key=lambda e: e["path"])
            assert len(derived) == 22 and len({e["path"].casefold() for e in derived}) == 22
            lock_data = z.read("ASSET_LOCK.json"); lock = json.loads(lock_data)
            assert lock == dict(schema_version=1, logical_original_root=ORIGINAL.as_posix(), models={k: dict(model_id=v[0], revision=v[1], files=v[2], bytes=v[3]) for k, v in SPECS.items()}, files=derived)
            assert hashlib.sha256(lock_data).hexdigest() == freeze["asset_lock_sha256"]
            expected["ASSET_LOCK.json"] = (freeze["asset_lock_sha256"], len(lock_data))
            for e in derived: expected["assets/" + e["path"]] = (e["sha256"], e["size_bytes"])
            for e in freeze["controls"]:
                assert e["archive_path"] in {"control/contract.md", "control/writer.py", "control/validator.py"}
                expected[e["archive_path"]] = (e["sha256"], e["size_bytes"])
            assert len(freeze["controls"]) == 3 and set(names) == set(expected) and len(names) == 30
            a.destination.mkdir(exist_ok=False)
            restored = []
            for info in infos:
                wanted = expected[info.filename]
                assert info.file_size == wanted[1]
                with z.open(info) as stream:
                    if info.filename.startswith("assets/"):
                        relative = info.filename[len("assets/"):]; destination = a.destination.joinpath(*safe_member(relative))
                        assert destination.is_relative_to(a.destination); destination.parent.mkdir(parents=True, exist_ok=True); no_reparse(destination)
                        h, size = hashlib.sha256(), 0
                        with destination.open("xb") as output:
                            for block in iter(lambda: stream.read(2 * 1024 * 1024), b""):
                                output.write(block); h.update(block); size += len(block)
                        assert (h.hexdigest(), size) == wanted
                        restored.append(dict(path=relative, sha256=wanted[0], size_bytes=size))
                    else:
                        assert stream_hash(stream) == wanted
            actual = {p.relative_to(a.destination).as_posix() for p in a.destination.rglob("*") if p.is_file() or p.is_symlink()}
            assert actual == {e["path"] for e in derived}
            for e in derived:
                path = a.destination / e["path"]; no_reparse(path)
                assert path.stat().st_nlink == 1 and file_hash(path) == (e["sha256"], e["size_bytes"])
            qwen_relative = roots["qwen"].relative_to(ORIGINAL).as_posix()
            index = json.loads((a.destination / qwen_relative / "model.safetensors.index.json").read_text(encoding="utf-8"))
            shards = set(index["weight_map"].values())
            assert all(len(safe_member(name)) == 1 for name in shards)
            assert shards == {PurePosixPath(e["path"]).name for e in derived if e["model"] == "qwen" and e["path"].endswith(".safetensors")}
            assert len(shards) == 2 and not blocked
        result.update(status="PASS_EXACT_PRETRAINED_ASSET_ARCHIVE_AND_RESTORATION_ONLY", archive_sha256=a.archive_sha256,
                      archive_members=30, restored_files=restored, restored_bytes=sum(e["size_bytes"] for e in restored), destination=str(a.destination),
                      authoritative_audit_pins=PINS, original_project_content_reads=0, qwen_index_shards=sorted(shards), qwen_index_tensor_names=len(index["weight_map"]),
                      all_restored_bytes_match_original_audits=True, full_pipeline_replay=False)
    except Exception as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc(),failed_outputs_retained=True)
    result.update(blocked_events=blocked, opened_paths=sorted(opened), finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with a.receipt.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2); stream.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "blocked_events", "finished_utc")}))
    return 0 if result["status"] == "PASS_EXACT_PRETRAINED_ASSET_ARCHIVE_AND_RESTORATION_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
