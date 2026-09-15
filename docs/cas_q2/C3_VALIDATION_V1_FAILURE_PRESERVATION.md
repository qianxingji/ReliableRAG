# C3 V1 failed-result preservation acceptance

2026-09-12 Asia/Shanghai. **CAS Q2 STATUS: NOT READY.**

The exact first full-validation failure is now preserved outside the active
runtime namespace and sealed in its dedicated sibling failure directory. The
failed report remains 5,505 bytes with SHA-256
`ca90d4d03eca6f6d1620aa9c0c03c9d821dc498c815b3bc5e2a11d7d642442ce`.
The original V1 attempt remains complete under failure manifest
`45f6ebc715282c0098538f68d16bb35144a1c58b9a52cfe47e6e008f7b04c8f6`.

Before the move, a separate ZIP archive captured the complete 17-file V1
attempt, an exact failed-report copy, the scope audit and operation controls.
All 29 archive members were rehashed from the ZIP. The archive SHA-256 is
`1e08e481a253ef2837dcfc62a690873c97ae498737672fa37119f61694730ed1`;
the external preservation task is sealed by
`20ccc68681ba45c52cac68b2f6204aa7d4a262e6a49109c8cf2d8e339aea0016`.

After that verification, exactly one same-volume native no-overwrite move placed
the report at
`outputs/cas_q2/empirical_runtime_validation_failures_v1/v1/INDEPENDENT_VALIDATION.json`.
The sibling failure manifest is
`9c7ec69191c05dccab7abeb2302e4cc0ff6db370b3777f127b9807859acb81bf`;
the relocation receipt is
`f41f49a8e2b310df136e609a3de5839e1e99b0fd807dcd26fb6e77e99ea06cda`.
An independent client review, SHA-256
`8669d2973fdc4bec330567574ab9171a2d31e9b786f01e08993badea34ac51dc`,
reopened the archive and rehashed every member, the moved report, sibling seal
and all 14 original runtime files.

The standard runtime namespace is again exactly its original 14 canonical and
replay files. The canonical/replay processes were not repeated. No current
payload was decoded, no Gold was read, no neural forward or fit occurred, and
the scientific-fit total remains 185. This acceptance permits the one frozen
V2 full validator run; it does not establish C3 acceptance or permit C4.
