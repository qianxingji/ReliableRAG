# CAS Q3 manuscript package

The anonymous scientific draft is `manuscript.tex`; secondary tables and audit
details are in `supplement.tex`. Run the following from the repository root:

```powershell
python scripts\build_cas_q3_manuscript_assets.py
```

The generator verifies the accepted SHA-256 hashes of `POINT_ESTIMATES.json`
and `INTERVALS.json`, reads aggregate evidence only, and rebuilds every numeric
table and both PDF figures. `ASSET_RECEIPT.json` records output hashes.

Build and verify the PDFs with:

```powershell
.\paper\build_pdfs.ps1
python scripts\verify_cas_q3_manuscript.py
python scripts\verify_cas_q3_compiled_pdfs.py
```

MiKTeX produced an 11-page main PDF and 3-page supplement under `output/pdf/`.
The static verifier passes 126 checks; the compiled verifier passes its log,
page, text and font checks. All 14 rendered pages passed project-lead and Astra
xhigh review. See `COMPILE_RECEIPT.json` and the P0-I audit records under
`docs/cas_q3/` for exact hashes and disclosed font/longtable notices.

The main manuscript is anonymous. `title_page_template.tex` and
`cover_letter_template.md` intentionally retain explicit author-input fields;
they must not be guessed. Project-license selection and CAS-journal
qualification also remain open.

For the ordered reviewer path across the manuscript, aggregate verification,
private reproduction scopes and retained failures, read
`docs/cas_q3/REVIEWER_EVIDENCE_MAP.md` and run:

```powershell
python scripts\verify_cas_q3_reviewer_evidence_map.py
```
