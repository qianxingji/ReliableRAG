# Project model routing

User instructions, 2026-09-11 and 2026-09-13:

> 日常固定 Sol High，关键科研决策和最终验收再 Astra xhigh。

Use the following exact routing. `Sol` means `gpt-5.6-sol`; `Astra` means
`gpt-6-astra`.

| Work | Model | Reasoning |
| --- | --- | --- |
| Routine code, script changes and tests | Sol | Medium or High |
| Formal experiments, benchmarks and numerical replay | Sol | High |
| P0-1 artifact authentication and provenance tracing | Sol | High |
| P0-1 final authenticity audit | Astra | xhigh |
| P0-2 baseline implementation and controlled experiments | Sol | High |
| P0-2 final fairness audit | Astra | xhigh |
| P0-3 routine experiment implementation | Sol | High |
| P0-3 research design and novelty judgment | Astra | xhigh |
| P0-3 major method decisions | Astra | xhigh |
| Ablation, sensitivity and robustness experiments | Sol | High |
| Ordinary experiment-result analysis | Sol | High |
| Anomalous results or conflicting conclusions | Astra | xhigh |
| Manuscript first draft, tables and experiment section, if authorized | Sol | High |
| Core Method argument and Claim boundaries | Astra | xhigh |
| Deciding whether evidence supports a Claim | Astra | xhigh |
| Full simulated-reviewer audit | Astra | xhigh |
| Final Submission Ready acceptance | Astra | xhigh |

Use Sol High as the routine default. Sol Medium is permitted only for routine
code, script changes and tests when the task does not include a formal run,
benchmark, numerical replay or research judgment. A formal stage's execution
remains Sol High even if its later final audit is assigned to Astra xhigh.
Return to Sol High after each bounded Astra decision or audit is recorded.
The user's 2026-09-13 instruction supersedes the earlier Astra High entries:
method design itself, novelty judgment and core Method/Claim argument now use
Astra xhigh.

Research design precedes core algorithm implementation. Work remains project
lead and client acceptance authority, ChatGPT owns research design and argument,
and Codex executes reviewed designs. The latest user policy supersedes earlier
prose assigning all Codex work to Astra. It does not change experiment models,
seeds, parameters, budgets, evidence requirements or sealed artifacts.

Apply explicit model/reasoning overrides through the available task continuation
control and check its result before claiming a switch. Keep work in the existing
task. A final audit means review of already concrete, frozen evidence; prepare
that evidence under the assigned Sol stage before switching. This document is
not evidence of a model replacement within an already running turn.
