"""Cost reconciliation on invented receipts, with no fresh answer decoding."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.empirical_cost_accounting import generation_projection, generation_cost, scoring_cost, retrieval_cost, timing, DATASETS, RETRIEVERS, STAGES, POLICIES
from scripts.empirical_outcome_native import definitions, PARSER_SHA
from scripts.empirical_pool_io import checked


def invented_generation():
    rows = []
    for ds in DATASETS:
        for retriever in RETRIEVERS:
            position = len(rows)//3
            for stage in STAGES:
                rows.append(dict(dataset=ds,retriever=retriever,sample_id="invented",position=position,stage=stage,
                    input_tokens=3,output_tokens=1,native_output_score_steps=2,logical_generation_calls=1,qwen_forward_calls=2,
                    input_token_ids=[15,16,17],attention_mask=[1,1,1],generated_token_ids=[18,19],prompt_sha256="opaque",
                    raw_text="DO_NOT_DECODE_RAW",parsed_text="DO_NOT_DECODE_PARSED",render={"text":"DO_NOT_DECODE_PASSAGE"},
                    parser_fallback=None,runtime_config_sha256="opaque"))
    counters = dict(repair_retrieval_calls=9, repair_retrieval_completed=9,repair_query_embedding_calls=6,bge_query_forward_calls=6,
        repair_bm25_calls=3,repair_dense_calls=3,repair_hybrid_calls=3,qwen_forward_calls=54)
    for stage in STAGES:
        counters.update({stage+"_generation_calls":9,stage+"_generation_completed":9,stage+"_forward_calls":18})
    build = dict(completed_traces=9,execution_counters=counters,scientific_fit_calls=0,fresh_gold_values_materialized=0,
        original_question_retrieval_calls=0,document_embedding_calls=0,bm25_structure_rebuild_calls=0,generation_failure_count=0,repair_failure_count=0)
    independent = dict(trace_count=9,counters=copy.deepcopy(counters))
    return rows, build, independent


def invented_scoring():
    def actual(calls,rows,tokens):
        return dict(attempted_forward_calls=calls,attempted_input_rows=rows,attempted_input_tokens_including_padding=tokens,devices=["cuda:0"])
    base = dict(native_eligible_traces=2,bge=dict(actual=actual(2250,36000,108000)),likelihood_cell_requests=8,
        qwen=dict(sequences_computed=6,cache_hits=2,computed_prompt_tokens=60,computed_answer_tokens=12,actual=actual(6,6,72)))
    gbv = dict(common_eligible_traces=1,completed_branches=3,attempted_branches=4,gbv=dict(actual=actual(4,15,1920)))
    policy = dict(N_all=18000,N_eligible=1,cap=900,neural_model_loads=0,neural_forward_calls=0,
        replacement_counts={p:0 if p=="Keep" else 1 for p in POLICIES})
    independent = dict(traces=18000,native_eligible_traces=2,common_eligible_traces=1,
        answer_semantics={d:dict(answer_texts=12000,forward_calls=750) for d in DATASETS},
        likelihood=dict(cell_requests=8,forward_calls=6,cache_hits=2,computed_prompt_tokens=60,computed_answer_tokens=12),
        journals=dict(likelihood_input_tokens=72,likelihood_forwards=6,nli_forwards=4,nli_input_rows=15,completed_nli_branches=3,nli_input_tokens_including_padding=1920),
        gbv=dict(forward_calls=4,nli_pairs=15,completed_branches=3,deterministic_unscorable_pairs=1))
    return base,gbv,policy,independent


class CostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=checked(Path("E:/paper/ReliableRAG/src/phase10/source_projection_v2r1.py"),PARSER_SHA)
        module,_=definitions(path,("_JSONByteCursor",),dict(json=json,Phase10FailClosed=RuntimeError))
        cls.Cursor=module._JSONByteCursor

    def project(self,rows,Cursor=None):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"invented.jsonl"
            path.write_text("".join(json.dumps(r)+"\n" for r in rows),encoding="utf-8")
            return list(generation_projection(path,Cursor or self.Cursor))

    def test_generation_projection_skips_answer_passage_values_and_all_tokens(self):
        seen=[]
        class Observed(self.Cursor):
            def read_string(self,*,path):
                value=super().read_string(path=path);seen.append(value);return value
        rows,build,independent=invented_generation()
        projected=self.project(rows,Observed)
        self.assertFalse(any(v.startswith("DO_NOT_DECODE") for v in seen))
        self.assertNotIn("input_token_ids",projected[0])
        result=generation_cost(projected,build,independent,questions_per_stratum=1)
        self.assertEqual(result['generation_by_stage']['a0']['input_tokens'],27)
        self.assertEqual(result['generation_by_stage']['repair_query']['qwen_forward_calls'],18)
        self.assertEqual(result['bm25_component_calls'],6)
        self.assertEqual(len(result['generation_by_cell']),27)

    def test_generation_rejects_incomplete_duplicate_order_counter_and_mask_damage(self):
        rows,build,independent=invented_generation();values=self.project(rows)
        variants=[values[:-1],values+values[:3],values[1:]+values[:1]]
        for field,value in (("input_tokens",4),("output_tokens",3),("position",True),("qwen_forward_calls",3),("sample_id","other")):
            changed=copy.deepcopy(values);changed[1][field]=value;variants.append(changed)
        for changed in variants:
            with self.assertRaises(ValueError):generation_cost(changed,build,independent,questions_per_stratum=1)
        bad=copy.deepcopy(build);bad['execution_counters']['repair_dense_calls']=4
        with self.assertRaises(ValueError):generation_cost(values,bad,independent,questions_per_stratum=1)

    def test_projection_rejects_unknown_fields_noninteger_arrays_and_negative_counts(self):
        rows,_,_=invented_generation()
        for field,value in (("answer", "forbidden"),("attention_mask",[1,2,1]),("input_token_ids",[15,"text",17]),("position",False)):
            changed=copy.deepcopy(rows);changed[0][field]=value
            with self.subTest(field=field),self.assertRaises((RuntimeError,ValueError)):self.project(changed)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"invented.jsonl"
            for raw in ('{"dataset":"hotpotqa","dataset":"hotpotqa"}',json.dumps(rows[0]).replace('[15, 16, 17]','[15,16,17,]')):
                path.write_text(raw,encoding="utf-8")
                with self.assertRaises((RuntimeError,ValueError)):list(generation_projection(path,self.Cursor))

    def test_scoring_includes_cached_cells_and_completed_branch_of_failed_pair(self):
        base,gbv,policy,independent=invented_scoring()
        result=scoring_cost(base,gbv,policy,independent)
        self.assertEqual(result['likelihood_cell_requests'],8)
        self.assertEqual(result['likelihood']['sequences_computed'],6)
        self.assertEqual(result['completed_nli_branches'],3)
        self.assertEqual(result['deterministic_unscorable_pairs'],1)
        for target,field,value in ((base['qwen'],'cache_hits',1),(gbv,'attempted_branches',3),
            (gbv['gbv']['actual'],'attempted_forward_calls',3),(policy['replacement_counts'],'HGB',0)):
            old=target[field];target[field]=value
            with self.assertRaises(ValueError):scoring_cost(base,gbv,policy,independent)
            target[field]=old

    def test_hybrid_components_and_missing_measurements_are_not_fabricated(self):
        counters=dict(bm25_structure_builds=3,embedding_document_rows=54716,embedding_forward_documents=3422,embedding_query_rows=12000,
            embedding_forward_queries=12000,embedding_forward_calls=15422,original_retrieval_calls=18000,original_bm25_calls=6000,original_dense_calls=6000,original_hybrid_calls=6000)
        build=dict(execution_counters=counters,datasets={d:dict(questions=2000,traces=6000,pool_documents=n) for d,n in zip(DATASETS,(11746,19352,23618))})
        self.assertEqual(retrieval_cost(build)['bm25_component_calls'],12000)
        self.assertEqual(timing({},boundary="missing")['missing_measurements'],['elapsed_seconds','cuda_allocator_peak_bytes'])
        with self.assertRaises(ValueError):timing({'elapsed_seconds':float('nan')},boundary="invalid")
        with self.assertRaises(ValueError):timing({'peak_allocated_cuda_bytes':-1},boundary="invalid",peak=True)

    def test_missing_prelabel_does_not_open_generation_or_make_cost_namespace(self):
        from scripts import audit_roa_empirical_cost as module
        with patch.object(module,'prerequisites',side_effect=RuntimeError('missing full prelabel')),patch.object(module,'verify_namespace') as other:
            with self.assertRaisesRegex(RuntimeError,'missing full prelabel'):module.authorized_inputs(Path('invented'),'a'*64)
            other.assert_not_called()
        self.assertTrue(all(p.is_file() for p in module.source_paths()))
        result=subprocess.run([sys.executable,'-B','-m','scripts.audit_roa_empirical_cost','--help'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_guard_allows_cost_projection_and_opaque_authentication_only(self):
        code=r'''
import sys
from pathlib import Path
from scripts.empirical_cost_guard import guard
from scripts.verify_roa_artifacts import digest
root,out,ledger,canonical,raw=(Path(p) for p in sys.argv[1:])
boundary=guard(root,out,[ledger,canonical,raw],[ledger])
assert ledger.read_text()=='allowed'
assert len(digest(canonical))==len(digest(raw))==64
for path in (canonical,raw):
    try:path.read_text()
    except RuntimeError:pass
    else:raise AssertionError('cost decode escaped')
def generate():pass
try:generate()
except RuntimeError:pass
else:raise AssertionError('generation allowed')
sys.setprofile(None)
assert boundary['forbidden_calls']==1
assert len(boundary['denied'])==3
'''
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'new';out.mkdir();raw=root/'data/raw/reference.json';raw.parent.mkdir(parents=True)
            ledger=root/'generation.jsonl';canonical=root/'canonical.jsonl'
            for p in (raw,ledger,canonical):p.write_text('allowed',encoding='utf-8')
            result=subprocess.run([sys.executable,'-B','-c',code,*map(str,(root,out,ledger,canonical,raw))],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__':
    unittest.main()
