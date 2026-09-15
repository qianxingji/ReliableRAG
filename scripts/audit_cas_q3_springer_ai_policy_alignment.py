#!/usr/bin/env python3
"""Freeze a bounded mapping of current Springer Nature AI policy to P0-I."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "cas_q3" / "P0_I_SPRINGER_NATURE_AI_POLICY_ALIGNMENT.json"
DEFAULT_ACCEPTANCE = ROOT / "docs" / "cas_q3" / "P0_I_SPRINGER_NATURE_AI_POLICY_ALIGNMENT.md"
ACCESSED_DATE = "2026-09-15"

SOURCES = (
    {
        "authority": "Springer Nature policy-update announcement",
        "url": "https://group.springernature.com/gp/group/media/press-releases/sn-policy-responsible-ai-use/53209516",
        "facts": [
            "Springer Nature announced the updated AI policy framework on 2026-09-10.",
        ],
    },
    {
        "authority": "Springer Nature journal-specific author guidance",
        "url": "https://link.springer.com/journal/10489/submission-guidelines",
        "facts": [
            "LLM use beyond AI-assisted copy editing should be documented in the Methods section or a suitable alternative.",
            "Human accountability for the final text and author agreement are required.",
        ],
    },
    {
        "authority": "Springer Nature editorial policy",
        "url": "https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation",
        "facts": [
            "Drafting and structuring with author input require disclosure, verification, and author accountability.",
            "Arguments, interpretations, and conclusions must remain author-led.",
            "AI-assisted visual or code generation must use verifiable inputs and receive human review and validation.",
        ],
    },
    {
        "authority": "Springer Nature editorial policy",
        "url": "https://www.springernature.com/gp/policies/editorial-policies/using-ai-in-research",
        "facts": [
            "AI support for analytical or interpretive processes requires methodological description and validation steps.",
            "Authors remain accountable for research decisions, outputs, and conclusions.",
        ],
    },
    {
        "authority": "Springer Nature researcher guidance and FAQ",
        "url": "https://group.springernature.com/gp/group/ai/ai-guidance-for-our-researchers-and-communities",
        "facts": [
            "Generative AI use should be declared in the Introduction or Acknowledgements, except copy-editing-only use.",
            "The disclosure guidance calls for tool versions, usage dates, prompts, and extent of contribution.",
        ],
    },
)

PREVIOUS_CANDIDATE = (
    "Generative AI tools (OpenAI ChatGPT/Codex) were used under author supervision "
    "for research-project coordination, code and evidence review, manuscript drafting, "
    "formatting, and language revision. The authors independently checked the underlying "
    "saved results, references, analyses, and final text and take full responsibility for "
    "the work. The tools were not listed as authors."
)

REVISED_CANDIDATE = (
    "Generative AI tools were used under author supervision for project planning and "
    "coordination; literature discovery and comparison; research-design and methodological "
    "option review; code scaffolding, implementation, debugging, and review; evidence, "
    "reproducibility, statistical, and numerical-result checking; interpretation "
    "stress-testing; and manuscript structuring, drafting, formatting, and language "
    "revision. Prompts instructed the tools to inspect retained artifacts, preserve failed "
    "runs and frozen protocols, compare methodological or editorial options, implement and "
    "test code, audit evidence and claims, and draft or revise text within author-specified "
    "boundaries. The tools did not fabricate or autonomously select data, references, "
    "results, claims, interpretations, or conclusions. Computational outputs were generated "
    "only by versioned code and frozen protocols and were independently checked against "
    "retained artifacts. The author independently reviewed the AI-assisted outputs, reran "
    "the documented verification procedures, checked references, analyses, claims, and the "
    "final text, made all final research and submission decisions, and accepts full "
    "responsibility. No AI tool was listed as an author."
)

USE_SCOPE = {
    "green_or_low_risk": [
        "project planning and coordination",
        "literature discovery and comparison",
        "code scaffolding and review",
        "formatting and language revision",
    ],
    "amber_or_requires_care": [
        "research-design and methodological option review",
        "code implementation and debugging",
        "statistical and numerical-result checking",
        "interpretation stress-testing",
        "manuscript structuring and drafting",
    ],
    "red_or_not_permitted_claimed": [],
}

SYNTHETIC_VALIDATION = {
    "directory": "E:/paper/ReliableRAG-applied-intelligence-private-synthetic-20260915-ai-policy-a",
    "source_archive_sha256": "e94e586c556112a998355ac0083a2e7777a04dca06da5b704e52cb5a45fa0ff5",
    "compiled_pdf_sha256": "0a486e7f7dcdaae0357f58301d85d3a15a35dc5fddc4b1550eecd7d2d55e05fb",
    "cover_letter_sha256": "e430fb658ddd7672f5f37137f4c13daee41c9b556fbc78b51ad3a5455a7d2948",
    "compiled_pages": 13,
    "nonembedded_fonts": 0,
    "type3_fonts": 0,
    "all_pages_visually_reviewed": True,
    "visual_defects_found": 0,
    "synthetic_identity_only": True,
    "real_owner_package_built": False,
}


def build() -> dict[str, object]:
    hosts = {urlparse(source["url"]).hostname for source in SOURCES}
    if hosts != {"link.springer.com", "www.springernature.com", "group.springernature.com"}:
        raise AssertionError("policy sources must remain on official Springer Nature hosts")
    if len({source["url"] for source in SOURCES}) != len(SOURCES):
        raise AssertionError("policy source URLs must be unique")
    for source in SOURCES:
        if not source["url"].startswith("https://") or not source["facts"]:
            raise AssertionError("each policy source needs an HTTPS URL and mapped facts")
    for marker in (
        "Prompts instructed the tools",
        "did not fabricate or autonomously select data",
        "versioned code and frozen protocols",
        "made all final research and submission decisions",
        "No AI tool was listed as an author",
    ):
        if marker not in REVISED_CANDIDATE:
            raise AssertionError(f"revised disclosure is missing boundary: {marker}")
    template = json.loads(
        (ROOT / "docs" / "cas_q3" / "OWNER_INPUTS_TEMPLATE.json").read_text(encoding="utf-8")
    )
    if template["declarations"]["ai_assistance_statement"] != REVISED_CANDIDATE:
        raise AssertionError("owner-input template and policy-aligned candidate differ")
    builder_path = ROOT / "scripts" / "build_cas_q3_applied_intelligence_private_submission.py"
    return {
        "schema_version": 1,
        "decision": "PARTIAL_PASS_CURRENT_SPRINGER_NATURE_AI_POLICY_MAPPED_AUTHOR_APPROVAL_FINAL_DATE_AND_ARTIFACT_OPEN",
        "cas_q3_status": "NOT_READY",
        "accessed_date": ACCESSED_DATE,
        "sources": list(SOURCES),
        "project_use_classification": USE_SCOPE,
        "policy_application": {
            "copy_editing_only_exception_applies": False,
            "journal_specific_methods_documentation_required": True,
            "introduction_or_acknowledgements_disclosure_also_requested_by_group_guidance": True,
            "tool_versions_required": True,
            "usage_dates_required": True,
            "prompt_scope_required": True,
            "extent_of_contribution_required": True,
            "human_validation_and_accountability_required": True,
        },
        "candidate_revision": {
            "previous_candidate": PREVIOUS_CANDIDATE,
            "previous_candidate_is_complete_for_current_policy": False,
            "revised_candidate": REVISED_CANDIDATE,
            "revised_candidate_covers_prompt_categories": True,
            "revised_candidate_claims_verbatim_complete_prompt_transcript": False,
            "tool_version_and_date_record_is_separate": True,
            "responsible_author_approval": False,
            "final_use_end_date": None,
        },
        "target_artifact_rule": {
            "private_builder_path": "scripts/build_cas_q3_applied_intelligence_private_submission.py",
            "private_builder_sha256": hashlib.sha256(builder_path.read_bytes()).hexdigest(),
            "private_builder_inserts_disclosure_in_methods_equivalent_study_design": True,
            "public_anonymous_source_contains_owner_placeholder_only": True,
            "author_populated_artifact_generated": False,
            "final_astra_xhigh_rebind_required": True,
        },
        "synthetic_target_validation": SYNTHETIC_VALIDATION,
        "remaining": [
            "responsible-author confirmation that the revised scope and prompt categories are complete and accurate",
            "final AI use end date after project work ends",
            "author-populated Applied Intelligence build using the approved disclosure",
            "final artifact-bound GPT-6 Astra xhigh policy, authenticity, fairness, claim, and reviewer audit",
        ],
        "p0_i_closed": False,
        "submission_authorized": False,
    }


def render(result: dict[str, object]) -> str:
    sources = "\n".join(
        f"- [{source['authority']}]({source['url']})（访问日期：{result['accessed_date']}）"
        for source in result["sources"]
    )
    green = "；".join(result["project_use_classification"]["green_or_low_risk"])
    amber = "；".join(result["project_use_classification"]["amber_or_requires_care"])
    remaining = "\n".join(f"- {item}" for item in result["remaining"])
    candidate = result["candidate_revision"]["revised_candidate"]
    return f"""# P0-I Springer Nature AI 政策对齐审计

