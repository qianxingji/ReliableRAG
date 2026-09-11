# Declare the Windows platform metadata bootstrap

Research Lead refinement before the v3 assembly run, 2026-09-11.
CAS Q2 STATUS: NOT READY.

Preserve v2 failure manifest
`9dd2b9a5fb458172cdd629f7cf2f07d1cf94137567da2e21cd1cd380161d3d64`.
The corrected import topology passed original retrieval/reader assembly and all
46 AST records plus the unchanged generation boundary. Base assembly then
imported sklearn -> SciPy -> NumPy testing -> platform.machine. CPython 3.10.6's
platform.uname requests Windows version through _syscmd_ver; the strict guard
rejected its NUL-device open before a subprocess started. No scientific call
or fresh outcome access occurred. Do not relabel the failed run as a PASS.

Version only the probe/controller; keep the 13-test-accepted v2 path adapter,
original support files and scientific sources unchanged. Before installing the
strict assembly guard, explicitly warm the standard platform.uname cache and
record the returned OS metadata. Apply a separate bootstrap audit: allow only
the authenticated base-Python platform._syscmd_ver call to System32/cmd.exe
with the exact `ver` command, at most once. The NUL open must be the stock
subprocess._get_devnull call in that same platform query. Record both events
and source hashes; deny other subprocesses, network, old-project content reads
and filesystem writes. There is no scientific import/execution in this phase.
After metadata bootstrap, disable those two exceptions and retain the original
strict source/config-only assembly guard without widening its permissions.

This explicit bootstrap is OS inventory, not an algorithm adaptation or model
forward. Both relocated roots still need complete original AST/boundary checks,
unchanged file sets and source/environment post-hashes. All prior limitations
and the P0 stage sequence remain in force.
