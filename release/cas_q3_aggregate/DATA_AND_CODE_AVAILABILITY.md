# Data and code availability boundary

This release candidate contains only reviewer-safe aggregate evidence and the
code needed to authenticate and check its reporting layer.

Included:

- aggregate point estimates and interval summaries;
- the aggregate manifest from the sealed analysis stage;
- the reporting verifier;
- the frozen statistical source inspected by that verifier; and
- self-contained scope, Claim and limitation documentation.

Excluded:

- benchmark questions, contexts and reference answers;
- original or repaired generated answers;
- per-question outcomes, policy actions and bootstrap multiplicities;
- model weights, indexes, learned estimator files and environment archives;
- absolute-path forensic receipts, user identifiers and Git metadata; and
- failed-run payloads and confidential reproduction archives.

The excluded scientific evidence remains preserved in the private canonical
record. Its absence means this package cannot regenerate candidates, rerun
models, refit selectors, recompute per-question metrics or recompute the 20,000
bootstrap draws. It verifies the published aggregate reporting layer only.

The project license is pending owner selection. Until a top-level license is
chosen and recorded in a rebuilt package, public distribution is not
authorized. Dataset, model and dependency terms remain separate from the
project license.
