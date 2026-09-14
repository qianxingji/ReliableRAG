# CAS Q3 manuscript package

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
inspected Applied Intelligence ranges. The static verifier passes 139 checks;
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
a font-clean 12-page PDF and a flat eight-member authored-source ZIP. This does
not close the unresolved difference between that current package and the
`smallcondensed` profile still named on the Applied Intelligence journal page.
A separate private transport combines those eight authored files with the
exact authenticated `sn-jnl.cls` and `sn-basic.bst`; two builds are byte-
identical and independently clean-compile to the already visually accepted
12-page PDF. See
`docs/cas_q3/P0_I_APPLIED_INTELLIGENCE_TEMPLATE_TRANSPORT_ACCEPTANCE.md`.
The transport remains anonymous, untracked, and submission-unauthorized.

After every private owner/institution field is validated, the fail-closed
`scripts/build_cas_q3_applied_intelligence_private_submission.py` builder can
generate the author-populated flat source ZIP, compiled PDF and cover letter in
a new ignored directory. Its synthetic end-to-end acceptance is recorded in
`docs/cas_q3/P0_I_APPLIED_INTELLIGENCE_PRIVATE_SUBMISSION_BUILDER_ACCEPTANCE.md`.
A successful private build still requires author review, publisher template-
path acceptance and the final Astra xhigh audit before submission.

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
