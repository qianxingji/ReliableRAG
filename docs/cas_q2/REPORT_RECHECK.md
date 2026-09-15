# ROA report arithmetic recheck — 2026-09-10

This is a new analysis of an existing report, not a new experiment or numerical
replay. The author's report SHA-256 is
`4090ec70c4a9154ecfc960c9c2bc26317b585d06cc308ee962a984e8981bbf6d`,
matching the pinned ROA manifest. No newer uploaded experimental artifacts or PR
results were available when this recheck began.

## What was checked

All 40 rows (5 methods x 5 repetitions, plus 5 methods x 3 LODO contexts) were
read from the exact report. Every row satisfies Actions=R+D+Neutral, Net=R-D,
and delta EM=100*Net/N. Each context has equal reported action counts across
methods. Printed EM uses nine decimals; the 1e-8 aggregate-arithmetic tolerance
only accommodates that formatting and does not change the 1e-10 model-replay
tolerance. F1 values were summarized as reported; they cannot be reconstructed
from the available counts alone.

## Five repetitions: mean ± sample standard deviation

All EM/F1 entries are **percentage-point improvements over Keep**, not absolute
accuracy. Every repetition reuses the same 4,500 questions / 13,500 traces.
Standard deviations describe split sensitivity, not independent samples or
confidence intervals. No hypothesis test or bootstrap was added.

| Method | Net | Damage | ΔEM pp | ΔF1 pp |
|---|---:|---:|---:|---:|
| GbV | 240.00 ± 3.39 | 15.80 ± 0.84 | 1.7778 ± 0.0251 | 2.2345 ± 0.0206 |
| HGB | 264.80 ± 2.77 | 19.00 ± 1.22 | 1.9615 ± 0.0206 | 2.3136 ± 0.0193 |
| ROA-FULL | 299.40 ± 4.62 | 13.00 ± 1.87 | 2.2178 ± 0.0342 | 2.7049 ± 0.0354 |
| ROA-NOGBV | 265.20 ± 5.07 | 27.80 ± 3.03 | 1.9644 ± 0.0376 | 2.3538 ± 0.0520 |
| V2, historical development context | 269.40 ± 5.41 | 22.60 ± 1.34 | 1.9956 ± 0.0401 | 2.3715 ± 0.0311 |

Differences are paired by repetition before calculating their standard deviation:

| ROA-FULL minus comparator | ΔEM pp | ΔF1 pp | Damage difference |
|---|---:|---:|---:|
| GbV | 0.4400 ± 0.0411 | 0.4703 ± 0.0351 | -2.80 ± 1.79 |
| HGB | 0.2563 ± 0.0470 | 0.3912 ± 0.0463 | -6.00 ± 1.87 |
| ROA-NOGBV | 0.2533 ± 0.0253 | 0.3510 ± 0.0364 | -14.80 ± 2.68 |

HGB is a stronger raw ranking comparator than GbV on mean EM/F1 here, while
GbV has fewer damage events; there is no single metric-independent winner.
ROA-NOGBV's mean Net is almost identical to HGB's and its Damage is higher.
The dependence ablation does not support independent replacement of GbV.

## LODO limitations that must remain visible

| Held-out dataset | FULL−HGB EM pp | FULL−GbV EM pp | FULL / HGB / GbV Damage |
|---|---:|---:|---:|
| MuSiQue | +0.1333 | +0.1111 | 3 / 1 / 1 |
| 2WikiMultiHopQA | -0.0444 | +0.3778 | 9 / 10 / 12 |
| HotpotQA | +0.3333 | +0.4444 | 3 / 8 / 2 |

FULL is not uniformly better than HGB on EM and does not uniformly avoid extra
damage relative to GbV. These are observed counts, not established differences
in population risk. LODO operates on the already opened cohort. It tests
transport of the top-level recovery fit, conditional on frozen upstream scores;
full-system unseen-domain generalization additionally requires upstream training
provenance. Retain the existing development decision without retrospectively
tightening or relaxing its thresholds.

The original report also records zero calibration strict-order changes in 56
jobs. It does not establish that Platt calibration improves top-K action quality.
Similarly, a 5% answer-switch cap does not imply a 95% reduction in retrieval,
generation or verifier cost: constructing the candidate pairs and scores has
already incurred upstream work.

## Research Lead decision

Keep ROA-FULL pending the two frozen supervised controls. Do not add more seeds,
risk heads, MILP searches or calibration variants to these opened development
results. The high-value unresolved question is the necessity of the full score
stack relative to supervised GbV alone and HGB+GbV. Fresh confirmation is still
a P0 submission prerequisite after the candidate and design are fixed.

Reproduce this report summary on the original machine:

```powershell
python -m scripts.summarize_roa_report --report E:/paper/ReliableRAG/outputs/daa_v3_development/recovery_only_isolation_v1/AUTHOR_REPORT.md
```

Machine-readable derived numbers: [REPORT_RECHECK.json](REPORT_RECHECK.json).
The source report and original predictions remain separate private artifacts.
**CAS Q2 STATUS: NOT READY.**
