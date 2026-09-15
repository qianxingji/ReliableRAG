#!/usr/bin/env python3
"""Derive the bounded date evidence for the declared Codex model families."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "cas_q3" / "P0_I_AI_TOOL_DATE_EVIDENCE.json"
DEFAULT_ACCEPTANCE = ROOT / "docs" / "cas_q3" / "P0_I_AI_TOOL_DATE_EVIDENCE.md"

EVIDENCE = (
    {
        "kind": "routing_rule",
        "path": "docs/cas_q2/MODEL_ROUTING.md",
        "sha256": "dec79674c679fef3dcdd31b49acd1ab053e725c4f9f7c10a467ba8f87fd36dc1",
        "creation_commit": "7d1fe3675fd1b0c301ebed921448c215a2c8810d",
        "creation_time": "2026-09-11T23:56:00+08:00",
        "required_markers": (
            "`Sol` means `gpt-5.6-sol`; `Astra` means",
            "`gpt-6-astra`",
            "not evidence of a model replacement within an already running turn",
        ),
        "proves_model_use": False,
    },
    {
        "kind": "retained_sol_use_record",
        "path": "docs/cas_q2/C4_JINJA_EXECUTION_BINDING_V2_ACCEPTANCE.md",
        "sha256": "08ad739047737d383b72eee638a9711a262627020a0a2d6fe8c74b74f3b15592",
        "creation_commit": "f6368506f495cc5a0e122bd5810fa0fa230305b2",
        "creation_time": "2026-09-12T04:36:43+08:00",
        "required_markers": ("Date: 2026-09-12. Client Research Lead review: Sol High.",),
        "model_family": "GPT-Sol",
        "model_id_from_routing_record": "gpt-5.6-sol",
        "reasoning": "high",
        "recorded_use_date": "2026-09-12",
        "proves_model_use": True,
    },
    {
        "kind": "retained_astra_use_record",
        "path": "docs/cas_q2/C3_VALIDATION_V1_FAILURE_REVIEW.md",
        "sha256": "3fcb423501c11ba376152ee642c454927740c263567d60aafda4e1fc73a5add9",
        "creation_commit": "e6cb54c78829caf7b001e1d9802e608a9f84d1bb",
        "creation_time": "2026-09-12T00:59:48+08:00",
        "required_markers": (
            "2026-09-12 Asia/Shanghai. **CAS Q2 STATUS: NOT READY.**",
            "This is the Astra xhigh anomaly audit required by MODEL_ROUTING.md.",
        ),
        "model_family": "GPT-Astra",
        "model_id_from_routing_record": "gpt-6-astra",
        "reasoning": "xhigh",
        "recorded_use_date": "2026-09-12",
        "proves_model_use": True,
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Separate retained use evidence from routing metadata and unknown dates."""
    use_records = [record for record in records if record["proves_model_use"]]
    by_model = {
        record["model_family"]: {
            "retained_use_evidence_date": record["recorded_use_date"],
            "evidence_path": record["path"],
            "evidence_creation_time": record["creation_time"],
        }
        for record in use_records
    }
    routing = next(record for record in records if record["kind"] == "routing_rule")
    verified = all(record.get("verified", False) for record in records)
    return {
        "schema_version": 1,
        "decision": (
            "PASS_EVIDENCE_BOUNDED_AI_TOOL_USE_CONFIRMED_BY_DATE_EXACT_RANGE_PENDING"
            if verified
            else "FAIL_AI_TOOL_DATE_EVIDENCE_INTEGRITY"
        ),
        "cas_q3_status": "NOT_READY",
        "routing_record": {
            "recorded_date": routing["creation_time"][:10],
            "proves_actual_use_on_that_date": False,
            "reason": "The routing document explicitly disclaims proving a model replacement within an already running turn.",
        },
        "retained_use_evidence_by_model": by_model,
        "joint_evidence_boundary": {
            "both_model_families_have_retained_use_evidence_by": max(
                item["retained_use_evidence_date"] for item in by_model.values()
            ),
            "is_actual_first_use_date": False,
            "is_complete_use_range": False,
        },
        "declaration_fields": {
            "actual_first_use_date": None,
            "actual_last_use_date": None,
            "exact_version_and_date_bounded_record_complete": False,
            "author_confirmation_required": True,
        },
        "evidence_records": records,
        "p0_i_closed": False,
        "submission_authorized": False,
    }


def audit(root: Path = ROOT) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for specification in EVIDENCE:
        record = dict(specification)
        path = root / record["path"]
        payload = path.read_text(encoding="utf-8") if path.is_file() else ""
        actual_hash = sha256(path) if path.is_file() else None
        record["actual_sha256"] = actual_hash
        record["file_present"] = path.is_file()
        record["hash_matches"] = actual_hash == record["sha256"]
        record["markers_present"] = all(marker in payload for marker in record["required_markers"])
        record["verified"] = record["file_present"] and record["hash_matches"] and record["markers_present"]
        record["required_markers"] = list(record["required_markers"])
        records.append(record)
    return derive(records)


def render_acceptance(result: dict[str, Any]) -> str:
    sol = result["retained_use_evidence_by_model"]["GPT-Sol"]
    astra = result["retained_use_evidence_by_model"]["GPT-Astra"]
    return f"""# P0-I AI 工具日期证据边界

**Decision: `{result['decision']}`**

**CAS Q3 STATUS: NOT READY.**

## 可证明的事实

- `MODEL_ROUTING.md` 于 2026-09-11 留存，定义 Sol 为 `gpt-5.6-sol`、Astra 为 `gpt-6-astra`；该文件自己明确说明它不能证明正在进行的 turn 已发生模型切换，因此 **2026-09-11 不是经认证的实际使用起始日**。
- 一条留存 Sol 专属执行记录是 `{sol['evidence_path']}`，记录日期为 **{sol['retained_use_evidence_date']}**。
- 一条留存 Astra 专属审计记录是 `{astra['evidence_path']}`；结合此前生效的路由文件，它对应 `gpt-6-astra` / `xhigh`，日期为 **{astra['retained_use_evidence_date']}**。
- 所以当前仓库证据只能证明：截至 **2026-09-12**，GPT-Sol 与 GPT-Astra 两个模型族都已经留下实际使用记录。

## 不能推出的事实

这不是任一模型的真实首次使用日期，也不是完整使用区间；仓库证据不能确定实际开始日或结束日。负责人仍须依据真实记录确认 `declarations.ai_tool_version_and_use_dates` 的完整起止日期。系统不得把 2026-09-11 或 2026-09-12 自动填成首次使用日，也不得用当前日期猜测结束日。

本证据只缩小待确认范围，不批准 AI assistance statement，不关闭 P0-I，不授权公开发布或投稿。

## 工程验收

- CAS Q3 专用发现：126/126 通过。
- 项目既有 `E:\\paper\\ReliableRAG\\.venv` 完整仓库发现：400 项通过，2 项因 Windows 符号链接权限和大小写不敏感文件系统跳过。
- 系统基础 Python 的先行完整发现加载了 370 项，因缺少 `torch`、`scipy`、`scikit-learn` 和 `threadpoolctl` 出现 2 个失败与 8 个导入错误；切换到项目已认证依赖环境后全部可执行项通过。因此该先行结果属于解释器依赖缺失，不是本次实现或科学实验失败。
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    args = parser.parse_args()
    result = audit()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    args.acceptance.write_text(render_acceptance(result), encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["decision"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
