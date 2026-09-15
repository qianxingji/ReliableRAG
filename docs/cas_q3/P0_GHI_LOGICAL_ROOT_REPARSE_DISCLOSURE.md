# P0-G/H/I logical-root reparse-scope disclosure

Decision: **CORRIGENDUM_LOGICAL_ROOT_SCAN_INCLUDED_DISCLOSED_EXTERNAL_JUNCTION_TARGET_NO_GATE_CLOSURE**.

**CAS Q3 STATUS: NOT READY.**

The 2026-09-14 and 2026-09-15 external-evidence scripts traverse each declared
directory with Python `os.walk`, resolve each reached file and deduplicate the
resolved path. On this Windows host, the logical path
`outputs/published_baseline_gbv_nli_v1/implementation/node_modules` is a junction
to the shared Codex primary-runtime dependency cache under `%USERPROFILE%`.
`os.walk` followed that junction even though ordinary symbolic-link following
was not requested.

The later image audit quantified the effect over the same three root arguments:
465,460 ordinary logical paths were visited, of which 7,796 resolve outside the
three declared physical roots. Those outside-resolved files include 34 common-
raster occurrences and 29 unique image hashes. The image audit labels this
scope explicitly in its machine result.

This corrects the earlier prose boundary: the recorded counts describe the
three logical roots **plus the one junction-reached shared-runtime target**, not
three physically self-contained directories. The target is host-local and may
change independently, so exact whole-scan counts are not portable evidence.

The scope expansion does not reverse the bounded negative candidate result.
The earlier searches completed over a superset without a read error, and the
three retained marker matches are project experimental-partition reports rather
than files from the shared runtime. Searching additional unrelated runtime files
cannot hide a matching file already traversed under the declared roots. It does,
however, require the expanded scope and portability limit to be disclosed rather
than silently attributed to the physical roots.

The prior scripts, JSON receipts and acceptance records remain unchanged as
historical evidence. Future external-root audits must either prune resolved paths
outside the declared physical roots or report their counts and role explicitly.
This corrigendum recovers no institutional record, closes no P0 gate and
authorizes neither submission nor distribution.
