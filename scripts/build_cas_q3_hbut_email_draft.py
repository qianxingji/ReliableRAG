#!/usr/bin/env python3
"""Build a deterministic, sender-free HBUT institutional-review email draft."""

from __future__ import annotations

import argparse
from email.message import EmailMessage
from email.policy import SMTP
import hashlib
import json
from pathlib import Path
import re
import tempfile


RECIPIENT = "kyc@mail.hbut.edu.cn"
SUBJECT = "咨询 Applied Intelligence 中科院升级版大类分区认定及 ReliableRAG 代码发布审查"
ATTACHMENT_NAME = "hbut_institutional_review_request_candidate.zip"
DRAFT_NAME = "hbut_institutional_review_request_draft.eml"
BOUNDARY = "===============ReliableRAG_HBUT_DRAFT_V1=="


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256(value: str, label: str) -> str:
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _source_commit(value: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError("source commit must be a lowercase 40-character Git SHA")
    return value


def body_text(packet_sha256: str, packet_acceptance_commit: str) -> str:
    return f"""湖北工业大学科技与产业处老师：

您好！拟向 Applied Intelligence（Print ISSN 0924-669X；Electronic ISSN 1573-7497）投稿 ReliableRAG 研究。现就投稿认定和项目原创代码发布事宜申请书面确认：

1. 如论文在 2026 年正式发表，学校是否以 2025 年中科院《期刊分区表》升级版认定；Applied Intelligence 是否认定为计算机科学大类三区及以上。
2. 论文以湖北工业大学为第一署名单位时，投稿前是否需要学院或学校审批，以及应保留的审批材料。
3. ReliableRAG 项目原创代码拟采用 Apache License 2.0 发布，是否需要校内知识产权、保密或成果发布审查；拟发布边界不含模型权重、原始基准文本/答案或逐问题结果。
4. Qwen2.5-3B-Instruct 及 DeBERTa 等第三方模型仅按各自许可和条款使用，不作为项目原创代码重新许可。请确认该边界下还需履行的校内审查程序。

随信仅附一份未发送前审阅包，SHA-256 为：
{packet_sha256}

该材料仍为匿名论文草稿和审查输入，不代表学校已确认分区、批准论文、确认著作权归属或批准代码发布。最终审批须绑定实际作者版论文及其 SHA-256。随附审查包的仓库验收提交为 {packet_acceptance_commit}。

[请发送人于正式发送前补充姓名、学院、联系方式，并核对收件地址和全部附件。]
"""


def build(
    packet: Path,
    expected_packet_sha256: str,
    output_dir: Path,
    packet_acceptance_commit: str,
) -> dict[str, object]:
    expected_packet_sha256 = _sha256(expected_packet_sha256, "expected packet SHA-256")
    packet_acceptance_commit = _source_commit(packet_acceptance_commit)
    if packet.name != ATTACHMENT_NAME or not packet.is_file() or packet.is_symlink():
        raise ValueError("packet must be the regular allowlisted HBUT request archive")
    packet_bytes = packet.read_bytes()
    if digest(packet_bytes) != expected_packet_sha256:
        raise ValueError("packet SHA-256 mismatch")

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    draft = output_dir / DRAFT_NAME
    if draft.exists():
        raise FileExistsError(f"refusing to overwrite existing email draft: {draft}")

    message = EmailMessage(policy=SMTP)
    message["To"] = RECIPIENT
    message["Subject"] = SUBJECT
    message["X-ReliableRAG-Draft-Status"] = "NOT-SENT"
    message["X-ReliableRAG-Packet-Commit"] = packet_acceptance_commit
    # Keep each unstructured header below the RFC 5322 recommended line length.
    # A single 64-character value is otherwise folded with semantic whitespace.
    message["X-ReliableRAG-Attachment-SHA256-1"] = expected_packet_sha256[:32]
    message["X-ReliableRAG-Attachment-SHA256-2"] = expected_packet_sha256[32:]
    message.set_content(body_text(expected_packet_sha256, packet_acceptance_commit), subtype="plain", charset="utf-8")
    message.add_attachment(
        packet_bytes,
        maintype="application",
        subtype="zip",
        filename=ATTACHMENT_NAME,
    )
    message.set_boundary(BOUNDARY)
    draft_bytes = message.as_bytes(policy=SMTP)

    with tempfile.NamedTemporaryFile(
        dir=output_dir, prefix=DRAFT_NAME + ".", suffix=".tmp", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(draft_bytes)
    try:
        temporary.replace(draft)
    finally:
        if temporary.exists():
            temporary.unlink()

    return {
        "schema_version": 1,
        "decision": "BUILT_DETERMINISTIC_HBUT_EMAIL_DRAFT_WITHOUT_SENDER_NOT_SENT",
        "draft": str(draft),
        "draft_sha256": digest(draft_bytes),
        "draft_size_bytes": len(draft_bytes),
        "packet_sha256": expected_packet_sha256,
        "packet_acceptance_commit": packet_acceptance_commit,
        "recipient": RECIPIENT,
        "subject": SUBJECT,
        "sender_identity_present": False,
        "transport_headers_present": False,
        "email_sent": False,
        "institutional_response_received": False,
        "distribution_authorized": False,
        "submission_authorized": False,
        "cas_q3_status": "NOT_READY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--packet-acceptance-commit", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            build(args.packet, args.packet_sha256, args.output_dir, args.packet_acceptance_commit),
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
