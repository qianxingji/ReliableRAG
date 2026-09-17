#!/usr/bin/env python3
"""Aggregate model/date facts from local Codex turn-context metadata only."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSION_ROOT = Path.home() / ".codex" / "sessions"
DEFAULT_OUTPUT = ROOT / "docs" / "cas_q3" / "P0_I_AI_TOOL_SESSION_METADATA.json"
DEFAULT_ACCEPTANCE = ROOT / "docs" / "cas_q3" / "P0_I_AI_TOOL_SESSION_METADATA.md"
THREAD_DIRECTORY_BASENAME = "reliablerag-research-project-lead-submission-ready"
CUTOFF_UTC = "2026-09-15T03:32:41.264Z"
TARGET_MODELS = {"gpt-6-astra", "gpt-5.6-sol"}
METADATA_LINE = re.compile(r'"type"\s*:\s*"(?:session_meta|turn_context)"')
SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def local_date(value: str) -> str:
    return parse_utc(value).astimezone(SHANGHAI).date().isoformat()


def metadata_records(path: Path) -> Iterable[dict[str, Any]]:
    """Parse only session_meta and turn_context lines; skip message/tool lines."""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not METADATA_LINE.search(line):
                continue
            yield json.loads(line)


def audit(
    session_root: Path,
    *,
    cutoff_utc: str = CUTOFF_UTC,
    thread_directory_basename: str = THREAD_DIRECTORY_BASENAME,
) -> dict[str, Any]:
    cutoff = parse_utc(cutoff_utc)
    selected_contexts: list[dict[str, str]] = []
    selected_session_count = 0
    session_files_scanned = 0

    for path in sorted(session_root.glob("**/*.jsonl")):
        has_metadata_before_cutoff = False
        session_matches = False
        contexts: list[dict[str, str]] = []
        for record in metadata_records(path):
            timestamp = record.get("timestamp")
            if not isinstance(timestamp, str) or parse_utc(timestamp) > cutoff:
                continue
            has_metadata_before_cutoff = True
            payload = record.get("payload", {})
            if record.get("type") == "session_meta":
                cwd = payload.get("cwd")
                if isinstance(cwd, str) and Path(cwd).name.casefold() == thread_directory_basename.casefold():
                    session_matches = True
            elif record.get("type") == "turn_context":
                model = payload.get("model")
                effort = payload.get("effort")
                if isinstance(model, str) and isinstance(effort, str):
                    contexts.append({"timestamp": timestamp, "model": model, "effort": effort})
        if has_metadata_before_cutoff:
            session_files_scanned += 1
        if session_matches:
            selected_session_count += 1
            selected_contexts.extend(contexts)

    model_events: dict[str, list[dict[str, str]]] = defaultdict(list)
    for context in selected_contexts:
        if context["model"] in TARGET_MODELS:
            model_events[context["model"]].append(context)

    model_summary: dict[str, Any] = {}
    for model in sorted(TARGET_MODELS):
        events = sorted(model_events.get(model, []), key=lambda item: parse_utc(item["timestamp"]))
        effort_counts: dict[str, int] = defaultdict(int)
        for event in events:
            effort_counts[event["effort"]] += 1
        model_summary[model] = {
            "turn_context_count": len(events),
            "reasoning_effort_counts": dict(sorted(effort_counts.items())),
            "first_observed_utc": events[0]["timestamp"] if events else None,
            "first_observed_asia_shanghai_date": local_date(events[0]["timestamp"]) if events else None,
            "last_observed_utc": events[-1]["timestamp"] if events else None,
            "last_observed_asia_shanghai_date": local_date(events[-1]["timestamp"]) if events else None,
        }

    target_contexts = [event for events in model_events.values() for event in events]
    canonical_metadata = json.dumps(
        sorted(target_contexts, key=lambda item: (item["timestamp"], item["model"], item["effort"])),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    all_models_present = all(model_summary[model]["turn_context_count"] > 0 for model in TARGET_MODELS)
    first_observed = min((event["timestamp"] for event in target_contexts), default=None)
    last_observed = max((event["timestamp"] for event in target_contexts), default=None)

    return {
        "schema_version": 1,
        "decision": (
            "PASS_LOCAL_CODEX_TURN_CONTEXT_METADATA_START_BOUND_END_DATE_PENDING"
            if all_models_present
            else "FAIL_LOCAL_CODEX_TURN_CONTEXT_TARGET_MODEL_MISSING"
        ),
        "cas_q3_status": "NOT_READY",
        "snapshot_cutoff_utc": cutoff_utc,
        "selection_scope": {
            "session_meta_cwd_basename": thread_directory_basename,
            "session_files_scanned": session_files_scanned,
            "selected_session_files": selected_session_count,
            "selected_session_identifiers_emitted": False,
            "absolute_paths_emitted": False,
            "message_response_or_tool_content_inspected": False,
        },
        "target_turn_context_count": len(target_contexts),
        "canonical_selected_metadata_sha256": hashlib.sha256(canonical_metadata).hexdigest(),
        "models": model_summary,
        "project_task_observation": {
            "first_observed_utc": first_observed,
            "first_observed_asia_shanghai_date": local_date(first_observed) if first_observed else None,
            "last_observed_utc": last_observed,
            "last_observed_asia_shanghai_date": local_date(last_observed) if last_observed else None,
            "last_observed_date_is_final_use_date": False,
            "complete_end_date_proved": False,
        },
        "declaration_boundary": {
            "tool_and_model_ids_supported": True,
            "project_task_start_date_supported": all_models_present,
            "final_use_end_date": None,
            "date_bounded_declaration_complete": False,
            "author_approval_still_required": True,
        },
        "p0_i_closed": False,
        "submission_authorized": False,
    }


def render(result: dict[str, Any]) -> str:
    astra = result["models"]["gpt-6-astra"]
    sol = result["models"]["gpt-5.6-sol"]
    observed = result["project_task_observation"]
    scope = result["selection_scope"]
    return f"""# P0-I 本地 Codex 会话元数据审计

