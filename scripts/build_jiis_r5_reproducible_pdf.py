#!/usr/bin/env python3
"""Build the reproducibility-aligned JIIS R5 PDF from the designated R3 PDF.

R3 is retained byte-for-byte. This builder replaces only the four paragraphs
whose repository-release state changed after R3 was compiled.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "source_reference" / "JIIS_Manuscript_R3.pdf"
OUTPUT = ROOT / "output" / "pdf" / "JIIS_Manuscript_R5_Reproducible.pdf"
SOURCE_SHA256 = "b01683e3431cd01c62739c66cd6045395f30362234c04f3315458602eebf6c2e"
PUBLIC_REPOSITORY = "https://github.com/qianxingji/ReliableRAG-Code"
PUBLIC_COMMIT = "44d22c66c2adbdce8ebc2289844a8b26e6929bd5"
EMBEDDED_BODY_FONT = Path(r"C:\Windows\Fonts\times.ttf")


REPLACEMENTS = {
    11: (
        fitz.Rect(59, 198, 536, 370),
        "Project-authored method and reporting code is publicly available at "
        "https://github.com/qianxingji/ReliableRAG-Code under Apache License 2.0. "
        "This manuscript is bound to commit 44d22c66c2adbdce8ebc2289844a8b26e6929bd5. "
        "The release contains the authenticated historical HGB source, paired NLI scorer, "
        "supervision-matched logistic fitting and disjoint calibration procedure, fixed selection "
        "and analysis kernels, and a text-free 18,000-trace numeric bundle with opaque question-group IDs. "
        "One public command exactly rebuilds all point estimates and the complete 20,000-draw "
        "question-cluster bootstrap, then runs the reporting and repository checks.\n\n"
        "Benchmark text and original IDs, contexts, references, generated answers, retrieved passages, "
        "model weights, fitted paper parameters, development labels, and private forensic records are not "
        "redistributed. The release reproduces the reported statistical layer from realized numeric traces; "
        "it does not regenerate the neural acquisition or refit the paper heads. Third-party data and models "
        "remain under their own terms. Appendix J states this boundary.",
    ),
    16: (
        fitz.Rect(59, 419, 536, 753),
        "The public source release is ReliableRAG-Code at Git commit "
        "44d22c66c2adbdce8ebc2289844a8b26e6929bd5. The repository URL is "
        "https://github.com/qianxingji/ReliableRAG-Code. The relevant files and Git blob identifiers are:\n\n"
        "Current head fitting: src/arbitration/empirical_panel.py; blob "
        "f27090ee94a04c4fc693dd9d0a61380660db13e9. The fit_panel function performs eligible-row "
        "selection, fit-only imputation and standardization, L2-logistic base fitting, and disjoint "
        "Platt calibration.\n\n"
        "Head contract and target: src/arbitration/empirical_contract.py; blob "
        "60bdaa96ef27072e856f30a1f163b3c768f240d1. It defines the fixed 3,600/900-question "
        "development split, feature widths, Recovery target, retriever indicators, and base/Platt settings.\n\n"
        "Paired NLI interface: src/verification/gbv_nli.py; blob "
        "8be2e0b54e6ff0fce61aba361b4fa4785904b724. It defines the hypothesis template, pair-length "
        "checks, chunking, entailment-label resolution, and branch aggregation.\n\n"
        "Statistical reproduction: scripts/reproduce_paper_statistics.py; blob "
        "19322ba6dcb3bf818e4bcda123041bb6ee2c2ace. The text-free numeric bundle has SHA-256 "
        "a930286d62bddf9f4837cb1beb4b863f0f94c1bc697b2311977a9b0eb18f09f7 and contains "
        "18,000 opaque-identity evaluation rows.\n\n"
        "The fitting interface records sample_count, class_counts, target_counts, partition/design hashes, "
        "preprocessing values, coefficients, and Platt parameters. The public release exposes the runnable "
        "procedure but not the labeled development rows or fitted paper bundles. The released evaluation "
        "rows support exact statistical reconstruction, not head refitting.",
    ),
    18: (
        fitz.Rect(59, 134, 536, 292),
        "The authenticated historical HGB feature source is publicly released as "
        "src/mars/state_symmetric.py at commit 44d22c66c2adbdce8ebc2289844a8b26e6929bd5; "
        "its SHA-256 is 3724b5ac77722b70cabdf2589379d5584942f34ec81f3f5a04f88e0665f8f717. "
        "The historical model-binding file src/mars/full_experiment.py has SHA-256 "
        "65713509ef6c8d094bb44ad2c47b0238ceade607616d3e729b31c56096326d50 and remains outside "
        "the public release.\n\n"
        "The original saved HGB artifact is 639,652 bytes with SHA-256 "
        "9245170f855435b5603b04013bd4fbab79a75d2761853a012ab9f3259600bf6e. Source-assembled "
        "replay reproduced all 1,539 HGB scores with zero numerical error. The serialized replay differed "
        "only in saved CPU-thread metadata (one rather than six); observed learned arrays and tree fields "
        "matched. Original per-estimator fit-time ID/matrix receipts and an independent original-fit witness "
        "remain unavailable, so this supports saved-computation equivalence, not independent authentication "
        "of the original training event.",
    ),
    20: (
        fitz.Rect(59, 83, 536, 370),
        "The public repository at https://github.com/qianxingji/ReliableRAG-Code, fixed for this manuscript "
        "at commit 44d22c66c2adbdce8ebc2289844a8b26e6929bd5, releases the current Recovery-head fitting "
        "procedure, paired NLI scorer, authenticated historical HGB feature source, eligibility and allocation "
        "code, aggregate-analysis code, and a text-free 18,000-trace numeric bundle. The bundle replaces benchmark "
        "IDs with dataset-local opaque ordinals while retaining sibling grouping, stable tie order, eligibility, "
        "scores, actions, and numeric EM/F1 outcomes.\n\n"
        "Running scripts/reproduce_all.py in the locked non-neural environment exactly rebuilds all nine-policy "
        "point estimates and the fixed-seed 20,000-draw stratified question-cluster bootstrap, including repeated "
        "global top-K allocation and fixed-action sensitivity. The rebuilt files must equal the sealed public "
        "POINT_ESTIMATES and INTERVALS files; the workflow then runs tests and integrity checks.\n\n"
        "The release excludes benchmark text and original IDs, references, generated answers, retrieved passages, "
        "model weights, fitted paper bundles, development labels, other historical estimator assets, and private "
        "execution receipts. It therefore reproduces the reported statistical layer from the realized numeric "
        "traces, but cannot regenerate retrieval, candidate answers, neural scores, or fitted heads. Incomplete "
        "historical generation and legacy-component specifications also remain. The comparisons consequently "
        "condition on the realized candidate pairs and saved scores.",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if sha256(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("R3 source hash mismatch")
    if not EMBEDDED_BODY_FONT.is_file():
        raise RuntimeError(f"Required embedded body font is missing: {EMBEDDED_BODY_FONT}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open(SOURCE)

    fit_receipt = {}
    for page_index, (box, text) in REPLACEMENTS.items():
        page = document[page_index]
        for link in page.get_links():
            link_box = fitz.Rect(link["from"])
            if box.intersects(link_box):
                page.delete_link(link)
        page.add_redact_annot(box, fill=(1, 1, 1))
        page.apply_redactions()
        page.insert_font(fontname="TimesNewRomanEmbedded", fontfile=str(EMBEDDED_BODY_FONT))
        font_size = {18: 9.85, 20: 10.0}.get(page_index, 10.35)
        spare = page.insert_textbox(
            fitz.Rect(box.x0 + 3, box.y0 + 1, box.x1 - 2, box.y1 - 1),
            text,
            fontname="TimesNewRomanEmbedded",
            fontsize=font_size,
            lineheight=1.18,
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT,
            overlay=True,
        )
        if spare < 0:
            raise RuntimeError(f"Replacement overflow on page {page_index + 1}: {spare}")
        fit_receipt[str(page_index + 1)] = round(spare, 3)

    metadata = dict(document.metadata or {})
    metadata["title"] = "Supervision-Matched Selection of Paired RAG Repairs: An Empirical Study of Accuracy and Damage"
    metadata["author"] = "qianxingji"
    metadata["subject"] = "Post-generation selection of paired RAG repairs; reproducibility-aligned R5"
    # Freeze metadata so identical source/code/font inputs produce identical bytes.
    metadata["modDate"] = "D:20260916040000Z"
    document.set_metadata(metadata)
    work_pdf = ROOT / "tmp" / "pdfs" / "JIIS_Manuscript_R5_Reproducible.work.pdf"
    work_pdf.parent.mkdir(parents=True, exist_ok=True)
    if work_pdf.exists():
        work_pdf.unlink()
    document.save(work_pdf, garbage=4, deflate=True, clean=True, no_new_id=True)
    document.close()

    check = fitz.open(work_pdf)
    link_count = 0
    for page_index in (11, 16, 20):
        page = check[page_index]
        # Times New Roman exposes inserted hyphens as soft hyphens during text
        # extraction, so bind the stable URL prefix and extend over the full URL.
        for prefix_box in page.search_for("https://github.com/qianxingji/"):
            link_box = fitz.Rect(prefix_box.x0, prefix_box.y0, min(prefix_box.x1 + 90, page.rect.x1 - 30), prefix_box.y1)
            page.insert_link({"kind": fitz.LINK_URI, "from": link_box, "uri": PUBLIC_REPOSITORY})
            link_count += 1
    if link_count != 3:
        raise RuntimeError(f"Expected three public-repository links, found {link_count}")
    if len(check) != 21:
        raise RuntimeError("Unexpected R5 page count")
    text = re.sub(r"\s+", " ", "\n".join(page.get_text() for page in check).replace("\u00ad", "-"))
    for required in (PUBLIC_REPOSITORY, PUBLIC_COMMIT, "src/arbitration/empirical_panel.py", "scripts/reproduce_all.py", "20,000-draw"):
        if required not in text:
            raise RuntimeError("Missing inserted text: " + required)
    for stale in (
        "fd5c6f11fd4308c9442218b02e39428110bbd36d",
        "a6da7d80aca082301824b320ec4698c0dfac7b12",
        "candidate is reported as rebuilt and checked",
        "cannot reconstruct the per-question top-K bootstrap",
    ):
        if stale in text:
            raise RuntimeError("Stale R3 release text remains: " + stale)
    if OUTPUT.exists():
        OUTPUT.unlink()
    check.save(OUTPUT, garbage=4, deflate=True, clean=True, no_new_id=True)
    check.close()
    print({"status": "PASS_JIIS_R5_BUILD", "output": str(OUTPUT), "sha256": sha256(OUTPUT), "spare_height": fit_receipt, "repository_links": link_count})


if __name__ == "__main__":
    main()
