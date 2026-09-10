"""Replay authenticated ROA parameters without fitting or changing sealed bytes.

Run primary and independent modes in separate processes and new directories.
The original source is byte pinned; only artifact locations and IO are adapted.
"""
from __future__ import annotations

import argparse
import importlib.util
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback

from scripts.verify_roa_artifacts import SPEC_PATH, digest, verify

REPO = Path(__file__).resolve().parents[1]
VENDOR = REPO / "src/arbitration/roa_original"
NAMES = ("controls", "design", "learning", "metrics", "independent")


def write_json(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def load_original(name: str):
    spec = importlib.util.spec_from_file_location(name, VENDOR / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def install_boundary(output: Path) -> dict:
    """Deny file mutations outside output and all network/process execution."""
    access = {"write_paths": set(), "blocked": []}

    def check_write(value):
        if isinstance(value, int):
            return
        path = Path(os.fsdecode(value)).resolve()
        if path != output and output not in path.parents:
            access["blocked"].append(str(path))
            raise RuntimeError("REPLAY_WRITE_OUTSIDE_OUTPUT:" + str(path))
        access["write_paths"].add(str(path))

    def audit(event, args):
        if event in ("socket.connect", "socket.bind", "subprocess.Popen", "os.system"):
            access["blocked"].append(event)
            raise RuntimeError("REPLAY_FORBIDDEN:" + event)
        if event == "open":
            mode, flags = args[1:3]
            if ((isinstance(mode, str) and any(c in mode for c in "wax+")) or
                (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))):
                check_write(args[0])
        if event in ("os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.utime", "os.truncate"):
            check_write(args[0])
        if event in ("os.rename", "os.link", "os.symlink"):
            check_write(args[0]); check_write(args[1])
    sys.addaudithook(audit)
    return access


def bind_original(root: Path, output: Path):
    c = load_original("controls")
    c.ROOT = root
    c.OUT = root / json.loads(SPEC_PATH.read_text())["namespace"]
    c.DHC = c.OUT.parent / "dual_head_constrained_v1"
    c.PRE = root / "outputs/daa_v2_fresh_v1/prelabel_seal_v3"
    c.SOURCES = {
        "base": c.PRE / "scoring/v2_base_scores.jsonl",
        "gbv": c.PRE / "scoring/gbv_scores.jsonl",
        "actions": c.PRE / "decisions/v2_actions.jsonl",
        "outcomes": root / "outputs/daa_v2_fresh_v1/final_evaluation/outcomes/fresh_numeric_outcomes.jsonl",
    }

    def writer(name, value):
        target = (output / name).resolve()
        target.relative_to(output)
        write_json(target, value)

    def guard(records):
        exact = {(root / r["path"]).resolve() for r in records} | set(c.SOURCES.values()) | {(root / n).resolve() for n in c.DOCS}
        runtime = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(), VENDOR]
        reads = {"read_paths": set(), "write_paths": set(), "blocked": []}

        def audit(event, args):
            if event != "open" or isinstance(args[0], int):
                return
            p = Path(os.fsdecode(args[0])).resolve()
            allowed = p in exact or any(p == d or d in p.parents for d in [c.OUT, output, *runtime])
            if not allowed:
                reads["blocked"].append(str(p))
                raise RuntimeError("REPLAY_UNAPPROVED_READ:" + str(p))
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(ch in mode for ch in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            reads["write_paths" if writing else "read_paths"].add(str(p))
        sys.addaudithook(audit)
        return reads
    c.write = writer
    c.guard = guard
    return c


def primary(c, output: Path) -> dict:
    """Use the original numeric/matrix, split, ranking and metric functions."""
    import numpy as np
    from scipy.special import expit
    from sklearn.linear_model import LogisticRegression
    d = load_original("design")
    learning = load_original("learning")
    metrics = load_original("metrics")

    def forbidden_fit(*args, **kwargs):
        raise RuntimeError("SCIENTIFIC_FIT_FORBIDDEN_IN_REPLAY")
    LogisticRegression.fit = forbidden_fit
    rows = c.keyed(c.OUT / "NUMERIC_FEATURES_PRIVATE.jsonl")
    ys = c.keyed(c.SOURCES["outcomes"])
    scores = c.keyed(c.OUT / "FROZEN_COMPARATORS_PRIVATE.jsonl")
    contexts = c.load(c.OUT / "SPLIT_MANIFEST.json")["contexts"]
    if [r["context"] for r in contexts] != d.contexts():
        raise RuntimeError("CONTEXT_COVERAGE")
    result = dict(status="PASS", contexts=0, models=0, prediction_rows=0,
                  max_logit_error=0.0, max_probability_error=0.0, max_metric_error=0.0,
                  action_membership_differences=0, jobs=[])

    def compare(actual, expected):
        if isinstance(expected, dict):
            if set(actual) != set(expected): raise RuntimeError("METRIC_FIELDS")
            for k in expected: compare(actual[k], expected[k])
        elif isinstance(expected, float):
            error = abs(actual - expected)
            result["max_metric_error"] = max(result["max_metric_error"], error)
            if not math.isfinite(actual) or error > 1e-10: raise RuntimeError("METRIC_ERROR")
        elif actual != expected: raise RuntimeError("METRIC_VALUE")

    with (output / "REPLAY_PREDICTIONS_PRIVATE.jsonl").open("x", encoding="utf-8") as predictions:
        for item in contexts:
            context = item["context"]
            parts = d.partition(set(rows), context)
            if d.receipt(parts, rows, ys) != item["partitions"]: raise RuntimeError("SPLIT_RECEIPT")
            kk = sorted(k for k in parts["test"] if rows[k]["eligible"])
            selected = {}
            for variant in d.VARIANTS:
                jid = context["id"] + "_" + variant
                model = c.load(c.OUT / "jobs" / jid / "MODEL.json")
                width = 11 if variant == "ROA-FULL" else 10
                transform = {k: np.asarray(v) for k, v in model["preprocessing"].items()}
                matrix = learning.matrix(learning.numeric(rows, kk, width), kk, **transform)
                if learning.ah(matrix) != model["design_hashes"]["test"]: raise RuntimeError("DESIGN_HASH")
                raw = matrix @ np.asarray(model["coef"]) + model["intercept"]
                prob = expit(raw * model["platt_slope"] + model["platt_intercept"])
                saved = c.keyed(c.OUT / "jobs" / jid / "PREDICTIONS_PRIVATE.jsonl")
                if set(saved) != set(kk): raise RuntimeError("PREDICTION_COVERAGE")
                for i, k in enumerate(kk):
                    errors = [abs(raw[i] - saved[k]["logit_R"]), abs(prob[i] - saved[k]["pR"])]
                    if not all(math.isfinite(v) and v <= 1e-10 for v in errors): raise RuntimeError("PREDICTION_ERROR:" + jid)
                    for label, error in zip(("max_logit_error", "max_probability_error"), errors):
                        result[label] = max(result[label], float(error))
                    predictions.write(json.dumps(dict(job_id=jid, **c.keydict(k), logit_R=float(raw[i]), pR=float(prob[i])), sort_keys=True) + "\n")
                selected[variant] = d.top(dict(zip(kk, prob)), item["cap"])
                result["prediction_rows"] += len(kk)
                result["models"] += 1
                result["jobs"].append(dict(job_id=jid, predictions=len(kk), model=c.rec(c.OUT / "jobs" / jid / "MODEL.json")))
            for m in ("HGB", "GbV", "V2"):
                selected[m] = d.top({k: scores[k][m] for k in kk}, item["cap"])
            seal = c.load(c.OUT / "partitions" / context["id"] / "ACTION_SEAL.json")
            for m, keys in selected.items():
                difference = len(keys.symmetric_difference(map(tuple, seal["selected_keys"][m])))
                result["action_membership_differences"] += difference
            if result["action_membership_differences"]: raise RuntimeError("ACTION_MEMBERSHIP")
            expected = c.load(c.OUT / "partitions" / context["id"] / "RESULT.json")["summary"]
            compare(metrics.summary(parts["test"], selected, ys, item["cap"]), expected)
            result["contexts"] += 1
    if (result["contexts"], result["models"], result["prediction_rows"]) != (28, 56, 38424):
        raise RuntimeError("FULL_COVERAGE_COUNTS")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("primary", "independent"), required=True)
    args = parser.parse_args()
    root, output = args.project_root.resolve(), args.output.resolve()
    if output == root or root in output.parents:
        parser.error("Output must be outside the original project, in a new directory")
    output.mkdir(parents=True, exist_ok=False)
    state = dict(status="FAIL", mode=args.mode, scientific_fit_calls=0, retrieval_generation_calls=0,
                 tolerance=1e-10, cas_q2_status="NOT READY", command=sys.argv, source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
                 source_status=subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True),
                 python=sys.version, executable=sys.executable, platform=platform.platform(),
                 versions={n: importlib.metadata.version(n) for n in ("numpy", "scipy", "scikit-learn", "threadpoolctl")})
    try:
        spec = json.loads(SPEC_PATH.read_text())
        integrity = verify(root, root / spec["manifest_path"], spec)
        write_json(output / "ROA_INTEGRITY_BEFORE.json", integrity)
        if integrity["integrity_status"] != "PASS": raise RuntimeError("ROA_INTEGRITY")
        entries = {Path(e["path"]).name: e for e in json.loads((root / spec["manifest_path"]).read_text())["files"] if e["path"].endswith(".py")}
        state["original_source"] = []
        for name in NAMES:
            p = VENDOR / (name + ".py")
            if digest(p) != entries[p.name]["sha256"]: raise RuntimeError("VENDORED_SOURCE_CHANGED:" + name)
            state["original_source"].append(entries[p.name])
        state["wrapper_sha256"] = digest(Path(__file__))
        from threadpoolctl import threadpool_info, threadpool_limits
        import numpy
        import scipy.special
        state["numerical_backends"] = threadpool_info()
        c = bind_original(root, output)
        boundary = install_boundary(output)
        c.frozen()
        parents = c.parents()
        write_json(output / "PARENT_VERIFICATION.json", parents)
        with threadpool_limits(1):
            if args.mode == "primary":
                state["replay"] = primary(c, output)
            else:
                ind = load_original("independent")
                if any(n in sys.modules for n in ("design", "learning", "metrics", "execute")):
                    raise RuntimeError("INDEPENDENT_ORACLE_IMPORT")
                ind.main()
                state["independent_checks"] = ind.CHECKS
                state["max_numeric_error"] = ind.MAX_ERROR
        # Original independent guard intentionally only permits its sealed inputs.
        # Recheck original payload hashes directly; do not reopen the spec afterward.
        manifest = json.loads((root / spec["manifest_path"]).read_text())
        for entry in manifest["files"]: c.check(entry)
        if digest(root / spec["manifest_path"]) != spec["manifest_sha256"]: raise RuntimeError("POST_MANIFEST")
        state["original_payloads_unchanged"] = len(manifest["files"])
        state["boundary"] = {k: sorted(v) if isinstance(v, set) else v for k, v in boundary.items()}
        state["status"] = "PASS"
    except Exception as exc:
        state["error"] = repr(exc)
        state["traceback"] = traceback.format_exc()
    write_json(output / "REPLAY_VALIDATION.json", state)
    print(json.dumps({k:v for k,v in state.items() if k in ("status", "mode", "error", "independent_checks", "max_numeric_error", "cas_q2_status")}))
    return 0 if state["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
