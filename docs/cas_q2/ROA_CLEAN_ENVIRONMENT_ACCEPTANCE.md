# Fresh numerical-library installation and full replay accepted

Research Lead acceptance, 2026-09-11. **CAS Q2 STATUS: NOT READY.**

The original saved-parameter replayer now passes with independently installed
third-party numerical libraries. It no longer needs the original project's
`.venv` for numerical execution. The separately installed CPython 3.10.6 base
and current Windows host are still reused; this is not a new OS/CPython install,
another-host test or complete neural-pipeline environment.

The [prospective contract](ROA_CLEAN_ENVIRONMENT_CONTRACT.md) was committed at
`d58b439` before acquiring wheels or installing packages. Numerical source/data
remain the previously accepted source snapshot `73f8158` and original v2 release.
No scientific implementation, parameter, rank/action rule or tolerance changed.
Actual evidence: [ROA_CLEAN_ENVIRONMENT_RESULTS.json](ROA_CLEAN_ENVIRONMENT_RESULTS.json).

## Three separate observed gates

| Gate | Result |
|---|---|
| Official wheel acquisition | Five exact-version wheels, 63,378,499 bytes; published SHA-256 and size verified |
| Fresh offline installation | Local files only, binary/hash lock enforced, dependency check passed |
| Installed distributions | Five locked numerical packages plus bundled pip 22.2.1 / setuptools 63.2.0 |
| Package and numerical backend locations | New environment; user and system site packages disabled |
| Primary full replay | 28 contexts, 56 saved models, 38,424 prediction rows |
| Primary logit / probability / metric maximum errors | 0 / 0 / 0 |
| Changed action memberships | 0 |
| Independent full replay | 2,744,203 checks; maximum error 0 |
| Old `.venv` accesses observed by replay guards | 0 |
| Installed environment files unchanged | 5,214 files / 213,473,724 bytes |
| All authenticated inputs unchanged after replay | 12,017 files |

The new environment was created at
`E:/paper/ReliableRAG-numerical-environment-v1`, outside both projects. Actual
installation used `--no-index --require-hashes --only-binary=:all:` and a local
wheel directory. The pip installation report records five local file URLs;
package checks and imported module/backend paths were then verified. Torch is
absent, and no GPU work or neural inference was performed by this stage.

The fixed [hash lock](../../requirements/roa-replay-win-cp310.lock) contains:

| Package | Version | Official version metadata |
|---|---|---|
| NumPy | 2.2.6 | [PyPI metadata](https://pypi.org/pypi/numpy/2.2.6/json) |
| SciPy | 1.15.3 | [PyPI metadata](https://pypi.org/pypi/scipy/1.15.3/json) |
| scikit-learn | 1.7.2 | [PyPI metadata](https://pypi.org/pypi/scikit-learn/1.7.2/json) |
| threadpoolctl | 3.6.0 | [PyPI metadata](https://pypi.org/pypi/threadpoolctl/3.6.0/json) |
| joblib | 1.5.3 | [PyPI metadata](https://pypi.org/pypi/joblib/1.5.3/json) |

The acquired metadata, selected-wheel records, complete wheel bytes, package
metadata/license copies and hashes are archived. The existing base interpreter
and bundled pip/setuptools wheels are separately recorded. Published wheel
hashes establish the acquired package bytes, not historical model-training
provenance. Numerical equivalence is established by the subsequent full replay.

## Reusable delivery and scope

Use [the offline runbook](ROA_OFFLINE_CPU_REPLAY_RUNBOOK.md). The private combined
kit is `ROA_REPLAY_OFFLINE_CPU_KIT_V1_PRIVATE.zip`: **123,569,624 bytes**, 72 outer
archive members, all re-read and hash-checked. It contains the previous complete
source/data review ZIP, official numerical and bootstrap wheels, installation
and complete replay evidence, acceptance scripts and contract/runbook copies.
The nested source/data review ZIP preserves the earlier failure records. The
original rejected archives and all source/data workspaces also remain intact.

External kit SHA-256:
`a336eac5c835d123091e8eb2fa32f68b4bfb3ccbc2d3de8b6670898288143f08`.

Accepted manifest pins:

- Official wheels:
  `bf30b0bf3d97156484f27005cc7b4435f3b5aac30f3281527ec56857149acdc1`.
- Offline installation:
  `2115a44cf582c515142ec8f76e135cb85f74e454a4604186cb732f4e4777a547`.
- Full new-environment replay:
  `44b87939aed4f39cf83e9d3907d476cd544765228fe6431b4b818d44be6dd9cf`.

No private archive, data, wheel or outcome was uploaded. The public repository
receives only the lock, curated results and documentation. Existing engineering
tests remain 151 / 149 pass / two Windows capability skips; no unnecessary suite
repeat or new synthetic test was substituted for the actual environment replay.

The unchanged replayer uses the original 1e-10 numeric gate, and both modes
passed with zero observed error. The existing Python open-event guard records
zero old-project/runtime fallback; it is not an OS sandbox. The original
numerical/control modules and replay wrapper remain byte-identical, with the
previously disclosed generic artifact-verifier Git LF/worktree CRLF distinction.

## Research still outstanding

At 08:44:58 UTC, C3's original process has 6,837/18,000 complete pairs and
20,512/54,000 generation receipts. This is a sequential, non-atomic newline-byte
snapshot, not complete runtime acceptance. All 41 frozen C3 source/config files
remain unchanged. New Gold reads remain zero and total scientific fits remain 178.

P0: complete canonical C3, its fixed replay and independent validation; execute
and accept C4 prelabel; run cost reconciliation and all four D stages; assess
the contribution from actual results. P1: full neural-pipeline environment,
absolute-path freeze portability, complete fresh-output delivery and honest
comparison/provenance scope. P2: no added model/feature/seed/budget search.

The leading rejection risks remain failed historical method-advancement rules,
no accepted novel-method candidate, incomplete fresh empirical findings and
seven missing original per-estimator fit-time ID/matrix receipts. This stage
does not fill those receipts, reconstruct original training, or eliminate
contamination limitations. CAS partition year, institutional rule and journal
remain user-undecided; no journal qualification or readiness is asserted.
