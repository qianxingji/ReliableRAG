# P0-G current project-license decision packet

Status: **OWNER SELECTED APACHE-2.0 FOR PROJECT-AUTHORED CODE; HOLDER, YEAR AND INSTITUTIONAL RELEASE REVIEW PENDING.**

**CAS Q3 STATUS: NOT READY.** The owner selected Apache License 2.0 for
ReliableRAG project-authored code. The exact official license text is present
at repository root and the corrected aggregate V2 candidate contains that same
text. This decision does not license third-party assets, authorize public
distribution, identify the legal copyright holder or satisfy an institutional
release review.

## Implemented state

- Selected code license: `Apache-2.0`.
- Root license: `LICENSE`, SHA-256
  `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
- Scope statement: `LICENSE_SCOPE.md`.
- Corrected anonymous aggregate candidate: V2 archive SHA-256
  `4eebb724b43a402600449286dd22b32b2b5c7b7720296e9276db45cffae9aaf8`.
- V2 applies Apache-2.0 only to its two project-authored verifier/statistical
  scripts and explicitly leaves non-code members and third-party materials
  outside that grant.
- Public distribution: withheld.

The official Apache text and application guidance are maintained by the Apache
Software Foundation:

- <https://www.apache.org/licenses/LICENSE-2.0.txt>
- <https://www.apache.org/legal/apply-license.html>

No project-specific `NOTICE` has been invented. The legal holder, copyright
year/range and any wording or approval required by Hubei University of
Technology must be confirmed first.

## Fixed third-party boundary

The project-code license does not cover HotpotQA, 2WikiMultiHopQA or MuSiQue
payloads; Qwen, BGE or DeBERTa weights/tokenizers; dependency wheels; generated
answers; per-question outcome ledgers; or private reproduction archives. None
of those payload classes is present in the V2 aggregate candidate.

The exact Qwen2.5-3B-Instruct revision is under the Qwen Research License, which
limits its grant to non-commercial purposes and has separate redistribution and
notice conditions. The exact non-`-c` DeBERTa checkpoint is labelled MIT at the
foundation-model level, but its author states that its training data include a
mix of licenses including non-commercial terms. The project excludes both
models' weights and retains institutional review of the intended publication
and release boundary.

## Remaining owner and institutional record

The following facts are still required and must not be guessed:

1. exact legal copyright holder for project-authored code;
2. copyright year or year range;
3. whether the holder may license all code intended for release;
4. whether institutional release review or project-specific `NOTICE` wording is
   required, and the retained approval if so;
5. institutional acceptance of the Qwen research-license boundary for the
   intended academic publication and code/evidence release;
6. institutional acceptance of the non-`-c` DeBERTa training-data caveat for
   the same route; and
7. final written authorization of V2 or a prospectively rebuilt successor.

The historical V1 archive and its `PENDING_OWNER_SELECTION` manifest remain
unchanged as evidence of the earlier state. They are not the current licensed
candidate.

## Promotion boundary

Once the missing holder/year/review facts are supplied, the project must decide
whether V2 can be released as built or whether a new package with an approved
notice is required. Any successor must use a new output path, rebuild twice,
match byte-for-byte, pass the independent archive validator and 129-check
aggregate verifier, retain identity/path scans, and obtain a persistent archive
identifier. Until those conditions pass, P0-G remains open.
