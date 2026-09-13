"""Prospective V3 environment binding over the accepted V2 validation adapter."""
import hashlib
import os
from pathlib import Path

from scripts.empirical_validation_binding_v2 import (EXPECTED_CONSTANTS, V2ValidationBindings,
    constant_assignments, dependency_inventory, source_record)
from scripts.empirical_validation_length import require

THREAD_VARIABLES = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")


def validate_native_default(pools, expected, numpy_version, environment):
    """Pure validation surface used by production and invented negatives."""
    require(all(name not in environment for name in THREAD_VARIABLES), "V3_THREAD_OVERRIDES_MUST_BE_ABSENT")
    require(numpy_version == "2.2.6", "V3_NUMPY_VERSION")
    blas_pools = [pool for pool in pools if pool.get("user_api") == "blas"]
    non_blas_pools = [pool for pool in pools if pool.get("user_api") != "blas"]
    require(len(blas_pools) == 1, "V3_EXACTLY_ONE_BLAS_POOL")
    pool = blas_pools[0]
    require(pool.get("internal_api") == "openblas", "V3_OPENBLAS_REQUIRED")
    require(pool.get("num_threads") == 12, "V3_EXACTLY_TWELVE_THREADS")
    require(pool.get("version") == "0.3.29", "V3_OPENBLAS_VERSION")
    require(pool.get("architecture") == "SkylakeX", "V3_OPENBLAS_ARCHITECTURE")
    require(pool.get("threading_layer") == "pthreads", "V3_OPENBLAS_THREADING_LAYER")
    path = Path(pool["filepath"]).resolve()
    require(path == Path(expected["path"]).resolve(), "V3_OPENBLAS_DLL_PATH")
    require(path.stat().st_size == expected["size_bytes"] and hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"],
            "V3_OPENBLAS_DLL_BYTES")
    return {"thread_environment": {name: None for name in THREAD_VARIABLES}, "numpy_version": numpy_version,
            "threadpools": blas_pools, "non_blas_threadpools": non_blas_pools,
            "dll_sha256": expected["sha256"]}


def observe_native_default(config):
    """Require the one census-supported global numerical execution mode."""
    import numpy as np
    from threadpoolctl import threadpool_info
    result = validate_native_default(threadpool_info(), config["v3_blas"], np.__version__, os.environ)
    result["numpy_version"] = np.__version__
    return result


class V3ValidationBindings(V2ValidationBindings):
    """Record start/end identity without changing any scientific helper."""
    def __init__(self, native, frozen, payloads, *, environment_start, **kwargs):
        super().__init__(native, frozen, payloads, **kwargs)
        self.environment_start = environment_start

    def binding_receipt(self):
        value = super().binding_receipt()
        value.update(binding_version="V3_NATIVE_DEFAULT_ENVIRONMENT",
            environment_start=self.environment_start,
            environment_end=observe_native_default(self.frozen),
            census_task_manifest_sha256=self.frozen["census_task_manifest_sha256"],
            census_client_audit_manifest_sha256=self.frozen["census_client_audit_manifest_sha256"],
            v2_literal_failure_preserved=True,
            scientific_checks_thresholds_helpers_and_comparisons_changed=False)
        value["entry_bindings"].insert(0, "execution environment: absent thread overrides and exact authenticated current native-default 12-thread BLAS")
        return value
