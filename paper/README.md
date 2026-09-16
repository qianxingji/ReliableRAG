# CAS Q3 manuscript package

The current review manuscript is the 21-page A4 PDF
`output/pdf/JIIS_Manuscript_R5_Reproducible.pdf`. It preserves the
author-designated `JIIS_Manuscript_R3.pdf` scientific content and replaces only
four release-state paragraphs so that the paper names and accurately scopes the
public repository at commit `44d22c66c2adbdce8ebc2289844a8b26e6929bd5`.
`LATEST_MANUSCRIPT.json` records the exact identities. The retained R3 source is
`source_reference/JIIS_Manuscript_R3.pdf`; the builder is
`../scripts/build_jiis_r5_reproducible_pdf.py`, and the 90-check receipt is
`JIIS_R5_REPRODUCIBILITY_VERIFICATION.json`.

Rebuild and verify this artifact with:

```powershell
python scripts\build_jiis_r5_reproducible_pdf.py
python scripts\verify_jiis_r5_reproducibility.py
python scripts\verify_latest_manuscript.py
```

The reproducibility revision binds a text-free 18,000-trace public numeric
bundle. The public workflow exactly reconstructs all point estimates and the
complete 20,000-draw bootstrap without model fitting or neural inference. It
does not change any scientific result. The split PDFs, editable TeX files, R3,
and R4 remain historical evidence for the earlier manuscript line.

The anonymous scientific draft is `manuscript.tex`; secondary tables and audit
details are in `supplement.tex`. Run the following from the repository root:

```powershell
python -m pip install -r paper\requirements.txt
python scripts\build_cas_q3_manuscript_assets.py
```

The generator verifies the accepted SHA-256 hashes of `POINT_ESTIMATES.json`
and `INTERVALS.json`, reads aggregate evidence only, and rebuilds every numeric
table and both PDF figures. `ASSET_RECEIPT.json` records output hashes.
The figure builder pins ReportLab and the hashes of its bundled Bitstream Vera
fonts, emits deterministic PDFs, and embeds the used TrueType subsets.

Build and verify the PDFs with:

```powershell
.\paper\build_pdfs.ps1
python scripts\verify_cas_q3_manuscript.py
python scripts\verify_cas_q3_compiled_pdfs.py
```

MiKTeX produced an 11-page main PDF and 3-page supplement under `output/pdf/`.
The abstract is 155 words and the source lists five keywords, meeting the
inspected Applied Intelligence ranges. The static verifier passes 141 checks;
the compiled verifier passes its log,
page, text and font checks. Both PDFs have zero nonembedded and zero Type 3
fonts. Visual review is recorded separately from the mechanical verifier; all
14 pages of the current rebuild passed project-lead review. The earlier
Astra xhigh review remains bound to the pre-font-correction artifact, so the
final target-specific package still requires a fresh Astra xhigh rebind. See
`COMPILE_RECEIPT.json` and the P0-I records under `docs/cas_q3/` for exact
hashes and the retained nonfatal supplement `longtable` notice.

The selected-target engineering preflight also compiles the same scientific
source with the authenticated December 2024 Springer Nature `sn-jnl` package to
a font-clean 12-page PDF and a flat eight-member authored-source ZIP. Official
journal and publisher guidance accepts the current template as a submission
route. This does not prove style equivalence between that package and the
`smallcondensed` profile still named on the Applied Intelligence journal page.
A separate private transport combines those eight authored files with the
exact authenticated `sn-jnl.cls` and `sn-basic.bst`; two builds are byte-
identical and independently clean-compile to the already visually accepted
12-page PDF. The current data/code-policy refresh transport has SHA-256
`d55ffb74cb8f88a9ec261c9a414219f511d92bd10eb4d888f5dbaa185d1c681e`;
the former `f4279c...` transport remains a historical build. See
`docs/cas_q3/P0_I_DATA_CODE_POLICY_REFRESH_ACCEPTANCE.md` and
`docs/cas_q3/P0_I_APPLIED_INTELLIGENCE_TEMPLATE_ROUTE_RESOLUTION.md`.
The transport remains anonymous, untracked, and submission-unauthorized.

After every private owner/institution field is validated, the fail-closed
`scripts/build_cas_q3_applied_intelligence_private_submission.py` builder can
generate the author-populated flat source ZIP, compiled PDF and cover letter in
a new ignored directory. Its synthetic end-to-end acceptance is recorded in
`docs/cas_q3/P0_I_APPLIED_INTELLIGENCE_PRIVATE_SUBMISSION_BUILDER_ACCEPTANCE.md`.
A successful private build still requires author review and the final Astra
xhigh audit before submission.

The main manuscript is anonymous and remains in a journal-neutral class.
`title_page_template.tex` and
`cover_letter_template.md` intentionally retain explicit author-input fields;
they must not be guessed. Apache License 2.0 is present for project-authored
code, while legal holder/year, release review, final authorization and persistent
archiving of the validated corrected candidate, and institutional CAS
qualification remain open.

For the ordered reviewer path across the manuscript, aggregate verification,
private reproduction scopes and retained failures, read
`docs/cas_q3/REVIEWER_EVIDENCE_MAP.md` and run:

```powershell
python scripts\verify_cas_q3_reviewer_evidence_map.py
```
