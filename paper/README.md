# CAS Q3 manuscript package

The anonymous scientific draft is `manuscript.tex`; secondary tables and audit
details are in `supplement.tex`. Run the following from the repository root:

```powershell
python scripts\build_cas_q3_manuscript_assets.py
```

The generator verifies the accepted SHA-256 hashes of `POINT_ESTIMATES.json`
and `INTERVALS.json`, reads aggregate evidence only, and rebuilds every numeric
table and both PDF figures. `ASSET_RECEIPT.json` records output hashes.

No TeX engine was available in the takeover environment on 2026-09-13, so the
sources have not yet passed an ordinary LaTeX/BibTeX compile. The two generated
PDF figures were rendered with Poppler and visually inspected. Do not describe
the manuscript PDF as compiled until the build status is updated.

The main manuscript is anonymous. `title_page_template.tex` and
`cover_letter_template.md` intentionally retain explicit author-input fields;
they must not be guessed. Project-license selection and CAS-journal
qualification also remain open.
