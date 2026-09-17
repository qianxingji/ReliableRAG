#!/usr/bin/env python3
"""Build a private redacted prompt ledger and a content-free public receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSION_ROOT = Path.home() / ".codex" / "sessions"
DEFAULT_OWNER_INPUT = ROOT / "docs" / "cas_q3" / "OWNER_INPUTS.local.json"
DEFAULT_PRIVATE_OUTPUT = ROOT / "evidence" / "private" / "ai_prompt_record" / "AI_PROMPT_RECORD.local.jsonl"
DEFAULT_OUTPUT = ROOT / "docs" / "cas_q3" / "P0_I_AI_PROMPT_RECORD.json"
DEFAULT_ACCEPTANCE = ROOT / "docs" / "cas_q3" / "P0_I_AI_PROMPT_RECORD.md"
THREAD_DIRECTORY_BASENAME = "reliablerag-research-project-lead-submission-ready"
CUTOFF_UTC = "2026-09-15T04:18:53.028Z"
AUTOMATIC_PREFIXES = (
    "<codex_internal_context",
    "<recommended_plugins>",
    "<environment_context>",
)


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def session_meta(path: Path, cutoff: datetime) -> dict[str, Any] | None:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            timestamp = record.get("timestamp")
            if not isinstance(timestamp, str) or parse_utc(timestamp) > cutoff:
                continue
            if record.get("type") == "session_meta" and isinstance(record.get("payload"), dict):
                return record["payload"]
    return None


def redaction_values(owner_input: Path | None) -> list[tuple[str, str]]:
    if owner_input is None or not owner_input.is_file():
        return []
    data = json.loads(owner_input.read_text(encoding="utf-8"))
    authorship = data.get("authorship", {})
    values: list[tuple[str, str]] = []
    for author in authorship.get("authors_in_order", []):
        if isinstance(author, dict) and isinstance(author.get("name"), str) and author["name"].strip():
            values.append((author["name"].strip(), "[REDACTED_AUTHOR_NAME]"))
    for key, replacement in (
        ("corresponding_author_name", "[REDACTED_AUTHOR_NAME]"),
        ("corresponding_author_email", "[REDACTED_EMAIL]"),
        ("corresponding_author_postal_address", "[REDACTED_POSTAL_ADDRESS]"),
    ):
        value = authorship.get(key)
        if isinstance(value, str) and value.strip():
            values.append((value.strip(), replacement))
    # Longest first avoids a shorter author token partly masking a full name.
    return sorted(set(values), key=lambda item: (-len(item[0]), item[0]))


def redact(text: str, values: list[tuple[str, str]]) -> tuple[str, int]:
    count = 0
    redacted = text
    for value, replacement in values:
        occurrences = redacted.count(value)
        if occurrences:
            redacted = redacted.replace(value, replacement)
            count += occurrences
    redacted, email_count = re.subn(
        r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])",
        "[REDACTED_EMAIL]",
        redacted,
    )
    return redacted, count + email_count


def audit(
    session_root: Path,
    *,
    cutoff_utc: str = CUTOFF_UTC,
    thread_directory_basename: str = THREAD_DIRECTORY_BASENAME,
    owner_input: Path | None = DEFAULT_OWNER_INPUT,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cutoff = parse_utc(cutoff_utc)
    scanned = 0
    roots: list[Path] = []
    for path in sorted(session_root.glob("**/*.jsonl")):
        metadata = session_meta(path, cutoff)
        if metadata is None:
            continue
        scanned += 1
        cwd = metadata.get("cwd")
        if (
            isinstance(cwd, str)
            and Path(cwd).name.casefold() == thread_directory_basename.casefold()
            and metadata.get("thread_source") == "user"
            and metadata.get("agent_path") is None
        ):
            roots.append(path)
    if len(roots) != 1:
        raise AssertionError(f"expected exactly one root user session, found {len(roots)}")

    values = redaction_values(owner_input)
    rows: list[dict[str, Any]] = []
    excluded: dict[str, int] = {prefix: 0 for prefix in AUTOMATIC_PREFIXES}
    message_records = 0
    input_chunks = 0
    raw_total_chars = 0
    redaction_count = 0
    with roots[0].open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            timestamp = record.get("timestamp")
            if not isinstance(timestamp, str) or parse_utc(timestamp) > cutoff:
                continue
            payload = record.get("payload")
            if (
                record.get("type") != "response_item"
                or not isinstance(payload, dict)
                or payload.get("type") != "message"
                or payload.get("role") != "user"
            ):
                continue
            message_records += 1
            for item in payload.get("content", []):
                if not isinstance(item, dict) or item.get("type") != "input_text" or not isinstance(item.get("text"), str):
                    continue
                input_chunks += 1
                text = item["text"]
                stripped = text.lstrip()
                matched_prefix = next((prefix for prefix in AUTOMATIC_PREFIXES if stripped.startswith(prefix)), None)
                if matched_prefix is not None:
                    excluded[matched_prefix] += 1
                    continue
                clean, replacements = redact(text, values)
                redaction_count += replacements
                raw_total_chars += len(text)
                rows.append(
                    {
                        "sequence": len(rows) + 1,
                        "timestamp_utc": timestamp,
                        "raw_sha256": digest(text.encode("utf-8")),
                        "raw_character_count": len(text),
                        "redacted_text": clean,
                    }
                )
    private_payload = b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8") for row in rows
    )
    canonical_raw = json.dumps(
        [{key: row[key] for key in ("sequence", "timestamp_utc", "raw_sha256", "raw_character_count")} for row in rows],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    receipt = {
        "schema_version": 1,
        "decision": "PASS_PRIVATE_REDACTED_ROOT_USER_PROMPT_LEDGER_SNAPSHOT_FINAL_RANGE_AND_AUTHOR_RELEASE_OPEN",
        "cas_q3_status": "NOT_READY",
        "snapshot_cutoff_utc": cutoff_utc,
        "selection_scope": {
            "session_files_with_metadata_scanned": scanned,
            "root_user_sessions_selected": len(roots),
            "thread_directory_basename": thread_directory_basename,
            "subagent_sessions_excluded": True,
            "system_and_developer_messages_excluded": True,
            "assistant_messages_and_tool_io_excluded": True,
            "automatic_context_prefixes_excluded": list(AUTOMATIC_PREFIXES),
            "automatic_context_chunk_counts": excluded,
            "user_message_records_seen": message_records,
            "user_input_text_chunks_seen": input_chunks,
            "retained_user_prompt_chunks": len(rows),
            "unique_exact_user_prompt_hashes": len({row["raw_sha256"] for row in rows}),
            "raw_prompt_characters": raw_total_chars,
        },
        "privacy_and_integrity": {
            "private_ledger_contains_redacted_prompt_text": True,
            "private_ledger_contains_complete_unredacted_prompt_set": False,
            "unaffected_prompt_chunks_may_remain_verbatim": True,
            "private_ledger_is_anonymous": False,
            "redaction_is_identity_minimization_not_anonymization": True,
            "raw_prompt_hashes_retained": True,
            "owner_value_and_email_redactions": redaction_count,
            "public_receipt_contains_prompt_text": False,
            "public_receipt_contains_session_identifier": False,
            "public_receipt_contains_absolute_session_path": False,
            "canonical_raw_prompt_metadata_sha256": digest(canonical_raw),
            "private_ledger_sha256": digest(private_payload),
            "private_ledger_bytes": len(private_payload),
        },
        "disclosure_boundary": {
            "prompt_snapshot_prepared": True,
            "snapshot_is_complete_through_cutoff": True,
            "snapshot_is_final_project_use_range": False,
            "responsible_author_content_review_complete": False,
            "responsible_author_release_approval": False,
            "editor_requested_or_approved_access_route": False,
            "verbatim_unredacted_prompt_release_prepared": False,
            "final_ai_use_end_date": None,
        },
        "operations": {
            "scientific_payloads_read": False,
            "model_forwards": 0,
            "scientific_fits": 0,
        },
        "p0_i_closed": False,
        "submission_authorized": False,
    }
    return rows, receipt


def render(receipt: dict[str, Any]) -> str:
    scope = receipt["selection_scope"]
    privacy = receipt["privacy_and_integrity"]
    return f"""# P0-I 私有 AI 提示词记录快照

