# Applied Intelligence data/code policy refresh acceptance

Decision: **PASS_DATA_CODE_POLICY_REFRESH_BASE_TARGET_TRANSPORT_AND_SYNTHETIC_BUILD_ACCEPTED_EXTERNAL_GATES_OPEN.**

**CAS Q3 STATUS: NOT READY.**

On 2026-09-15 the project rechecked the Applied Intelligence submission
guidelines, Springer Nature research-data policy and FAQ, and the Springer
Nature software/code-sharing guidance. The manuscript now distinguishes the
historical aggregate witness from the corrected Apache-aware candidate, states
that the public repository exists, and explicitly leaves the final submission
revision and permanent archive identifier open. Restricted benchmark or model
evidence is offered only if requested, through a channel designated or accepted
by the handling editor. No particular private-delivery channel is claimed to be
preapproved.

The anonymous base manuscript rebuild passes 141 static checks. Its 11-page PDF
has SHA-256 `6304d8a407d728265dbc375d968e3e3349470f73d1cae4a77e1093511f2771b7`;
the 3-page supplement has SHA-256
`ad271207b268dac05592b555d4a357e79cb36be5a0e86e571eb616d4c7e71a49`.
The reproducible PDF-text proxy counts 4,048 tokens before References and 4,745
for the full document. All 14 pages were visually inspected and have zero
observed clipping, overlap, broken glyph, blank-page or figure/table-placement
defects. Both PDFs have zero nonembedded and zero Type 3 fonts.

The selected-target `sn-jnl` preflight is 12 pages with PDF SHA-256
`6e3d40864f2acfa506c282c096059b147cff4a2d22d859ae9a2036fed6f42f97`
and authored-source ZIP SHA-256
`e28e3c3820b321e7af444dc9ba57cb49e6890b7623d2dfadce6878dca41a4a8a`.
Its verifier passes 38 checks; all 12 pages were visually inspected with zero
observed defects and zero nonembedded or Type 3 fonts.

Two new private complete-source transports were created in distinct external
directories. Both archives have SHA-256
`d55ffb74cb8f88a9ec261c9a414219f511d92bd10eb4d888f5dbaa185d1c681e`,
contain the same ten flat anonymous members, pass 56 independent validation
checks each, and clean-compile to the exact accepted 12-page target PDF bytes.
A synthetic-only private build then exercised the updated author-package path.
Its ten-member source archive has SHA-256
`36eb522d2bbe5305a812a938e68d2fd5120adaacbefa0d77145a706abb783d90`,
its 13-page PDF has SHA-256
`a21e80ad06b45eb0044de3cf4c1a98f3220b738589b29b49f2dcc48eb211aa40`,
and its cover letter has SHA-256
`e430fb658ddd7672f5f37137f4c13daee41c9b556fbc78b51ad3a5455a7d2948`.
All 13 pages were visually inspected with zero observed defects. Synthetic
identity and declaration values are test fixtures and are not author facts. A
second build using the builder's default transport path reproduced the source
archive, PDF and cover-letter hashes exactly.

The previous transport SHA-256
`f4279cf38aa09a1ddc212b9b295e0c73b78a67b7262845e72a6df584edeb8fdd`
and all prior synthetic packages remain preserved as historical builds. They
were not mutated, overwritten or relabelled as the refreshed package.

The first reviewer-map verification attempt failed because a stale assertion
still required the historical transport's compiled PDF (`f423cd...`) to equal
the refreshed target PDF (`6e3d40...`). The failure is retained here. The
verifier was corrected to authenticate the historical bytes as historical and
to bind only the refreshed `d55ffb...` transport to the current target PDF. This
was an engineering evidence-map failure, not a scientific-result failure.

Final local validation authenticates 194 reviewer-map records in 1,472 checks,
and the fail-closed submission gate authenticates 228 repository hashes in 819
checks before returning its expected `NOT_READY` exit code 2. All 135 CAS Q3
tests pass. The complete repository suite passes 409 tests with two documented
Windows platform skips. The privacy-safe real owner-input check remains
fail-closed at six missing fields and zero validation errors.

This work read no scientific payload, ran no model forward and performed no
scientific fit. It supplies no owner or institutional approval, creates no real
author package, and authorizes neither distribution nor submission. P0-G and
P0-I remain open.
