"""Guarded source/config assembly only, in a fresh relocated interpreter process."""
import argparse
from dataclasses import dataclass
import datetime
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
from pathlib import Path
import site
import sys
import traceback
import types


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", type=Path, required=True)
    parser.add_argument("--transport-sha256", required=True)
    args = parser.parse_args()
    payload = args.transport.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == args.transport_sha256
    config = json.loads(payload)
    out = args.transport.parent.resolve()
    environment = Path(config["environment"]).resolve()
    base = Path(sys.base_prefix).resolve()
    windows = Path(os.environ["SystemRoot"]).resolve()
    assert Path(sys.prefix).resolve() == environment and site.ENABLE_USER_SITE is False
    assert sys.flags.isolated and sys.dont_write_bytecode and os.environ["CUDA_VISIBLE_DEVICES"] == "-1"
    roots = {k: Path(v["physical"]).resolve() for k, v in config["roots"].items()}
    expected = {roots[e["root"]].joinpath(*Path(e["relative_path"]).parts): e for e in config["files"]}
    assert len(expected) == len(config["files"])
    this = Path(__file__).resolve()
    assert this in expected and hashlib.sha256(this.read_bytes()).hexdigest() == expected[this]["sha256"]
    helper = roots["engineering"] / "scripts/empirical_delivery_paths_v2.py"
    assert helper in expected and hashlib.sha256(helper.read_bytes()).hexdigest() == expected[helper]["sha256"]
    spec = importlib.util.spec_from_file_location("delivery_paths", helper)
    adapter = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = adapter
    exec(compile(helper.read_bytes(), str(helper), "exec"), adapter.__dict__)
    bindings = {k: adapter.RootBinding(v["logical"], Path(v["physical"])) for k, v in config["roots"].items()}
    files = adapter.BoundFiles(bindings, config["files"])
    files.verify_exact_fileset()
    blocked, opened, science_calls = [], set(), []
    permitted_libraries = (environment, base, windows)
    bootstrap_active = True
    bootstrap_events = []
    optional_import_refusals = []
    fixes_source = environment / "Lib/site-packages/sklearn/utils/fixes.py"
    fixes_sha256 = "5c9908a77a54970344c455b29b2e90ff014ef86f1b71ae9fdc1207f53a3ae5ab"
    assert hashlib.sha256(fixes_source.read_bytes()).hexdigest() == fixes_sha256
    bootstrap_sources = {
        base / "Lib/platform.py": "95801e4fde8f28a7f41397551eb417d650fa584d780029660610700114efbad0",
        base / "Lib/subprocess.py": "54356e454227e4085419f455caf5e97e9c4c99995a10ac1e5f685015eff9c038",
    }
    for p, expected_hash in bootstrap_sources.items():
        assert hashlib.sha256(p.read_bytes()).hexdigest() == expected_hash
    shell = windows / "System32/cmd.exe"
    assert Path(os.environ["COMSPEC"]).resolve() == shell.resolve()

    def original_platform_query():
        frame = sys._getframe(1)
        while frame is not None:
            if frame.f_code is platform._syscmd_ver.__code__ and Path(frame.f_globals.get("__file__", "")).resolve() == base / "Lib/platform.py":
                return True
            frame = frame.f_back
        return False

    def allowed(p):
        return p in expected or any(p == root or p.is_relative_to(root) for root in permitted_libraries)

    def audit(event, values):
        if bootstrap_active and event in {"open", "subprocess.Popen"} and original_platform_query():
            if event == "subprocess.Popen":
                executable, command, cwd, child_env = values
                if (sum(e["event"] == event for e in bootstrap_events) == 0
                        and (executable is None or Path(executable).resolve() == shell.resolve())
                        and command == os.environ["COMSPEC"] + ' /c "ver"' and cwd is None and child_env is None):
                    bootstrap_events.append(dict(event=event, executable=executable, command=command, scope="Windows version metadata only"))
                    return
            if event == "open" and not isinstance(values[0], int):
                p = Path(os.fsdecode(values[0])).resolve()
                mode, flags = values[1:3]
                caller = sys._getframe(1)
                if (p == Path(os.devnull).resolve() and mode is None and isinstance(flags, int)
                        and flags & (os.O_WRONLY | os.O_RDWR) == os.O_RDWR and not flags & (os.O_CREAT | os.O_TRUNC)
                        and caller.f_code is subprocess.Popen._get_devnull.__code__
                        and not any(e["event"] == "nul_capability_open" for e in bootstrap_events)):
                    bootstrap_events.append(dict(event="nul_capability_open", path=str(p), flags=flags, scope="Stock subprocess DEVNULL for ver"))
                    return
        if event == "import" and values[0] == "pyarrow" and not bootstrap_active:
            caller = sys._getframe(1)
            if (not optional_import_refusals and caller.f_globals.get("__name__") == "sklearn.utils.fixes"
                    and caller.f_code.co_name == "<module>" and Path(caller.f_globals.get("__file__", "")).resolve() == fixes_source.resolve()):
                optional_import_refusals.append(dict(module="pyarrow", source_sha256=fixes_sha256,
                    action="ModuleNotFoundError preserves absent optional target; no module or data loaded"))
                raise ModuleNotFoundError("PyArrow target is unavailable to source-only assembly", name="pyarrow")
        if event == "import" and values[0].split(".")[0] in {"torch", "transformers", "datasets", "sentencepiece", "pyarrow", "faiss"}:
            blocked.append(dict(event=event, module=values[0]))
            raise RuntimeError("NEURAL_OR_RAW_DATA_IMPORT_FORBIDDEN")
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "socket.gethostbyname", "socket.sendto", "subprocess.Popen", "os.system", "urllib.Request"}:
            blocked.append(dict(event=event))
            raise RuntimeError("NETWORK_OR_PROCESS_FORBIDDEN")
        if event == "open" and not isinstance(values[0], int):
            p = Path(os.fsdecode(values[0])).resolve()
            mode, flags = values[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if (writing and not p.is_relative_to(out)) or (not writing and not allowed(p) and p != args.transport.resolve()):
                blocked.append(dict(event=event, path=str(p), writing=bool(writing)))
                raise RuntimeError("UNDECLARED_FILE_ACCESS")
            opened.add(str(p))
        if event in {"os.remove", "os.rmdir", "os.mkdir", "os.rename", "os.replace", "os.truncate", "os.symlink", "os.link"}:
            for value in values[:2] if event in {"os.rename", "os.replace", "os.symlink", "os.link"} else values[:1]:
                if isinstance(value, (str, bytes, os.PathLike)) and not Path(os.fsdecode(value)).resolve().is_relative_to(out):
                    blocked.append(dict(event=event, path=os.fsdecode(value)))
                    raise RuntimeError("SOURCE_OR_ENVIRONMENT_MUTATION_FORBIDDEN")

    forbidden_calls = {"fit", "fit_transform", "partial_fit", "from_pretrained", "forward", "_ensure_loaded", "encode", "generate",
                       "generate_answer", "generate_repair_query", "score_likelihoods", "base_scores", "restore_dataset", "frozen_inputs"}

    def profile(frame, event, arg):
        module = frame.f_globals.get("__name__", "")
        scientific_module = module.startswith(("src.", "sklearn.", "torch.", "transformers.", "accepted_", "delivery_native_"))
        if event == "call" and scientific_module and frame.f_code.co_name in forbidden_calls:
            science_calls.append(dict(name=frame.f_code.co_name, filename=frame.f_code.co_filename))
            raise RuntimeError("SCIENTIFIC_EXECUTION_FORBIDDEN_IN_ASSEMBLY")

    result = dict(status="FAIL", started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  scope="Authenticated relocated native assembly only; no numerical or neural pipeline replay",
                  cas_q2_status="NOT READY", transport_sha256=args.transport_sha256)
    sys.addaudithook(audit)
    sys.setprofile(profile)
    try:
        try:
            platform_facts = platform.uname()._asdict()
        finally:
            bootstrap_active = False
        assert sum(e["event"] == "subprocess.Popen" for e in bootstrap_events) == 1
        assert sum(e["event"] == "nul_capability_open" for e in bootstrap_events) == 1
        result.update(platform_bootstrap=platform_facts, bootstrap_sources={str(p): h for p, h in bootstrap_sources.items()})
        import numpy as np
        loader = adapter.SourceLoader(files)
        original = roots["original"]
        for relative in adapter.SUPPORT_PATHS:
            loader.load(Path(relative).stem, original / relative)
        runtime_wrapper = loader.load("delivery_native_runtime", original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/native_runtime.py")
        runtime, runtime_nodes, boundary = runtime_wrapper.accepted()
        golden_runtime = json.loads(files.checked_physical(roots["engineering"] / "outputs/cas_q2/empirical_runtime_native_tests_v1/CPU_TEST_RESULT.json").read_text(encoding="utf-8"))
        assert runtime_nodes == golden_runtime["accepted_native_ast_nodes"]
        assert boundary == golden_runtime["generation_boundary"]
        wrapper = loader.load("delivery_native_base", original / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/native_base.py")
        native = wrapper.assemble()
        v2 = types.ModuleType("src.arbitration.v2_ensemble")
        v2.__dict__.update(np=np, dataclass=dataclass)
        sys.modules[v2.__name__] = v2
        names = {"V2_SCORE_FEATURES", "V2_LABELS", "V2_LAMBDA_DAMAGE", "V2_META_ALPHA", "V2_ACTION_RATE", "V2_GROUP_FOLDS",
                 "V2_GROUP_SEED", "V2EnsembleBundle", "empirical_cdf", "transition_utility", "score_unseen", "action_budget"}
        v2_nodes = wrapper.take(v2, "src/arbitration/v2_ensemble.py", names)
        loader.load("src.evaluation.answer_normalization", original / "src/evaluation/answer_normalization.py")
        loader.load("src.evaluation.fresh_schema", original / "src/evaluation/fresh_schema.py")
        scoring_nodes = native.source_definitions + v2_nodes
        golden_scoring = json.loads(files.checked_physical(roots["engineering"] / "outputs/cas_q2/empirical_saved_scoring_preflight_v2/CPU_PREFLIGHT.json").read_text(encoding="utf-8"))
        assert scoring_nodes == golden_scoring["native_ast_nodes"]
        assert not blocked and not science_calls
        assert len(optional_import_refusals) == 1
        assert not any(name == "pyarrow" or name.startswith("pyarrow.") for name in sys.modules)
        assert not any("ReliableRAG-neural-targets-v1" in p for p in sys.path)
        modules, packages = {}, {}
        for name, module in list(sys.modules.items()):
            path = getattr(module, "__file__", None)
            if isinstance(path, str) and not path.startswith("<"):
                p = Path(path).resolve()
                assert allowed(p), ("MODULE_OUTSIDE_DELIVERY", name, str(p))
                modules[name] = str(p)
            if name == "src" or name.startswith("src."):
                for path in getattr(module, "__path__", []):
                    assert Path(path).resolve().is_relative_to(original)
                packages[name] = list(getattr(module, "__path__", []))
        assert all(not Path(p).resolve().is_relative_to(Path("E:/paper/ReliableRAG")) for p in sys.path if p)
        files.verify_exact_fileset()
        result.update(status="PASS_RELOCATED_NATIVE_ASSEMBLY_ONLY", executable=sys.executable, prefix=sys.prefix, sys_path=sys.path,
                      original_runtime_ast_records=runtime_nodes, original_generation_boundary=boundary, original_scoring_ast_records=scoring_nodes,
                      supported_imports=loader.loaded, native_package_namespace_paths=packages, loaded_python_modules=modules,
                      copied_files_unchanged=len(config["files"]), original_metadata_rewritten=False,
                      observed_old_project_content_accesses=0, model_loads=0, neural_forwards=0, scientific_fits=0, fresh_outcome_values=0)
    except Exception as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc())
    finally:
        sys.setprofile(None)
    result.update(blocked_events=blocked, forbidden_scientific_calls=science_calls, bootstrap_events=bootstrap_events, optional_import_refusals=optional_import_refusals, opened_paths=sorted(opened),
                  finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with (out / "ASSEMBLY_RESULT.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2); stream.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "blocked_events", "forbidden_scientific_calls", "finished_utc")}))
    return 0 if result["status"] == "PASS_RELOCATED_NATIVE_ASSEMBLY_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
