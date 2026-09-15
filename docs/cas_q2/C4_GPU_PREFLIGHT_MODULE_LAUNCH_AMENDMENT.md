# C4 GPU preflight module-launch amendment

CAS Q2 STATUS: **NOT READY**. Frozen prospectively on 2026-09-12 after the
pre-config launch failure and before any C4 model load or forward.

## Preserved failure

The first C4 GPU-preflight command invoked
`scripts/preflight_roa_empirical_scoring_gpu.py` as a file. Python therefore
placed the script directory, rather than the repository root, at `sys.path[0]`.
The entry failed on its first repository import with
`ModuleNotFoundError: No module named 'scripts'`.

The failure happened before argument parsing, `StageRun` construction,
configuration or benchmark reads, output-namespace creation, model loading,
CUDA initialization, forward calls, fitting or Gold access. Its external task
manifest is
`98ddd984d9e1de5f8d36a1eb52d767a8116806ab58c0341bfbe2c8b21e687471`.
The failed command and stderr remain immutable.

## Frozen correction

Run the existing source as a module from the exact engineering repository root:

```powershell
& 'E:\paper\ReliableRAG\.venv\Scripts\python.exe' -B -X utf8 `
  -m scripts.preflight_roa_empirical_scoring_gpu `
  --project-root 'E:\paper\ReliableRAG' `
  --runtime-manifest-sha256 dc2905224798b07302db8950f68db228de1faff9042c44dbaee7111ba107878f
```

This correction changes only Python's repository-package bootstrap. The module,
scientific helpers, C3 predecessor, invented fixtures, models, revisions,
precision, seed, batch sizes, numerical checks, counters and single-use output
namespace remain those already frozen by the C4 contracts. The entry's `--help`
path was executed successfully with this module form before the corrected
scientific launch; it creates no output and loads no model.

The corrected command may run only from a clean committed checkout. If it
creates `empirical_scoring_gpu_preflight_v1`, that directory is single use and
must be accepted or retained as failed. No further launch correction is implied.

