# Client Lead acceptance: fixed empirical panel and fresh ID cohort

2026-09-11. **CAS Q2 STATUS: NOT READY.**

The scientific replication design was frozen at 0c18a9c before its new model
fits and sample selection. It is a fixed-policy attribution/tradeoff study,
not a claim that either failed novel-method advancement rule now passes.

Stage A is accepted under EMPIRICAL_PANEL_ACCEPTANCE.md: five separate fixed
base/Platt model bundles, ten new scientific fits, 178 total takeover fits;
3,600 training and 900 calibration questions; 57,388 independent checks over
16,010 probe predictions, maximum numeric error 0. The probe is explicitly
overlapping development data; no performance metrics or model selection used it.

Stage B code was committed at 8bf2da8 before one positive selection. Exactly
2,000 questions from each of HotpotQA, 2Wiki and MuSiQue were selected in the
frozen hash order. The 6,000-question cohort has zero dataset/ID overlap with
the known 18,600-question exclusion union. It implies 18,000 eventual retriever
traces. Independent reconstruction passed all 111 checks, including order,
source/exclusion hashes and the six endpoint planning calculations.

Stage B manifest SHA-256:
6070c63b9cbf3277ef328d059dcaabc98480ba2bb60503b66ad2faa5e816b62a.
No fresh runtime text was projected, no inference ran and no fresh Gold/outcome
was decoded during A/B. ID-level exclusion does not prove semantic deduplication,
absence of unlogged use, or pretraining decontamination.

Accept the **actual fixed 2,000-per-dataset selection and planning numbers**
with the explicit prose correction in EMPIRICAL_SAMPLE_SIZE_CORRIGENDUM.md.
The original claim about the largest multiple of 100 was wrong. No frozen
artifact or chosen ID is changed to hide this error.

The conservative planning sensitivity (worst development SD among all five
repetitions, sqrt(4500/6000) scaling, Bonferroni six-endpoint normal approximation)
has EM half-widths about 0.178/0.239/0.198 pp for FULL–fusion / fusion–HGB-only /
fusion–GbV-only; with 1.5x uncertainty inflation these become 0.268/0.358/0.297 pp.
These are assumptions for planning, not achieved fresh precision or promised
power. In particular, they do not justify claiming equivalence of FULL/fusion.

## Next executable work

Implement the stage C adapters in bounded substeps: value-blind projection/pool
preflight and construction; retrieval; candidate generation; frozen score
extraction; then fixed-model scoring and prelabel action sealing. Reuse exact
authenticated native scientific functions and retain new namespaces, failed
attempts and all inputs. The current old V2 executors have hardcoded cohort
sizes, roots and write destinations, so they must not be run as-is.

Fresh outcome mapping remains behind independently accepted complete prelabel
seals. The full scientific protocol is frozen; the stage C/D engineering input
freezes and implementations are not yet complete. Do not call their absence
external approval waiting. The client Lead continues to own acceptance.

P0: actual fresh replication and a sufficient contribution remain missing;
upstream historical training receipts, journal CAS identity/year/category and
institutional recognition remain unresolved. P1: faithful external comparisons,
cost and public release quality; a justified extra replication axis if claims
require it. P2: no automatic model/feature/seed/budget search. Nothing here
certifies Submission Ready or clears a novel-method deployment recommendation.
