# C3 V3.2 isolated bootstrap: client acceptance

Research Lead acceptance, Astra xhigh, 2026-09-12 Asia/Shanghai.  
**CAS Q2 STATUS: NOT READY.** The bootstrap-only gate is accepted. It permits one
V3.2 launch after the implementation commit is present remotely; it does not
accept C3 or any scientific result.

The wrapper imports only `runpy`, `sys` and `pathlib`, authenticates its expected
repository location under Python `-I`, inserts that path once and executes the
unchanged V3.1 entry. Running from outside the repository, the exact isolated
`--help` path exits zero with empty stderr. A separate wrong-pin case passes the
repository import boundary and is rejected by the unchanged V3.1
`V3_BINDING_CONFIG_PIN` check before config parsing or payload access.

The gate confirms the unchanged V3.1 entry SHA-256
`270d50ef62f7c32df413d149c1a84e1ad3e7f497adbc2081e6a4799d9a165676`
and binding SHA-256
`0e0c44f954454defdd3f0134c30ed2cb7fb1e777d5c95e60640b7171d5c5f564`.
The fixture task manifest is
`c8d66e7144813ca5a49c91d851a36b5e3af48ec87dcd9946094c932fe26cfb26`;
the independent client-audit manifest is
`9fdf6a8e5ef232d0006dc27959098b0bcc7ad083bb01a7f2c23e2deb8feb0b7e`.
All 16 private archive members were reopened and rehashed; archive SHA-256 is
`15948062665f6fc4bccf47fee29b8369cda9b5f47e8f50e46fc2ea067067b5ac`.

No current runtime payload or configuration was parsed, and there were zero Gold
reads, neural forwards and fits. All 30,823 environment files remain unchanged.
The V3.1 launch failure remains preserved and is bound into this evidence.

P0 permits one V3.2 launch only after remote commit alignment. That launch must
bind every earlier failure and accepted gate, invoke the unchanged V3.1 validator
through this wrapper, and retain any failure without automatic retry. C4 remains
blocked pending full C3 acceptance and its actual predecessor check.
