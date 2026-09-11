# Neural inventory v2: preserve failure and complete inspection

Research Lead decision, 2026-09-11, before the second inventory run.
CAS Q2 STATUS: NOT READY. The original inventory contract remains unchanged.

The v1 run stopped after inspecting 35 distributions and authenticating 22
model assets. Its failure manifest is
`4b0d3a3662d5051fd4b2cbd6ed732e4ce65af0621324854403caff00b3328ec8`.
Keep the script, partial metadata and failure directory unchanged.

The platform-marker probe in CPython 3.10 on this Windows host calls
`platform.win32_ver`, which can invoke a read-only OS query. Preparing that
subprocess first opens the `nul` device. The inventory guard rejected that open
before the process could start. The diagnostic manifest is
`3240903795b5445e00b48845daf6c45f414272aed9de01f4ec58353d2ced3967`.
In v2, collect the platform-marker environment before enabling the existing
strict inventory guard, alongside the read-only device query. Record the marker
values; retain the guard against later processes, network, scientific imports
and writes outside the new output namespace. No scientific source changes.

The NumPy RECORD discrepancy is real, not a reason to change the expected hash.
For `numpy/distutils/__pycache__/conv_template.cpython-310.pyc`, the installed
RECORD has both an empty hash/size declaration and the official wheel's hashed
8,278-byte declaration. The current file is 8,284 bytes. The two bytecode files
have different embedded source paths. Both exactly match compilation of the
same official source using their respective embedded filenames; neither code
object was executed during diagnosis. This narrows the discrepancy but does
not make the installed bytes match RECORD or reconstruct installation history.
The follow-up diagnostic manifest is
`1070a0bd94c419836f04c23e672ecbd8585792955a8e428aa85bfaf68efc71cf`.

V2 records duplicate declarations and checks both nonempty size and digest
without stopping at the first discrepancy. It must retain every mismatch in
the result. Complete dependency, physical-file, model and source-path inventory
and post-inventory unchanged checks even if RECORD discrepancies remain. Such
a result is a completed inventory with reported issues, not a clean-environment
PASS. No original RECORD, cache, source, tolerance or pinned manifest is edited.
Only a later separate clean installation can establish a reconstructed neural
environment; do not repair the environment of the running C3 process.
