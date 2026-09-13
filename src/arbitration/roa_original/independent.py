"""Separate numeric reconstruction. No executor/design/learning/metrics imports, no fits."""
import hashlib
import math
import statistics
import itertools
import numpy as np
from scipy.special import expit
from threadpoolctl import threadpool_limits, threadpool_info
from controls import OUT, ROOT, DHC, SOURCES, load, keyed, key, keydict, kh, lines, rec, check, write, parents, frozen, guard, guard_receipt, require, now

FIELDS=['state_symmetric_hgb','state_symmetric_logistic','no_cross_state','no_B','no_evidence_change',
        'no_answer_form','ordinary_compact_logistic','B_rule','higher_own_likelihood','likelihood_margin','gbv_margin']
VAR=['ROA-FULL','ROA-NOGBV']; RET=['bm25','dense','hybrid']; METHODS=VAR+['HGB','GbV','V2']
DS=['musique','2wikimultihopqa','hotpotqa']; SEEDS=[20260917,20260918,20260919,20260920,20260921]
CHECKS=0; MAX_ERROR=0.0
def equal(actual, expected, path='root'):
    global CHECKS,MAX_ERROR
    CHECKS+=1
    if isinstance(expected,dict):
        require(isinstance(actual,dict) and set(actual)==set(expected),'DICT:'+path)
        for n,v in expected.items(): equal(actual[n],v,path+'/'+str(n))
    elif isinstance(expected,(tuple,list)):
        require(isinstance(actual,(tuple,list)) and len(actual)==len(expected),'LIST:'+path)
        for i,(a,b) in enumerate(zip(actual,expected)): equal(a,b,path+'/'+str(i))
    elif isinstance(expected,float):
        require(isinstance(actual,(int,float)) and not isinstance(actual,bool) and math.isfinite(actual),'NUMBER:'+path)
        error=abs(actual-expected); MAX_ERROR=max(MAX_ERROR,error)
        require(error<=1e-10,'FLOAT:'+path+':'+str(error))
    else: require(type(actual)==type(expected) and actual==expected,'VALUE:'+path)
def ah(a): return hashlib.sha256(np.asarray(a,dtype='<f8').tobytes()).hexdigest()
def hashmod(text): return int.from_bytes(hashlib.sha256(text.encode('utf-8')).digest(),'big')%5
def split(allkeys,c):
    result={p:set() for p in ('fit','cal','test')}
    for k in allkeys:
        ds,_,qid=k
        if c['stage']=='primary':
            is_test=hashmod(f"v3-dhc-outer-v1|{c['seed']}|{ds}|{qid}")==c['outer']
            token=f"v3-dhc-outer-cal-v1|{c['seed']}|{c['outer']}|{ds}|{qid}"
        else:
            is_test=ds==c['heldout']
            token=f"v3-dhc-lodo-final-cal-v1|20260922|{c['heldout']}|{ds}|{qid}"
        result['test' if is_test else 'cal' if hashmod(token)==0 else 'fit'].add(k)
    return result
def summarize(kk, selected, outcomes, cap=None):
    metrics={}
    for m in METHODS:
        action=set(kk)&selected[m]; transitions=[(outcomes[k]['a0_em'],outcomes[k]['a1_em']) for k in sorted(action)]
        recovery=transitions.count((0,1)); damage=transitions.count((1,0)); net=recovery-damage
        metrics[m]=dict(N_all=len(kk),actions=len(action),recovery=recovery,damage=damage,
            neutral=transitions.count((0,0))+transitions.count((1,1)),net=net,
            delta_em_pp=100*net/len(kk) if kk else None,
            delta_f1_pp=100*math.fsum(outcomes[k]['a1_f1']-outcomes[k]['a0_f1'] for k in sorted(action))/len(kk) if kk else None,cap=cap)
    comparisons={}
    for v in VAR:
        comparisons[v]={}
        for m in METHODS:
            if m==v: continue
            comparisons[v][m]=dict(delta_em_pp=metrics[v]['delta_em_pp']-metrics[m]['delta_em_pp'] if kk else None,
                delta_f1_pp=metrics[v]['delta_f1_pp']-metrics[m]['delta_f1_pp'] if kk else None,
                net_difference=metrics[v]['net']-metrics[m]['net'],damage_difference=metrics[v]['damage']-metrics[m]['damage'])
    return dict(methods=metrics,comparisons=comparisons)
