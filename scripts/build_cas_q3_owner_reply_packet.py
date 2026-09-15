#!/usr/bin/env python3
"""Build a privacy-safe, one-reply checklist from missing owner-input paths."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.verify_cas_q3_owner_inputs import ROOT, validate
    from scripts.audit_cas_q3_springer_ai_policy_alignment import REVISED_CANDIDATE
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from verify_cas_q3_owner_inputs import ROOT, validate
    from audit_cas_q3_springer_ai_policy_alignment import REVISED_CANDIDATE


DEFAULT_INPUT = ROOT / "docs" / "cas_q3" / "OWNER_INPUTS.local.json"
DEFAULT_OUTPUT = ROOT / "docs" / "cas_q3" / "P0_I_RESPONSIBLE_AUTHOR_ONE_REPLY_PACKET_ZH.md"
DEFAULT_RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_RESPONSIBLE_AUTHOR_ONE_REPLY_PACKET_VERIFICATION.json"

AI_ASSISTANCE_CANDIDATE = REVISED_CANDIDATE
NO_COMPETING_INTERESTS_CANDIDATE = "The author declares no competing interests."


PROMPTS_ZH = {
    "authorship.authors_in_order[0].credit_role_assignment": (
        "按实际贡献列出作者承担的 CRediT 角色；至少一个角色，不要填写未发生的贡献。"
    ),
    "declarations.funding_statement": "Funding statement（无外部资助也请明确写出）。",
    "declarations.competing_interests_statement": "Competing interests statement。",
    "declarations.ethics_statement_or_approval": (
        "Ethics statement / approval（依据学校规则确认公开 benchmark 计算实验是否不涉及人或动物伦理审批）。"
    ),
    "declarations.ai_assistance_statement_approved=true": (
        "是否批准当前 AI assistance statement 候选措辞（是/否；否时给出真实替代措辞）。"
    ),
    "declarations.ai_tool_version_and_use_dates": "实际使用的 AI 工具、版本及使用日期范围。",
    "declarations.overlapping_work_or_preprint_disclosure": (
        "Overlapping work / preprint disclosure（无则写 NONE_DISCLOSED）。"
    ),
    "declarations.originality_confirmed=true": "是否确认论文原创且没有一稿多投（是/否）。",
    "declarations.exclusive_submission_confirmed=true": (
        "是否确认 Applied Intelligence 为当前唯一投稿目标（是/否）。"
    ),
    "declarations.all_authors_approved_final_manuscript_and_order=true": (
        "全部作者是否批准最终稿和作者顺序（是/否；单作者也需确认）。"
    ),
    "declarations.institutional_manuscript_approval_required": (
        "学校是否要求投稿前论文审批（是/否/待核实）。"
    ),
    "declarations.institutional_manuscript_approval_status=APPROVED": (
        "学校要求投稿前审批；请在实际获批后确认状态为 APPROVED，并保留书面证据。"
    ),
    "declarations.institutional_manuscript_approval_evidence": (
        "若要求投稿前审批，给出审批状态与留存证据；若不要求，给出负责人确认记录。"
    ),
    "project_license.legal_copyright_holder": (
        "ReliableRAG 原创代码的法律版权人（个人/学校/其他，写法须经确认）。"
    ),
    "project_license.copyright_year_or_range": "版权年份或年份范围。",
    "project_license.institutional_release_review_required": (
        "学校是否要求代码公开发布前审查（是/否/待核实）；若要求，请给出审批状态与留存证据。"
    ),
    "project_license.release_review_status=APPROVED": (
        "学校要求代码公开发布前审查；请在实际获批后确认状态为 APPROVED，并保留书面证据。"
    ),
    "target_journal.institution_recognized_cas_edition_year": (
        "湖北工业大学采用的中科院《期刊分区表》升级版年份/版本，以及 Applied Intelligence "
        "在计算机科学大类三区及以上的留存记录路径或经办部门。"
    ),
}


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def render(missing: list[str]) -> str:
    numbered = "\n".join(f"{index}. `{path}`" for index, path in enumerate(missing, start=1))
    prompts = "\n".join(
        f"{index}. `{path}`：{PROMPTS_ZH.get(path, '请提供该字段的真实、可核验值。')}"
        for index, path in enumerate(missing, start=1)
    )
    candidate_lines: list[str] = []
    if "declarations.ai_assistance_statement_approved=true" in missing:
        candidate_lines.append(
            "- AI assistance statement 候选：\n\n"
            f"  > {AI_ASSISTANCE_CANDIDATE}\n\n"
            "  该候选按 2026-09-15 核验的 Springer Nature 新政策补充了方法选项、"
            "统计/数值复核、解释压力测试和提示词类别。见 "
            "[政策对齐审计](P0_I_SPRINGER_NATURE_AI_POLICY_ALIGNMENT.md)。"
            "请明确回答是否完整准确并批准；如不准确，请给出替代措辞。"
        )
    if "declarations.ai_tool_version_and_use_dates" in missing:
        candidate_lines.append(
            "- AI 工具记录格式：`OpenAI Codex (GPT-Astra and GPT-Sol), "
            "YYYY-MM-DD to YYYY-MM-DD`。日期必须按实际使用范围填写。"
        )
        candidate_lines.append(
            "- [AI 工具日期证据边界](P0_I_AI_TOOL_DATE_EVIDENCE.md)只证明两种模型族"
            "不晚于 2026-09-12 已有留存使用记录；这不是实际最早使用日，也不是完整"
            "使用区间，最终起止日期仍须作者依据真实记录确认。"
        )
        candidate_lines.append(
            "- [本地 Codex 会话元数据审计](P0_I_AI_TOOL_SESSION_METADATA.md)进一步支持"
            "项目任务开始日为 2026-09-10，工具为 `gpt-6-astra`（high/xhigh）与"
            "`gpt-5.6-sol`（high）。固定快照末次观察日为 2026-09-15，但项目仍在"
            "继续，不能把它写成最终结束日。可审核格式：`OpenAI Codex "
            "(gpt-6-astra, high/xhigh; gpt-5.6-sol, high), 2026-09-10 to YYYY-MM-DD`。"
        )
        candidate_lines.append(
            "- [私有提示词记录快照](P0_I_AI_PROMPT_RECORD.md)已在固定截止时间筛出 47 个"
            "root-user 提示块并保存脱敏文本与原始哈希。它不公开提示正文、不是最终使用"
            "区间，也未获负责人逐条审核或编辑访问授权。"
        )
    if "declarations.competing_interests_statement" in missing:
        candidate_lines.append(
            f"- 如果确实不存在利益冲突，可确认：`{NO_COMPETING_INTERESTS_CANDIDATE}`；"
            "否则请如实列出实际关系。"
        )
    if any("institutional_manuscript_approval" in path for path in missing):
        candidate_lines.append(
            "- 论文审批证据请存入 Git 忽略目录 "
            "`evidence/private/institutional_manuscript_approval/`，并按 "
            "`docs/cas_q3/INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD_TEMPLATE.json` 填写 Git 忽略的 "
            "`docs/cas_q3/INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD.local.json`；记录须绑定获批稿件的实际 SHA-256、审批日期和经办单位。"
        )
    if any(
        path in missing
        for path in (
            "project_license.institutional_release_review_required",
            "project_license.release_review_status=APPROVED",
        )
    ):
        candidate_lines.append(
            "- 代码发布审查证据请存入 Git 忽略目录 "
            "`evidence/private/institutional_release_record/`，并提供文件名、审批日期和经办单位。"
        )
    candidates = "\n".join(candidate_lines) or "- 当前缺失项没有预置候选文本，请填写真实值。"
    return f"""# P0-I 负责人一次回复确认单

