# CPU smoke refinement: one authenticated local IPv6 capability probe

Research Lead decision, 2026-09-11, before the revised smoke process.
CAS Q2 STATUS: NOT READY.

The offline installation and independent official-payload/RECORD checks passed,
but the first combined acceptance failed because its import guard recorded a
socket bind. Preserve the installation directory and failure manifest
`6f31eabcdaf4e1ddb286cf72736806595f8f82d506d164d099cf712e90a1a09b`.
Do not reinstall or alter its 21,267 frozen files.

A separate diagnostic retained the guard and reproduced the call during
Transformers import, through Requests/urllib3. Diagnostic manifest:
`7d2d7d18854ddc929a8d8199be4e99786153b58bcc7f7b6c0a7f2695d7205777`.
The authenticated `urllib3/util/connection.py` source has SHA-256
`2633bbdb69731e5ccb5cf4e4afd65605d86c7979cc5633126f50c92d5ad74a74`.
Its `_has_ipv6("::1")` creates an IPv6 socket, attempts to bind the local loopback
address at port zero, and closes the socket. It does not listen, connect, resolve
a remote host or transfer application data. The original guard's exception was
caught by this capability test, and the final no-blocked-events check correctly
kept the acceptance failed despite successful CPU fixtures.

In a new v2 smoke namespace, permit at most one such bind only when the address
is exactly `("::1", 0)`, socket family/type are IPv6/stream, and the direct caller
is the `_has_ipv6` function object in the authenticated urllib3 module at its
new-environment path. Record that capability event separately and require the
socket to be closed after import. Keep all connects, DNS requests, other binds,
HTTP requests and later subprocesses denied. Do not change urllib3, any other
installed package, the original smoke result, hashes or scientific thresholds.
Retain the same CPU fixtures and no-CUDA/no-pretrained-model conditions.

Before the revised probe, independently rehash the existing installed file set
against its pre-smoke freeze and authenticate all accepted payload/installation
receipts. Afterward recheck all installed files, the original 30,823 environment
files and frozen installation inputs. A new PASS is limited to offline package
installation plus bounded CPU import/binary checks with a recorded local IPv6
capability probe. It is not an assertion that the first process passed, that no
socket call occurred, or that CUDA/pretrained-pipeline replay has been tested.