**CAS Q3 STATUS: NOT READY.**

Decision: `{receipt['decision']}`

本审计固定到 `{receipt['snapshot_cutoff_utc']}`，只选择当前 ReliableRAG 根任务的
root-user session。它排除子代理、system/developer、assistant、工具输入输出，以及
Codex 自动注入的 goal、plugin 和 environment context 块。

共观察 {scope['user_message_records_seen']} 条 user message 记录和
{scope['user_input_text_chunks_seen']} 个 input-text 块；排除自动上下文后保留
{scope['retained_user_prompt_chunks']} 个用户提示块，其中
{scope['unique_exact_user_prompt_hashes']} 个精确内容哈希唯一，总计
{scope['raw_prompt_characters']} 个字符。私有 JSONL 仅保存脱敏文本、时间、长度和原始
提示哈希；执行了 {privacy['owner_value_and_email_redactions']} 次负责人值或邮箱替换。
没有命中敏感值的提示块可以逐字保留，因此该私有账本是身份最小化记录而不是匿名记录，
也不声称已经清除全部可识别项目线索。公开记录不含提示正文、会话标识或绝对 session 路径。

私有账本 SHA-256 为 `{privacy['private_ledger_sha256']}`，大小
{privacy['private_ledger_bytes']} bytes；它保存在 Git 忽略目录
`evidence/private/ai_prompt_record/`。原始未脱敏文本仍只存在于本机 Codex 会话，未另行
复制或准备发布。

该快照补强 Springer Nature 要求的 prompt-scope 可追溯性，但项目仍在继续。负责人
尚未逐条审核或批准披露，编辑也没有指定访问路径；最终结束日期仍为空。因此它不关闭
P0-I，不授权公开提示词、发布代码或投稿。
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-root", type=Path, default=DEFAULT_SESSION_ROOT)
    parser.add_argument("--cutoff-utc", default=CUTOFF_UTC)
    parser.add_argument("--thread-directory-basename", default=THREAD_DIRECTORY_BASENAME)
    parser.add_argument("--owner-input", type=Path, default=DEFAULT_OWNER_INPUT)
    parser.add_argument("--private-output", type=Path, default=DEFAULT_PRIVATE_OUTPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--acceptance", type=Path, default=DEFAULT_ACCEPTANCE)
    args = parser.parse_args()
    rows, receipt = audit(
        args.session_root,
        cutoff_utc=args.cutoff_utc,
        thread_directory_basename=args.thread_directory_basename,
        owner_input=args.owner_input,
    )
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    private_payload = b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8") for row in rows
    )
    args.private_output.write_bytes(private_payload)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    args.acceptance.write_text(render(receipt), encoding="utf-8", newline="\n")
    public_result = {
        "decision": receipt["decision"],
        "retained_user_prompt_chunks": receipt["selection_scope"]["retained_user_prompt_chunks"],
        "private_ledger_sha256": receipt["privacy_and_integrity"]["private_ledger_sha256"],
        "public_prompt_text_emitted": False,
        "p0_i_closed": False,
        "submission_authorized": False,
    }
    print(json.dumps(public_result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
