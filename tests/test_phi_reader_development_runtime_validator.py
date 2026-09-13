from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np

from scripts import validate_phi_reader_development_runtime as validator


class FakeTokenizer:
    pad_token_id = 0
    chat_template = "fake-template"

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        return "<user>" + messages[0]["content"] + "<assistant>"

    def __call__(self, prompts, **_kwargs):
        if isinstance(prompts, str): prompts = [prompts]
        return {"input_ids": [[ord(char) for char in prompt] for prompt in prompts]}

    def batch_decode(self, rows, *, skip_special_tokens):
        assert skip_special_tokens is True
        return ["".join(chr(value) for value in row if value) for row in rows]


def canonical_line(value):
    return validator.canonical(value) + b"\n"


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def make_seal(directory: Path):
    files = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != "SHA256_MANIFEST.json":
            row = validator.record(path); row["path"] = path.relative_to(directory).as_posix(); files.append(row)
    write_json(directory / "SHA256_MANIFEST.json", {"status": "PASS", "files": files,
        "excludes_only": "SHA256_MANIFEST.json", "exact_recursive_coverage": True})


def evidence(prefix="d"):
    return [{"rank": rank, "document_id": f"{prefix}{rank}", "content_hash": str(rank) * 64,
             "retrieval_score": float(6 - rank), "title": f"Title {rank}", "text": f"Text {rank}"}
            for rank in range(1, 6)]


def generation_row(stage="a0"):
    tokenizer = FakeTokenizer(); question = "Who?"; rows = evidence()
    rebuilt = validator.reconstruct_generation(tokenizer, "Q={question}\nE={evidence}", question, rows)
    raw = "Answer: yes" if stage != "repair_query" else "Search Query: alpha beta"
    generated = [ord(char) for char in raw]
    return {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s", "position": 0,
        "stage": stage, **rebuilt, "attention_mask": [1] * rebuilt["input_tokens"],
        "generated_token_ids": generated, "raw_text": raw, "parsed_text": "yes" if stage != "repair_query" else "alpha beta",
        "parser_fallback": False if stage == "repair_query" else None, "output_tokens": len(generated),
        "native_output_score_steps": len(generated), "question_sha256": validator.text_sha(question),
        "evidence_sha256": validator.object_sha(rows), "logical_generation_calls": 1, "phi_forward_calls": len(generated),
        "reader": "phi", "guard_input_tokens": rebuilt["input_tokens"], "runtime_config_sha256": "a" * 64}


