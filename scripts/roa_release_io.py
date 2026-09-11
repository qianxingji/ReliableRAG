"""Byte-only, failure-preserving private release IO; no scientific imports."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile


def canonical(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("NONCANONICAL_PATH")
    parts = value.split("/")
    reserved = {"CON", "PRN", "AUX", "NUL"} | {f"{p}{i}" for p in ("COM", "LPT") for i in range(1, 10)}
    if any(p in ("", ".", "..") or p[-1:] in (".", " ") or
           any(ord(c) < 32 or c in ':*?"<>|' for c in p) or
           p.split(".")[0].upper() in reserved for p in parts):
        raise ValueError("NONCANONICAL_PATH")
    if PurePosixPath(value).is_absolute():
        raise ValueError("ABSOLUTE_PATH")
    return value


def safe(root: Path, name: str, *, exists: bool = True) -> Path:
    """Reject links/junctions at every existing path component, including root."""
    name = canonical(name)
    root = root.absolute()
    target = root / name
    for p in [*reversed(target.parents), target]:
        if p.exists() or p.is_symlink():
            s = p.lstat()
            if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400:
                raise ValueError("REPARSE_OR_SYMLINK")
    target.resolve().relative_to(root.resolve())
    if exists and not target.is_file():
        raise ValueError("MISSING_REGULAR_FILE:" + name)
    return target


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for b in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def record(root: Path, path: Path) -> dict:
    return dict(path=path.relative_to(root).as_posix(), size_bytes=path.stat().st_size, sha256=sha(path))


def records_index(records: list[dict]) -> dict[str, dict]:
    result, folded = {}, {}
    for e in records:
        name = canonical(e["path"])
        if type(e["size_bytes"]) is not int or e["size_bytes"] < 0 or not re.fullmatch("[0-9a-f]{64}", e["sha256"]):
            raise ValueError("INVALID_RECORD")
        if name.casefold() in folded and folded[name.casefold()] != name:
            raise ValueError("CASE_ALIAS")
        if name in result and result[name] != e:
            raise ValueError("CONFLICTING_RECORD")
        result[name] = e
        folded[name.casefold()] = name
    return result


def verify_record(root: Path, entry: dict) -> None:
    path = safe(root, entry["path"])
    before = path.stat()
    actual = sha(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("CHANGED_DURING_READ")
    if after.st_size != entry["size_bytes"] or actual != entry["sha256"]:
        raise ValueError("HASH_MISMATCH:" + entry["path"])


def write_json(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def archive_check(path: Path, entries: list[dict]) -> None:
    expected = records_index(entries)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(expected) or set(names) != set(expected):
            raise ValueError("ARCHIVE_COVERAGE")
        for name, e in expected.items():
            info = archive.getinfo(name)
            if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16) or info.file_size != e["size_bytes"]:
                raise ValueError("ARCHIVE_MEMBER_TYPE_OR_SIZE")
            h, size = hashlib.sha256(), 0
            with archive.open(name) as stream:
                for b in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(b)
                    size += len(b)
            if size != e["size_bytes"] or h.hexdigest() != e["sha256"]:
                raise ValueError("ARCHIVE_MEMBER_HASH")


def package_bytes(root: Path, output: Path, entries: list[dict]) -> None:
    """Never delete a failed partial archive; callers record the failure."""
    expected = records_index(entries)
    safe(output.parent, output.name, exists=False)
    with output.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name, e in sorted(expected.items()):
                path = safe(root, name)
                h, size = hashlib.sha256(), 0
                with path.open("rb") as source, archive.open(name, "w") as member:
                    for b in iter(lambda: source.read(1024 * 1024), b""):
                        h.update(b)
                        size += len(b)
                        member.write(b)
                if size != e["size_bytes"] or h.hexdigest() != e["sha256"]:
                    raise ValueError("CHANGED_DURING_COPY:" + name)
        stream.flush()
        os.fsync(stream.fileno())
    archive_check(output, list(expected.values()))
    for entry in expected.values():
        verify_record(root, entry)


def extract_bytes(archive_path: Path, root: Path, entries: list[dict]) -> None:
    archive_check(archive_path, entries)
    safe(root.parent, root.name, exists=False)
    root.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive_path) as archive:
        for entry in records_index(entries).values():
            target = safe(root, entry["path"], exists=False)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry["path"]) as source, target.open("xb") as sink:
                for b in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(b)
            verify_record(root, entry)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != set(records_index(entries)):
        raise ValueError("EXTRACTION_COVERAGE")
