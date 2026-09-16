# Mistral test a0/query implementation note

Date: 2026-09-17. **CAS Q3 STATUS: NOT READY.**

Status: `PASS_LABEL_BLIND_TEST_A0_ENGINEERING_NOT_EXECUTED`.
This is an implementation and source-binding result. It is not a reader result,
does not contain generated answers, and does not authorize test execution.

## Scope and source chain

`scripts/run_mistral_test_a0_query.py` implements the first component of the
frozen test acquisition route. It binds these immutable label-blind sources:

- test preparation manifest SHA-256
  `7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258`;
- 18,000-row trace SHA-256
  `87d5aff0bc77da76624b541326c523d41b00fa6c84ecefd4d6a050de66b25a29`;
- candidate-pool manifest SHA-256
  `4b654f0d12eaf6a9bc08e4522932cffb3fea1845eb9bbcfb2d7c2fab3b87ab98`;
- Mistral input-freeze manifest SHA-256
  `588b4d86fb6048ade1bba52731829496772d62fd522a260a7a4c60ec584586ca`;
- private input ledger SHA-256
  `538970511fe517a21ef7baee4dc5eb216ce748b2c2222b3960c356a53a12f8ac`.

Every trace must have the exact frozen position, dataset, retriever, sample ID,
`role=test` and ordered original-top-five hash. The population must contain
2,000 traces in every dataset by retriever cell and three retriever siblings for
each of 6,000 questions. Questions and ordered evidence are reconstructed from
the candidate-pool runtime and document rows. No development trace, existing
answer string, outcome or reference label is accepted as an input.

The executor plans exactly 18,000 `a0` and 18,000 repair-query generations. It
uses the same Mistral revision, prompts, parser, NF4/double-quant/BF16 runtime,
batch size one, durable intent/result journal and exact-input resume semantics as
development. The Windows GPU mutex is intentionally identical to the active
development mutex, preventing concurrent development and test model work.

## Independent validation

`scripts/validate_mistral_test_a0_query.py` imports neither the producer nor the
neural reader. It independently verifies the manifest and durable journal,
reconstructs every question and evidence set, tokenizes all 36,000 prompts,
checks prompt and token hashes, decodes generated token IDs, reruns both parsers,
and verifies output lengths and finite chosen-token log probabilities. Its
expected terminal status is
`PASS_INDEPENDENT_FULL_SOURCE_MISTRAL_TEST_A0_QUERY`.

Six invented-only contract tests cover exact population and operation counts,
identity and role failures, ordered evidence reconstruction, label-blind source
pins, shared GPU exclusion, validator independence and canonical hash agreement.
All six pass. The complete Mistral engineering suite passes 113/113.

A separate label-blind source smoke read the real frozen trace, input ledger and
candidate-pool rows and reconstructed all 18,000 traces, 6,000 question groups
and five evidence documents per trace. It made zero model forwards and zero
Gold or outcome reads. No formal test output namespace was created.

## Remaining evidence and risks

- P0: complete and independently accept development acquisition and all
  downstream development stages.
- P1: implement test repair, `a1_likelihood`, witness replay and neural scoring;
  then execute the one-time test chain after all predecessor gates pass.
- P2: update manuscript, supplement and public numeric reproduction artifacts
  only after independently accepted outcomes exist.

The main rejection risks remain an uncertain fusion increment over
`HGB_ONLY_R`, rare Damage, one repair operator, known benchmark identities and
end-to-end neural reproduction cost.