**Decision: `{result['decision']}`**

**CAS Q3 STATUS: NOT READY.**

固定截止时间为 `{result['snapshot_cutoff_utc']}`。审计扫描本机 Codex session JSONL，
只解析 `session_meta` 与 `turn_context` 行，并以当前 ReliableRAG 项目任务目录名选择
会话；不解析消息、response 或工具内容，也不输出绝对路径或会话标识。

## 结果

- 扫描 {scope['session_files_scanned']} 个 session 文件，选中 {scope['selected_session_files']} 个项目会话，共 {result['target_turn_context_count']} 条目标模型 `turn_context`。
- `gpt-6-astra`：{astra['turn_context_count']} 条；effort 计数 `{json.dumps(astra['reasoning_effort_counts'], sort_keys=True)}`；首个本地日期 {astra['first_observed_asia_shanghai_date']}，末次观察日期 {astra['last_observed_asia_shanghai_date']}。
- `gpt-5.6-sol`：{sol['turn_context_count']} 条；effort 计数 `{json.dumps(sol['reasoning_effort_counts'], sort_keys=True)}`；首个本地日期 {sol['first_observed_asia_shanghai_date']}，末次观察日期 {sol['last_observed_asia_shanghai_date']}。
- 选中元数据规范化 SHA-256：`{result['canonical_selected_metadata_sha256']}`。

## 声明边界

该本机记录支持把 ReliableRAG 项目任务的 AI 使用开始日期写为 **{observed['first_observed_asia_shanghai_date']}**，并支持精确工具 ID `gpt-6-astra` 与 `gpt-5.6-sol`。截止快照的末次观察日期为 **{observed['last_observed_asia_shanghai_date']}**，但项目仍在继续，所以该日期不是最终结束日。最终投稿前必须重新冻结末次使用日期并由作者批准完整 AI assistance statement。

本审计不关闭 P0-I，不授权公开发布或投稿。

## 工程验收

首次基础-Python 调用在生成结果前因系统没有 IANA `tzdata` 失败。实现随后改用协议时区 `Asia/Shanghai` 在 2026 年固定对应的 UTC+08:00 偏移，不新增依赖；三个合成回归测试、129 项 CAS Q3 专用发现和项目环境 403 项完整仓库发现全部通过，完整发现另有两项 Windows 平台条件跳过。该工程失败不涉及消息内容、模型调用、科学数据或实验结果。
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-root", type=Path, default=DEFAULT_SESSION_ROOT)
    parser.add_argument("--cutoff-utc", default=CUTOFF_UTC)
    parser.add_argument("--thread-directory-basename", default=THREAD_DIRECTORY_BASENAME)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    args = parser.parse_args()
    result = audit(
        args.session_root,
        cutoff_utc=args.cutoff_utc,
        thread_directory_basename=args.thread_directory_basename,
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    args.acceptance.write_text(render(result), encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["decision"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
