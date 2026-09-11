# Authenticate the native loss class alias in HGB state observation

Research Lead refinement before diagnostic v4, 2026-09-11.

Diagnostic v3 reaches the persisted native loss object and rejects its reported
class name _loss.CyHalfBinomialLoss because the observer admits only src/sklearn/
numpy class namespaces. Preserve that failed observation. It performed no fit
or score and has not established the state differences.

Permit this exact class only after proving that its type is the identical
CyHalfBinomialLoss exported by the already loaded sklearn._loss._loss extension.
Require that module's actual binary path is the accepted new environment's
Lib/site-packages/sklearn/_loss/_loss.cp310-win_amd64.pyd, whose bytes must match
the previously accepted installed-file receipt. Record its actual path/hash,
the exported identity and original reported _loss class name. No arbitrary
underscore-module class is admitted. Keep full reduction-state observation and
all other unsupported-state failures; do not omit or substitute the loss state.

Use a new v4 observer and namespace, preserving v1-v3 and the failed seven-fit
gate. No model or expected hash is edited; no fit, scoring or label access is
allowed. CAS Q2 STATUS remains NOT READY and actual fit total remains 185.
