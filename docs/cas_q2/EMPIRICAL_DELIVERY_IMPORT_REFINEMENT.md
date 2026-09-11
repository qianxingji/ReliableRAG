# Preserve the original support import topology

Research Lead correction before the v2 assembly run, 2026-09-11.
CAS Q2 STATUS: NOT READY.

The first adapter and guarded process, committed at b99e506, failed before native
assembly with `Original import utility missing`. Preserve the complete v1
namespace and failure manifest
`0225eb7c633088a370c92f15999f174fc768c124fae54f6e1d886106e2ff451b`.
No model, fit, forward or fresh outcome was accessed; no access-guard event
was recorded. This is an adapter implementation error, not a scientific failure.

AST inspection of the three previously pinned, unchanged support files shows
that retrieval_support defines no import_file, whereas runtime_support and
v3_support each define one. The original design's import replacement applies
only to those existing functions. Version the adapter and probe separately;
leave v1 source and evidence untouched.

For retrieval_support require import_file to remain absent, rebind the six
approved Path globals, and preserve every other global object. For the other
two modules require the existing import_file function and replace only that
function plus their declared Path globals. Reject an unexpected import helper
presence/absence before mutation. No synthetic helper is added to retrieval.
All original source hashes, 21 Path bindings, scientific definitions and golden
AST/boundary comparisons remain unchanged. Add direct tests for absence and
unexpected presence, then run the two fresh relocated processes under the
same source-only/CPU boundary. A PASS still means assembly only.
