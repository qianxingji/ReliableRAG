"""V3.1 environment binding with one NumPy target and frozen auxiliary pools."""
import hashlib
import os
from pathlib import Path

from scripts.empirical_validation_binding_v2 import (EXPECTED_CONSTANTS, V2ValidationBindings,
    constant_assignments, dependency_inventory, source_record)
from scripts.empirical_validation_length import require

THREAD_VARIABLES = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
POOL_FIELDS = ("user_api", "internal_api", "num_threads", "version", "threading_layer", "architecture")


def _pool_path(pool):
    return Path(pool["filepath"]).resolve()


def _validate_identity(pool, expected, reason):
    require(all(pool.get(field) == expected.get(field) for field in POOL_FIELDS), reason)
    path = _pool_path(pool)
    require(path == Path(expected["path"]).resolve(), reason)
    require(path.stat().st_size == expected["size_bytes"] and
            hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"], reason)


def validate_native_default(pools, target, auxiliary, numpy_version, environment, phase):
    """Pure fail-closed validation for the frozen V3.1 numerical runtime."""
    require(phase in {"start", "end"}, "V3_1_PHASE")
    require(all(name not in environment for name in THREAD_VARIABLES), "V3_1_THREAD_OVERRIDES_MUST_BE_ABSENT")
    require(numpy_version == "2.2.6", "V3_1_NUMPY_VERSION")
    target_path = Path(target["path"]).resolve()
    target_pools = [pool for pool in pools if _pool_path(pool) == target_path]
    require(len(target_pools) == 1, "V3_1_EXACTLY_ONE_TARGET_NUMPY_BLAS_POOL")
    _validate_identity(target_pools[0], target, "V3_1_TARGET_NUMPY_BLAS_IDENTITY")
    other = [pool for pool in pools if _pool_path(pool) != target_path]
    if phase == "start":
        require(not other, "V3_1_AUXILIARY_POOL_AT_START")
    else:
        expected_by_path = {Path(item["path"]).resolve(): item for item in auxiliary}
        require(len(expected_by_path) == len(auxiliary), "V3_1_DUPLICATE_AUXILIARY_EXPECTATION")
        actual_by_path = {_pool_path(item): item for item in other}
        require(len(actual_by_path) == len(other) and set(actual_by_path) == set(expected_by_path),
                "V3_1_AUXILIARY_POOL_SET")
        for path, expected in expected_by_path.items():
            _validate_identity(actual_by_path[path], expected, "V3_1_AUXILIARY_POOL_IDENTITY")
    return {"phase": phase, "thread_environment": {name: None for name in THREAD_VARIABLES},
            "numpy_version": numpy_version, "target_numpy_blas_pool": target_pools[0],
            "auxiliary_threadpools": other, "target_dll_sha256": target["sha256"]}


def observe_native_default(config, phase):
    import numpy as np
    from threadpoolctl import threadpool_info
    return validate_native_default(threadpool_info(), config["v3_blas"], config["v3_auxiliary_pools"],
        np.__version__, os.environ, phase)


class V31ValidationBindings(V2ValidationBindings):
    """Record the corrected start/end numerical runtime without scientific changes."""
    def __init__(self, native, frozen, payloads, *, environment_start, **kwargs):
        super().__init__(native, frozen, payloads, **kwargs)
        self.environment_start = environment_start

    def binding_receipt(self):
        value = super().binding_receipt()
        value.update(binding_version="V3_1_NUMPY_TARGET_AND_FROZEN_AUXILIARIES",
            environment_start=self.environment_start,
            environment_end=observe_native_default(self.frozen, "end"),
            census_task_manifest_sha256=self.frozen["census_task_manifest_sha256"],
            census_client_audit_manifest_sha256=self.frozen["census_client_audit_manifest_sha256"],
            environment_anomaly_audit_manifest_sha256=self.frozen["environment_anomaly_audit_manifest_sha256"],
            v2_literal_failure_preserved=True, v3_fixture_failures_preserved=2,
            scientific_checks_thresholds_helpers_and_comparisons_changed=False)
        value["entry_bindings"].insert(0,
            "execution environment: exact NumPy target at both boundaries and exact frozen auxiliary set at end")
        return value
