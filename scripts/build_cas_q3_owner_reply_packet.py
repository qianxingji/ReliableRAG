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
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from verify_cas_q3_owner_inputs import ROOT, validate


DEFAULT_INPUT = ROOT / "docs" / "cas_q3" / "OWNER_INPUTS.local.json"
DEFAULT_OUTPUT = ROOT / "docs" / "cas_q3" / "P0_I_RESPONSIBLE_AUTHOR_ONE_REPLY_PACKET_ZH.md"
DEFAULT_RECEIPT = ROOT / "docs" / "cas_q3" / "P0_I_RESPONSIBLE_AUTHOR_ONE_REPLY_PACKET_VERIFICATION.json"


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def render(missing: list[str]) -> str:
    numbered = "\n".join(f"{index}. `{path}`" for index, path in enumerate(missing, start=1))
    return f"""# P0-I 负责人一次回复确认单

**CAS Q3 STATUS: NOT READY.**

生成时本地负责人输入还缺 **{len(missing)}** 项，且已有字段没有校验错误。本文件只列出缺失字段路径和静态填写说明；生成器不会把本地文件中已经填写的姓名、邮箱、地址或声明文本写入仓库。已核验并写入本地文件的学校所在城市和邮编无需重复提供。

## 当前缺失字段

{numbered}

## 一次回复模板

请复制下面代码块并一次填写。方括号内容是说明，不能确认的项目写“待核实”，不要猜测。个人事实和作者声明由负责人确认；中科院分区、机构审批及代码发布审查仍须保留独立证据。

```text
【单位与作者】
1. 院系/部门的正式中英文署名：
2. 通讯作者正式署名：
3. 通讯作者有效邮箱：
可选：ORCID（官方指南为 if available/recommended）；单独邮寄地址仅在不同于已填写单位地址时提供。

【CRediT 贡献】
4. 按实际贡献列出每位作者承担的 CRediT 角色。每位作者至少一个角色；不要为了填满表格虚构 Supervision、Project administration 或其他未发生的贡献：

【论文声明】
5. Funding statement（无外部资助也请明确写出）：
6. Competing interests statement：
7. Ethics statement / approval（请依据学校规则确认公开 benchmark 计算实验是否不涉及人或动物伦理审批）：
8. AI assistance statement 是否批准当前候选措辞（是/否；否时给出真实替代措辞）：
9. 实际使用的 AI 工具、版本及使用日期范围：
10. Overlapping work / preprint disclosure（无则写 NONE_DISCLOSED）：
11. 是否确认论文原创且没有一稿多投（是/否）：
12. 是否确认 Applied Intelligence 为当前唯一投稿目标（是/否）：
13. 全部作者是否批准最终稿和作者顺序（是/否；单作者也需确认）：
14. 学校是否要求投稿前论文审批（是/否/待核实）：
15. 若要求，审批状态与留存证据；若不要求，给出负责人确认记录：
可选：Acknowledgements；没有致谢对象时可以不设置该段。

【代码版权与发布】
16. ReliableRAG 原创代码的法律版权人（个人/学校/其他，写法须经确认）：
17. 版权年份或年份范围：
18. 学校是否要求代码公开发布前审查（是/否/待核实）；若要求，请给出审批状态与留存证据：

【中科院分区独立证据】
19. 湖北工业大学采用的中科院《期刊分区表》升级版年份/版本，以及 Applied Intelligence 在计算机科学大类三区及以上的留存记录路径或经办部门：
```

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
    data = json.loads(args.input.read_text(encoding="utf-8"))
    content, receipt = build(data)
    payload = content.encode("utf-8")
    args.output.write_bytes(payload)
    receipt["packet_path"] = args.output.relative_to(ROOT).as_posix()
    receipt["packet_sha256"] = digest(payload)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