def groups(kk, selected, outcomes):
    result={}
    for name,labels in [('dataset',sorted(DS)),('retriever',RET),('dataset_x_retriever',[(d,r) for d in sorted(DS) for r in RET])]:
        cells=[]
        for label in labels:
            subset={k for k in kk if (k[0] if name=='dataset' else k[1] if name=='retriever' else (k[0],k[1]))==label}
            cells.append(dict(cell=label,summary=summarize(subset,selected,outcomes)))
        result[name]=cells
    return result
def verdict(reps,lodo):
    success={}; medians={}; damage={}; transport={}
    for v in VAR:
        success[v]={}
        for m in ('HGB','GbV'):
            success[v][m]=len([1 for r in reps if r['pooled']['methods'][v]['net']>r['pooled']['methods'][m]['net']
                              and r['pooled']['methods'][v]['damage']<=r['pooled']['methods'][m]['damage']])
        medians[v]={n:statistics.median(r['pooled']['comparisons'][v]['GbV'][n] for r in reps) for n in ('delta_em_pp','delta_f1_pp')}
        damage[v]=statistics.median(r['pooled']['methods'][v]['damage'] for r in reps)
        transport[v]={m:{l['heldout']:l['summary']['comparisons'][v][m]['delta_em_pp'] for l in lodo} for m in ('HGB','GbV')}
    gap=statistics.median(r['pooled']['comparisons']['ROA-FULL']['ROA-NOGBV']['delta_em_pp'] for r in reps)
    fewer=sum(r['pooled']['methods']['ROA-FULL']['damage']<=r['pooled']['methods']['GbV']['damage'] for r in reps)
    s=[success[VAR[0]]['HGB']>=4,success[VAR[0]]['GbV']>=4,medians[VAR[0]]['delta_em_pp']>=.4,
       medians[VAR[0]]['delta_f1_pp']>=.3,fewer>=4,all(v>=0 for v in transport[VAR[0]]['GbV'].values()),
       all(v>=-.1 for v in transport[VAR[0]]['HGB'].values())]
    rejected={'success_vs_GbV_below_3':success[VAR[0]]['GbV']<3,'median_em_nonpositive':medians[VAR[0]]['delta_em_pp']<=0}
    independent=[success[VAR[1]]['GbV']>=4,medians[VAR[1]]['delta_em_pp']>=.3,gap<=.1,
                 all(v>=-.1 for v in transport[VAR[1]]['GbV'].values()),damage[VAR[1]]<=damage[VAR[0]]+2]
    if all(s): status='ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE'; dependency='BASELINE_INDEPENDENCE_SUPPORTED' if all(independent) else 'GBV_AUGMENTED_ONLY'
    elif any(rejected.values()): status='ROA_FULL_REJECTED'; dependency=None
    else: status='ROA_FULL_INCONCLUSIVE'; dependency=None
    cc={f'condition_{i+1}':b for i,b in enumerate(s)}
    return dict(decision=status,dependence_label=dependency,support_conditions=cc,rejection_triggers=rejected,
        independence_conditions={f'condition_{i+1}':b for i,b in enumerate(independent)} if all(s) else None,
        success_counts=success,median_minus_GbV=medians,median_damage=damage,full_damage_le_GbV_repetitions=fewer,
        median_FULL_minus_NOGBV_em_pp=gap,lodo_em_comparisons=transport,failed_support_conditions=[k for k,v in cc.items() if not v],
        cohort_role='V3_DEVELOPMENT_ONLY',final_full_development_model_fitted=False,fresh_confirmatory_ID_selection=False)
