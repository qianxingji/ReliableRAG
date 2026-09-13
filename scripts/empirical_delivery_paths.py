"""Explicit authenticated source transport; never used by the live controllers.

Logical identities stay in original metadata. Physical locations and the three
support modules' approved Path globals are recorded separately. Scientific
functions are neither rewritten nor replaced.
"""
from dataclasses import dataclass
import hashlib
import importlib.util
from pathlib import Path, PureWindowsPath
import re
import stat
import sys
import types


def require(ok, message):
    if not ok:
        raise ValueError(message)


def windows_identity(value):
    require(isinstance(value, str) and bool(re.match(r"^[A-Za-z]:[/\\]", value)), "Absolute local Windows identity required")
    path = PureWindowsPath(value)
    require(path.is_absolute() and not path.is_reserved(), "Invalid logical identity")
    require(all(part and part not in {".", ".."} and ":" not in part and part == part.rstrip(" .")
                and not PureWindowsPath(part).is_reserved()
                for part in re.split(r"[/\\]", value[3:])), "Logical path alias or traversal")
    return path


def relative_identity(value):
    require(isinstance(value, str) and value and not value.startswith(("/", "\\")), "Relative member required")
    parts = re.split(r"[/\\]", value)
    require(all(p and p not in {".", ".."} and ":" not in p and p == p.rstrip(" .")
                and not PureWindowsPath(p).is_reserved() for p in parts), "Relative path alias or traversal")
    path = PureWindowsPath(value)
    require(not path.drive and not path.is_reserved(), "Reserved member")
    return path


def safe_file(path, root):
    path, root = Path(path).absolute(), Path(root).absolute()
    require(path.is_relative_to(root), "Physical member outside root")
    for node in (*reversed(path.parents), path):
        if node.exists() or node.is_symlink():
            info = node.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
                    "Symlink or reparse point forbidden")
    require(path.is_file() and path.stat().st_nlink == 1, "Regular unaliased file required")
    require(path.resolve().is_relative_to(root.resolve()), "Resolved member escaped root")
    return path.resolve()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class RootBinding:
    logical: str
    physical: Path


class BoundFiles:
    """Resolve only explicitly bound records; there is no search/fallback path."""
    def __init__(self, roots, records):
        self.roots = dict(roots)
        self.logical, self.physical = {}, {}
        specs = list(self.roots.values())
        for i, root in enumerate(specs):
            logical = windows_identity(root.logical)
            physical = Path(root.physical)
            require(physical.is_absolute(), "Physical root must be absolute")
            require(".." not in physical.parts, "Physical root traversal forbidden")
            for previous in specs[:i]:
                other = windows_identity(previous.logical)
                require(not logical.is_relative_to(other) and not other.is_relative_to(logical), "Logical root overlap")
                other_physical = Path(previous.physical).absolute()
                require(not physical.is_relative_to(other_physical) and not other_physical.is_relative_to(physical), "Physical root overlap")
        for entry in records:
            require(set(entry) == {"root", "relative_path", "logical_path", "sha256", "size_bytes"}, "Exact file-record schema")
            require(entry["root"] in self.roots, "Unknown logical root")
            root = self.roots[entry["root"]]
            relative = relative_identity(entry["relative_path"])
            logical = windows_identity(entry["logical_path"])
            require(logical == windows_identity(root.logical) / relative, "Logical identity differs from root/member")
            require(type(entry["size_bytes"]) is int and entry["size_bytes"] >= 0 and
                    isinstance(entry["sha256"], str) and bool(re.fullmatch("[0-9a-f]{64}", entry["sha256"])), "Invalid digest or size")
            physical = Path(root.physical).absolute().joinpath(*relative.parts)
            require(logical not in self.logical and physical not in self.physical, "Duplicate logical/physical alias")
            self.logical[logical] = dict(entry)
            self.physical[physical] = logical

    def checked(self, logical):
        identity = windows_identity(str(logical))
        require(identity in self.logical, "Unbound logical file")
        entry = self.logical[identity]
        root = self.roots[entry["root"]]
        path = safe_file(Path(root.physical).joinpath(*relative_identity(entry["relative_path"]).parts), root.physical)
        require(path.stat().st_size == entry["size_bytes"] and digest(path) == entry["sha256"], "Bound file digest/size mismatch")
        return path

    def checked_physical(self, path):
        physical = Path(path).absolute()
        require(physical in self.physical, "Unbound physical file; fallback forbidden")
        return self.checked(str(self.physical[physical]))

    def verify_exact_fileset(self):
        actual = {p.absolute() for root in self.roots.values() for p in Path(root.physical).rglob("*") if p.is_file() or p.is_symlink()}
        require(actual == set(self.physical), "Exact transported file set differs")
        for logical in self.logical:
            self.checked(str(logical))


