"""Tests for privacy-safe Codex turn-context metadata aggregation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_cas_q3_codex_session_metadata import audit


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class CodexSessionMetadataTests(unittest.TestCase):
    def test_selected_metadata_is_aggregated_without_private_paths_or_session_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                {
                    "timestamp": "2026-09-10T15:00:00Z",
                    "type": "session_meta",
                    "payload": {"cwd": "C:/Sensitive/User/reliable-task", "id": "secret-session-id"},
                },
                {
                    "timestamp": "2026-09-10T15:01:00Z",
                    "type": "response_item",
                    "payload": {"content": "private message content"},
                },
                {
                    "timestamp": "2026-09-10T15:02:00Z",
                    "type": "turn_context",
                    "payload": {"model": "gpt-6-astra", "effort": "xhigh"},
                },
                {
                    "timestamp": "2026-09-11T16:02:00Z",
                    "type": "turn_context",
                    "payload": {"model": "gpt-5.6-sol", "effort": "high"},
                },
            ]
            write_jsonl(root / "selected.jsonl", rows)
            result = audit(
                root,
                cutoff_utc="2026-09-12T00:00:00Z",
                thread_directory_basename="reliable-task",
            )
            serialized = json.dumps(result)
            self.assertEqual(
                result["decision"],
                "PASS_LOCAL_CODEX_TURN_CONTEXT_METADATA_START_BOUND_END_DATE_PENDING",
            )
            self.assertEqual(result["selection_scope"]["selected_session_files"], 1)
            self.assertEqual(result["target_turn_context_count"], 2)
            self.assertEqual(result["project_task_observation"]["first_observed_asia_shanghai_date"], "2026-09-10")
            self.assertNotIn("Sensitive", serialized)
            self.assertNotIn("secret-session-id", serialized)
            self.assertNotIn("private message content", serialized)
            self.assertFalse(result["selection_scope"]["message_response_or_tool_content_inspected"])

    def test_unrelated_session_and_post_cutoff_context_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_jsonl(
                root / "selected.jsonl",
                [
                    {"timestamp": "2026-09-10T00:00:00Z", "type": "session_meta", "payload": {"cwd": "C:/x/reliable-task"}},
                    {"timestamp": "2026-09-10T01:00:00Z", "type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "high"}},
                    {"timestamp": "2026-09-10T02:00:00Z", "type": "turn_context", "payload": {"model": "gpt-5.6-sol", "effort": "high"}},
                    {"timestamp": "2026-09-13T00:00:00Z", "type": "turn_context", "payload": {"model": "gpt-5.6-sol", "effort": "high"}},
                ],
            )
            write_jsonl(
                root / "unrelated.jsonl",
                [
                    {"timestamp": "2026-09-09T00:00:00Z", "type": "session_meta", "payload": {"cwd": "C:/x/other-task"}},
                    {"timestamp": "2026-09-09T01:00:00Z", "type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "ultra"}},
                ],
            )
            write_jsonl(
                root / "future.jsonl",
                [
                    {"timestamp": "2026-09-13T00:00:00Z", "type": "session_meta", "payload": {"cwd": "C:/x/reliable-task"}},
                    {"timestamp": "2026-09-13T01:00:00Z", "type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "xhigh"}},
                ],
            )
            result = audit(root, cutoff_utc="2026-09-12T00:00:00Z", thread_directory_basename="reliable-task")
            self.assertEqual(result["selection_scope"]["session_files_scanned"], 2)
            self.assertEqual(result["selection_scope"]["selected_session_files"], 1)
            self.assertEqual(result["target_turn_context_count"], 2)
            self.assertEqual(result["models"]["gpt-5.6-sol"]["turn_context_count"], 1)
            self.assertNotIn("ultra", result["models"]["gpt-6-astra"]["reasoning_effort_counts"])

    def test_missing_target_model_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_jsonl(
                root / "selected.jsonl",
                [
                    {"timestamp": "2026-09-10T00:00:00Z", "type": "session_meta", "payload": {"cwd": "C:/x/reliable-task"}},
                    {"timestamp": "2026-09-10T01:00:00Z", "type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "xhigh"}},
                ],
            )
            result = audit(root, cutoff_utc="2026-09-12T00:00:00Z", thread_directory_basename="reliable-task")
            self.assertEqual(result["decision"], "FAIL_LOCAL_CODEX_TURN_CONTEXT_TARGET_MODEL_MISSING")
            self.assertFalse(result["declaration_boundary"]["date_bounded_declaration_complete"])
            self.assertFalse(result["submission_authorized"])


if __name__ == "__main__":
    unittest.main()
