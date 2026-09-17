"""Single-use D execution lifecycle with authenticated and decoded inputs split."""
import datetime
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from scripts.empirical_outcome_stage_io import STAGES, STATUSES, prerequisites, inputs
from scripts.empirical_outcome_guard_v2 import guard
from scripts.empirical_pool_io import REPO, load, record, require
from scripts.empirical_retrieval_io import configure_environment, boundary_record, seal
from scripts.replay_roa_original import write_json


class OutcomeRun:
    def __init__(self, root, stage, pins):
        self.root, self.stage, self.pins = Path(root).resolve(), stage, pins
        self.out = STAGES[stage]
        require(not self.out.exists(), "Single-use D execution namespace")
        require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "Commit D executable sources first")
        self.commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        prior = prerequisites(stage, pins)
        self.audit, self.paths, self.readable = inputs(self.root, stage, prior)
        self.paths.append(Path(sys.executable))
        self.out.mkdir(parents=True, exist_ok=False)
        self.started, self.boundary, self.records = time.perf_counter(), None, []
        self.phase = dict(stage="setup", completed_rows=0)
        self.result = dict(status="FAIL", cas_q2_status="NOT READY", source_commit=self.commit, stage=stage,
            scientific_fit_calls=0, neural_model_loads=0, model_forward_calls=0, new_retrieval_calls=0, new_generation_calls=0,
            raw_reference_strings_materialized=0, numeric_outcome_rows_read=0, predecessor_manifests=pins)

    def prepare(self):
        environment = configure_environment(self.out)
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        self.spec = load(self.root / "outputs/daa_v2_fresh_v1/final_evaluation/preflight/MAPPING_INPUT_SPEC.json")
        from scripts.empirical_outcome_native import native
        self.metric, self.Cursor, self.readers, definitions = native(self.root, self.spec)
        import numpy as np
        from threadpoolctl import threadpool_info
        threadpool_info()
        metadata = platform.uname()._asdict()
        original = self.audit["original_environment"]
        require(sys.version == original["python"] and np.__version__ == original["numpy"], "Original D interpreter/NumPy versions")
        self.parquet = None
        if self.stage in {"mapping", "outcome_validation"}:
            package = self.root / "tmp/daa_v2_hotpot_full_column_reader"
            sys.path.insert(0, str(package))
            import pyarrow
            import pyarrow.parquet as pq
            require(Path(pyarrow.__file__).resolve() == package / "pyarrow/__init__.py" and
                pyarrow.__version__ == original["pyarrow"] == "20.0.0", "Original pinned selected-column reader")
            self.parquet = pq
        self.records = [record(p) for p in sorted(set(self.paths))]
        write_json(self.out / "EXECUTABLE_FREEZE.json", dict(source_commit=self.commit, stage=self.stage, command=sys.argv,
            started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), inputs=self.records,
            decoded_input_paths=[str(p) for p in self.readable], predecessor_manifests=self.pins, environment=environment,
            platform_metadata=metadata, python=sys.version, numpy_version=np.__version__, native_definition_hashes=definitions))
        self.boundary = guard(self.root, self.out, self.paths, mode=self.stage, readable_paths=self.readable)

    def start_gold(self):
        require(self.stage in {"mapping", "outcome_validation"} and self.boundary is not None, "Only guarded accepted method-blind process may map Gold")
        write_json(self.out / "GOLD_ACCESS_STARTED.json", dict(prelabel_manifest=self.pins["prelabel"],
            selected_question_count=6000, method_inputs_decodable=False, reread_for_independent_validation=self.stage == "outcome_validation"))
        self.result.update(raw_reference_strings_materialized=None, selected_question_labels_materialized=None,
            gold_access_started=True, partial_failure_access_count_policy="Unknown until the selected-reference reader returns; never report zero after a failed partial read")

    def error(self, exc):
        frames, tb = [], exc.__traceback__
        while tb:
            frames.append(dict(file=tb.tb_frame.f_code.co_filename, line=tb.tb_lineno, function=tb.tb_frame.f_code.co_name))
            tb = tb.tb_next
        self.result.update(status="FAIL", error_type=type(exc).__name__, diagnostic="DETAILS_WITHHELD_TO_PREVENT_REFERENCE_TEXT_LOGGING", code_locations=frames)
        if isinstance(exc, OSError) and exc.filename:
            self.result["filesystem_path"] = str(exc.filename)

    def finish(self, *, success=False, independent=None):
        try:
            if success:
                for entry in self.records:
                    require(record(Path(entry["path"])) == entry, "D source/input changed during execution")
                require(self.boundary is not None and not self.boundary["denied"] and self.boundary["forbidden_calls"] == 0, "Clean complete D execution boundary")
                if independent is not None:
                    require(self.stage in {"outcome_validation", "analysis_validation"}, "Separate independent D report")
                    write_json(self.out / "INDEPENDENT_VALIDATION.json", independent)
                    write_json(self.out / "SEAL.json", dict(status=STATUSES[self.stage], predecessor_manifests=self.pins,
                        independent_sha256=record(self.out / "INDEPENDENT_VALIDATION.json")["sha256"],
                        cas_q2_status="NOT READY", source_inputs_unchanged=True))
                self.result.update(status=STATUSES[self.stage], source_inputs_unchanged=True)
        except Exception as exc:
            self.error(exc)
        finally:
            sys.setprofile(None)
        if self.boundary is not None:
            self.result["boundary"] = boundary_record(self.boundary)
        self.result.update(phase=self.phase, elapsed_seconds=time.perf_counter()-self.started,
            completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        write_json(self.out / "BUILD_RECEIPT.json", self.result)
        seal(self.out)
        print(self.result["status"], flush=True)
        return 2 if self.result["status"] == "FAIL" else 0
