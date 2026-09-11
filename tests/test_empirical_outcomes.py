"""Original selective readers and independent metrics on invented references."""
import copy
import io
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

from scripts.empirical_outcome_native import authenticate, native, canonical_answer_rows
from scripts.empirical_outcome_independent import metrics, validate_numeric_rows


class OutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path("E:/paper/ReliableRAG")
        spec, _, _, _ = authenticate(root)
        cls.metric, cls.Cursor, cls.readers, _ = native(root, spec)

    def test_independent_metric_matches_original_special_empty_alias_and_repeat_cases(self):
        cases = (("The BLUE cog!", ["blue cog"]), ("yes no", ["yes"]), ("yes", ["yes no"]),
            ("noanswer", ["NoAnswer"]), ("", ["the"]), ("", ["silver"]), ("one one blue", ["one blue blue"]),
            ("blue cog", ["silver", "The blue cog!"]), ("一只银色齿轮", ["一只银色齿轮"]), ("café", ["cafe", "café"]))
        for answer, references in cases:
            with self.subTest(answer=answer):
                em, f1 = metrics(answer, references)
                self.assertEqual(em, int(self.metric.exact_match(answer, references)))
                self.assertLessEqual(abs(f1-self.metric.token_f1(answer, references)), 1e-15)

    def test_json_reader_skips_unselected_reference_and_all_support_values(self):
        seen = []
        class ObservedCursor(self.Cursor):
            def read_string(self, *, path):
                value = super().read_string(path=path)
                seen.append(value)
                return value
        rows = [dict(answer="DO_NOT_DECODE_UNSELECTED", id="unselected", supporting_facts=["DO_NOT_DECODE_SUPPORT"]),
            dict(answer="silver", id="selected", answer_aliases=["gray metal", ""], question="DO_NOT_DECODE_QUESTION")]
        for json_lines in (False, True):
            seen.clear()
            raw = ("\n".join(json.dumps(r) for r in rows) if json_lines else json.dumps(rows)).encode()
            values, receipt = self.readers.json_references(lambda: io.BytesIO(raw), {"selected"}, id_field="id",
                json_lines=json_lines, aliases=True, Cursor=ObservedCursor)
            self.assertEqual(values, {"selected": ["silver", "gray metal", ""]})
            self.assertEqual(receipt['selected_question_labels'], 1)
            self.assertEqual(receipt['unselected_reference_python_values_materialized'], 0)
            self.assertFalse(any(value.startswith("DO_NOT_DECODE") for value in seen))

    def test_canonical_answer_projection_skips_questions_passages_and_rejects_extra_fields(self):
        seen = []
        class ObservedCursor(self.Cursor):
            def read_string(self, *, path):
                value = super().read_string(path=path)
                seen.append(value)
                return value
        branch = dict(dataset="hotpotqa", retriever="bm25", sample_id="invented", a0="silver", a1="blue",
            question="DO_NOT_DECODE_QUESTION", evidence0=["DO_NOT_DECODE_E0"], evidence1=["DO_NOT_DECODE_E1"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"branches.jsonl"
            path.write_text(json.dumps(branch)+"\n", encoding="utf-8")
            actual = list(canonical_answer_rows(path, ObservedCursor))
            self.assertEqual(set(actual[0]), {"dataset", "retriever", "sample_id", "a0", "a1"})
            self.assertFalse(any(value.startswith("DO_NOT_DECODE") for value in seen))
            path.write_text(json.dumps({**branch, 'gold': 'forbidden'})+"\n", encoding="utf-8")
            with self.assertRaises(RuntimeError): list(canonical_answer_rows(path, ObservedCursor))

    def test_independent_numeric_coverage_metrics_and_schema_reject_corruption(self):
        references = {("hotpotqa", "invented"): ["silver", "metal gray"]}
        branches = [dict(dataset="hotpotqa", retriever=r, sample_id="invented", a0="silver", a1="blue")
            for r in ("bm25", "dense", "hybrid")]
        rows = [{**{k: b[k] for k in ('dataset', 'retriever', 'sample_id')}, 'a0_em':1, 'a1_em':0, 'a0_f1':1., 'a1_f1':0.} for b in branches]
        report = validate_numeric_rows(branches, references, rows, question_count=1)
        self.assertEqual(report['metric_values_checked'], 12)
        for field, value in (('a0_em', True), ('a1_em', 1), ('a0_f1', .9), ('answer', 'forbidden'), ('sample_id', 'foreign')):
            broken = copy.deepcopy(rows); broken[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_numeric_rows(branches, references, broken, question_count=1)
        with self.assertRaises(ValueError): validate_numeric_rows(branches[:-1], references, rows[:-1], question_count=1)

    def test_duplicate_source_ids_and_missing_selected_references_fail(self):
        for data, selected in (([dict(id='same',answer='a'),dict(id='same',answer='b')], {'same'}),
            ([dict(id='one',answer='silver')], {'missing'})):
            raw = json.dumps(data).encode()
            with self.assertRaises(RuntimeError):
                self.readers.json_references(lambda: io.BytesIO(raw), selected, id_field='id', json_lines=False, aliases=False, Cursor=self.Cursor)

    def test_original_parquet_selected_scalar_reader_on_invented_file(self):
        package = Path('E:/paper/ReliableRAG/tmp/daa_v2_hotpot_full_column_reader')
        sys.path.insert(0, str(package))
        import pyarrow as pa
        import pyarrow.parquet as pq
        self.assertEqual(Path(pa.__file__).resolve(), package/'pyarrow/__init__.py')
        self.assertEqual(pa.__version__, '20.0.0')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'invented.parquet'
            pq.write_table(pa.table(dict(id=['selected', 'unselected'], answer=['silver', 'DO_NOT_SELECT'],
                question=['unneeded', 'unneeded'], supporting_facts=['unneeded', 'unneeded'])), path)
            refs, receipt = self.readers.parquet_references(path, {'selected'}, pq)
            self.assertEqual(refs, {'selected': ['silver']})
            self.assertEqual(receipt['decoded_columns'], ['id', 'answer'])
            self.assertFalse(receipt['supporting_fact_question_context_columns_decoded'])
            self.assertTrue(receipt['physical_page_decompression_may_include_unselected_rows'])

    def test_real_D_guard_separates_mapping_and_numeric_analysis_inputs(self):
        code = r'''
import sys
from pathlib import Path
from scripts import empirical_outcome_guard as module
base=Path(sys.argv[1]);mode=sys.argv[2];root=base/'original';repo=base/'engineering';out=base/'out';out.mkdir()
raw=root/'data/raw/toy.json';policy=repo/'outputs/cas_q2/empirical_prelabel_policies_v1/POLICIES.json'
branch=repo/'outputs/cas_q2/empirical_runtime_v1/canonical_branches.jsonl';model=root/'model.joblib'
for path in (raw,policy,branch,model):path.parent.mkdir(parents=True,exist_ok=True);path.write_text('invented')
module.REPO=repo
state=module.guard(root,out,[raw,policy,branch,model],mode=mode)
allowed={raw,branch} if mode in {'mapping','outcome_validation'} else {policy}
for path in (raw,policy,branch,model):
    try:assert path.read_text()=='invented'
    except RuntimeError:assert path not in allowed
    else:assert path in allowed
with (out/'result.json').open('x') as f:f.write('preserved')
try:(out/'result.json').write_text('overwrite')
except RuntimeError:pass
else:raise AssertionError('overwritten output')
assert (out/'result.json').read_text()=='preserved'
print('PASS')
'''
        for mode in ('mapping', 'outcome_validation', 'analysis', 'analysis_validation'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                result = subprocess.run([sys.executable, '-B', '-c', code, tmp, mode], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), 'PASS')

    def test_inventory_allows_opaque_hash_but_denies_actual_label_decode_and_fit(self):
        code = r'''
import sys
from pathlib import Path
from scripts.empirical_outcome_guard import guard
from scripts.verify_roa_artifacts import digest
root=Path(sys.argv[1]);out=root/'new';out.mkdir();raw=root/'data/raw/toy.json'
raw.parent.mkdir(parents=True);raw.write_text('invented')
state=guard(root,out,[raw],mode='audit')
assert len(digest(raw))==64
try:raw.read_text()
except RuntimeError:pass
else:raise AssertionError('Gold decode in inventory')
def fit():raise AssertionError('fit body executed')
try:fit()
except RuntimeError:pass
else:raise AssertionError('fit ran')
assert len(state['denied'])==2
print('PASS')
'''
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, '-B', '-c', code, tmp], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'PASS')


if __name__ == '__main__':
    unittest.main()
