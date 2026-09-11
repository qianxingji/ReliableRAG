# Bounded ROA replay release and relocation contract

Research Lead decision, 2026-09-11, before new packaging or relocation execution.
CAS Q2 STATUS: NOT READY.

## Concrete need and scope

The authenticated original review ZIP contains only 216 ROA payloads and its
manifest. The accepted original replay also authenticated 2,601 distinct parent
and executable-input files (290,042,069 bytes), including six Windows environment
files. The old ZIP is a namespace review artifact, not a sufficient replay input
package. This is a measured release dependency gap, not a new scientific question.

Create a separate, local, private release containing the complete file closure
required by the existing saved-parameter replayer, the committed source as a
self-contained Git bundle, exact environment facts, and execution instructions.
Keep the old ZIP and all failures. The old packager removes a partial archive
on failure; leave its frozen bytes intact and use a new fail-preserving packager.
No artifact is uploaded by this task.

## Authentication and packaging

Derive data records from the original pinned ROA manifest, all four manifests
whose hashes occur literally in the original controls source, ROA executable
freeze, and DHC's bound input anchors, task/protocol records and R1 executable
freeze. Authenticate each metadata file before decoding it. Do not execute
parent code. Require all five namespaces' exact file sets and every input's
original size and SHA-256, rejecting conflicting records and noncanonical,
case-aliased, traversal, symlink or Windows reparse paths.

Copy payloads as opaque bytes; do not decode historical answer/outcome rows
while packaging and do not read fresh C3/C4/D payloads. Preserve project-relative
paths and all parent failures. Record the original source commit and source
bundle checksum. Stream-check copied data against the pre-existing digests,
reopen the archive and rehash every member; recheck source files afterwards.
Exclusive creation only. Retain partial archives and failure receipts on error;
never clean or retry into an existing namespace. Store a final manifest only
after package validation, with explicit scope rather than a readiness claim.

## Prospective portability check

In new directories outside the original project and engineering worktree,
extract exactly the verified data archive and clone the included Git bundle at
its recorded commit. Run the unchanged `scripts.replay_roa_original` primary
and independent modes once each in separate processes and output directories.
Add only an external path-access guard: reject original-project data/docs/code
reads and engineering-worktree reads, except the existing Python runtime under
the original `.venv`. Record permitted runtime reads separately. The guard must
not replace numerical functions, saved parameters, tolerances, ranks or actions.

Acceptance requires the existing full gates: 28 contexts, 56 saved models,
38,424 prediction rows, zero changed action memberships, the original 1e-10
numeric limit, complete independent validation, all 216 ROA payloads unchanged,
all release data unchanged, and no fallback data access to the old directories.
Preserve any failed attempt; investigate and version a correction before retry.
This is one relocation verification of saved-parameter replay, not a rerun of
scientific fits, an upstream training reconstruction, or a new result selection.

## Claim limits and remaining release work

The six copied environment files are authentication artifacts, not an installed
environment. The check reuses this host's Python 3.10.6 and installed numerical
libraries. Record versions and backend details; do not claim a clean installation,
another host/OS, or a fully offline environment has been tested. A source Git
bundle also contains history, so it stays private together with the data ZIP.

The bounded package does not contain all neural assets, all upstream training
receipts, the new empirical pipeline, or its not-yet-completed outputs. Fresh
pipeline absolute-path freeze relocation and complete environment reconstruction
remain separate release requirements. The seven historical per-estimator fit-time
ID/matrix receipts remain missing. Total scientific fits stay 178; fresh Gold
reads stay zero. Continue the original C3 process without competing for its GPU.
