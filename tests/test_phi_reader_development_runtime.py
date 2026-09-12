import tempfile
import unittest
from pathlib import Path

from scripts.build_phi_reader_development_runtime import (
    LEDGER_FILES, require_unsealed_runtime_namespace, selected_reference_bytes, verify_applicable_joint_bindings,
)
from scripts.phi_reader_development_runtime_common import (
    DurableCallEvents,
    DurableJsonl,
    GuardedGenerationTokenizer,
    event_id,
    object_sha,
    validate_call_events,
    validate_frozen_generation_capture,
    validate_output_name,
    validate_resume_prefix,
    validate_trace_input_binding,
    verify_manifest_members,
    verify_recorded_tree,
    verify_selected_manifest_members,
)
from scripts.phi_reader_development_runtime_guard import DevelopmentRuntimeIOPolicy
from scripts.phi_reader_input_freeze_common import canonical, digest, record


class FakeTensor:
    def __init__(self, rows): self.rows = rows; self.shape = (len(rows), len(rows[0]))
    def __getitem__(self, index): return self.rows[index]


class FakeTokenizer:
    eos_token_id = 7
    def __call__(self, *args, **kwargs):
        return {"input_ids": FakeTensor([[2, 3]]), "attention_mask": FakeTensor([[1, 1]])}


class FakeTokenizerWithBatch:
    eos_token_id = 7
    def __init__(self, ids, mask): self.ids, self.mask = ids, mask
    def __call__(self, *args, **kwargs):
        return {"input_ids": FakeTensor(self.ids), "attention_mask": FakeTensor(self.mask)}


