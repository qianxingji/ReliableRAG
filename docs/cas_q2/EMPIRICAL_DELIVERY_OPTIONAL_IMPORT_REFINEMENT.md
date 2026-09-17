# Preserve absent optional PyArrow during sklearn import

Research Lead refinement before the v4 probe, 2026-09-11.
CAS Q2 STATUS: NOT READY.

Preserve v3 failure manifest
`a2ce4b3ae879bfdc4d656fa5d6b14b0fe2a86bea64c32aa50995abe3543d2cb4`.
The explicit Windows metadata bootstrap succeeded, then sklearn.utils.fixes
probed optional PyArrow availability. PyArrow is deliberately in a separate
target directory, which this source-only process does not add to sys.path.
The audit hook's RuntimeError prevented sklearn's normal ImportError fallback.
No PyArrow code or data was loaded; the run still failed and remains a failure.

Version only the probe/controller. For exactly one top-level `import pyarrow`
availability probe from the authenticated sklearn.utils.fixes source, deny it
with ModuleNotFoundError(name='pyarrow') and record that denied optional probe
separately. This reproduces the absent optional package condition of this
isolated role; do not add its target path, import a replacement module or change
any package/scientific source. All other forbidden imports still fail the run.
Require no loaded pyarrow module, no optional target path, no data access and
exactly this one recorded availability refusal. The original file/read guard,
scientific-call guard and all golden comparisons remain unchanged.
