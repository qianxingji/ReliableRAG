# C1 Windows metadata correction before any fresh projection

The first C1 attempt at commit e8d5d9de8e657a18bd59279c9e27d85d1a853616
failed before EXECUTABLE_FREEZE.json or any runtime/pool row was written.
Its output-only guard rejected an open of the Windows NUL device during
platform.platform() metadata collection. The original failure receipt and
execution manifest remain at outputs/cas_q2/empirical_candidate_pool_v1.

Do not relax the guard. The v2 executor replaces that metadata query with
sys.platform and sys.getwindowsversion(), which need no external process/device
open. The frozen C1 protocol otherwise remains unchanged. The v2 namespace is
outputs/cas_q2/empirical_candidate_pool_v2. Source/cohort/model/statistical
parameters and all selected IDs are identical. This is an infrastructure retry,
not another scientific draw or fit. Preserve the v1 source and output bytes.

The v2 validator calls the unchanged independent validator with only its output
directory rebound. The v2 freeze records both core and wrapper sources and this
correction before projection. The failed attempt performed no projection, model
inference, fitting or outcome evaluation. CAS Q2 STATUS: NOT READY.
