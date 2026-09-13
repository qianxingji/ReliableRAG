#!/usr/bin/env python3
"""Build manuscript tables and vector figures from sealed aggregate evidence.

This script deliberately reads only accepted aggregate JSON.  It never reads
Gold strings, answer text, per-trace outcomes, bootstrap draws, or model files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path
from typing import Iterable

import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


POINT_SHA256 = "b03ddad8fa35f582a63403c029942104c3f5da1a961110edc2a62f09871f4d3b"
INTERVAL_SHA256 = "6d454afeec7c125c0cc4d182556af6db214a867aa4f62f7a6fbd1e6e22b09331"
REPORTLAB_VERSION = "4.4.9"
VERA_SHA256 = "c4c45690b345435b2cba52ecabe275f05e49b389b39fe68ad03afbb551288d3d"
VERA_BOLD_SHA256 = "cc037385e4d55bfde89b13e03091ee93bf40c0c52ddd391ff031ab276f13b8e9"
POLICIES = (
    "Keep", "HGB", "GbV", "ROA-FULL", "ROA-NOGBV", "HGB_GBV_R",
    "HGB_ONLY_R", "GBV_ONLY_R", "V2",
)
DISPLAY = {
    "HGB_GBV_R": r"HGB+GbV$_R$",
    "HGB_ONLY_R": r"HGB-only$_R$",
    "GBV_ONLY_R": r"GbV-only$_R$",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, expected: str) -> dict:
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(f"sealed hash mismatch for {path}: {actual} != {expected}")
    return json.loads(path.read_text(encoding="utf-8"))


def signed(value: float) -> str:
    return f"{value:+.4f}"


def interval(bounds: Iterable[float]) -> str:
    lo, hi = bounds
    return f"[{lo:+.4f}, {hi:+.4f}]"


def name(policy: str) -> str:
    return DISPLAY.get(policy, policy)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def main_results(points: dict) -> str:
    rows = []
    for policy in POLICIES:
        p = points["policies"][policy]
        rows.append(
            f"{name(policy)} & {p['replacements']:,} & {p['recovery']:,} & "
            f"{p['damage']:,} & {p['neutral']:,} & {p['net']:+,} & "
            f"{100*p['em_rate']:.4f} & {p['delta_em_pp']:+.4f} & "
            f"{100*p['token_f1']:.4f} & {p['delta_f1_pp']:+.4f} & "
            f"{p['damage_rate_pp']:.4f} \\\\"
        )
    return "\n".join([
        "% Generated from sealed POINT_ESTIMATES.json; do not edit by hand.",
        r"\begin{tabular}{lrrrrrrrrrr}",
        r"\toprule",
        r"Policy & Act. & Rec. & Dmg. & Neu. & Net & EM (\%) & $\Delta$EM (pp) & F1 (\%) & $\Delta$F1 (pp) & Dmg. rate (\%) \\",
        r"\midrule",
        *rows,
        r"\bottomrule",
        r"\end{tabular}",
    ])


def comparison_rows(intervals: dict, mode: str) -> str:
    rows = []
    for c in intervals[mode]["comparisons"]:
        em = c["endpoints"]["em_difference_pp"]
        dmg = c["endpoints"]["damage_rate_difference_pp"]
        decision = "Met" if c["joint_em_improvement_and_damage_reduction"] else "Not met"
        rows.append(
            f"{name(c['left'])} $-$ {name(c['right'])} & {signed(em['point_pp'])} & "
            f"{interval(em['adjusted_percentile_range_pp'])} & {signed(dmg['point_pp'])} & "
            f"{interval(dmg['adjusted_percentile_range_pp'])} & {decision} \\\\"
        )
    role = "Primary, top-$K$ reallocated within each bootstrap draw" if mode == "reallocated" else "Sensitivity, actions held fixed"
    return "\n".join([
        f"% {role}; generated from sealed INTERVALS.json.",
        r"\begin{tabular}{lrrrrl}",
        r"\toprule",
        r"Ordered comparison & $\Delta$EM & Adjusted range & $\Delta$Damage & Adjusted range & Joint rule \\",
        r"\midrule",
        *rows,
        r"\bottomrule",
        r"\end{tabular}",
    ])


def study_design() -> str:
    rows = [
        ("Question groups / traces", "6,000 / 18,000"),
        ("Datasets", "HotpotQA, 2WikiMultiHopQA, MuSiQue; 2,000 questions each"),
        ("Retrievers", "BM25, BGE dense, hybrid RRF; one sibling trace per question"),
        ("Dataset-specific pool sizes", "19,352; 11,746; 23,618 documents (54,716 total)"),
        ("Reader", r"Qwen2.5-3B-Instruct, revision \texttt{aa8e7253\ldots 04d1}"),
        ("Development supervision", "4,500 questions / 13,500 traces; 3,600 fit + 900 calibration"),
        ("Fresh eligibility / denominator", "4,267 / 18,000 traces"),
        ("Action allocation", r"Global $K=900$ for each switching policy; Keep selects zero"),
        ("Primary resampling", "20,000 dataset-stratified question-cluster draws"),
    ]
    body = [f"{a} & {b} \\\\" for a, b in rows]
    return "\n".join([
        "% Generated/frozen study-design summary.",
        r"\begin{tabular}{p{0.31\linewidth}p{0.63\linewidth}}",
        r"\toprule", r"Component & Frozen setting \\", r"\midrule", *body,
        r"\bottomrule", r"\end{tabular}",
    ])


def breakdown(points: dict, dimension: str) -> str:
    rows = []
    for cell in points["fixed_global_action_breakdowns"][dimension]:
        label = cell["cell"].replace("_", r"\_")
        for policy in POLICIES:
            p = cell["policies"][policy]
            rows.append(
                f"{label} & {name(policy)} & {p['replacements']:,} & {p['recovery']:,} & "
                f"{p['damage']:,} & {p['net']:+,} & {p['delta_em_pp']:+.4f} & "
                f"{p['delta_f1_pp']:+.4f} \\\\"
            )
    return "\n".join([
        "% Secondary descriptive breakdown; global actions are not reallocated per cell.",
        r"\begin{longtable}{llrrrrrr}",
        r"\toprule", r"Cell & Policy & Act. & Rec. & Dmg. & Net & $\Delta$EM (pp) & $\Delta$F1 (pp) \\",
        r"\midrule", r"\endfirsthead", r"\toprule",
        r"Cell & Policy & Act. & Rec. & Dmg. & Net & $\Delta$EM (pp) & $\Delta$F1 (pp) \\",
        r"\midrule", r"\endhead", *rows, r"\bottomrule", r"\end{longtable}",
    ])


class Pdf:
    """Deterministic one-page vector PDF writer with embedded Vera fonts."""

    regular_name = "ReliableRAGVera"
    bold_name = "ReliableRAGVeraBold"
    registered = False

    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.ops: list[tuple] = []

    def line(self, x1, y1, x2, y2, width=1, rgb=(0, 0, 0)):
        self.ops.append(("line", x1, y1, x2, y2, width, rgb))

    def rect(self, x, y, w, h, fill=(1, 1, 1), stroke=(0, 0, 0)):
        self.ops.append(("rect", x, y, w, h, fill, stroke))

    def text(self, x, y, value, size=10, bold=False, rgb=(0, 0, 0)):
        self.ops.append(("text", x, y, value, size, bold, rgb))

    def circle(self, x, y, r, fill=(0.2, 0.4, 0.7)):
        self.ops.append(("circle", x, y, r, fill))

    @classmethod
    def register_fonts(cls) -> tuple[Path, Path]:
        font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
        regular = font_dir / "Vera.ttf"
        bold = font_dir / "VeraBd.ttf"
        if reportlab.Version != REPORTLAB_VERSION:
            raise RuntimeError(f"ReportLab version mismatch: {reportlab.Version} != {REPORTLAB_VERSION}")
        if sha256(regular) != VERA_SHA256 or sha256(bold) != VERA_BOLD_SHA256:
            raise RuntimeError("ReportLab Vera font hash mismatch")
        if not cls.registered:
            pdfmetrics.registerFont(TTFont(cls.regular_name, str(regular)))
            pdfmetrics.registerFont(TTFont(cls.bold_name, str(bold)))
            cls.registered = True
        return regular, bold

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.register_fonts()
        canvas = Canvas(
            str(path),
            pagesize=(self.width, self.height),
            invariant=1,
            pageCompression=0,
            initialFontName=self.regular_name,
        )
        for op in self.ops:
            if op[0] == "line":
                _, x1, y1, x2, y2, width, rgb = op
                canvas.setStrokeColorRGB(*rgb)
                canvas.setLineWidth(width)
                canvas.line(x1, y1, x2, y2)
            elif op[0] == "rect":
                _, x, y, w, h, fill, stroke = op
                canvas.setFillColorRGB(*fill)
                canvas.setStrokeColorRGB(*stroke)
                canvas.rect(x, y, w, h, stroke=1, fill=1)
            elif op[0] == "text":
                _, x, y, value, size, bold, rgb = op
                canvas.setFillColorRGB(*rgb)
                canvas.setFont(self.bold_name if bold else self.regular_name, size)
                canvas.drawString(x, y, value)
            elif op[0] == "circle":
                _, x, y, r, fill = op
                canvas.setFillColorRGB(*fill)
                canvas.circle(x, y, r, stroke=0, fill=1)
            else:
                raise RuntimeError(f"unknown PDF operation: {op[0]}")
        canvas.showPage()
        canvas.save()


def pipeline_figure(path: Path) -> None:
    p = Pdf(720, 300)
    boxes = [
        (25, 195, 125, 48, "Retrieve top-5", "q -> E0"),
        (220, 195, 140, 48, "Generate a0", "inputs: q + E0"),
        (220, 120, 140, 48, "Generate repair query", "inputs: q + E0"),
        (415, 120, 125, 48, "Retrieve / replace", "depth 50 / rank 5 -> E1"),
        (585, 120, 110, 48, "Generate a1", "inputs: q + E1"),
    ]
    for x, y, w, h, t1, t2 in boxes:
        p.rect(x, y, w, h, (0.93, 0.96, 0.99), (0.18, 0.34, 0.52))
        p.text(x + 8, y + 29, t1, 10, True)
        p.text(x + 8, y + 12, t2, 8)
    p.line(150, 219, 218, 219, 1.4, (0.18, 0.34, 0.52))
    p.line(88, 195, 88, 144, 1.4, (0.18, 0.34, 0.52))
    p.line(88, 144, 218, 144, 1.4, (0.18, 0.34, 0.52))
    p.line(360, 144, 413, 144, 1.4, (0.18, 0.34, 0.52))
    p.line(540, 144, 583, 144, 1.4, (0.18, 0.34, 0.52))
    p.text(26, 99, "a0 is not an input to the repair query.", 9)
    p.rect(240, 35, 455, 55, (0.97, 0.95, 0.88), (0.55, 0.42, 0.12))
    p.text(260, 68, "Precompute label-free scores for fixed (a0, a1)", 10, True)
    p.text(260, 49, "Each switching policy selects K=900 traces; Keep selects zero.", 10)
    p.line(290, 195, 385, 180, 1.1, (0.35, 0.35, 0.35))
    p.line(385, 180, 385, 91, 1.1, (0.35, 0.35, 0.35))
    p.line(640, 120, 640, 91, 1.1, (0.35, 0.35, 0.35))
    p.text(25, 269, "Shared candidate acquisition occurs before every policy decision", 13, True)
    p.text(25, 18, "Gold references are opened only after all policy action memberships are sealed.", 9)
    p.save(path)


def scatter_figure(points: dict, path: Path) -> None:
    p = Pdf(720, 470)
    left, bottom, right, top = 85, 80, 665, 405
    p.line(left, bottom, right, bottom, 1.2)
    p.line(left, bottom, left, top, 1.2)
    xmax, ymax = 0.23, 2.2
    for i in range(6):
        x = i * 0.04
        px = left + (x / xmax) * (right - left)
        p.line(px, bottom, px, top, 0.3, (0.82, 0.82, 0.82))
        p.text(px - 8, bottom - 20, f"{x:.2f}", 8)
    for i in range(6):
        y = i * 0.4
        py = bottom + (y / ymax) * (top - bottom)
        p.line(left, py, right, py, 0.3, (0.82, 0.82, 0.82))
        p.text(left - 36, py - 3, f"{y:.1f}", 8)
    colors = {
        "Keep": (0.25, 0.25, 0.25), "HGB_GBV_R": (0.78, 0.16, 0.12),
        "HGB_ONLY_R": (0.12, 0.42, 0.68), "GBV_ONLY_R": (0.18, 0.60, 0.35),
    }
    offsets = {
        "Keep": (7, 7), "HGB": (7, -14), "GbV": (12, -23), "ROA-FULL": (-40, 10),
        "ROA-NOGBV": (8, 9), "HGB_GBV_R": (8, 8), "HGB_ONLY_R": (8, -15),
        "GBV_ONLY_R": (-83, 6), "V2": (8, 7),
    }
    for policy in POLICIES:
        row = points["policies"][policy]
        x = row["damage_rate_pp"]
        y = 100 * row["recovery"] / points["N_all"]
        px = left + (x / xmax) * (right - left)
        py = bottom + (y / ymax) * (top - bottom)
        p.circle(px, py, 5 if policy == "HGB_GBV_R" else 4, colors.get(policy, (0.45, 0.45, 0.45)))
        dx, dy = offsets[policy]
        if policy in ("GbV", "GBV_ONLY_R"):
            end_x = px + dx + (57 if dx < 0 else -2)
            p.line(px, py, end_x, py + dy + 3, 0.6, (0.4, 0.4, 0.4))
        p.text(px + dx, py + dy, name(policy).replace("$_R$", "_R"), 8, policy == "HGB_GBV_R")
    p.text(235, 32, "Damage rate over all 18,000 traces (%)", 10, True)
    p.text(85, 420, "Recovery rate over all 18,000 traces (%)", 10, True)
    p.text(85, 445, "Descriptive recovery-damage positions at the fixed global action allocation", 13, True)
    p.save(path)


def deterministic_pdf(path: Path, render) -> None:
    """Render twice in isolated directories and publish only byte-identical output."""
    with tempfile.TemporaryDirectory(prefix="cas_q3_figure_") as temporary:
        base = Path(temporary)
        first = base / "first.pdf"
        second = base / "second.pdf"
        render(first)
        render(second)
        if first.read_bytes() != second.read_bytes():
            raise RuntimeError(f"nondeterministic vector PDF render: {path.name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(first.read_bytes())


def build(root: Path) -> dict:
    source = root / "outputs" / "cas_q2" / "empirical_analysis_v1"
    points = load_json(source / "POINT_ESTIMATES.json", POINT_SHA256)
    intervals = load_json(source / "INTERVALS.json", INTERVAL_SHA256)
    if tuple(points["policies"]) != POLICIES:
        raise RuntimeError("policy order or membership changed")
    if points["N_all"] != 18000 or points["question_groups"] != 6000 or points["primary_global_cap"] != 900:
        raise RuntimeError("frozen study cardinality changed")
    if intervals["draws"] != 20000 or intervals["interval_family_size"] != 6:
        raise RuntimeError("frozen statistical family changed")

    paper = root / "paper"
    write(paper / "tables" / "study_design.tex", study_design())
    write(paper / "tables" / "main_results.tex", main_results(points))
    write(paper / "tables" / "primary_comparisons.tex", comparison_rows(intervals, "reallocated"))
    write(paper / "tables" / "fixed_action_sensitivity.tex", comparison_rows(intervals, "fixed_action"))
    write(paper / "tables" / "dataset_breakdown.tex", breakdown(points, "dataset"))
    write(paper / "tables" / "retriever_breakdown.tex", breakdown(points, "retriever"))
    deterministic_pdf(
        paper / "figures" / "paired_pipeline.pdf",
        pipeline_figure,
    )
    deterministic_pdf(
        paper / "figures" / "recovery_damage.pdf",
        lambda path: scatter_figure(points, path),
    )

    outputs = [
        paper / "tables" / "study_design.tex",
        paper / "tables" / "main_results.tex",
        paper / "tables" / "primary_comparisons.tex",
        paper / "tables" / "fixed_action_sensitivity.tex",
        paper / "tables" / "dataset_breakdown.tex",
        paper / "tables" / "retriever_breakdown.tex",
        paper / "figures" / "paired_pipeline.pdf",
        paper / "figures" / "recovery_damage.pdf",
    ]
    receipt = {
        "schema_version": 1,
        "decision": "PASS_AGGREGATE_ONLY_MANUSCRIPT_ASSET_BUILD",
        "sources": {
            "outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json": POINT_SHA256,
            "outputs/cas_q2/empirical_analysis_v1/INTERVALS.json": INTERVAL_SHA256,
        },
        "scientific_fits": 0,
        "model_forwards": 0,
        "gold_or_answer_text_read": False,
        "vector_pdf_renderer": {
            "engine": f"ReportLab {REPORTLAB_VERSION}",
            "regular_font": "Bitstream Vera",
            "regular_font_sha256": VERA_SHA256,
            "bold_font": "Bitstream Vera Bold",
            "bold_font_sha256": VERA_BOLD_SHA256,
            "font_embedding": "subset_embedded_true_type",
            "deterministic_pdf_mode": True,
            "two_build_byte_identity_required": True,
        },
        "outputs": {str(p.relative_to(root)).replace("\\", "/"): sha256(p) for p in outputs},
    }
    write(paper / "ASSET_RECEIPT.json", json.dumps(receipt, indent=2, sort_keys=True))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    receipt = build(args.root.resolve())
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
