# Prospective engineering correction: source-only scoring imports

CAS Q2 STATUS: NOT READY. Effective 2026-09-11 before a second CPU preflight.

The first saved-scoring CPU preflight at 4316d4e failed before any saved model
load or numeric probe. Preserve its complete namespace and original source.
Manifest: d57d4d55849f32a981bae477fcbb1b98a84e9a42bdef705725dd56c2158a6fbd.
The original Python file allowlist rejected an unlisted project read.

A separately saved diagnostic reproduced that first read exactly: Python's
importlib loader tried the nonexistent
prelabel_seal_v3/__pycache__/v3_support.cpython-310.pyc before opening the
authenticated .py source. No source module body, model, fresh branch or Gold was
read by that failed import. The read observer recorded a path and existence
metadata only. The diagnostic source SHA-256 is
18b42174fa4fe912efa55f5299bebe3c231bbe9a136958e3506d9905843fdf81.
The diagnostic directory is empirical_scoring_import_diagnostic_v1.

Use a new versioned import bridge that compiles the authenticated Python source
bytes directly into module_from_spec namespaces, without checking or writing a
bytecode cache. Route the historical support module's import_file IO binding
through this source-only bridge before assembling the native definitions.
Preserve all selected scientific AST bodies, class/module identities, learned
model bytes, matrices, feature order, predictions, resolver and thresholds.
This changes the import mechanism only; no original file is modified and no
unlisted bytecode exception is added to the guard. Compare the native feature
assembly records against the sealed historical BASE_SCORE_PROVENANCE.json.

Run the same three invented probes and independent downstream arithmetic once
in empirical_saved_scoring_preflight_v2, with a new committed executable freeze
that binds both attempts and the diagnostic. Keep the v1 output/code/hash exact.
Record errors with code-location metadata if necessary, never branch values.
No fresh scoring, neural forwards, fitting, model selection or Gold access is
authorized by this correction. The independent C3 generation pass is unaffected.
