# Phi/BGE joint preflight V2 witness correction

2026-09-12. **CAS Q2 STATUS: NOT READY.**

V1 successfully loaded both models and completed two invented Phi generations
and one BGE forward, but its long invented question omitted the word `toy` used
by the accepted 9,472-token Phi witness. The final assertion therefore compared
different inputs and failed before saving admissions or CUDA peaks. V1 remains
sealed at `outputs/cas_q2/phi_bge_joint_gpu_preflight_v1`, manifest SHA-256
`692c75ac0a625bc3c5aec37562b0be5e73832d7b315df399b044a1b9600464c1`.
It contains zero benchmark, Gold, answer-source or fit access.

V2 changes only the invented question to the exact prior witness text, writes
both admissions and captures before the equality assertion, and uses a new
namespace. All model, prompt, guard, forward and acceptance rules remain fixed.
