"""C4 durable-stage tests: invented CPU logits, real saved heads, no fresh inputs."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import torch
from threadpoolctl import threadpool_limits

from scripts.empirical_scoring_journals import Ledger, ForwardCounter, ForwardJournal, DurableGbV, compact_base, compact_gbv
from scripts.empirical_scoring_stage_independent import bound_trace, JournalValidation, actual_counter
from scripts.empirical_scoring_stage_io import read_rows, stage_prerequisites, serialize_allocation, restore_allocation
from scripts.empirical_scoring_stage_run import StageRun
from scripts.empirical_scoring_binding_fixtures import invented_bound_rows, POOL_SHA, CONFIG_SHA
from scripts.empirical_scoring_import_v2 import native_scoring
from scripts.empirical_scoring_io import saved_models
from scripts.empirical_scoring_pipeline import score_likelihood_trace, score_gbv_trace, common_policy_ledger
from scripts.empirical_policy_independent import validate_policies
from scripts.empirical_neural_checks import Checks
from scripts.empirical_likelihood_witness import LikelihoodWitness
from scripts.empirical_gbv_witness import GbVWitness
from scripts.empirical_likelihood_independent import LikelihoodValidation
from scripts.empirical_gbv_independent import GbVValidation
import test_empirical_likelihood_witness as likelihood_fixture
import test_empirical_gbv_witness as gbv_fixture


class StageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        likelihood_fixture.LikelihoodWitnessTests.setUpClass()
        gbv_fixture.GbVWitnessTests.setUpClass()
        cls.wrapper, cls.native, cls.v2, cls.eligibility, _, _ = native_scoring(Path("E:/paper/ReliableRAG"))
        cls.models, cls.bundle, cls.panel = saved_models(Path("E:/paper/ReliableRAG"), cls.native, cls.v2)

    def trace(self, index=0, answers=None):
        rows = invented_bound_rows(index=index, answers=answers)
        value = bound_trace(*rows, dict(pool_sha={"hotpotqa": POOL_SHA}, runtime_config_sha=CONFIG_SHA), index, Checks())
        value["answer_semantic_agreement"] = .125
        return value

    def test_independent_binding_matches_native_and_rejects_corruption(self):
        from scripts.empirical_scoring_bindings import restore_bound_trace
        rows = invented_bound_rows()
        context = dict(pool_sha={"hotpotqa": POOL_SHA}, runtime_config_sha=CONFIG_SHA)
        actual = bound_trace(*rows, context, 0, Checks())
        expected = restore_bound_trace(self.wrapper, *rows, pool_sha=POOL_SHA, runtime_config_sha=CONFIG_SHA)
        self.assertEqual(actual, expected)
        for component, field, value in ((0, "a0", "altered"), (1, "question_sha256", "0" * 64),
            (2, "position", True), (3, "pool_sha256", "0" * 64), (0, "gold", "forbidden")):
            broken = copy.deepcopy(rows)
            broken[component][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                bound_trace(*broken, context, 0, Checks())

    def fixture(self, folder):
        first = self.trace()
        repeated = copy.deepcopy(first)
        repeated["sample_id"] = "invented-cache-repeat"
        traces = [first, repeated, self.trace(2, ("silver", "invented word " * 100)), self.trace(3, ("silver", "silver"))]
        lmodel = likelihood_fixture.LikelihoodWitnessTests().scorer(folder / "cache")
        nmodel = gbv_fixture.GbVWitnessTests().scorer()
        lw, nw = LikelihoodWitness(lmodel), GbVWitness(nmodel, gbv_fixture.GbVWitnessTests.native)
        lc, nc = ForwardCounter(lmodel.model), ForwardCounter(nmodel.model)
        lf, nf, nb = [Ledger(folder / name) for name in ("likelihood.jsonl", "nli.jsonl", "branches.jsonl")]
        phase = {}
        lj, nj = ForwardJournal(lmodel.model, lw, lf, phase), ForwardJournal(nmodel.model, nw, nf, phase, nli=True)
        durable = DurableGbV(nw, nb, phase)
        base, gbv = [], []
        try:
            with threadpool_limits(limits=1):
                for i, trace in enumerate(traces):
                    durable.begin(trace, i)
                    base.append(compact_base(score_likelihood_trace(self.wrapper, self.native, self.models, self.eligibility, trace, lw)))
                    gbv.append(compact_gbv(score_gbv_trace(self.eligibility, trace, durable)))
                allocation = common_policy_ledger(traces, base, gbv, self.eligibility, self.v2, self.bundle, self.panel)
        finally:
            for item in (lj, nj, lc, nc, lw, nw, lf, nf, nb):
                item.close()
        (folder / "scores.json").write_text(json.dumps(dict(base=base, gbv=gbv, allocation=serialize_allocation(allocation))), encoding="utf-8")
        records = json.loads((folder / "scores.json").read_text(encoding="utf-8"))
        return traces, records, list(read_rows(folder / "likelihood.jsonl")), list(read_rows(folder / "nli.jsonl")), list(read_rows(folder / "branches.jsonl")), lmodel, nmodel, lc, nc

    def test_complete_durable_file_roundtrip_and_partial_second_branch_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            traces, records, lf, nf, nb, lm, nm, lc, nc = self.fixture(Path(tmp))
            journal = JournalValidation(lf, nf, nb)
            lv = LikelihoodValidation(lm.tokenizer, lm.answer_template, lm.resolved_revision)
            nv = GbVValidation(nm.tokenizer, nm.model.config.id2label, max_length=64)
            for i, (trace, base, gbv) in enumerate(zip(traces, records["base"], records["gbv"], strict=True)):
                journal.base(trace, base, i, lv)
                journal.gbv(trace, gbv, i, nv)
            summary = journal.finish()
            # The long-answer pair also reuses its two unchanged a0 cells.
            self.assertEqual((lv.requests, lv.hits, nv.branches, nv.unscorable), (12, 6, 5, 1))
            self.assertEqual((summary["likelihood_forwards"], summary["nli_forwards"]), (lc.calls, nc.calls))
            self.assertEqual(summary["likelihood_input_tokens"], lc.input_tokens_with_padding)
            self.assertEqual(summary["nli_input_tokens_including_padding"], nc.input_tokens_with_padding)
            self.assertEqual(records["gbv"][2]["failed_branch"], "F1")
            self.assertEqual(nb[-1]["state"], "F0")
            self.assertIsNotNone(records["gbv"][2]["F0"])
            self.assertEqual(records["base"][1]["forward_witnesses"], [])
            with threadpool_limits(limits=1):
                report = validate_policies(traces, records["base"], records["gbv"], restore_allocation(records["allocation"]),
                    self.models, self.native.ordinary.ORDINARY_NAMES, self.bundle, self.panel)
            self.assertEqual(report["eligible_count"], 2)
            self.assertLessEqual(report["max_numeric_error"], 1e-10)

    def test_missing_duplicate_wrong_trace_and_orphan_journals_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            traces, records, lf, nf, nb, lm, nm, _, _ = self.fixture(Path(tmp))
            for mode in ("missing", "duplicate", "wrong_trace", "orphan", "branch_mismatch", "wrong_state", "boolean_ref"):
                left, right, branches, values = map(copy.deepcopy, (lf, nf, nb, records))
                if mode == "missing": left.pop(0)
                elif mode == "duplicate": left.insert(1, copy.deepcopy(left[0]))
                elif mode == "wrong_trace": left[0]["sample_id"] = "wrong"
                elif mode == "orphan": right.append(copy.deepcopy(right[-1]))
                elif mode == "branch_mismatch": branches[0]["result"]["score"] = 0.
                elif mode == "wrong_state": right[0]["state"] = "F1"
                else: values["base"][0]["forward_witnesses"][0] = True
                journal = JournalValidation(left, right, branches)
                lv = LikelihoodValidation(lm.tokenizer, lm.answer_template, lm.resolved_revision)
                nv = GbVValidation(nm.tokenizer, nm.model.config.id2label, max_length=64)
                with self.subTest(mode=mode), self.assertRaises(ValueError):
                    for i, trace in enumerate(traces):
                        journal.base(trace, values["base"][i], i, lv)
                        journal.gbv(trace, values["gbv"][i], i, nv)
                    journal.finish()

    def test_actual_counter_preserves_failed_forward_and_journal_keeps_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = gbv_fixture.GbVWitnessTests().scorer()
            observed = GbVWitness(model, gbv_fixture.GbVWitnessTests.native)
            count = ForwardCounter(model.model)
            ledger = Ledger(Path(tmp) / "forwards.jsonl")
            phase = dict(dataset="hotpotqa", retriever="bm25", sample_id="invented", position=0, state="F0")
            journal = ForwardJournal(model.model, observed, ledger, phase, nli=True)
            try:
                observed.score_branch("Color?", "silver", ["An invented silver cog."])
                model.model.bad = True
                with self.assertRaisesRegex(RuntimeError, "logits shape/finite"):
                    observed.score_branch("Color?", "silver", ["An invented silver cog."])
                self.assertEqual((count.calls, ledger.rows), (2, 1))
            finally:
                for item in (journal, observed, count, ledger): item.close()
            self.assertEqual(len(list(read_rows(Path(tmp) / "forwards.jsonl"))), 1)

    def test_missing_prerequisite_creates_no_output_or_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "unstarted"
            with patch("scripts.empirical_scoring_stage_run.STAGES", {"base": target}), \
                patch("scripts.empirical_scoring_stage_run.subprocess.check_output", side_effect=["", "inventedcommit"]), \
                patch("scripts.empirical_scoring_stage_run.stage_prerequisites", side_effect=RuntimeError("unfinished C3")), \
                patch("scripts.empirical_scoring_stage_run.bound_inputs") as inputs:
                with self.assertRaisesRegex(RuntimeError, "unfinished C3"):
                    StageRun(Path(tmp), "base", {})
                inputs.assert_not_called()
            self.assertFalse(target.exists())
        with self.assertRaisesRegex(RuntimeError, "Exact predecessor"):
            stage_prerequisites("base", dict(runtime="a" * 64))

    def test_cpu_counter_rejects_wrong_device_extra_calls_and_boolean_values(self):
        good = dict(attempted_forward_calls=1, attempted_input_rows=1, attempted_input_tokens_including_padding=12, devices=["cuda:0"])
        actual_counter(Checks(), good, calls=1, rows=1, tokens=12)
        for field, value in (("devices", ["cpu"]), ("attempted_forward_calls", 2), ("attempted_input_rows", True)):
            with self.assertRaises(ValueError):
                actual_counter(Checks(), {**good, field: value}, calls=1, rows=1, tokens=12)

    def test_complete_prerequisite_chain_rejects_partial_replay_gold_or_wrong_ancestor(self):
        from scripts import empirical_scoring_stage_io as io
        pins = {name: str(i) * 64 for i, name in enumerate(("runtime", "gpu_preflight", "base", "gbv", "policies"), 1)}
        validation = dict(status="PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY", canonical_traces=18000, questions=6000,
            replay_traces=180, exact_replay_match=True, model_forward_calls=0, scientific_fit_calls=0, fresh_gold_values_materialized=0)
        freezes = {"runtime": {"inputs": []}}
        for name, ancestors in (("gpu_preflight", ["runtime"]), ("base", ["runtime", "gpu_preflight"]),
            ("gbv", ["runtime", "gpu_preflight", "base"]), ("policies", ["runtime", "gpu_preflight", "base", "gbv"])):
            freezes[name] = dict(inputs=[], predecessor_manifests={k: pins[k] for k in ancestors})
        folders = {io.RUNTIME: "runtime", **{path: name for name, path in io.STAGES.items()}}
        def load(path):
            name = folders[path.parent]
            if path.name == "INDEPENDENT_VALIDATION.json": return validation
            if path.name == "SEAL.json": return dict(status="PASS_CANDIDATE_PAIR_ACQUISITION_ONLY", independent_sha256="f" * 64)
            if path.name == "EXECUTABLE_FREEZE.json": return freezes[name]
            return dict(status=io.EXPECTED_STATUS[name], source_inputs_unchanged=True)
        with patch.object(io, "verify_namespace", return_value=[]), patch.object(io, "load", side_effect=load), \
            patch.object(io, "record", return_value={"sha256": "f" * 64}):
            self.assertEqual(stage_prerequisites("independent", pins), [])
            for field, value in (("replay_traces", 179), ("exact_replay_match", False), ("fresh_gold_values_materialized", 1)):
                old = validation[field]
                validation[field] = value
                with self.subTest(field=field), self.assertRaises(RuntimeError):
                    stage_prerequisites("independent", pins)
                validation[field] = old
            freezes["policies"]["predecessor_manifests"]["base"] = "e" * 64
            with self.assertRaisesRegex(RuntimeError, "predecessor chain"):
                stage_prerequisites("independent", pins)

    def test_stage_specific_weight_and_benchmark_decoding_rules(self):
        code = r'''
import sys
from pathlib import Path
from scripts import empirical_scoring_stage_guard as module
root=Path(sys.argv[1]);stage=sys.argv[2];out=root/'out';out.mkdir()
q=root/'data/models/huggingface/models--Qwen--Qwen2.5-3B-Instruct/model.safetensors'
n=root/'outputs/published_baseline_gbv_nli_v1/infrastructure/model_snapshot/model.safetensors'
f=root/'outputs/cas_q2/other/branches.jsonl'
s=root/'saved.joblib'
for path in (q,n,f,s):path.parent.mkdir(parents=True,exist_ok=True);path.write_text('invented')
module.REPO=root
receipt=module.guard(root,out,[q,n,f,s],stage=stage)
allowed={'gpu_preflight':{q,n,s},'base':{q,f,s},'gbv':{n,f},'policies':{f,s},'independent':{f,s}}[stage]
for path in (q,n,f,s):
    try:assert path.read_text()=='invented'
    except RuntimeError:assert path not in allowed
    else:assert path in allowed
assert len(receipt['denied'])==4-len(allowed)
print('PASS')
'''
        for stage in ("gpu_preflight", "base", "gbv", "policies", "independent"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                process = subprocess.run([sys.executable, "-B", "-c", code, tmp, stage], capture_output=True, text=True)
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertEqual(process.stdout.strip(), "PASS")

    def test_stage_guard_denies_real_weight_open_and_neural_forward_in_cpu_stage(self):
        code = r'''
import json,sys
from pathlib import Path
from scripts.empirical_scoring_stage_guard import guard
from scripts.verify_roa_artifacts import digest
root=Path(sys.argv[1]);out=root/'out';out.mkdir()
q=root/'data/models/huggingface/models--Qwen--Qwen2.5-3B-Instruct/model.safetensors'
q.parent.mkdir(parents=True);q.write_bytes(b'invented not weights')
receipt=guard(root,out,[q],stage='independent')
assert len(digest(q))==64
try:q.read_bytes()
except RuntimeError:pass
else:raise AssertionError('CPU validator decoded weights')
class Toy:
    def parameters(self):return []
    def forward(self):raise AssertionError('forbidden forward body ran')
try:Toy().forward()
except RuntimeError:pass
else:raise AssertionError('CPU validator forwarded')
print(json.dumps(dict(denials=len(receipt['denied']))))
'''
        with tempfile.TemporaryDirectory() as tmp:
            process = subprocess.run([sys.executable, "-B", "-c", code, tmp], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["denials"], 2)


if __name__ == "__main__":
    unittest.main()
