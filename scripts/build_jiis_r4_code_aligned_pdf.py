#!/usr/bin/env python3
"""Build the code-aligned JIIS R4 PDF from the author-designated R3 PDF.

R3 is retained byte-for-byte. This builder replaces only the four paragraphs
whose repository-release state changed after R3 was compiled.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re

import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "source_reference" / "JIIS_Manuscript_R3.pdf"
OUTPUT = ROOT / "output" / "pdf" / "JIIS_Manuscript_R4_Code_Aligned.pdf"
SOURCE_SHA256 = "b01683e3431cd01c62739c66cd6045395f30362234c04f3315458602eebf6c2e"
PUBLIC_REPOSITORY = "https://github.com/qianxingji/ReliableRAG-Code"
PUBLIC_COMMIT = "a6da7d80aca082301824b320ec4698c0dfac7b12"
EMBEDDED_BODY_FONT = Path(r"C:\Windows\Fonts\times.ttf")


REPLACEMENTS = {
    11: (
        fitz.Rect(59, 198, 536, 370),
        "Project-authored method and reporting code is publicly available at "
        "https://github.com/qianxingji/ReliableRAG-Code under Apache License 2.0. "
        "This manuscript is bound to commit a6da7d80aca082301824b320ec4698c0dfac7b12. "
        "The release contains the authenticated historical HGB source, paired NLI scorer, "
        "supervision-matched logistic fitting and disjoint calibration procedure, fixed selection "
        "and analysis kernels, sealed aggregate point estimates and intervals, and runnable tests.\n\n"
        "Benchmark text, model weights, generated answers, per-question outcomes and action "
        "memberships, fitted paper parameters, and private forensic records are not redistributed. "
        "The released verifier checks 129 aggregate reporting statements but cannot reconstruct "
        "the per-question top-K bootstrap or the complete 18,000-trace neural acquisition. Third-party "
        "data and models remain under their own terms. Appendix J states this reproduction boundary.",
    ),
    16: (
        fitz.Rect(59, 419, 536, 753),
        "The public source release is ReliableRAG-Code at Git commit "
        "a6da7d80aca082301824b320ec4698c0dfac7b12. The repository URL is "
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
        "The fitting interface records sample_count, class_counts, target_counts, partition/design hashes, "
        "preprocessing values, coefficients, and Platt parameters. The public release exposes the runnable "
        "procedure but not the labeled rows or fitted paper bundles. Development-probe predictions are "
        "saved-parameter checks, not held-out performance estimates.",
    ),
    18: (
        fitz.Rect(59, 134, 536, 292),
        "The authenticated historical HGB feature source is publicly released as "
        "src/mars/state_symmetric.py at commit a6da7d80aca082301824b320ec4698c0dfac7b12; "
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
        "at commit a6da7d80aca082301824b320ec4698c0dfac7b12, releases the current Recovery-head fitting "
        "procedure, paired NLI scorer, authenticated historical HGB feature source, eligibility and allocation "
        "code, aggregate-analysis code, sealed aggregate point estimates and intervals, and tests. Its aggregate "
        "verifier checks 129 reported statements.\n\n"
        "The release excludes raw benchmark text, model weights, generated answer text, per-question scores, "
        "eligibility/grouping rows, reference-derived outcomes, action memberships, fitted paper bundles, other "
        "historical estimator assets, bootstrap multiplicities, and private ledgers. It therefore supports source "
        "inspection and aggregate reporting verification, not independent reconstruction of the per-question "
        "top-K bootstrap or end-to-end neural regeneration.\n\n"
        "Three evidence levels remain distinct. First, the public interfaces in Appendix D.3 specify current "
        "fitting and NLI scoring. Second, this paper and the released aggregate JSON specify the fixed comparison, "
        "event counts, HGB construction, and statistical ranges. Third, the excluded per-question and fitted-asset "
        "records are required to reconstruct the complete selected action sets. Passing public tests does not "
        "replace those records. Candidate acquisition also cannot be fully reconstructed because the literal "
        "generation prompts, exact historical lexical tokenizer, and complete definitions of other legacy score "
        "sources are unavailable. The comparisons consequently condition on the realized candidate pairs and "
        "saved scores.",
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
    metadata["subject"] = "Post-generation selection of paired RAG repairs; code-aligned R4"
    metadata["modDate"] = datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%SZ")
    document.set_metadata(metadata)
    work_pdf = ROOT / "tmp" / "pdfs" / "JIIS_Manuscript_R4_Code_Aligned.work.pdf"
    work_pdf.parent.mkdir(parents=True, exist_ok=True)
    if work_pdf.exists():
        work_pdf.unlink()
    document.save(work_pdf, garbage=4, deflate=True, clean=True)
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
        raise RuntimeError("Unexpected R4 page count")
    text = re.sub(r"\s+", " ", "\n".join(page.get_text() for page in check).replace("\u00ad", "-"))
    for required in (PUBLIC_REPOSITORY, PUBLIC_COMMIT, "src/arbitration/empirical_panel.py", "129 reported statements"):
        if required not in text:
            raise RuntimeError("Missing inserted text: " + required)
    for stale in ("fd5c6f11fd4308c9442218b02e39428110bbd36d", "candidate is reported as rebuilt and checked"):
        if stale in text:
            raise RuntimeError("Stale R3 release text remains: " + stale)
    if OUTPUT.exists():
        OUTPUT.unlink()
    check.save(OUTPUT, garbage=4, deflate=True, clean=True)
    check.close()
    print({"status": "PASS_JIIS_R4_BUILD", "output": str(OUTPUT), "sha256": sha256(OUTPUT), "spare_height": fit_receipt, "repository_links": link_count})


if __name__ == "__main__":
    main()