def trace(position=0):
    return {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": f"s{position}", "position": position}


class PhiDevelopmentRuntimeTests(unittest.TestCase):
    def test_guard_observes_exact_native_batch(self):
        phase = {"stage": "a1", "position": 9}; admissions = []
        value = GuardedGenerationTokenizer(FakeTokenizer(), phase, admissions)(["prompt"], return_tensors="pt")
        self.assertEqual(value["input_ids"].shape, (1, 2))
        self.assertEqual(admissions, [{"stage": "a1", "position": 9, "input_tokens": 2}])

    def test_guard_rejects_unknown_stage_batch_mask_and_ceiling(self):
        cases = [
            ("loading", [[2]], [[1]]),
            ("a0", [[2], [3]], [[1], [1]]),
            ("repair_query", [[2, 3]], [[1, 0]]),
            ("a1", [list(range(9473))], [[1] * 9473]),
        ]
        for stage, ids, mask in cases:
            with self.subTest(stage=stage, rows=len(ids), width=len(ids[0])):
                guarded = GuardedGenerationTokenizer(FakeTokenizerWithBatch(ids, mask), {"stage": stage, "position": 0}, [])
                with self.assertRaises(RuntimeError): guarded(["prompt"], return_tensors="pt")

    def test_durable_ledger_round_trip_and_noncanonical_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rows.jsonl"; ledger = DurableJsonl(path, resume=False)
            ledger.append({"b": 2, "a": 1}); ledger.close()
            resumed = DurableJsonl(path, resume=True); self.assertEqual(resumed.rows, [{"a": 1, "b": 2}]); resumed.close()
            path.write_text('{"b":2,"a":1}\n', encoding="utf-8")
            with self.assertRaises(RuntimeError): DurableJsonl(path, resume=True)

    def test_fresh_durable_ledgers_do_not_retain_appended_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = DurableJsonl(Path(folder) / "rows.jsonl", resume=False, retain_rows=False)
            for index in range(100): ledger.append({"index": index, "payload": "x" * 1000})
            self.assertEqual(ledger.rows, []); self.assertEqual(ledger.row_count, 100); ledger.close()

    def test_resume_history_can_be_validated_then_released(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rows.jsonl"; initial = DurableJsonl(path, resume=False)
            initial.append({"index": 0}); initial.close()
            resumed = DurableJsonl(path, resume=True); self.assertEqual(len(resumed.rows), 1)
            resumed.release_rows(); resumed.append({"index": 1})
            self.assertEqual(resumed.rows, []); self.assertEqual(resumed.row_count, 2); resumed.close()

    def test_streaming_call_events_keep_only_pending_intent(self):
        with tempfile.TemporaryDirectory() as folder:
            events = DurableCallEvents(Path(folder) / "events.jsonl", resume=False, retain_rows=False)
            for index in range(50):
                identifier = f"event-{index}"
                events.intent({"event": "intent", "event_id": identifier, "operation": "a0"})
                events.completion({"event": "completion", "event_id": identifier, "operation": "a0",
                    "ledger": "generation_receipts", "ledger_row_sha256": "a" * 64})
            self.assertTrue(events.paired); self.assertEqual(events.rows, [])
            self.assertEqual(events.completed, {}); self.assertEqual(events.completed_count, 50)
            self.assertEqual(events.ledger.row_count, 100); events.close()

    def test_call_events_bind_after_main_ledger_and_unpaired_intent_blocks_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"; row = dict(trace(), stage="a0", value="ok",
                runtime_config_sha256="a" * 64, question_sha256="b" * 64, evidence_sha256="c" * 64)
            journal = DurableCallEvents(path, resume=False)
            identifier = event_id(row, "a0")
            journal.intent({"event": "intent", "event_id": identifier, "operation": "a0",
                "dataset": row["dataset"], "retriever": row["retriever"], "sample_id": row["sample_id"], "position": 0,
                "runtime_config_sha256": row["runtime_config_sha256"], "question_sha256": row["question_sha256"],
                "evidence_sha256": row["evidence_sha256"]})
            journal.completion({"event": "completion", "event_id": identifier, "operation": "a0",
                "ledger": "generation_receipts", "ledger_row_sha256": object_sha(row)})
            journal.close()
            ledgers = {"generation_receipts": [row], "repair_bindings": []}
            reopened = DurableJsonl(path, resume=True)
            validate_call_events(reopened.rows, ledgers); reopened.close()
            unmatched = Path(folder) / "unmatched.jsonl"
            broken = DurableJsonl(unmatched, resume=False)
            broken.append({"event": "intent", "event_id": identifier, "operation": "a0"}); broken.close()
            with self.assertRaisesRegex(RuntimeError, "unpaired"):
                DurableCallEvents(unmatched, resume=True)

    def test_call_event_completion_hash_tampering_is_rejected(self):
        row = dict(trace(), stage="a0", runtime_config_sha256="a" * 64,
            question_sha256="b" * 64, evidence_sha256="c" * 64)
        identifier = event_id(row, "a0")
        events = [
            {"event": "intent", "event_id": identifier, "operation": "a0", **trace(),
             "runtime_config_sha256": "a" * 64, "question_sha256": "b" * 64, "evidence_sha256": "c" * 64},
            {"event": "completion", "event_id": identifier, "operation": "a0",
             "ledger": "generation_receipts", "ledger_row_sha256": "0" * 64},
        ]
        with self.assertRaisesRegex(RuntimeError, "row hash"):
            validate_call_events(events, {"generation_receipts": [row], "repair_bindings": []})

    def test_call_event_operation_inputs_are_bound_to_scientific_rows(self):
        generation = dict(trace(), stage="a0", runtime_config_sha256="a" * 64,
            question_sha256="b" * 64, evidence_sha256="c" * 64)
        gid = event_id(generation, "a0")
        generation_events = [
            {"event": "intent", "event_id": gid, "operation": "a0", **trace(),
             "runtime_config_sha256": "a" * 64, "question_sha256": "b" * 64, "evidence_sha256": "d" * 64},
            {"event": "completion", "event_id": gid, "operation": "a0", "ledger": "generation_receipts",
             "ledger_row_sha256": object_sha(generation)},
        ]
        with self.assertRaisesRegex(RuntimeError, "input binding"):
            validate_call_events(generation_events, {"generation_receipts": [generation], "repair_bindings": []})
        repair = dict(trace(), runtime_config_sha256="a" * 64, query_sha256="e" * 64, requested_depth=50)
        rid = event_id(repair, "repair_retrieval")
        repair_events = [
            {"event": "intent", "event_id": rid, "operation": "repair_retrieval", **trace(),
             "runtime_config_sha256": "a" * 64, "query_sha256": "f" * 64, "requested_depth": 50},
            {"event": "completion", "event_id": rid, "operation": "repair_retrieval", "ledger": "repair_bindings",
             "ledger_row_sha256": object_sha(repair)},
        ]
        with self.assertRaisesRegex(RuntimeError, "repair call intent"):
            validate_call_events(repair_events, {"generation_receipts": [], "repair_bindings": [repair]})

    def test_resume_prefix_accepts_one_partial_trace(self):
        traces = [trace(0), trace(1)]
        key = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s0"}
        generations = [dict(key, stage=s) for s in ("a0", "repair_query")]
        ledgers = {"generation_receipts": generations, "repair_bindings": [], "canonical_branches": [], "branch_provenance": []}
        completed, partial = validate_resume_prefix(traces, ledgers)
        self.assertEqual(completed, 0); self.assertEqual(partial["present"]["repair_query"], True)

    def test_resume_prefix_accepts_every_durable_partial_trace_boundary(self):
        trace_row = trace(0); key = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s0"}
        stages = (
            ("a0",),
            ("a0", "repair_query"),
            ("a0", "repair_query", "repair"),
            ("a0", "repair_query", "repair", "a1"),
            ("a0", "repair_query", "repair", "a1", "provenance"),
        )
        for present in stages:
            with self.subTest(present=present):
                ledgers = {"generation_receipts": [dict(key, stage=stage) for stage in ("a0", "repair_query", "a1") if stage in present],
                    "repair_bindings": [dict(key)] if "repair" in present else [],
                    "branch_provenance": [dict(key)] if "provenance" in present else [],
                    "canonical_branches": []}
                completed, partial = validate_resume_prefix([trace_row], ledgers)
                self.assertEqual(completed, 0); self.assertEqual(partial["index"], 0)

    def test_resume_prefix_treats_branch_write_as_complete_trace(self):
        key = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s0"}
        ledgers = {"generation_receipts": [dict(key, stage=stage) for stage in ("a0", "repair_query", "a1")],
            "repair_bindings": [dict(key)], "branch_provenance": [dict(key)], "canonical_branches": [dict(key)]}
        completed, partial = validate_resume_prefix([trace(0)], ledgers)
        self.assertEqual((completed, partial), (1, None))

    def test_resume_prefix_rejects_stage_gap(self):
        traces = [trace(0)]
        key = {"dataset": "hotpotqa", "retriever": "bm25", "sample_id": "s0"}
        ledgers = {"generation_receipts": [dict(key, stage="a1")], "repair_bindings": [], "canonical_branches": [], "branch_provenance": []}
        with self.assertRaises(RuntimeError): validate_resume_prefix(traces, ledgers)

    def test_output_name_cannot_escape_namespace(self):
        self.assertEqual(validate_output_name("phi-dev-candidate_v1"), "phi-dev-candidate_v1")
        for bad in ("../escape", "a/b", "a\\b", ".", "", " C:"):
            with self.subTest(name=bad), self.assertRaises(RuntimeError): validate_output_name(bad)

    def test_terminal_runtime_namespace_can_never_resume_or_be_reused(self):
        for marker in ("BUILD_RECEIPT.json", "RUNTIME_FAILURE.json", "SHA256_MANIFEST.json"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as folder:
                output = Path(folder); (output / marker).write_text("{}\n", encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "immutable"):
                    require_unsealed_runtime_namespace(output)

    def test_full_trace_order_and_frozen_capture_binding(self):
        traces, frozen = [], []
        for position in range(13_500):
            dataset = ("hotpotqa", "2wikimultihopqa", "musique")[position // 4500]
            retriever = ("bm25", "dense", "hybrid")[position % 3]
            row = {"dataset": dataset, "retriever": retriever, "sample_id": f"s{position}",
                   "position": position, "original_top5_ids": [f"d{position}-{i}" for i in range(5)]}
            traces.append(row)
            frozen.append({"cohort": "development", "dataset": dataset, "retriever": retriever,
                "sample_id": row["sample_id"], "position": position,
                "original_top5_ids_sha256": object_sha(row["original_top5_ids"]), "role": "fit"})
        index = validate_trace_input_binding(traces, frozen)
        self.assertEqual(len(index), 13_500)
        frozen[100], frozen[101] = frozen[101], frozen[100]
        with self.assertRaisesRegex(RuntimeError, "trace order"):
            validate_trace_input_binding(traces, frozen)

    def test_deterministic_capture_binds_prompt_ids_render_and_admission(self):
        capture = {"prompt_sha256": "a" * 64, "input_tokens": 2, "input_token_ids": [2, 3],
            "render": {"context_truncated": False, "per_document_truncated": [False] * 5}}
        witness = {"answer": {"prompt_sha256": "a" * 64, "input_tokens": 2,
            "input_token_ids_sha256": object_sha([2, 3]), "context_truncated": False,
            "per_document_truncated": [False] * 5}}
        validate_frozen_generation_capture(capture, witness, "a0", 2)
        capture["input_token_ids"] = [2, 4]
        with self.assertRaisesRegex(RuntimeError, "token IDs"):
            validate_frozen_generation_capture(capture, witness, "a0", 2)

    def test_io_policy_allows_only_frozen_assets_and_selected_output(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); repo = base / "repo"; original = base / "original"; output = repo / "outputs/cas_q2/run"
            allowed = original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/trace_manifest.jsonl"
            pool_payload = original / "outputs/daa_v2_fresh_v1/pool_freeze/pools/hotpotqa_documents.jsonl"
            policy = DevelopmentRuntimeIOPolicy(repository=repo, original=original, output=output,
                allowed_reads=[allowed, pool_payload])
            policy.check_read(allowed)
            policy.check_read(pool_payload); policy.check_scan(pool_payload.parent)
            policy.check_write(output / "generation_receipts.jsonl")
            for denied in (original / "data/raw/gold.json", original / "src/unlisted.py",
                           pool_payload.parent / "new-unsealed.jsonl",
                           original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/canonical_branches.jsonl"):
                with self.subTest(path=denied), self.assertRaises(RuntimeError): policy.check_read(denied)
            with self.assertRaises(RuntimeError): policy.check_write(repo / "outside.json")

    def test_io_policy_allows_venv_scans_and_rejects_unlisted_project_scans(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); repo = base / "repo"; original = base / "original"
            policy = DevelopmentRuntimeIOPolicy(repository=repo, original=original,
                output=repo / "outputs/cas_q2/run")
            policy.check_scan(original / ".venv/Lib/site-packages/torch")
            policy.check_scan(repo / ".venv/Lib/site-packages/transformers")
            for denied in (original / "src/unlisted", repo / "scripts/unlisted"):
                with self.subTest(path=denied), self.assertRaisesRegex(RuntimeError, "unlisted project"):
                    policy.check_scan(denied)

    def test_runtime_audit_boundary_order_keeps_model_loads_inside(self):
        source = (Path(__file__).resolve().parents[1] / "scripts/build_phi_reader_development_runtime.py").read_text(encoding="utf-8")
        main = source[source.index("def main() -> int:"):]
        ordered = [main.index(fragment) for fragment in (
            "input_paths = source_paths", "input_records =", "pins = verify_pins", "import torch", "import transformers",
            "configure_torch(torch)", "load_original_native(original)", "boundary = install_boundary",
            "torch.cuda.mem_get_info()", "bge._ensure_loaded()", "reader._ensure_loaded()", "read_runtime_inputs(original)")]
        self.assertEqual(ordered, sorted(ordered))

    def test_manifest_allowlist_ignores_only_unsealed_pycache_and_rejects_other_extra(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); namespace = base / "outputs/frozen"; namespace.mkdir(parents=True)
            payload = namespace / "payload.json"; payload.write_text("{}\n", encoding="utf-8")
            cache = namespace / "__pycache__"; cache.mkdir(); (cache / "old.pyc").write_bytes(b"old")
            manifest = namespace / "SHA256_MANIFEST.json"
            manifest.write_bytes(canonical({"files": [{"path": payload.relative_to(base).as_posix(),
                "size_bytes": payload.stat().st_size, "sha256": digest(payload)}]}) + b"\n")
            members = verify_manifest_members(namespace=namespace, manifest_path=manifest,
                expected_manifest_sha256=digest(manifest), record_base=base, allow_only_extra_pycache=True)
            self.assertIn(payload.resolve(), members); self.assertNotIn((cache / "old.pyc").resolve(), members)
            (namespace / "extra.txt").write_text("extra", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "non-pycache"):
                verify_manifest_members(namespace=namespace, manifest_path=manifest,
                    expected_manifest_sha256=digest(manifest), record_base=base, allow_only_extra_pycache=True)

    def test_accepted_model_tree_rejects_tamper_and_extra_member(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); first = root / "config.json"; first.write_text("{}", encoding="utf-8")
            accepted = [record(first)]
            self.assertEqual(verify_recorded_tree(root, accepted), [first.resolve()])
            extra = root / "extra.bin"; extra.write_bytes(b"x")
            with self.assertRaisesRegex(RuntimeError, "members"): verify_recorded_tree(root, accepted)
            extra.unlink(); first.write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "hash"): verify_recorded_tree(root, accepted)

    def test_joint_binding_excludes_prospective_implementation_but_binds_original_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); original = base / "original"; prospective = base / "prospective"
            original.mkdir(); prospective.mkdir()
            source = original / "native.py"; source.write_text("accepted", encoding="utf-8")
            implementation = prospective / "runtime_common.py"; implementation.write_text("new prospective version", encoding="utf-8")
            interpreter = original / "python.exe"; interpreter.write_bytes(b"accepted interpreter")
            accepted = {source.resolve(): record(source), interpreter.resolve(): record(interpreter),
                implementation.resolve(): {**record(implementation), "sha256": "0" * 64}}
            verify_applicable_joint_bindings([source, interpreter, implementation], accepted,
                original=original, interpreter=interpreter)
            source.write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "applicable input"):
                verify_applicable_joint_bindings([source, interpreter, implementation], accepted,
                    original=original, interpreter=interpreter)

    def test_selected_old_runtime_manifest_rejects_tamper_missing_and_duplicate_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); namespace = base / "outputs/runtime"; namespace.mkdir(parents=True)
            member = namespace / "trace_manifest.jsonl"; member.write_text("{}\n", encoding="utf-8")
            row = {"path": member.relative_to(base).as_posix(), "size_bytes": member.stat().st_size, "sha256": digest(member)}
            manifest = namespace / "SHA256_MANIFEST.json"
            manifest.write_bytes(canonical({"files": [row]}) + b"\n")
            verified = verify_selected_manifest_members(namespace=namespace, manifest_path=manifest,
                expected_manifest_sha256=digest(manifest), record_base=base, required_paths=[member])
            self.assertEqual(verified, [manifest.resolve(), member.resolve()])
            member.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "member hash"):
                verify_selected_manifest_members(namespace=namespace, manifest_path=manifest,
                    expected_manifest_sha256=digest(manifest), record_base=base, required_paths=[member])
            member.write_text("{}\n", encoding="utf-8")
            missing = namespace / "MISSING_MANIFEST.json"; missing.write_bytes(canonical({"files": []}) + b"\n")
            with self.assertRaisesRegex(RuntimeError, "missing from manifest"):
                verify_selected_manifest_members(namespace=namespace, manifest_path=missing,
                    expected_manifest_sha256=digest(missing), record_base=base, required_paths=[member])
            duplicate = namespace / "DUPLICATE_MANIFEST.json"; duplicate.write_bytes(canonical({"files": [row, row]}) + b"\n")
            with self.assertRaisesRegex(RuntimeError, "duplicate"):
                verify_selected_manifest_members(namespace=namespace, manifest_path=duplicate,
                    expected_manifest_sha256=digest(duplicate), record_base=base, required_paths=[member])

    def test_replay_decodes_only_selected_fixed_line_positions_and_counts_truthfully(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            selected = [trace(0), trace(2)]
            for ledger, filename in LEDGER_FILES.items():
                lines = []
                if ledger == "generation_receipts":
                    for position in range(3):
                        for stage in ("a0", "repair_query", "a1"):
                            lines.append((canonical({**trace(position), "stage": stage, "raw_text": "raw", "parsed_text": "answer"}) + b"\n")
                                         if position != 1 else b"NON_TARGET_BAD_JSON\n")
                else:
                    for position in range(3):
                        lines.append(canonical(trace(position)) + b"\n" if position != 1 else b"NON_TARGET_BAD_JSON\n")
                (root / filename).write_bytes(b"".join(lines))
            maps, signatures, audit = selected_reference_bytes(root, selected, canonical_trace_count=3)
            self.assertEqual(audit["rows_decoded"], 12)
            self.assertEqual(audit["answer_fields_decoded"], 12)
            self.assertEqual(audit["raw_lines_scanned"], 18)
            self.assertGreater(audit["raw_bytes_scanned"], 0)
            self.assertEqual(len(maps["generation_receipts"]), 6)
            self.assertTrue(all(size > 0 and len(sha) == 64 for sha, size in signatures.values()))


if __name__ == "__main__": unittest.main()
