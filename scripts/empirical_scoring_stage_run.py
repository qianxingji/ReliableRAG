"""Shared execution lifecycle; scientific loops remain explicit per stage."""
import importlib.metadata
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from scripts.empirical_scoring_stage_io import REPO, STAGES, stage_prerequisites, bound_inputs, record, require
from scripts.empirical_scoring_stage_guard import guard
from scripts.empirical_retrieval_io import configure_environment, boundary_record, seal
from scripts.replay_roa_original import write_json


class StageRun:
    def __init__(self, root, stage, pins):
        self.root, self.stage, self.pins = Path(root).resolve(), stage, pins
        self.out = STAGES[stage]
        require(not self.out.exists(), "Single-use C4 execution namespace")
        require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit C4 execution first")
        self.commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        prior = stage_prerequisites(stage, pins)
        self.audit, self.pre, self.paths, self.context = bound_inputs(self.root, stage, pins, prior)
        self.paths.append(Path(sys.executable))
        self.out.mkdir(parents=True, exist_ok=False)
        self.boundary, self.records, self.phase = None, [], dict(stage="setup", position=None)
        self.started = time.perf_counter()
        self.result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=self.commit, stage=stage,
            scientific_fit_calls=0, answer_generation_calls=0, new_retrieval_calls=0, fresh_gold_values_materialized=0)

    def prepare(self):
        environment = configure_environment(self.out)
        extra = dict(HF_HUB_CACHE=str(self.out / "cache/hf/hub"), HUGGINGFACE_HUB_CACHE=str(self.out / "cache/hf/hub"))
        os.environ.update(extra)
        environment.update(extra)
        package_root = self.root / "outputs/published_baseline_gbv_nli_v1/infrastructure/python_packages"
        sys.path.insert(0, str(package_root))
        # Authenticated libraries/metadata only; no pretrained model is loaded here.
        import torch
        import transformers
        import sentencepiece
        import joblib
        import sklearn.ensemble, sklearn.linear_model, sklearn.pipeline, sklearn.preprocessing
        from threadpoolctl import threadpool_info
        from transformers import AutoModel, AutoModelForCausalLM, AutoModelForSequenceClassification, AutoTokenizer
        platform_metadata = platform.uname()._asdict()
        threadpool_info()
        joblib.cpu_count(only_physical_cores=True)
        require(Path(sentencepiece.__file__).resolve() == package_root / "sentencepiece/__init__.py" and
            sentencepiece.__version__ == "0.2.1", "Authenticated native SentencePiece package")
        versions = {name: importlib.metadata.version(name) for name in self.pre["environment"]["versions"]}
        require(versions == self.pre["environment"]["versions"], "Original scoring package versions")
        if self.stage not in {"policies", "independent"}:
            require(torch.cuda.is_available(), "No scoring CPU fallback")
            torch.cuda.init()
            torch.cuda.reset_peak_memory_stats()
        self.records = [record(p) for p in sorted(set(self.paths))]
        write_json(self.out / "EXECUTABLE_FREEZE.json", dict(source_commit=self.commit, stage=self.stage,
            command=sys.argv, inputs=self.records, environment=environment, platform_metadata=platform_metadata,
            versions=versions, sentencepiece_version=sentencepiece.__version__, predecessor_manifests=self.pins,
            runtime_context=self.context, fresh_outcome_access_authorized=False))
        self.boundary = guard(self.root, self.out, self.paths, stage=self.stage)

    def error(self, exc):
        frames, tb = [], exc.__traceback__
        while tb:
            frames.append(dict(file=tb.tb_frame.f_code.co_filename, line=tb.tb_lineno, function=tb.tb_frame.f_code.co_name))
            tb = tb.tb_next
        self.result.update(status="FAIL", error_type=type(exc).__name__, diagnostic=str(exc), code_locations=frames)

    def finish(self, success_status=None, *, acceptance=None):
        try:
            if success_status is not None:
                for entry in self.records:
                    require(record(Path(entry["path"])) == entry, "C4 source/input changed during execution")
                require(self.boundary is not None and not self.boundary["denied"], "Complete C4 scientific boundary")
                if acceptance is not None:
                    require(self.stage == "independent", "Separate independent acceptance output")
                    write_json(self.out / "INDEPENDENT_VALIDATION.json", acceptance)
                    write_json(self.out / "SEAL.json", dict(status=success_status, predecessor_manifests=self.pins,
                        independent_sha256=record(self.out / "INDEPENDENT_VALIDATION.json")["sha256"],
                        scientific_fit_calls=0, model_forward_calls=0, fresh_gold_values_materialized=0,
                        scope="Complete frozen prelabel only; no outcome analysis or submission readiness"))
                self.result.update(status=success_status, source_inputs_unchanged=True)
        except Exception as exc:
            self.error(exc)
        finally:
            sys.setprofile(None)
        if self.boundary is not None:
            self.result["execution_boundary"] = boundary_record(self.boundary)
        self.result.update(phase=self.phase, elapsed_seconds=time.perf_counter() - self.started)
        write_json(self.out / "BUILD_RECEIPT.json", self.result)
        seal(self.out)
        print(self.result["status"], self.result.get("diagnostic", ""), flush=True)
        return 2 if self.result["status"] == "FAIL" else 0