**CAS Q3 STATUS: NOT READY.**

生成时本地负责人输入还缺 **{len(missing)}** 项，且已有字段没有校验错误。本文件只列出缺失字段路径和静态填写说明；生成器不会把本地文件中已经填写的姓名、邮箱、地址或声明文本写入仓库。已核验并写入本地文件的学校所在城市和邮编无需重复提供。

## 当前缺失字段

{numbered}

## 可直接审核的候选措辞与证据位置

{candidates}

## 一次回复模板

请复制下面代码块并一次填写。这里只列出当前仍缺的项目；已经验收的院系、正式署名和通讯邮箱不会再次索取。不能确认的项目写“待核实”，不要猜测。个人事实和作者声明由负责人确认；中科院分区、机构审批及代码发布审查仍须保留独立证据。

```text
{prompts}
```

可选：ORCID（官方指南为 if available/recommended）；单独邮寄地址仅在不同于已填写单位地址时提供；没有致谢对象时可以不设置 Acknowledgements 段。

## 验收边界

填完上述模板后，项目组仍需把事实写入 Git 忽略的 `OWNER_INPUTS.local.json`，运行结构校验，生成新的私有 Applied Intelligence 投稿包，并完成机构分区证据、模板适配及最终 GPT-6 Astra xhigh 真实性和 claim 审计。本确认单本身不授权公开发布或投稿。
"""


def build(data: Any) -> tuple[str, dict[str, Any]]:
    result = validate(data)
    missing = result["missing_field_paths"]
    if result["validation_error_paths"]:
        raise ValueError("owner input has validation errors; fix structure before generating reply packet")
    if not missing:
        raise ValueError("owner input is already complete; no reply packet is needed")
    content = render(missing)
    receipt = {
        "schema_version": 1,
        "decision": "PASS_PRIVACY_SAFE_ONE_REPLY_PACKET_GENERATED_OWNER_CONFIRMATION_PENDING",
        "cas_q3_status": "NOT_READY",
        "missing_field_count": len(missing),
        "missing_field_paths": missing,
        "validation_error_count": 0,
        "personal_values_emitted": False,
        "real_owner_inputs_complete": False,
        "independent_cas_authority_verified": False,
        "distribution_authorized": False,
        "submission_authorized": False,
    }
    return content, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    receipt_path = args.receipt.resolve()
    data = json.loads(input_path.read_text(encoding="utf-8"))
    content, receipt = build(data)
    payload = content.encode("utf-8")
    output_path.write_bytes(payload)
    receipt["packet_path"] = output_path.relative_to(ROOT.resolve()).as_posix()
    receipt["packet_sha256"] = digest(payload)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
