"""Tests for the privacy-preserving local AI prompt record."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_cas_q3_ai_prompt_record import audit, render


def row(timestamp: str, kind: str, payload: dict[str, object]) -> str:
    return json.dumps({"timestamp": timestamp, "type": kind, "payload": payload}) + "\n"


class AiPromptRecordTests(unittest.TestCase):
    def fixture(self, root: Path, *, thread_source: str = "user", agent_path: str | None = None) -> Path:
        path = root / f"session-{len(list(root.glob('*.jsonl')))}.jsonl"
        content = row(
            "2026-09-15T00:00:00Z",
            "session_meta",
            {
                "cwd": "C:/work/reliablerag-research-project-lead-submission-ready",
                "thread_source": thread_source,
                "agent_path": agent_path,
            },
        )
        path.write_text(content, encoding="utf-8")
        return path

    def append_message(self, path: Path, timestamp: str, role: str, texts: list[str]) -> None:
        payload = {
            "type": "message",
            "role": role,
            "content": [{"type": "input_text", "text": text} for text in texts],
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(row(timestamp, "response_item", payload))

    def test_root_user_prompts_are_retained_and_injected_context_is_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selected = self.fixture(root)
            subagent = self.fixture(root, thread_source="subagent", agent_path="/root/sub")
            self.append_message(
                selected,
                "2026-09-15T00:01:00Z",
                "user",
                ["Run the bounded audit", "<environment_context>automatic</environment_context>"],
            )
            self.append_message(selected, "2026-09-15T00:02:00Z", "assistant", ["not a user prompt"])
            self.append_message(subagent, "2026-09-15T00:03:00Z", "user", ["subagent copy"])
            rows, receipt = audit(root, owner_input=None)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["redacted_text"], "Run the bounded audit")
            self.assertEqual(receipt["selection_scope"]["root_user_sessions_selected"], 1)
            self.assertEqual(receipt["selection_scope"]["retained_user_prompt_chunks"], 1)
            self.assertEqual(
                receipt["selection_scope"]["automatic_context_chunk_counts"]["<environment_context>"],
                1,
            )
            self.assertFalse(receipt["privacy_and_integrity"]["public_receipt_contains_prompt_text"])

    def test_owner_values_and_generic_emails_are_redacted_but_raw_hash_is_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selected = self.fixture(root)
            owner = root / "owner.json"
            owner.write_text(
                json.dumps(
                    {
                        "authorship": {
                            "authors_in_order": [{"name": "Private Person"}],
                            "corresponding_author_name": "Private Person",
                            "corresponding_author_email": "private@example.org",
                            "corresponding_author_postal_address": "Private Address 1",
                        }
                    }
                ),
                encoding="utf-8",
            )
            original = "Private Person private@example.org other@example.net Private Address 1"
            self.append_message(selected, "2026-09-15T00:01:00Z", "user", [original])
            rows, receipt = audit(root, owner_input=owner)
            self.assertNotIn("Private Person", rows[0]["redacted_text"])
            self.assertNotIn("@", rows[0]["redacted_text"])
            self.assertNotIn("Private Address 1", rows[0]["redacted_text"])
            self.assertEqual(len(rows[0]["raw_sha256"]), 64)
            self.assertGreaterEqual(receipt["privacy_and_integrity"]["owner_value_and_email_redactions"], 4)
            self.assertFalse(receipt["privacy_and_integrity"]["private_ledger_contains_complete_unredacted_prompt_set"])
            self.assertTrue(receipt["privacy_and_integrity"]["unaffected_prompt_chunks_may_remain_verbatim"])
            self.assertFalse(receipt["privacy_and_integrity"]["private_ledger_is_anonymous"])

    def test_cutoff_and_final_authorization_boundaries_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selected = self.fixture(root)
            self.append_message(selected, "2026-09-15T00:01:00Z", "user", ["included"])
            self.append_message(selected, "2026-09-16T00:01:00Z", "user", ["too late"])
            rows, receipt = audit(root, cutoff_utc="2026-09-15T12:00:00Z", owner_input=None)
            self.assertEqual([item["redacted_text"] for item in rows], ["included"])
            self.assertFalse(receipt["disclosure_boundary"]["snapshot_is_final_project_use_range"])
            self.assertFalse(receipt["disclosure_boundary"]["responsible_author_content_review_complete"])
            self.assertIsNone(receipt["disclosure_boundary"]["final_ai_use_end_date"])
            self.assertFalse(receipt["p0_i_closed"])
            self.assertFalse(receipt["submission_authorized"])
            text_value = render(receipt)
            self.assertNotIn("included", text_value)
            self.assertIn("CAS Q3 STATUS: NOT READY", text_value)


if __name__ == "__main__":
    unittest.main()
