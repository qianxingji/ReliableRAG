# Sample-size rationale correction, 2026-09-11

**CAS Q2 STATUS: NOT READY.** This correction is issued after the ID-only stage
B selection/audit and before any fresh question/context projection, inference
or outcome mapping for the new cohort.

EMPIRICAL_REPLICATION_PROTOCOL_V1.md and its generated PRECISION_PLANNING.json
incorrectly describe 2,000 as the largest multiple of 100 below the 2,105-ID
Hotpot availability. That arithmetic statement is false: the largest such
multiple is **2,100**. The protocol, executed selector, output planning file and
their hashes are retained unchanged so the original error is visible.

The executed design fixed **2,000 questions per dataset, 6,000 total**, before
selection and before any fresh outcomes. The chosen size is a round 2,000-
question balanced study within the available frame; it is not the maximum
available balanced sample. The planning analysis concerns this fixed size and
provides variance sensitivity, not guaranteed power. The remaining 105 Hotpot
IDs are unused, not a replacement reserve.

The Research Lead retains the prospectively selected 6,000 IDs and all model,
seed, pipeline, cap and analysis parameters. There is no enlargement to 2,100,
redraw, model selection or effect-based adaptation. This correction changes the
sample-size description only. An independent validator checked the numerical
planning formulas and selection, not the erroneous prose's mathematical claim;
that distinction must remain explicit in the stage acceptance.