class ValidatorPrimitivesTests(unittest.TestCase):
    def test_validator_has_no_forbidden_runtime_import(self):
        source = Path(validator.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): names.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom): names.append(node.module or "")
        self.assertFalse(any("build_phi_reader_development_runtime" in name or
                             "phi_reader_development_runtime_common" in name or
                             "phi_reader_development_runtime_guard" in name for name in names))

    def test_transformers_import_precedes_boundary_and_snapshot_load_follows_it(self):
        source = Path(validator.__file__).read_text(encoding="utf-8")
        imported = source.index("from transformers import AutoTokenizer")
        boundary = source.index("boundary = install_boundary", imported)
        loaded = source.index("AutoTokenizer.from_pretrained", boundary)
        self.assertLess(imported, boundary); self.assertLess(boundary, loaded)

    def test_safe_namespace_name(self):
        self.assertEqual(validator.safe_name("phi-validation.fake_1"), "phi-validation.fake_1")
        for value in ("../escape", "a/b", "a\\b", "", ".", ".."):
            with self.assertRaises(RuntimeError): validator.safe_name(value)

    def test_runtime_audit_boundary_exact_binding_passes(self):
        boundary = validator.EXPECTED_RUNTIME_AUDIT_BOUNDARY_START
        validator.validate_runtime_audit_boundary({"audit_boundary_start": boundary},
                                                  {"audit_boundary_start": boundary})

    def test_runtime_audit_boundary_tamper_is_rejected_on_either_side(self):
        boundary = validator.EXPECTED_RUNTIME_AUDIT_BOUNDARY_START
        for freeze_value, receipt_value in ((boundary + " tampered", boundary), (boundary, boundary + " tampered")):
            with self.subTest(freeze=freeze_value == boundary), self.assertRaisesRegex(RuntimeError, "audit boundary"):
                validator.validate_runtime_audit_boundary({"audit_boundary_start": freeze_value},
                                                          {"audit_boundary_start": receipt_value})

    def test_runtime_model_load_counts_pass_and_reject_tampering(self):
        receipt = {"bge_model_loads": 1, "reader_model_loads": 1, "nli_model_loads": 0}
        validator.validate_runtime_model_load_counts(receipt)
        for field, value in (("bge_model_loads", 0), ("reader_model_loads", 0), ("nli_model_loads", 1)):
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, "model load counts"):
                validator.validate_runtime_model_load_counts({**receipt, field: value})

    def test_canonical_jsonl_rejects_partial_and_noncanonical(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "rows.jsonl"; path.write_bytes(b'{"b":2,"a":1}\n')
            with self.assertRaisesRegex(RuntimeError, "noncanonical"): validator.read_canonical_jsonl(path)
            path.write_bytes(b'{"a":1}')
            with self.assertRaisesRegex(RuntimeError, "partial"): validator.read_canonical_jsonl(path)

    def test_exact_seal_rejects_tamper_and_extra(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "x").write_text("one", encoding="utf-8"); make_seal(root)
            validator.verify_exact_seal(root)
            (root / "extra").write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "coverage"): validator.verify_exact_seal(root)
            (root / "extra").unlink(); (root / "x").write_text("two", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "hash"): validator.verify_exact_seal(root)

    def test_pinned_seal_rejects_rewritten_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "x").write_text("one", encoding="utf-8"); make_seal(root)
            pin = validator.digest(root / "SHA256_MANIFEST.json"); validator.verify_pinned_seal(root, pin)
            write_json(root / "SHA256_MANIFEST.json", {"status": "PASS", "files": [],
                "excludes_only": "SHA256_MANIFEST.json", "exact_recursive_coverage": True})
            with self.assertRaisesRegex(RuntimeError, "pinned"): validator.verify_pinned_seal(root, pin)

    def test_nonweight_inputs_are_rehashed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "source.py"; path.write_text("x", encoding="utf-8"); row = validator.record(path)
            self.assertEqual(validator.verify_runtime_input_records([row], {})["nonweight_records_rehashed"], 1)
            path.write_text("y", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "changed"): validator.verify_runtime_input_records([row], {})

    def test_gold_named_input_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "development_gold.json"; path.write_text("secret", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Gold-bearing"):
                validator.verify_runtime_input_records([validator.record(path)], {})

    def test_weight_record_is_bound_without_reading_contents(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "model.safetensors"; path.write_bytes(b"AAAA")
            row = {"path": str(path.resolve()), "size_bytes": 4, "sha256": "f" * 64}
            audit = validator.verify_runtime_input_records([row], {path.resolve(): dict(row)})
            self.assertEqual(audit["weight_records_bound_without_byte_read"], 1)

    def test_replay_input_extension_exact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); core = root / "core"; canonical = root / "canonical"; core.write_text("c"); canonical.write_text("r")
            core_row, extra_row = validator.record(core), validator.record(canonical)
            validator.validate_replay_input_extension([core_row], [core_row, extra_row], [canonical])
            rogue = root / "rogue"; rogue.write_text("x")
            with self.assertRaisesRegex(RuntimeError, "replay-only"):
                validator.validate_replay_input_extension([core_row], [core_row, extra_row, validator.record(rogue)], [canonical])

    def test_replay_input_extension_rejects_changed_core_record(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "core"; path.write_text("x"); row = validator.record(path); changed = dict(row, sha256="0" * 64)
            with self.assertRaisesRegex(RuntimeError, "common executable"):
                validator.validate_replay_input_extension([row], [changed], [])

    def test_model_snapshot_exact_records_reject_extra_member(self):
        with tempfile.TemporaryDirectory() as td:
            original = Path(td)
            roots = [original / f"data/models/huggingface/models--microsoft--Phi-3.5-mini-instruct/snapshots/{validator.PHI_REVISION}",
                     original / f"data/models/huggingface/models--BAAI--bge-base-en-v1.5/snapshots/{validator.BGE_REVISION}"]
            records, joint = [], {}
            for root in roots:
                root.mkdir(parents=True); path = root / "tokenizer.json"; path.write_text("{}")
                row = validator.record(path); records.append(row); joint[path.resolve()] = dict(row)
            self.assertEqual(validator.validate_model_snapshot_records(records, joint, original),
                             {"phi_snapshot_files": 1, "bge_snapshot_files": 1})
            (roots[0] / "extra.json").write_text("{}")
            with self.assertRaisesRegex(RuntimeError, "exact accepted"):
                validator.validate_model_snapshot_records(records, joint, original)

    def test_snapshot_read_policy_is_exact_file_allowlist(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); snapshot = root / "snapshot"; snapshot.mkdir()
            tokenizer = snapshot / "tokenizer.json"; tokenizer.write_text("{}")
            extra = snapshot / "new-config.json"; extra.write_text("{}")
            allowed = {tokenizer.resolve()}
            self.assertTrue(validator.validator_read_allowed(tokenizer, allowed=allowed, output=root / "out", environment_roots=()))
            self.assertFalse(validator.validator_read_allowed(extra, allowed=allowed, output=root / "out", environment_roots=()))

    def test_validator_temp_environment_is_confined_to_output(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(os.environ, {}, clear=False):
            old_tempdir = tempfile.tempdir
            try:
                output = Path(td) / "validation"; output.mkdir()
                temp_root = validator.configure_validator_environment(output)
                self.assertTrue(temp_root.is_relative_to(output))
                self.assertEqual({os.environ[key] for key in ("TMP", "TEMP", "TMPDIR")}, {str(temp_root)})
                self.assertEqual(Path(tempfile.gettempdir()), temp_root)
            finally:
                tempfile.tempdir = old_tempdir

    def test_render_preserves_all_headers_and_reports_truncation(self):
        rows = evidence(); rows[0]["text"] = "z" * 1000
        rendered, metadata = validator.render_evidence(rows, budget=300)
        self.assertEqual(metadata["text"], rendered)
        self.assertEqual(metadata["ordered_passed_document_ids"], [f"d{i}" for i in range(1, 6)])
        self.assertTrue(metadata["context_truncated"])
        self.assertTrue(all(identifier in rendered for identifier in metadata["ordered_passed_document_ids"]))

    def test_answer_and_query_parsers(self):
        self.assertEqual(validator.parse_answer("\nFinal answer: Paris\nmore"), "Paris")
        self.assertEqual(validator.parse_query("x\nSearch Query: alpha", "q"), ("alpha", False))
        self.assertEqual(validator.parse_query("x\nfallback", "q"), ("fallback", True))

    def test_trace_and_fixed_subset_order(self):
        traces, frozen = [], []
        for dataset in validator.DATASETS:
            for retriever in validator.RETRIEVERS:
                position = len(traces); ids = [f"{dataset}:{retriever}:{i}" for i in range(5)]
                trace = {"dataset": dataset, "retriever": retriever, "sample_id": dataset + "-sample", "position": position,
                         "original_top5_ids": ids, "original_top5_row_sha256": "f" * 64}
                traces.append(trace); frozen.append({"cohort": "development", "dataset": dataset, "retriever": retriever,
                    "sample_id": dataset + "-sample", "position": position, "role": "fit",
                    "original_top5_ids_sha256": validator.object_sha(ids)})
        index = validator.validate_trace_sources(traces, list(traces), frozen, trace_count=9, replay_per_cell=1)
        self.assertEqual(len(index), 9)
        traces[1], traces[2] = traces[2], traces[1]
        with self.assertRaisesRegex(RuntimeError, "sequence"): validator.validate_trace_sources(traces, [], frozen, trace_count=9, replay_per_cell=0)

    def _stream_fixture(self, root: Path, count: int = 4):
        traces = [{"dataset": "hotpotqa", "retriever": "bm25", "sample_id": f"s{i}", "position": i}
                  for i in range(count)]
        ledgers = {name: [] for name in validator.LEDGERS}; events = []
        for trace in traces:
            generations = []
            for stage in validator.STAGES:
                row = {**trace, "stage": stage, "runtime_config_sha256": "a" * 64,
                       "question_sha256": "b" * 64, "evidence_sha256": "c" * 64,
                       "phi_forward_calls": 1, "guard_input_tokens": 10, "parsed_text": "x",
                       "parser_fallback": False if stage == "repair_query" else None}
                generations.append(row); ledgers["generation_receipts"].append(row)
            repair = {**trace, "runtime_config_sha256": "a" * 64, "query_sha256": "d" * 64,
                      "requested_depth": 50}; ledgers["repair_bindings"].append(repair)
            ledgers["branch_provenance"].append(dict(trace)); ledgers["canonical_branches"].append(dict(trace))
            for operation, ledger, row in (("a0", "generation_receipts", generations[0]),
                    ("repair_query", "generation_receipts", generations[1]),
                    ("repair_retrieval", "repair_bindings", repair), ("a1", "generation_receipts", generations[2])):
                identifier = validator.event_id(row, operation)
                fields = {key: row[key] for key in ("dataset", "retriever", "sample_id", "position", "runtime_config_sha256")}
                fields.update(({"question_sha256": row["question_sha256"], "evidence_sha256": row["evidence_sha256"]}
                               if ledger == "generation_receipts" else {"query_sha256": row["query_sha256"], "requested_depth": 50}))
                events += [{"event": "intent", "event_id": identifier, "operation": operation, **fields},
                    {"event": "completion", "event_id": identifier, "operation": operation, "ledger": ledger,
                     "ledger_row_sha256": validator.object_sha(row)}]
        for name, filename in validator.LEDGERS.items():
            (root / filename).write_bytes(b"".join(canonical_line(row) for row in ledgers[name]))
        (root / "call_events.jsonl").write_bytes(b"".join(canonical_line(row) for row in events))
        counters = {"phi_forward_calls": count * 3, "repair_retrieval_calls": count,
            "repair_retrieval_completed": count, "repair_bm25_calls": count, "repair_dense_calls": 0,
            "repair_hybrid_calls": 0, "repair_query_embedding_calls": 0, "bge_query_forward_calls": 0}
        for stage in validator.STAGES:
            counters[stage + "_generation_calls"] = counters[stage + "_generation_completed"] = count
            counters[stage + "_forward_calls"] = count
        receipt = {"counters": counters, "guard_admission_count": count * 3, "guard_admission_max_tokens": 10,
            "stratum_counts": {f"{dataset}/{retriever}": count if (dataset, retriever) == ("hotpotqa", "bm25") else 0
                               for dataset in validator.DATASETS for retriever in validator.RETRIEVERS},
            "question_clusters": count, "fail_closed_counts": {}, "replay_canonical_reference_rows_decoded": 0,
            "replay_canonical_string_fields_decoded": 0, "replay_canonical_answer_fields_decoded": 0,
            "replay_canonical_reference_raw_lines_scanned": 0, "replay_canonical_reference_raw_bytes_scanned": 0,
            "replay_exact_match": None}
        return traces, {"namespace": root, "receipt": receipt, "freeze": {"mode": "canonical"},
                        "runtime_config_sha256": "a" * 64}

    def test_streaming_validator_retains_only_selected_reference_rows(self):
        with tempfile.TemporaryDirectory() as td:
            traces, run = self._stream_fixture(Path(td), count=40)
            frozen = {(row["dataset"], row["retriever"], row["sample_id"]): {} for row in traces}
            with mock.patch.object(validator, "load_dataset_assets", return_value={}), \
                 mock.patch.object(validator, "validate_trace_bundle"):
                summary = validator.validate_run_streaming(run, selected=traces, frozen_index=frozen,
                    tokenizer=FakeTokenizer(), templates={}, original=Path(td), capture_positions={7, 31})
            self.assertEqual(summary["ledger_counts"]["generation_receipts"], 120)
            self.assertEqual(summary["event_rows"], 320); self.assertEqual(summary["captured_rows"], 12)
            self.assertEqual(len(summary["captured"]), 2)
            self.assertEqual(sum(len(rows) for rows in summary["captured"].values()), 8)
            self.assertNotIn("generation_receipts", summary)

    def test_streaming_validator_rejects_trailing_ledger_row(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); traces, run = self._stream_fixture(root, count=1)
            with (root / validator.LEDGERS["canonical_branches"]).open("ab") as stream:
                stream.write(canonical_line({"extra": True}))
            frozen = {(row["dataset"], row["retriever"], row["sample_id"]): {} for row in traces}
            with mock.patch.object(validator, "load_dataset_assets", return_value={}), \
                 mock.patch.object(validator, "validate_trace_bundle"), self.assertRaisesRegex(RuntimeError, "trailing"):
                validator.validate_run_streaming(run, selected=traces, frozen_index=frozen,
                    tokenizer=FakeTokenizer(), templates={}, original=root)


class EventAndPromptTests(unittest.TestCase):
    def _event_fixture(self):
        generations = []
        for stage in validator.STAGES:
            generations.append({"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s", "position": 0,
                "stage": stage, "runtime_config_sha256": "a" * 64, "question_sha256": "b" * 64, "evidence_sha256": "c" * 64})
        repair = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s", "position": 0,
                  "runtime_config_sha256": "a" * 64, "query_sha256": "d" * 64, "requested_depth": 50}
        ledgers = {"generation_receipts": generations, "repair_bindings": [repair]}
        events = []
        for operation, row, ledger in (("a0", generations[0], "generation_receipts"),
                                       ("repair_query", generations[1], "generation_receipts"),
                                       ("repair_retrieval", repair, "repair_bindings"),
                                       ("a1", generations[2], "generation_receipts")):
            identifier = validator.event_id(row, operation)
            fields = {key: row[key] for key in ("dataset", "retriever", "sample_id", "position", "runtime_config_sha256")}
            if ledger == "generation_receipts": fields.update(question_sha256=row["question_sha256"], evidence_sha256=row["evidence_sha256"])
            else: fields.update(query_sha256=row["query_sha256"], requested_depth=50)
            events += [{"event": "intent", "event_id": identifier, "operation": operation, **fields},
                       {"event": "completion", "event_id": identifier, "operation": operation, "ledger": ledger,
                        "ledger_row_sha256": validator.object_sha(row)}]
        return events, ledgers

    def test_events_bind_complete_operation_inputs(self):
        events, ledgers = self._event_fixture(); validator.validate_events(events, ledgers)

    def test_events_reject_unpaired_intent(self):
        events, ledgers = self._event_fixture()
        with self.assertRaisesRegex(RuntimeError, "unpaired"): validator.validate_events(events[:-1], ledgers)

    def test_events_reject_generation_input_tamper(self):
        events, ledgers = self._event_fixture(); events[0]["question_sha256"] = "e" * 64
        with self.assertRaisesRegex(RuntimeError, "scientific input"): validator.validate_events(events, ledgers)

    def test_events_reject_repair_query_tamper(self):
        events, ledgers = self._event_fixture(); events[4]["query_sha256"] = "e" * 64
        with self.assertRaisesRegex(RuntimeError, "scientific input"): validator.validate_events(events, ledgers)

    def test_events_reject_completion_hash_tamper(self):
        events, ledgers = self._event_fixture(); events[1]["ledger_row_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "completion"): validator.validate_events(events, ledgers)

    def test_generation_reconstructs_dynamic_a1(self):
        row = generation_row("a1"); trace = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s", "position": 0}
        provenance = {"e0": evidence("e"), "e1": evidence()}; branch = {"question": "Who?"}
        validator.validate_generation(row, trace=trace, frozen={}, provenance=provenance, branch=branch,
            tokenizer=FakeTokenizer(), templates={"answer": "Q={question}\nE={evidence}", "repair_query": ""}, config_sha="a" * 64)

    def test_generation_rejects_dynamic_a1_token_tamper(self):
        row = generation_row("a1"); row["input_token_ids"][0] += 1
        trace = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s", "position": 0}
        with self.assertRaisesRegex(RuntimeError, "prompt/token"):
            validator.validate_generation(row, trace=trace, frozen={}, provenance={"e0": evidence("e"), "e1": evidence()},
                branch={"question": "Who?"}, tokenizer=FakeTokenizer(),
                templates={"answer": "Q={question}\nE={evidence}", "repair_query": ""}, config_sha="a" * 64)

    def test_generation_rejects_dynamic_a1_render_text_tamper(self):
        row = generation_row("a1"); row["render"]["text"] += " tampered"
        trace = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s", "position": 0}
        with self.assertRaisesRegex(RuntimeError, "render/guard"):
            validator.validate_generation(row, trace=trace, frozen={}, provenance={"e0": evidence("e"), "e1": evidence()},
                branch={"question": "Who?"}, tokenizer=FakeTokenizer(),
                templates={"answer": "Q={question}\nE={evidence}", "repair_query": ""}, config_sha="a" * 64)

    def test_generation_binds_a0_input_freeze(self):
        row = generation_row("a0"); witness = {"answer": {"prompt_sha256": row["prompt_sha256"], "input_tokens": row["input_tokens"],
            "input_token_ids_sha256": validator.object_sha(row["input_token_ids"]), "context_truncated": row["render"]["context_truncated"],
            "rendered_context_characters": row["rendered_context_characters"],
            "per_document_truncated": row["render"]["per_document_truncated"]}}
        trace = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s", "position": 0}
        validator.validate_generation(row, trace=trace, frozen=witness, provenance={"e0": evidence(), "e1": evidence("e")},
            branch={"question": "Who?"}, tokenizer=FakeTokenizer(),
            templates={"answer": "Q={question}\nE={evidence}", "repair_query": ""}, config_sha="a" * 64)
        witness["answer"]["input_tokens"] += 1
        with self.assertRaisesRegex(RuntimeError, "input-freeze"):
            validator.validate_generation(row, trace=trace, frozen=witness, provenance={"e0": evidence(), "e1": evidence("e")},
                branch={"question": "Who?"}, tokenizer=FakeTokenizer(),
                templates={"answer": "Q={question}\nE={evidence}", "repair_query": ""}, config_sha="a" * 64)

    def test_generated_ids_bind_raw_text_and_parser(self):
        row = generation_row("a1"); row["raw_text"] = "Answer: no"
        trace = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s", "position": 0}
        with self.assertRaisesRegex(RuntimeError, "raw text"):
            validator.validate_generation(row, trace=trace, frozen={}, provenance={"e0": evidence("e"), "e1": evidence()},
                branch={"question": "Who?"}, tokenizer=FakeTokenizer(),
                templates={"answer": "Q={question}\nE={evidence}", "repair_query": ""}, config_sha="a" * 64)


class RetrievalAndReplayTests(unittest.TestCase):
    def test_bm25_recomputation_uses_repeated_query_terms(self):
        payload = {"document_ids": ["d0", "d1"], "lengths": [2, 2], "average_length": 2.0,
                   "terms": [{"term": "x", "idf": 1.0, "postings": [[0, 2], [1, 1]]}]}
        scores = validator.bm25_scores("x x", payload)
        self.assertGreater(scores[0], scores[1]); self.assertAlmostEqual(scores[0], 2 * (5 / 3.5))

    def test_ordered_scores_breaks_ties_by_document_order(self):
        self.assertEqual([row["document_id"] for row in validator.ordered_scores(np.array([1., 1., 0.]), ["z", "a", "b"], 2)], ["z", "a"])

    def test_rrf_reconstructs_scores_and_first_seen_ties(self):
        a = [{"document_id": "a", "rank": 1, "score": 9.}, {"document_id": "b", "rank": 2, "score": 8.}]
        b = [{"document_id": "b", "rank": 1, "score": 9.}, {"document_id": "a", "rank": 2, "score": 8.}]
        fused = validator.rrf([a, b], 2)
        self.assertEqual([row["document_id"] for row in fused], ["a", "b"])
        self.assertEqual(fused[0]["score"], 1 / 61 + 1 / 62)

    def test_compare_ranking_rejects_score_tamper(self):
        row = [{"document_id": "a", "rank": 1, "score": 1.0}]
        with self.assertRaisesRegex(RuntimeError, "score"): validator.compare_ranking(row, [dict(row[0], score=2.0)], "score")

    def _dense_repair_fixture(self):
        ids = [f"d{i}" for i in range(60)]
        matrix = np.zeros((60, 768), dtype=np.float32); matrix[:, 0] = np.arange(60, 0, -1, dtype=np.float32)
        vector = [0.0] * 768; vector[0] = 1.0
        ranking = validator.ordered_scores(matrix @ np.asarray(vector, dtype=np.float32), ids, 50)
        e0_ids = ["d0", "d1", "d2", "d3", "d10"]
        e0 = [{"document_id": item, "rank": rank, "text": item} for rank, item in enumerate(e0_ids, 1)]
        e1 = [*e0[:4], {"document_id": "d4", "rank": 5, "text": "d4"}]
        row = {"dataset": "hotpotqa", "retriever": "dense", "sample_id": "s", "position": 0,
            "requested_depth": 50, "repair_retrieval_calls": 1, "replacement_position_zero_based": 4,
            "fail_closed_reason": None, "query_sha256": validator.text_sha("query"), "ranking": ranking,
            "component_rankings": {"dense": ranking}, "dense_query_vector": vector, "e0_ids": e0_ids,
            "e1_ids": ["d0", "d1", "d2", "d3", "d4"], "replaced_document_id": "d10",
            "inserted_document_id": "d4", "inserted_candidate_rank": 5}
        trace = {"dataset": "hotpotqa", "retriever": "dense", "sample_id": "s", "position": 0,
                 "original_top5_ids": e0_ids}
        return row, trace, {"e0": e0, "e1": e1}, {"evidence0": [x["text"] for x in e0], "evidence1": [x["text"] for x in e1]}, {
            "hotpotqa": {"document_ids": ids, "dense": matrix}}

    def test_saved_dense_vector_recomputes_complete_ranking(self):
        row, trace, provenance, branch, retrieval = self._dense_repair_fixture()
        validator.validate_repair(row, trace=trace, provenance=provenance, branch=branch, query="query", retrieval=retrieval)

    def test_saved_dense_vector_tamper_is_rejected(self):
        row, trace, provenance, branch, retrieval = self._dense_repair_fixture(); row["dense_query_vector"][0] = -1.0
        with self.assertRaisesRegex(RuntimeError, "recomputation"):
            validator.validate_repair(row, trace=trace, provenance=provenance, branch=branch, query="query", retrieval=retrieval)

    def test_replay_four_ledger_byte_identity(self):
        traces = [{"position": 1}]
        canonical_raw = {name: ([b"g0\n", b"g1\n", b"g2\n", b"g3\n", b"g4\n", b"g5\n"] if name == "generation_receipts"
                                else [b"x0\n", b"x1\n"]) for name in validator.LEDGERS}
        replay_raw = {name: ([b"g3\n", b"g4\n", b"g5\n"] if name == "generation_receipts" else [b"x1\n"])
                      for name in validator.LEDGERS}
        validator.verify_replay_bytes(canonical_raw, replay_raw, traces)
        replay_raw["canonical_branches"][0] = b"bad\n"
        with self.assertRaisesRegex(RuntimeError, "byte identity"): validator.verify_replay_bytes(canonical_raw, replay_raw, traces)

    def test_answer_string_accounting_is_truthful(self):
        ledgers = {"generation_receipts": [{"stage": stage} for stage in validator.STAGES], "canonical_branches": [{}],
                   "repair_bindings": [], "branch_provenance": []}
        self.assertEqual(validator.answer_string_field_count(ledgers), 6)

    def test_exact_replay_reference_accounting(self):
        ledgers = {"generation_receipts": [{"stage": stage, "s": stage} for stage in validator.STAGES],
            "repair_bindings": [{"s": "repair"}], "branch_provenance": [{"s": "provenance"}],
            "canonical_branches": [{"a0": "x", "a1": "y"}]}
        raw = {name: [canonical_line(row) for row in rows] for name, rows in ledgers.items()}
        selected = [row for rows in ledgers.values() for row in rows]
        receipt = {"replay_canonical_reference_rows_decoded": 6,
            "replay_canonical_string_fields_decoded": sum(validator.string_field_count(row) for row in selected),
            "replay_canonical_answer_fields_decoded": 6, "replay_canonical_reference_raw_lines_scanned": 6,
            "replay_canonical_reference_raw_bytes_scanned": sum(len(value) for rows in raw.values() for value in rows)}
        validator.validate_replay_reference_accounting(receipt, ledgers, raw, [{"position": 0}])
        receipt["replay_canonical_string_fields_decoded"] -= 1
        with self.assertRaisesRegex(RuntimeError, "accounting"):
            validator.validate_replay_reference_accounting(receipt, ledgers, raw, [{"position": 0}])

    def test_receipt_counts_recomputed_exactly(self):
        selected = [{"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s"}]
        generations = [dict(generation_row(stage), parsed_text="" if stage == "a0" else generation_row(stage)["parsed_text"])
                       for stage in validator.STAGES]
        ledgers = {"generation_receipts": generations, "repair_bindings": [{}], "branch_provenance": [{}],
                   "canonical_branches": [{}]}
        counters = {"phi_forward_calls": sum(row["phi_forward_calls"] for row in generations),
            "repair_retrieval_calls": 1, "repair_retrieval_completed": 1, "repair_bm25_calls": 1,
            "repair_dense_calls": 0, "repair_hybrid_calls": 0, "repair_query_embedding_calls": 0,
            "bge_query_forward_calls": 0}
        for stage in validator.STAGES:
            counters[stage + "_generation_calls"] = counters[stage + "_generation_completed"] = 1
            counters[stage + "_forward_calls"] = sum(row["phi_forward_calls"] for row in generations if row["stage"] == stage)
        receipt = {"counters": counters, "guard_admission_count": 3,
            "guard_admission_max_tokens": max(row["guard_input_tokens"] for row in generations),
            "stratum_counts": {f"{dataset}/{retriever}": int((dataset, retriever) == ("hotpotqa", "bm25"))
                               for dataset in validator.DATASETS for retriever in validator.RETRIEVERS},
            "question_clusters": 1, "fail_closed_counts": {"empty_a0_retained": 1},
            "replay_canonical_reference_rows_decoded": 0, "replay_canonical_string_fields_decoded": 0,
            "replay_canonical_answer_fields_decoded": 0, "replay_canonical_reference_raw_lines_scanned": 0,
            "replay_canonical_reference_raw_bytes_scanned": 0, "replay_exact_match": None}
        validator.validate_receipt_counts({"receipt": receipt, "freeze": {"mode": "canonical"}}, ledgers, selected)
        receipt["fail_closed_counts"]["unexplained"] = 1
        with self.assertRaisesRegex(RuntimeError, "fail-closed"):
            validator.validate_receipt_counts({"receipt": receipt, "freeze": {"mode": "canonical"}}, ledgers, selected)

    def test_runtime_config_fixed_values(self):
        config = {"reader": "microsoft/Phi-3.5-mini-instruct", "reader_revision": validator.PHI_REVISION,
            "bge": "BAAI/bge-base-en-v1.5", "bge_revision": validator.BGE_REVISION, "dtype": "torch.bfloat16",
            "batch_size": 1, "active_reader_instances": 1, "answer_max_new_tokens": 48, "repair_query_max_new_tokens": 64,
            "context_budget_characters": 16000, "maximum_generation_input_tokens": 9472, "original_evidence_top_k": 5,
            "original_question_retrieval_calls": 0, "repair_candidate_depth": 50, "replacement_position_zero_based": 4,
            "same_retriever_repair": True, "do_sample": False, "runtime_seed": 20260830,
            "reader_model_class": "Phi3ForCausalLM", "bge_model_class": "BertModel",
            "device": "cuda:0", "reader_attention": "sdpa", "bge_attention": "sdpa",
            "versions": {"torch": "2.7.1+cu128", "transformers": "4.53.2", "numpy": "2.2.6"},
            "effective_generation_configs": {stage: {"do_sample": False, "max_new_tokens": 64 if stage == "repair_query" else 48,
                "use_cache": True, "return_dict_in_generate": True, "output_scores": True,
                "temperature": None, "top_p": None, "top_k": None} for stage in validator.STAGES}}
        validator.validate_runtime_config(config)
        config["batch_size"] = 2
        with self.assertRaisesRegex(RuntimeError, "batch_size"): validator.validate_runtime_config(config)


if __name__ == "__main__":
    unittest.main()