def main():
    threadpool_info(); frozen(); pp=parents(); access=guard(pp['files'])
    source={n:keyed(p) for n,p in SOURCES.items()}; a=source['actions']; b=source['base']; g=source['gbv']; y=source['outcomes']
    equal(len(a),13500); equal(len({(k[0],k[2]) for k in a}),4500)
    require(set(a)==set(b)==set(g)==set(y),'SOURCE_ALIGNMENT')
    features={}; comparison={}
    for k in sorted(a):
        equal(set(b[k]['scores']),set(FIELDS[:-1]))
        vv=[b[k]['scores'][n] for n in FIELDS[:-1]]+[g[k]['gbv_margin']]
        features[k]=dict(**keydict(k),numeric=[float(v) if v is not None and math.isfinite(v) else None for v in vv],eligible=a[k]['v2_eligible_and_scorable'])
        equal(a[k]['v2_eligible_and_scorable'],a[k]['hgb_eligible_and_scorable'])
        comparison[k]=dict(**keydict(k),HGB=a[k]['hgb_score'],GbV=g[k]['gbv_margin'],V2=a[k]['v2_score'])
    equal(sum(v['eligible'] for v in features.values()),3202)
    equal(keyed(OUT/'NUMERIC_FEATURES_PRIVATE.jsonl'),features)
    equal(keyed(DHC/'NUMERIC_FEATURES_PRIVATE.jsonl'),features)
    equal(keyed(OUT/'FROZEN_COMPARATORS_PRIVATE.jsonl'),comparison)
    schema=load(OUT/'FEATURE_SCHEMA.json')
    base_params=dict(C=1.0,solver='lbfgs',class_weight=None,max_iter=5000,penalty='l2',tol=1e-4,fit_intercept=True,random_state=None)
    cal_params=dict(C=1e6,solver='lbfgs',class_weight=None,max_iter=2000,penalty='l2',tol=1e-4,fit_intercept=True,random_state=None)
    equal(schema['base'],base_params); equal(schema['platt'],cal_params)
    for v in VAR:
        names=FIELDS if v=='ROA-FULL' else FIELDS[:-1]
        equal(schema['variants'][v],dict(numeric=names,dimension=len(names)*2+3,feature_order=names+['missing.'+n for n in names]+['retriever.'+r for r in RET]))
    split_manifest=load(OUT/'SPLIT_MANIFEST.json')
    expected_contexts=[dict(stage='primary',seed=s,outer=o,inner=None,id=f'p_{s}_{o}_final') for s in SEEDS for o in range(5)]+[
        dict(stage='lodo',seed=20260922,heldout=h,inner=None,id=f'l_{h}_final') for h in DS]
    equal([r['context'] for r in split_manifest['contexts']],expected_contexts)
    dhc_splits={r['context']['id']:r for n in ('SPLIT_MANIFEST.json','LODO_SPLIT_MANIFEST.json') for r in load(DHC/n)['contexts'] if r['context']['inner'] is None}
    manifest=load(OUT/'MODEL_FIT_MANIFEST.json'); equal(len(manifest['jobs']),56); equal(len(manifest['calls']),112)
    events=list(lines(OUT/'MODEL_FIT_CALLS_PRIVATE.jsonl')); equal(len(events),224)
    equal([e for e in events if e['event']=='fit_completed'],manifest['calls'])
    jobmap={r['job_id']:r for r in manifest['jobs']}; equal(len(jobmap),56)
    callmap={(r['job_id'],r['stage']):r for r in manifest['calls']}; equal(len(callmap),112)
    dhc_jobs={r['context']['id']:r for r in load(DHC/'MODEL_FIT_MANIFEST.json')['jobs'] if r['context']['inner'] is None}
    expected_outer_preds=[]; expected_outer_actions=[]; expected_lodo_preds=[]; expected_lodo_actions=[]
    outer=load(OUT/'OUTER_RESULTS.json')['repetitions']; groupreport=load(OUT/'DATASET_RETRIEVER_BREAKDOWN.json')['repetitions']; lodo=load(OUT/'LODO_TRANSPORT.json')['transports']
    equal([r['seed'] for r in outer],SEEDS); equal([r['heldout'] for r in lodo],DS)
    pooled={s:{m:set() for m in METHODS} for s in SEEDS}; caps={s:0 for s in SEEDS}
    ranking=[]; full_matches=0; fitted_jobs=set(); primary_seal=load(OUT/'PRIMARY_OUTPUT_SEAL.json')
    for item,c in zip(split_manifest['contexts'],expected_contexts):
        parts=split(set(a),c); test=parts['test']; n=len(test); cap=round(n*.05); equal(item['cap'],cap)
        group_sets={p:{(k[0],k[2]) for k in kk} for p,kk in parts.items()}
        require(group_sets['fit'].isdisjoint(group_sets['cal']|group_sets['test']) and group_sets['cal'].isdisjoint(group_sets['test']),'INDEPENDENT_GROUP_LEAKAGE')
        eligible={p:sorted(k for k in kk if features[k]['eligible']) for p,kk in parts.items()}
        for p in parts:
            count=[sum((y[k]['a0_em']==0 and y[k]['a1_em']==1)==v for k in eligible[p]) for v in (0,1)]
            if p!='test': require(min(count)>0,'INDEPENDENT_CLASS')
            rr=dict(N_all=len(parts[p]),N_groups=len(group_sets[p]),N_eligible=len(eligible[p]),keys_sha256=kh(parts[p]),eligible_keys_sha256=kh(eligible[p]),recovery_target_counts=count)
            equal(item['partitions'][p],rr)
            prior=dhc_splits[c['id']]['partitions'][p]
            for field in ('N_all','N_groups','N_eligible','keys_sha256','eligible_keys_sha256'): equal(prior[field],rr[field])
            equal(prior['target_counts']['R'],count)
        predicted={}; selections={}
        for variant in VAR:
            jid=c['id']+'_'+variant; fitted_jobs.add(jid); job=jobmap[jid]; check(job['model']); check(job['predictions'])
            equal(job['context'],c); equal(job['variant'],variant)
            model=load(ROOT/job['model']['path']); equal(model['head'],'R'); equal(model['context'],c); equal(model['partitions'],item['partitions'])
            width=11 if variant=='ROA-FULL' else 10
            values={p:np.array([[np.nan if z is None else z for z in features[k]['numeric'][:width]] for k in kk],dtype=float) for p,kk in eligible.items()}
            med=np.nanmedian(values['fit'],axis=0); filled=np.where(np.isfinite(values['fit']),values['fit'],med)
            mean=np.mean(filled,axis=0); std=np.std(filled,axis=0); std[std==0]=1.0
            equal(model['preprocessing'],dict(median=med.tolist(),mean=mean.tolist(),std=std.tolist()))
            design={}
            for p,arr in values.items():
                missing=~np.isfinite(arr); imputed=np.where(missing,med,arr)
                hot=np.array([[float(k[1]==r) for r in RET] for k in eligible[p]])
                design[p]=np.hstack(((imputed-mean)/std,missing.astype(float),hot))
                equal(model['design_hashes'][p],ah(design[p])); equal(model['partition_key_hashes'][p],kh(eligible[p]))
            coef=np.asarray(model['coef']); equal(len(coef),width*2+3); equal(model['feature_dimension'],width*2+3)
            raw=design['test'].dot(coef)+model['intercept']; probability=expit(raw*model['platt_slope']+model['platt_intercept'])
            expected_predictions={k:dict(**keydict(k),logit_R=float(raw[i]),pR=float(probability[i])) for i,k in enumerate(eligible['test'])}
            equal(keyed(ROOT/job['predictions']['path']),expected_predictions)
            predicted[variant]={k:{n:r[n] for n in ('logit_R','pR')} for k,r in expected_predictions.items()}
            order=sorted(eligible['test'],key=lambda k:(-predicted[variant][k]['pR'],k)); selections[variant]=set(order[:cap])
            previous=-math.inf; reversals=0; ties=0
            order_asc=sorted(eligible['test'],key=lambda k:(predicted[variant][k]['pR'],k))
            for _,block in itertools.groupby(order_asc,key=lambda k:predicted[variant][k]['pR']):
                block=list(block); vv=[predicted[variant][k]['logit_R'] for k in block]
                reversals+=int(min(vv)<previous); previous=max(previous,max(vv)); ties+=int(len(block)>1)
            ranking.append(dict(job_id=jid,platt_slope=model['platt_slope'],strict_order_reversal_blocks=reversals,
                calibrated_tie_blocks=ties,ranking_unchanged_except_ties=reversals==0,calibrated_ranking_always_used=True))
            for stage,p in [('base','fit'),('platt','cal')]:
                call=callmap[(jid,stage)]; equal(call['parameters'],base_params if stage=='base' else cal_params); equal(call['head'],'R'); equal(call['variant'],variant)
                target=np.array([int(y[k]['a0_em']==0 and y[k]['a1_em']==1) for k in eligible[p]],dtype=np.uint8)
                xx=design[p] if stage=='base' else (design[p]@coef+model['intercept']).reshape(-1,1)
                equal(call['design_sha256'],ah(xx)); equal(call['target_sha256'],hashlib.sha256(target.tobytes()).hexdigest())
                equal(call['keys_sha256'],kh(eligible[p])); equal(call['sample_count'],len(target))
                equal(call['class_counts'],np.bincount(target,minlength=2).tolist()); equal(model['target_counts'][p],call['class_counts'])
                equal(call['warnings'],[]); equal(call['iterations'],model['base_iterations' if stage=='base' else 'platt_iterations'])
                require(load(OUT/'EXECUTABLE_CONFIG_FREEZE.json')['frozen_utc']<call['started_utc']<=call['completed_utc'],'FREEZE_BEFORE_FIT')
                matches=[e for e in events if e['job_id']==jid and e['stage']==stage]
                equal([e['event'] for e in matches],['fit_started','fit_completed'])
                equal({k:v for k,v in matches[1].items() if k not in ('event','completed_utc','iterations','warnings')},
                      {k:v for k,v in matches[0].items() if k!='event'})
                if c['stage']=='lodo': require(primary_seal['sealed_utc']<call['started_utc'],'LODO_AFTER_PRIMARY')
            if variant=='ROA-FULL':
                prior_model=load(ROOT/dhc_jobs[c['id']]['model']['path'])
                equal(model['preprocessing'],prior_model['preprocessing'])
                for name in ('coef','intercept','platt_slope','platt_intercept'): equal(model[name],prior_model['heads']['R'][name],'FULL_DHC/'+name)
                full_matches+=1
        for m in ('HGB','GbV','V2'):
            selections[m]=set(sorted(eligible['test'],key=lambda k:(-comparison[k][m],k))[:cap])
        require(all(len(v)==cap for v in selections.values()),'INDEPENDENT_K')
        seal=load(OUT/'partitions'/c['id']/'ACTION_SEAL.json'); equal(seal['context'],c); equal(seal['cap'],cap)
        equal(seal['eligible_keys_sha256'],kh(eligible['test'])); equal(seal['heldout_metrics_computed'],False)
        equal(seal['selected_keys'],{m:[list(k) for k in sorted(selections[m])] for m in METHODS})
        equal(seal['models'],[jobmap[c['id']+'_'+v] for v in VAR])
        result=load(OUT/'partitions'/c['id']/'RESULT.json'); check(result['action_seal'])
        require(max(callmap[(c['id']+'_'+v,'platt')]['completed_utc'] for v in VAR)<=seal['sealed_utc']<=result['metrics_computed_utc'],'PRE_METRIC_ACTION_SEAL')
        ss=summarize(test,selections,y,cap); gg=groups(test,selections,y)
        equal(result['summary'],ss); equal(result['context'],c)
        predrows=[dict(context_id=c['id'],**keydict(k),eligible=features[k]['eligible'],predictions={v:predicted[v].get(k) for v in VAR}) for k in sorted(test)]
        actrows=[dict(context_id=c['id'],**keydict(k),eligible=features[k]['eligible'],actions={m:k in selections[m] for m in METHODS}) for k in sorted(test)]
        if c['stage']=='primary':
            i=SEEDS.index(c['seed']); o=c['outer']; equal(outer[i]['folds'][o],result); equal(groupreport[i]['folds'][o],dict(outer=o,cells=gg))
            for m in METHODS: require(pooled[c['seed']][m].isdisjoint(selections[m]),'DUPLICATE_REPETITION_ACTION'); pooled[c['seed']][m]|=selections[m]
            caps[c['seed']]+=cap; expected_outer_preds+=predrows; expected_outer_actions+=actrows
        else:
            i=DS.index(c['heldout']); equal(lodo[i],dict(heldout=c['heldout'],seed=20260922,summary=ss,breakdown=gg,result=result))
            expected_lodo_preds+=predrows; expected_lodo_actions+=actrows
        print('VERIFIED '+c['id'],flush=True)
    equal(fitted_jobs,set(jobmap)); equal(full_matches,28)
    for i,s in enumerate(SEEDS):
        equal(outer[i]['pooled'],summarize(set(a),pooled[s],y,caps[s])); equal(groupreport[i]['pooled'],groups(set(a),pooled[s],y))
    for name,expected in [('OUTER_PREDICTIONS_PRIVATE.jsonl',expected_outer_preds),('OUTER_ACTIONS_PRIVATE.jsonl',expected_outer_actions),
                          ('LODO_PREDICTIONS_PRIVATE.jsonl',expected_lodo_preds),('LODO_ACTIONS_PRIVATE.jsonl',expected_lodo_actions)]:
        equal(list(lines(OUT/name)),expected,name)
        equal(len(expected),67500 if name.startswith('OUTER') else 13500)
        equal(len({(r['context_id'],key(r)) for r in expected}),len(expected))
    equal(load(OUT/'CALIBRATION_RANKING_CHECK.json'),dict(jobs=ranking,ranking_change_events=sum(not r['ranking_unchanged_except_ties'] for r in ranking),calibrated_ranking_used=True))
    dd=verdict(outer,lodo); equal(load(OUT/'DEVELOPMENT_DECISION.json'),dd)
    for r in primary_seal['files']: check(r)
    complete=load(OUT/'SCIENTIFIC_EXECUTION_COMPLETE.json'); equal(complete['scientific_fit_calls'],112)
    for name in ('Damage_fit_calls','MILP_calls','inner_selection_calls'): equal(complete[name],0)
    equal(complete['guard']['blocked'],[]); require(all(p.startswith(OUT.relative_to(ROOT).as_posix()+'/') for p in complete['guard']['write_paths']),'SCIENTIFIC_WRITE_SCOPE')
    parents(); frozen()
    write('INDEPENDENT_VALIDATION.json',dict(status='PASS',validated_utc=now(),checks=CHECKS,max_numeric_error=MAX_ERROR,tolerance=1e-10,
        main_executor_imported=False,independent_fit_calls=0,independent_MILP_calls=0,
        DHC_exact_FULL_recovery_models_matched=full_matches,split_contexts=28,model_bundles=56,scientific_fit_calls=112,
        all_features_splits_predictions_actions_metrics_LODO_decisions_reconstructed=True,
        all_parent_manifests_unchanged=True,pre_metric_action_seals_verified=True,primary_sealed_before_LODO=True,
        decision=dd['decision'],dependence_label=dd['dependence_label'],guard=guard_receipt(access)))
    print('INDEPENDENT PASS checks='+str(CHECKS)+' max_error='+str(MAX_ERROR),flush=True)

if __name__=='__main__':
    with threadpool_limits(1): main()
