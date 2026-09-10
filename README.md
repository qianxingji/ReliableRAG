# ReliableRAG

Research on selective adoption of repaired RAG answers. Current target:
**CAS Journal Ranking Q2 Submission Ready**, on one RTX 5060 Ti 16 GB.
CAS Q2 is not JCR Q2. Scientific integrity, fairness and reproducibility remain mandatory.

**CAS Q2 STATUS: NOT READY**

ROA-FULL is the current development-supported candidate. Its benefit depends on
GbV verifier scores. The final deployment model and fresh V3 confirmation remain outstanding.

## Continue here

1. Read [AGENTS.md](AGENTS.md) and [CURRENT_TASK.md](docs/cas_q2/CURRENT_TASK.md).
2. Authenticate the private ROA artifacts on the machine holding them:

   ```powershell
   python -m scripts.verify_roa_artifacts --project-root E:/paper/ReliableRAG
   ```

3. Complete the replay handoff, then implement the bounded
   [supervision-matched controls](docs/cas_q2/CONTROLS_PROTOCOL.md).

The checker only reads/hashes files. It does not execute archived scripts, train,
generate or establish numerical reproducibility. Private artifacts are not in
this checkout; missing files are a blocking result.

- [Project charter](docs/cas_q2/PROJECT_CHARTER.md)
- [Current method](docs/cas_q2/CURRENT_METHOD.md)
- [Evidence index](docs/cas_q2/EVIDENCE_INDEX.json)
- [Reproducibility gaps](docs/cas_q2/REPRODUCIBILITY_GAPS.md)
- [Rechecked development summary and limitations](docs/cas_q2/REPORT_RECHECK.md)
- [本地 Codex 执行与回传任务卡](docs/cas_q2/LOCAL_CODEX_HANDOFF_ZH.md)
- [Method and baseline position](docs/cas_q2/METHOD_AND_BASELINE_POSITION.md)
- [Confirmation design and unresolved preflight](docs/cas_q2/CONFIRMATION_DESIGN.md)

Historical protocols are retained. `CODEX_TASK_PHASE0.md` is not the current starting task.
