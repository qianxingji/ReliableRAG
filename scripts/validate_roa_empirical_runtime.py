"""Independent full runtime receipts/repair arithmetic and bounded token replay."""
import argparse
import ast
import collections
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import numpy as np

from scripts.empirical_runtime_io import REPO, OUT, POOL, RETRIEVAL, PREPARATION, GPU_OUT, QREV, bound_inputs, load, record, require, read_rows
from scripts.empirical_runtime_contract import canonical, sha_json as jsha, trace_key
from scripts.empirical_runtime_guard import guard
from scripts.empirical_retrieval_io import configure_environment, seal, boundary_record
from scripts.replay_roa_original import write_json
from scripts.verify_roa_artifacts import digest, safe_file, relative_path

DATASETS=("hotpotqa","2wikimultihopqa","musique")
RETRIEVERS=("bm25","dense","hybrid")
BRANCH_FIELDS={"dataset","retriever","sample_id","question","a0","a1","evidence0","evidence1"}
def tsha(value): return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_independent_functions(root):
    """Compile original independent pure definitions; never import its executor."""
    path=root/"outputs/daa_v2_fresh_v1/runtime_branch_freeze/independent_validate.py"
    names={"no_forbidden_fields","parsed_answer","parsed_query","render","validate_branch",
           "rank_entries","bm25_scores","rrf","validate_rank","replacement","validate_generation","expected_evidence"}
    tree=ast.parse(path.read_text(encoding="utf-8-sig"))
    nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in names) or
           (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="FORBIDDEN" for t in n.targets))]
    require({n.name for n in nodes if isinstance(n,ast.FunctionDef)}==names,"Independent native helper set")
    scope=dict(np=np,re=__import__("re"),math=math,collections=collections,require=require,
               tsha=tsha,jsha=jsha,trace_key=trace_key,BRANCH_FIELDS=BRANCH_FIELDS)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),"exec"),scope)
    return {name:scope[name] for name in names}


def check_sidecar_fields(provenance,repair):
    require(set(provenance)=={"dataset","retriever","sample_id","position","original_top5_row_sha256","e0","e1",
        "question_sha256","canonical_row_sha256","runtime_config_sha256","repair_binding_row_sha256","pool_sha256"},"Provenance exact fields")
    require(set(repair)=={"dataset","retriever","sample_id","position","query_sha256","ranking","component_rankings","dense_query_vector",
        "e0_ids","e1_ids","inserted_document_id","inserted_candidate_rank","replaced_document_id","replacement_position_zero_based",
        "requested_depth","repair_retrieval_calls","pool_sha256","fail_closed_reason"},"Repair exact fields")


def restore_state(dataset,pre):
    docs=read_rows(POOL/"pools"/(dataset+".jsonl"));runtime=read_rows(POOL/"runtime"/(dataset+".jsonl"))
    indexed={d["id"]:dict(document_id=d["id"],content_hash=d["content_hash"],title=d["title"],
                       text=d["title"]+"\n"+"".join(d["sentences"])) for d in docs}
    ids=[d["id"] for d in docs];index=RETRIEVAL/"indexes"/dataset
    structure=load(index/"bm25_structure.json")
    require(structure["document_ids"]==ids,"Independent stored BM25 order")
    matrix=np.load(index/"document_embeddings.npy",allow_pickle=False)
    require(matrix.dtype==np.float32 and matrix.shape==(len(ids),768),"Independent document matrix")
    return dict(ids=ids,docs=indexed,questions={r["id"]:r["question"] for r in runtime},
        binding=dict(pool_sha256=digest(POOL/"pools"/(dataset+".jsonl"))),
        terms={x["term"]:x for x in structure["terms"]},lengths=np.asarray(structure["lengths"],dtype=np.float64),
        average_length=structure["average_length"],matrix=matrix,
        original={r:{x["sample_id"]:x["ranking"][:5] for x in read_rows(RETRIEVAL/"rankings"/(dataset+"_"+r+".jsonl"))} for r in RETRIEVERS})


