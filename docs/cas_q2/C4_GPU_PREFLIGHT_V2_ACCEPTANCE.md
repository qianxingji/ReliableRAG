# C4 V2 invented GPU preflight: client acceptance

Date: 2026-09-12. Client Research Lead review: Sol High.
CAS Q2 STATUS: **NOT READY**.

Decision: **ACCEPTED_C4_V2_GPU_PREFLIGHT_INVENTED_ONLY**. The complete V2
invented GPU compatibility protocol passed and base scoring is authorized under
the same exact binding and predecessor chain. This does not provide benchmark
quality, Gold, model-fit, retrieval, contribution or final-candidate evidence.

The only V2 run used source commit
`f6368506f495cc5a0e122bd5810fa0fa230305b2` and binding config
`b449d7366c1202262ee62a2a4d5a4dfc605017c755ccb61131b5ace82ce384e3`.
Its scientific namespace is
`outputs/cas_q2/empirical_scoring_gpu_preflight_v2`, sealed under manifest
`1aabac381c8a5e5381f46729f49e9afcaae915c1fa84cd375141486e513b530a`.
The external raw-log task manifest is
`3dd82ce8a8d865011f8e8d559f0e844f335633f73f4b47e980d50e003b13ead9`.
Never repeat or relocate this V2 run. The preserved V1 failure remains unchanged.

The native GPU counters match the prospective protocol exactly:

- BGE: two forwards, 22 rows and 8,210 padded input tokens;
- Qwen: eight forwards, eight rows and 33,618 padded input tokens for 12
  requests with four exact cache hits; all four long cells total 8,192 tokens
  and record truncation;
- NLI: seven forwards, 33 pairs, five completed branches and one deterministic
  unscorable pair at the second hypothesis. The long-premise path spans more
  than five chunks.

The exact Jinja binding admitted one authenticated `compiler.generate` call from
the authenticated direct `Environment._generate` caller, delegated 17,584,560
other profile events, inherited no descendant exemption and recorded no boundary
denial. The active bound profile was present immediately before success
finalization. The client reconstructed the original pre-binding result hash and
verified the separately written binding receipt.

The client independently replayed the saved witnesses without model forwards:
30 semantic checks, 136 likelihood checks and 376 NLI checks. The maximum NLI
probability error was `6.603025604068335e-08`, below the frozen
`9.5367431640625e-07` bound. It rehashed all 444 executable inputs, all 30,912
environment files, the 25 scientific-manifest entries, the five external-run
entries, C3, V1 and both V2 CPU-gate namespaces. Seven staged NLI files remain
byte-identical to their original sources. Client audit manifest:
`65a7916f2d6db67158d49b7ba2be4994519decef102a3e1fad87c4c9a31cca71`.
The reopened metadata archive is
`600e5ca8881cfa71060ef8546026fb81f165a3a86f15d43543e26f8556e07b1d`;
large cache/model copies remain sealed and rehashed in the scientific namespace.

The stderr length notice `2122 > 512` is the expected pre-chunking observation
for the invented long NLI premise. Independent reconstruction confirms that
emitted chunks fit the 512-token limit and cover the premise; it is not a model
indexing failure.

Next, execute the full 18,000-trace base-scoring stage once with Sol High through
`run_roa_empirical_scoring_bound_v2`, using this accepted V2 manifest as its exact
predecessor. Preserve any failure and audit the sealed base result before GbV.

P0 remains base, GbV, policy and independent prelabel completion, followed by
cost/D execution and contribution assessment. P1 remains complete cost,
provenance and release fidelity. P2 remains CAS year/category/target-journal
qualification; the user has left that scope pending.
