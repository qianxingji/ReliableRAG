# P0-I supplement longtable notice triage

Date: 2026-09-13 (Asia/Shanghai).

Decision: **ACCEPT AS AN UPSTREAM VERSION-SCOPED NONFATAL NOTICE; RECHECK IN
THE FINAL TARGET ENVIRONMENT.**

**CAS Q3 STATUS: NOT READY.** This triage explains one retained log notice. It
does not waive a target journal's source/PDF rules or close the final artifact
audit.

## Observed condition

The installed MiKTeX build loads `longtable` 2025-10-13 v4.24. When the dataset
table crosses the first supplement page boundary, pdfTeX records:

```text
ignored error: Infinite glue shrinkage found in box being split
```

The process exits successfully. The compiled verifier records zero fatal
errors, unresolved citations/references, overfull/underfull boxes, unembedded
fonts and Type 3 fonts. All three supplement pages were rendered and inspected;
the table header, continuation rows and following sections are complete.

## Independent diagnosis

The LaTeX Project's official `latex2e` issue tracker reproduces this exact
notice with a plain sufficiently long `longtable`, describes it as harmless in
the reported case, and records the fix under the 2026 Q2 release milestone:
<https://github.com/latex3/latex2e/issues/1907>. The official LaTeX news for
tools changes states that the glue used by `longtable` was changed to use only
a finite shrink component:
<https://www.latex-project.org/news/latex2e-news/ltnews43.pdf>.

Local probes removed `\raggedbottom`, inserted a page break before the table,
and reduced both breakdown tables to `\small`; all retained three or four
legible pages and the same upstream notice. Those probes were temporary and
were not adopted. They confirm that changing manuscript pagination is not a
sound way to conceal a package-version diagnostic.

## Final handling rule

Keep the current log and three-page supplement as authenticated evidence. At
target-journal conversion, build with the journal-supported current LaTeX
environment and rerun the strict compiled verifier. If the selected submission
system treats the notice as fatal despite complete output, use only a
target-template-supported multipage table construction and require exact table
cell equality before acceptance. Do not remove rows, shrink Claims or suppress
the log message to manufacture a clean result.
