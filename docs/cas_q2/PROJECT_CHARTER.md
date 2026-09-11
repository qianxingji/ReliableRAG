# ReliableRAG project charter
Effective 2026-09-10, from the user's explicit project-goal update.

## Goal and authority

Deliver a paper competitive for a CAS Journal Ranking Q2 journal. This means the
Chinese Academy of Sciences journal partition, not JCR Q2. The previous CAS Q1
ambition is no longer a hard acceptance criterion. Verify the journal's year,
ISSN, major/minor category and institutional recognition rule before submission.

Work is Research Project Lead: priorities, research decisions, task contracts,
review and stage acceptance. ChatGPT pro 6 handles research/method/experiment
design and argument. Codex GPT-6 Astra implements reviewed designs, tests, runs
experiments and prepares PRs. These labels describe the agreed division of work;
this file does not claim that external model sessions have been started.

The user's current instructions supersede old goal text. Preserve historical
protocols and outcomes rather than changing their thresholds retrospectively.

## Scientific requirements

- A meaningful research question and a specific, evidenced contribution.
- Clearly distinguish the project, method, components, baselines and ablations.
- Competitive comparisons, including negative results and the strongest relevant controls.
- Match data, preprocessing, evaluation, tuning/label budgets and action budgets.
  Action-count matching does not establish retrieval/LLM/NLI cost equality.
- Keep all seeds and failures; no test-label tuning or selective publication.
- Trace each important number to commit/config/seed/environment/script/prediction.
- Match every claim to evidence from that exact method/version/population.
- Experiments are chosen for scientific need; do not mechanically add modules or seeds.

## Stage acceptance

Output exactly one overall status: `CAS Q2 STATUS: NOT READY` or
`CAS Q2 STATUS: SUBMISSION READY`. Technical integrity, numerical replay,
development support and submission readiness are separate judgments.

NOT READY reports must cover: leading rejection risk; missing core evidence;
method, baseline, experimental-completeness and argument issues; next priorities.
P0 blocks credible submission, P1 materially improves competitiveness, P2 is optional.

## Current decision

2026-09-11 latest execution state: the fixed-policy empirical replication
scientific design is frozen in EMPIRICAL_REPLICATION_PROTOCOL_V1.md. Five fixed
comparison models and the 6,000-question ID-only cohort passed independent
acceptance; see EMPIRICAL_AB_ACCEPTANCE.md and the separate sample-size prose
corrigendum. Stage C1's guarded native runtime projections and candidate pools
passed independent acceptance (EMPIRICAL_C1_ACCEPTANCE.md). C2 input availability
passed, but acquisition adapters, prelabel sealing and outcome analysis remain
pending. Total takeover fits: 178.
Both historical method-advancement failures remain unchanged.

The user confirmed that CAS partition year, institutional major/minor-category
recognition and target journal are undecided. Record them as pending, not as an
experimental blocker or a verified journal qualification.

Earlier post-control decision, retained as history:

2026-09-11 superseding execution state: saved-parameter replay passed and the
prespecified controls are complete. ROA-FULL's complexity criterion and the
subsequent minimal-fusion advancement criterion both failed. No final candidate
is cleared. Follow P0_3_RESEARCH_DECISION.md for the bounded research reassessment;
the earlier candidate rationale below is historical, not permission to ignore
these results or start confirmation.

Historical pre-control decision: keep ROA-FULL as the sole candidate pending contribution controls and final
confirmation. Its label is GBV_AUGMENTED_ONLY. Do not resume risk-gate, dual-head,
MILP or sibling searches without a new Research Lead design. Preserve V2's
failed primary comparison. The shortest credible next step uses cached scores.

Current overall status: **NOT READY**.