**CAS Q3 STATUS: NOT READY.**

Decision: `{result['decision']}`

## 当前政策与适用判断

{sources}

Applied Intelligence 的期刊级指南要求将超出纯 copy editing 的 LLM 使用写入 Methods 或合适的替代部分。Springer Nature 当前总政策进一步要求披露工具版本、使用日期、提示词和贡献范围，并要求分析、解释和结论保持作者主导。因本项目包含生成式研究设计、代码、分析复核和起草支持，纯 copy-editing 例外不适用。

本项目的低风险用途包括：{green}。需要谨慎并明确记录人工复核的用途包括：{amber}。本审计没有把任何无监督生成的假设、数据、结果或结论认定为可接受用途。

## 待负责人批准的替代声明

旧候选只覆盖协调、代码/证据审查和写作，遗漏方法选项、统计/数值复核、解释压力测试和提示词范围，不能作为当前政策下的完整声明。新的候选是：

> {candidate}

具体工具、模型、推理等级和最终日期范围仍由单独字段记录。该候选描述提示词类别，不声称公开了逐字完整会话；负责人仍须确认类别是否完整、是否需要向编辑提供更细的私有记录，以及最终结束日期。

私有 Applied Intelligence 构建器现将获批声明写入 Study design 内的 Methods 等价小节，并保留匿名公共源中的占位状态。新的合成身份端到端构建生成 13 页 PDF，编译、字体和全部页面视觉检查通过；它不包含真实负责人身份，也不是实名投稿包。

## 尚未关闭

{remaining}

本审计不批准声明，不关闭 P0-I，不授权发布或投稿。
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    args = parser.parse_args()
    result = build()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    args.acceptance.write_text(render(result), encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