def validate_all(root,preparation_sha):
    pre,paths=bound_inputs(root,preparation_sha)
    trace_rows=read_rows(PREPARATION/"TRACE_MANIFEST_PRIVATE.jsonl")
    replay_rows=read_rows(PREPARATION/"REPLAY_SUBSET_PRIVATE.jsonl")
    wanted=set()
    for d in DATASETS:
        for r in RETRIEVERS:
            group=[t for t in trace_rows if (t["dataset"],t["retriever"])==(d,r)]
            require(len(group)==2000,"Independent replay stratum")
            ranked=sorted((hashlib.sha256(("daa-v2-runtime-replay-v1|"+d+"|"+r+"|"+t["sample_id"]).encode()).digest(),t["sample_id"]) for t in group)
            wanted.update((d,r,sid) for h,sid in ranked[:20])
    require(replay_rows==[t for t in trace_rows if trace_key(t) in wanted] and len(replay_rows)==180,"Exact independent replay membership/order")
    require(len(trace_rows)==18000 and [t["position"] for t in trace_rows]==list(range(18000)),"Trace positions")
    globals().update(load_independent_functions(root))
    manifests={}
    for mode,base in (("canonical",OUT),("replay",OUT/"replay")):
        mp=base/"EXECUTION_MANIFEST.json";manifest=load(mp);manifests[mode]=manifest;paths.append(mp)
        for e in manifest["files"]:
            q=safe_file(base,relative_path(e["path"]))
            require(digest(q)==e["sha256"] and q.stat().st_size==e["size_bytes"],"Runtime payload byte binding")
            paths.append(q)
        freeze=load(base/"EXECUTABLE_FREEZE.json")
        for e in freeze["inputs"]:
            require(record(Path(e["path"]))==e,"Runtime frozen input/source changed");paths.append(Path(e["path"]))
        require(freeze["runtime_config_sha256"]==pre["runtime_config_sha256"],"Scientific generation configuration")
    expected={e["path"] for e in manifests["canonical"]["files"]}|{"EXECUTION_MANIFEST.json"}|{
        "replay/"+e["path"] for e in manifests["replay"]["files"]}|{"replay/EXECUTION_MANIFEST.json"}
    require({p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()}==expected,"Complete runtime namespace")
    from transformers import AutoTokenizer
    scope=guard(root,OUT,paths,tokenizer_only=True)
    tokenizer=AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct",revision=QREV,
        cache_dir=root/"data/models/huggingface",local_files_only=True,trust_remote_code=False)
    require(tsha(tokenizer.chat_template)==pre["runtime_config"]["tokenizer_chat_template_sha256"],"Pinned tokenizer template")
    templates={"answer":(root/"prompts/baseline_v1.txt").read_text(encoding="utf-8"),
               "repair_query":(root/"prompts/repair_missing_v1.txt").read_text(encoding="utf-8")}
    reports={};actual_keys=[];canonical_references={};replay_keys={trace_key(t) for t in replay_rows};artifacts=[]
    for mode,base,traces in (("canonical",OUT,trace_rows),("replay",OUT/"replay",replay_rows)):
        receipt=load(base/"BUILD_RECEIPT.json")
        require(receipt["status"]==("GENERATED_PENDING_REPLAY_AND_INDEPENDENT" if mode=="canonical" else "PASS_BOUNDED_REPLAY_PENDING_INDEPENDENT"),"Completed runtime pass")
        require(receipt["execution_boundary"]["denied"]==[] and receipt["source_inputs_unchanged"],"Runtime boundaries and unchanged sources")
        require(receipt["completed_traces"]==len(traces),"Actual pass count")
        require(all(receipt[k]==0 for k in ("scientific_fit_calls","fresh_gold_values_materialized","original_question_retrieval_calls","document_embedding_calls","bm25_structure_rebuild_calls")),"Forbidden runtime calls")
        counters=collections.Counter();failclosed=collections.Counter();strata=collections.Counter();state=None;dataset=None;count=0
        paths=[base/p for p in ('canonical_branches.jsonl','branch_provenance.jsonl','repair_bindings.jsonl','generation_receipts.jsonl')]
        handles=[p.open(encoding='utf-8') for p in paths]
        try:
            for trace in traces:
                values=[json.loads(next(h)) for h in handles[:3]];branch,provenance,repair=values
                gens=[json.loads(next(handles[3])) for _ in range(3)]
                require(all(trace_key(v)==trace_key(trace) for v in values+gens),'Ledger aligned trace sequence')
                check_sidecar_fields(provenance,repair)
                validate_branch(branch);no_forbidden_fields(provenance);no_forbidden_fields(repair)
                d,r,sid=trace_key(trace)
                strata[(d,r)]+=1
                require(provenance['runtime_config_sha256']==pre['runtime_config_sha256'],'Provenance configuration binding')
                if dataset!=d:state=restore_state(d,pre);dataset=d
                question=state['questions'][sid];require(branch['question']==question and provenance['question_sha256']==tsha(question),'Frozen question binding')
                require(provenance['pool_sha256']==state['binding']['pool_sha256'] and repair['position']==trace['position'],'Provenance pool and repair position binding')
                e0=expected_evidence(trace['original_top5_ids'],state['original'][r][sid],state)
                require(provenance['e0']==e0 and branch['evidence0']==[x['text'] for x in e0],'Original Top5 ID/text/score binding')
                require(provenance['original_top5_row_sha256']==trace['original_top5_row_sha256'] and provenance['position']==trace['position'],'Original Top5 parent byte binding')
                validate_generation(gens[0],trace,'a0',e0,question,tokenizer,templates,pre)
                validate_generation(gens[1],trace,'repair_query',e0,question,tokenizer,templates,pre)
                query=gens[1]['parsed_text'];require(repair['query_sha256']==tsha(query) and repair['pool_sha256']==state['binding']['pool_sha256'],'Repair query/pool binding')
                valid=set(state['ids']);validate_rank(repair['ranking'],valid,50)
                depth=100 if r=='hybrid' else 50;components={}
                if r in {'bm25','hybrid'}:components['bm25']=rank_entries(bm25_scores(query,state),state['ids'],depth)
                if r in {'dense','hybrid'}:
                    vector=np.asarray(repair['dense_query_vector'],dtype=np.float32)
                    require(vector.shape==(768,) and np.isfinite(vector).all(),'Saved repair-query embedding schema')
                    components['dense']=rank_entries(state['matrix']@vector,state['ids'],depth)
                    counters['repair_query_embedding_calls']+=1;counters['bge_query_forward_calls']+=1
                else:require(repair['dense_query_vector'] is None,'BM25 cannot use dense query')
                require(repair['component_rankings']==components,'Independent repair component ranks/scores')
                expected_ranking=rrf(components['bm25'],components['dense']) if r=='hybrid' else components[r]
                require(repair['ranking']==expected_ranking,'Independent repair ranking/ties/fusion')
                e1_ids,inserted=replacement(expected_ranking,trace['original_top5_ids'])
                require(repair['e0_ids']==trace['original_top5_ids'] and repair['e1_ids']==e1_ids,'Exact native repaired Top5 binding')
                require(repair['inserted_document_id']==inserted['document_id'] and repair['inserted_candidate_rank']==inserted['rank'],'First eligible replacement')
                require(repair['replaced_document_id']==trace['original_top5_ids'][4] and repair['replacement_position_zero_based']==4 and repair['requested_depth']==50 and repair['repair_retrieval_calls']==1 and repair['fail_closed_reason'] is None,'Repair operator controls')
                e1=e0[:4]+[{'rank':5,**state['docs'][inserted['document_id']],'retrieval_score':inserted['score']}]
                require(provenance['e1']==e1 and branch['evidence1']==[x['text'] for x in e1],'Repaired evidence full pool text binding')
                validate_generation(gens[2],trace,'a1',e1,question,tokenizer,templates,pre)
                require(branch['a0']==gens[0]['parsed_text'] and branch['a1']==gens[2]['parsed_text'],'Canonical parsed answers binding, no quality assessment')
                require(provenance['canonical_row_sha256']==jsha(branch) and provenance['repair_binding_row_sha256']==jsha(repair),'Canonical/repair sidecar hashes')
                for gen in gens:
                    stage=gen['stage'];counters[stage+'_generation_calls']+=1;counters[stage+'_generation_completed']+=1
                    counters[stage+'_forward_calls']+=gen['qwen_forward_calls'];counters['qwen_forward_calls']+=gen['qwen_forward_calls']
                    if stage!='repair_query' and not gen['parsed_text']:failclosed['empty_'+stage+'_retained']+=1
                    if stage=='repair_query' and gen['parser_fallback']:failclosed['native_repair_parser_fallback_retained']+=1
                counters['repair_retrieval_calls']+=1;counters['repair_retrieval_completed']+=1;counters['repair_'+r+'_calls']+=1
                signature=jsha({'branch':branch,'provenance':provenance,'repair':repair,'generation':gens})
                if mode=='canonical':
                    actual_keys.append(trace_key(branch))
                    if trace_key(trace) in replay_keys:canonical_references[trace_key(trace)]=signature
                else:require(signature==canonical_references[trace_key(trace)],'DETERMINISTIC_REPLAY_MISMATCH_STOP_PRESERVE_BOTH')
                count+=1
                if count%100==0:print(json.dumps({'stage':'independent_nonmodel_validation','mode':mode,'traces_checked':count,'expected':len(traces)}),flush=True)
            require(all(h.readline()=='' for h in handles),'Extra ledger rows')
        finally:
            for h in handles:h.close()
        require(dict(counters)==receipt['execution_counters'] and dict(failclosed)==receipt['fail_closed_counts'],'Actual call/fail-closed counters reconcile with every receipt')
        require(strata==collections.Counter({(d,r):(2000 if mode=='canonical' else 20) for d in DATASETS for r in RETRIEVERS}),'Exact observed per-stratum coverage')
        require(receipt['stratum_counts']=={d:{r:strata[(d,r)] for r in RETRIEVERS} for d in DATASETS},'Observed stratum counters match build receipt')
        require(receipt['generation_failure_count']==receipt['repair_failure_count']==0,'No unaccounted runtime failure')
        reports[mode]={'status':'PASS','trace_count':count,'stratum_counts':receipt['stratum_counts'],'counters':dict(counters),'fail_closed_counts':dict(failclosed),
            'all_prompt_input_hashes_token_sequences_and_parsers_verified':True,'all_retrieval_bindings_independently_recomputed':True,'actual_backend':receipt['actual_backend']}
        artifacts.extend(receipt['artifacts']);artifacts.append(record(base/'BUILD_RECEIPT.json'))

    require(len(actual_keys)==len(set(actual_keys))==18000 and actual_keys==[trace_key(t) for t in trace_rows],"All canonical trace keys")
    require(len(canonical_references)==180 and reports["canonical"]["actual_backend"]==reports["replay"]["actual_backend"],"Bounded replay configuration")
    require(scope["denied"]==[],"Independent tokenizer-only scope")
    for rec in artifacts:require(record(Path(rec["path"]))==rec,"Runtime artifact changed during validation")
    return dict(status="PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY",cas_q2_status="NOT READY",
        canonical_traces=18000,questions=6000,replay_traces=180,model_forward_calls=0,scientific_fit_calls=0,
        fresh_gold_values_materialized=0,canonical_and_replay=reports,exact_replay_match=True,
        execution_boundary=boundary_record(scope),
        limitations="Every saved receipt and repair ranking checked, with 180-trace actual token replay; not a second full neural reader reproduction or answer-quality evaluation.")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root",type=Path,required=True)
    p.add_argument("--preparation-manifest-sha256",required=True)
    args=p.parse_args()
    require(not (OUT/"INDEPENDENT_VALIDATION.json").exists(),"Single-use runtime validation")
    configure_environment(OUT);platform.uname()._asdict()
    import transformers
    result=dict(status="FAIL",cas_q2_status="NOT READY",model_forward_calls=0,scientific_fit_calls=0,fresh_gold_values_materialized=0)
    try:result=validate_all(args.project_root.resolve(),args.preparation_manifest_sha256)
    except Exception as exc:result.update(error_type=type(exc).__name__,diagnostic=str(exc))
    write_json(OUT/"INDEPENDENT_VALIDATION.json",result)
    if result["status"]=="FAIL":print(json.dumps(result));return 2
    write_json(OUT/"SEAL.json",dict(status="PASS_CANDIDATE_PAIR_ACQUISITION_ONLY",independent_sha256=digest(OUT/"INDEPENDENT_VALIDATION.json"),cas_q2_status="NOT READY"))
    seal(OUT);print(result["status"]);return 0


if __name__=="__main__":
    sys.dont_write_bytecode=True
    raise SystemExit(main())
