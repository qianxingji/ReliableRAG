#!/usr/bin/env python3
"""Build the JIIS R6 major revision from the verified R5 PDF."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re

import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/pdf/JIIS_Manuscript_R5_Reproducible.pdf"
OUTPUT = ROOT / "output/pdf/JIIS_Manuscript_R6_Major_Revision.pdf"
SOURCE_SHA256 = "fdb055b765899bc71e3d0258c4e65e3a70a10bccd7bb409e9ac73f32c7f0258b"
PUBLIC_URL = "https://github.com/qianxingji/ReliableRAG-Code"
PUBLIC_COMMIT = "038d769e96d092a2eec3bbc5df9f45f3c2a17ff0"
FONT = Path(r"C:\Windows\Fonts\times.ttf")


REPLACEMENTS = {
    1: (
        fitz.Rect(59, 63, 536, 178),
        "Prior work already predicts benefit between two generated answers, so selection itself is not claimed as "
        "new. Our empirical contribution is controlled signal attribution: the original/repaired RAG candidates, "
        "downstream fit/calibration recipe, eligibility, and 900-action allocation are held fixed, and EM gain and "
        "harmful replacement must improve jointly. This separates an observed signal increment from differences in "
        "supervision or intervention frequency.\n\n"
        "Across five matched heads and four contextual policies, adding HGB to GbV-only passes the joint rule, "
        "whereas adding GbV to the stronger HGB-only head does not. This directional boundary and full-population "
        "Recovery/Damage accounting are the contribution. They remain conditional on one reader and candidate "
        "pipeline and are neither a new architecture nor an interaction test.",
    ),
    4: (
        fitz.Rect(59, 249, 536, 333),
        "The five fitted heads share 4,500 development questions and 13,500 traces. A deterministic within-dataset "
        "hash order assigns 3,600 questions (10,800 traces) to fitting and 900 questions (2,700 traces) to disjoint "
        "calibration, with retriever siblings kept together. Eligibility is then applied inside each partition. "
        "Every base head therefore fits 2,572 eligible traces: 2,015 negatives and 557 Recovery positives. Every "
        "Platt calibrator uses 630 eligible traces: 498 negatives and 132 positives. These are the effective "
        "numerical sample sizes; 10,800 and 2,700 are partition population counts.",
    ),
    9: (
        fitz.Rect(59, 92, 536, 190),
        "The public record separates reproducibility levels. The released text-free development bundle contains "
        "13,500 numeric traces with opaque group identities, frozen fit/calibration roles, eligibility, 11 score "
        "inputs, and binary EM outcomes. It exactly refits the five current Recovery heads (five base models plus "
        "five Platt calibrators) and checks preprocessing values, coefficients, iterations, target counts, and "
        "design hashes. A separate 18,000-trace evaluation bundle exactly reconstructs all point estimates and the "
        "20,000-draw question-cluster bootstrap. These are full current-head and statistical reproductions from "
        "realized numeric inputs, not end-to-end regeneration of retrieval, candidate answers, or neural scores.",
    ),
    11: (
        fitz.Rect(59, 198, 536, 370),
        "Project-authored method and reporting code is publicly available at "
        "https://github.com/qianxingji/ReliableRAG-Code under Apache License 2.0. This manuscript is bound to commit "
        "038d769e96d092a2eec3bbc5df9f45f3c2a17ff0. The release contains the authenticated historical HGB source, "
        "paired NLI scorer, current-head fitting code, accepted parameter records, a text-free 13,500-trace "
        "development bundle, and a text-free 18,000-trace evaluation bundle. One public command exactly refits all "
        "five current heads, rebuilds all nine-policy point estimates and the complete 20,000-draw question-cluster "
        "bootstrap, and runs reporting and repository-integrity checks.\n\n"
        "The development fit has 2,572 eligible traces (557 positive) and calibration has 630 (132 positive). "
        "Benchmark text and original IDs, references, generated answers, retrieved passages, model weights, "
        "historical learned estimators, and private forensic records are not redistributed. The release therefore "
        "does not regenerate retrieval, candidate generation, neural scoring, or historical upstream training. "
        "Third-party data and models remain under their own terms; Appendix J states the same boundary.",
    ),
    16: (
        fitz.Rect(59, 64, 536, 106),
        "The eligible fitting/calibration totals are 2,572/630 rather than the partition totals 10,800/2,700. "
        "Their class counts are 2,015 negative and 557 positive for fitting, and 498 negative and 132 positive for "
        "calibration. All five current heads use these same rows and Recovery labels.",
    ),
    16.1: (
        fitz.Rect(59, 419, 536, 753),
        "The public source release is ReliableRAG-Code at Git commit "
        "038d769e96d092a2eec3bbc5df9f45f3c2a17ff0; the repository URL is "
        "https://github.com/qianxingji/ReliableRAG-Code. Key Git blobs are:\n\n"
        "Current-head fitting: src/arbitration/empirical_panel.py, blob "
        "f27090ee94a04c4fc693dd9d0a61380660db13e9; contract/target: "
        "src/arbitration/empirical_contract.py, blob 60bdaa96ef27072e856f30a1f163b3c768f240d1; paired NLI: "
        "src/verification/gbv_nli.py, blob 8be2e0b54e6ff0fce61aba361b4fa4785904b724.\n\n"
        "The text-free development bundle DEVELOPMENT_NUMERIC.jsonl.gz has SHA-256 "
        "8867daa8c8d827d5aa928627d8de068656e35760b47f784c38d328a369afe7f0. It contains 13,500 "
        "opaque-identity rows, including 2,572 eligible fit rows (557 positive) and 630 eligible calibration rows "
        "(132 positive). CURRENT_HEADS.json has SHA-256 "
        "a519b80b08ece87c59d296a3b590a1cda31de16122c68a1e0efe5a2c27f1e5ea and records all preprocessing "
        "values, base coefficients/intercepts, Platt slope/intercept, iterations, target counts, and hashes. "
        "scripts/reproduce_current_heads.py (blob 9b150b1f1183b7e927b80c871c8b53cfda37ce9b) refits all ten logistic models exactly.\n\n"
        "The evaluation bundle has SHA-256 a930286d62bddf9f4837cb1beb4b863f0f94c1bc697b2311977a9b0eb18f09f7; "
        "scripts/reproduce_paper_statistics.py (blob 19322ba6dcb3bf818e4bcda123041bb6ee2c2ace) reconstructs all "
        "18,000 evaluation rows, point estimates, and bootstrap results. For each base head of width d, the fitted "
        "model has d coefficients plus one intercept; the Platt model adds a slope and intercept. Thus ROA-FULL, "
        "ROA-NOGBV, HGB+GbV_R, HGB-only_R, and GbV-only_R contain 28, 26, 10, 8, and 8 learned scalar parameters, "
        "respectively, excluding stored preprocessing statistics.",
    ),
    18: (
        fitz.Rect(59, 134, 536, 292),
        "The authenticated historical HGB feature source is publicly released as src/mars/state_symmetric.py at "
        "commit 038d769e96d092a2eec3bbc5df9f45f3c2a17ff0; its SHA-256 is "
        "3724b5ac77722b70cabdf2589379d5584942f34ec81f3f5a04f88e0665f8f717. The historical model-binding file "
        "src/mars/full_experiment.py has SHA-256 65713509ef6c8d094bb44ad2c47b0238ceade607616d3e729b31c56096326d50 "
        "and remains outside the public release.\n\n"
        "The original saved HGB artifact is 639,652 bytes with SHA-256 "
        "9245170f855435b5603b04013bd4fbab79a75d2761853a012ab9f3259600bf6e. Source-assembled replay reproduced "
        "all 1,539 HGB scores with zero numerical error. The serialized replay differed only in saved CPU-thread "
        "metadata (one rather than six); observed learned arrays and tree fields matched. Original per-estimator "
        "fit-time ID/matrix receipts and an independent original-fit witness remain unavailable, so this supports "
        "saved-computation equivalence, not independent authentication of the original training event.",
    ),
    20: (
        fitz.Rect(59, 83, 536, 370),
        "The public repository at https://github.com/qianxingji/ReliableRAG-Code, fixed for this manuscript at "
        "commit 038d769e96d092a2eec3bbc5df9f45f3c2a17ff0, releases the current Recovery-head fitting procedure, accepted "
        "current-head parameter records, paired NLI scorer, authenticated historical HGB feature source, "
        "eligibility/allocation code, and two text-free numeric bundles.\n\n"
        "The 13,500-row development bundle retains opaque sibling groups, frozen fit/calibration roles, eligibility, "
        "11 numeric inputs, and binary EM outcomes. Running scripts/reproduce_current_heads.py exactly refits five "
        "base logistic heads and five disjoint Platt calibrators. It verifies the accepted preprocessing, learned "
        "parameters, iterations, target counts, ranking metadata, and design hashes. The effective fit/calibration "
        "sizes are 2,572/630, with 557/132 Recovery positives.\n\n"
        "The 18,000-row evaluation bundle retains opaque sibling groups, stable tie order, eligibility, scores, "
        "actions, and numeric EM/F1 outcomes. The complete public workflow exactly rebuilds all nine-policy point "
        "estimates and the fixed-seed 20,000-draw stratified question-cluster bootstrap, including repeated global "
        "top-K allocation and fixed-action sensitivity.\n\n"
        "The release excludes benchmark text and original IDs, references, generated answers, retrieved passages, "
        "model weights, historical fitted estimators, and private execution receipts. It cannot regenerate retrieval, "
        "candidate answers, neural scores, or historical upstream training. Incomplete historical generation and "
        "legacy-component specifications remain; the comparisons condition on realized candidate pairs and saved "
        "scores.",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if sha256(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("R5 source hash mismatch")
    document = fitz.open(SOURCE)
    spare_heights = {}
    for key, (box, text) in REPLACEMENTS.items():
        page_index = int(key)
        page = document[page_index]
        for link in page.get_links():
            if box.intersects(fitz.Rect(link["from"])):
                page.delete_link(link)
        page.add_redact_annot(box, fill=(1, 1, 1))
        page.apply_redactions()
        page.insert_font(fontname="TimesNewRomanEmbedded", fontfile=str(FONT))
        font_size = {1: 9.8, 11: 9.8}.get(key, 10.1)
        spare = page.insert_textbox(
            fitz.Rect(box.x0 + 3, box.y0 + 1, box.x1 - 2, box.y1 - 1),
            text,
            fontname="TimesNewRomanEmbedded",
            fontsize=font_size,
            lineheight=1.16,
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT,
            overlay=True,
        )
        if spare < 0:
            raise RuntimeError(f"replacement overflow for {key}: {spare}")
        spare_heights[str(key)] = round(spare, 3)

    metadata = dict(document.metadata or {})
    metadata["subject"] = "JIIS major revision R6: contribution, effective samples, fitted parameters, and exact current-head refit"
    metadata["modDate"] = "D:20260916120000Z"
    document.set_metadata(metadata)
    work = ROOT / "tmp/pdfs/JIIS_Manuscript_R6_Major_Revision.work.pdf"
    work.parent.mkdir(parents=True, exist_ok=True)
    if work.exists():
        work.unlink()
    document.save(work, garbage=4, deflate=True, clean=True, no_new_id=True)
    document.close()

    check = fitz.open(work)
    links = 0
    for page_index in (11, 16, 20):
        page = check[page_index]
        for prefix_box in page.search_for("https://github.com/qianxingji/"):
            box = fitz.Rect(prefix_box.x0, prefix_box.y0, min(prefix_box.x1 + 90, page.rect.x1 - 30), prefix_box.y1)
            page.insert_link({"kind": fitz.LINK_URI, "from": box, "uri": PUBLIC_URL})
            links += 1
    text = re.sub(r"\s+", " ", "\n".join(page.get_text() for page in check).replace("\u00ad", "-"))
    required = (
        PUBLIC_COMMIT,
        "2,572 eligible traces",
        "557 Recovery positives",
        "630 eligible traces",
        "132 positives",
        "28, 26, 10, 8, and 8 learned scalar parameters",
        "scripts/reproduce_current_heads.py",
        "exactly refits the five current Recovery heads",
        "adding HGB to GbV-only passes the joint rule",
    )
    for marker in required:
        if marker not in text:
            raise RuntimeError("missing marker: " + marker)
    stale = (
        "44d22c66c2adbdce8ebc2289844a8b26e6929bd5",
        "public materials do not report the eligible fitting/calibration row totals",
        "does not regenerate the neural acquisition or refit the paper heads",
        "not sufficient to reconstruct selection within the question-cluster bootstrap",
    )
    for marker in stale:
        if marker in text:
            raise RuntimeError("stale marker remains: " + marker)
    if links != 3:
        raise RuntimeError(f"expected three repository links, got {links}")
    if OUTPUT.exists():
        OUTPUT.unlink()
    check.save(OUTPUT, garbage=4, deflate=True, clean=True, no_new_id=True)
    check.close()
    print({"status": "PASS_JIIS_R6_BUILD", "output": str(OUTPUT), "sha256": sha256(OUTPUT), "links": links, "spare_heights": spare_heights})


if __name__ == "__main__":
    main()