ORIGINAL_ROOT = "E:/paper/ReliableRAG"
SUPPORT_PATHS = {
    "outputs/daa_v2_fresh_v1/retrieval_freeze/retrieval_support.py": (
        "c648e1b0b2ba4b957ae01e9c2e0784bfe7ee72c6d3bc1ac8cd7fcb671c8ca54c",
        dict(ROOT="", OUT="outputs/daa_v2_fresh_v1/retrieval_freeze", POOL="outputs/daa_v2_fresh_v1/pool_freeze",
             COHORT="outputs/daa_v2_fresh_v1/cohort_freeze", CACHE="data/models/huggingface",
             SNAPSHOT="data/models/huggingface/models--BAAI--bge-base-en-v1.5/snapshots/a5beb1e3e68b9ab74eb54cfd186867f64f240e1a")),
    "outputs/daa_v2_fresh_v1/runtime_branch_freeze/runtime_support.py": (
        "d4bacc0112c06df55b924961fb0296204ae8f12e6a19de8020b1feeaca4039c7",
        dict(ROOT="", OUT="outputs/daa_v2_fresh_v1/runtime_branch_freeze", RET="outputs/daa_v2_fresh_v1/retrieval_freeze",
             POOL="outputs/daa_v2_fresh_v1/pool_freeze", COHORT="outputs/daa_v2_fresh_v1/cohort_freeze",
             CACHE="data/models/huggingface", HIST="outputs/phase10_extension_private_v2r3")),
    "outputs/daa_v2_fresh_v1/prelabel_seal_v3/v3_support.py": (
        "5efe2e745dd5ad5c6f5c986d7d2179c2f7ee6be92b22e2e769d354c141849e38",
        dict(ROOT="", OUT="outputs/daa_v2_fresh_v1/prelabel_seal_v3", OLD="outputs/daa_v2_fresh_v1/prelabel_seal",
             V2="outputs/daa_v2_fresh_v1/prelabel_seal_v2", RUNTIME="outputs/daa_v2_fresh_v1/runtime_branch_freeze",
             HIST="outputs/mars_full", BASELINE="outputs/published_baseline_gbv_nli_v1",
             BINDING="outputs/daa_v2_fresh_v1/prelabel_seal_v2/binding/canonical_metadata_binding.jsonl")),
}


def bind_support(module, physical_root, relative_paths, importer):
    """Validate all changes before mutation; leave all scientific objects intact."""
    before = dict(module.__dict__)
    path_names = {name for name, value in before.items() if isinstance(value, Path)}
    require(path_names == set(relative_paths), "Unexpected or missing support Path globals")
    changes = {}
    for name, relative in relative_paths.items():
        require(before[name] == Path(ORIGINAL_ROOT) / relative, "Original support binding differs")
        changes[name] = Path(physical_root) / relative
    require(isinstance(before.get("import_file"), types.FunctionType), "Original import utility missing")
    module.__dict__.update(changes)
    module.import_file = importer
    changed = set(changes) | {"import_file"}
    require(set(module.__dict__) == set(before), "Support global set changed")
    require(all(module.__dict__[name] is value for name, value in before.items() if name not in changed), "Non-IO support object changed")
    return dict(bindings={name: dict(logical=str(before[name]), physical=str(value)) for name, value in changes.items()},
                unchanged_scientific_function_objects=True, import_file_replaced_by_authenticated_loader=True)


class SourceLoader:
    def __init__(self, files):
        self.files, self.loaded, self.owned = files, [], {}

    def load(self, name, physical_path):
        path = self.files.checked_physical(physical_path)
        require(path.suffix == ".py", "Source-only import requires Python source")
        identity = self.files.physical[path]
        require(name not in sys.modules or self.owned.get(name) == identity, "Existing unowned module cannot be overwritten")
        entry = self.files.logical[identity]
        relative = PureWindowsPath(entry["relative_path"]).as_posix()
        support = None
        if windows_identity(self.files.roots[entry["root"]].logical) == windows_identity(ORIGINAL_ROOT):
            support = SUPPORT_PATHS.get(relative)
        if support is not None:
            require(entry["sha256"] == support[0], "Original support source identity differs")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        self.owned[name] = identity
        exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
        receipt = dict(module=name, logical_source=str(identity), source_sha256=entry["sha256"])
        if support is not None:
            expected, bindings = support
            receipt.update(bind_support(module, self.files.roots[entry["root"]].physical, bindings, self.load))
        self.loaded.append(receipt)
        return module
