"""Only the two frozen ROA variants, DHC final splits, and mechanical decisions."""
import hashlib
import math
import statistics
from controls import require, kh

NUMERIC = ['state_symmetric_hgb', 'state_symmetric_logistic', 'no_cross_state', 'no_B',
           'no_evidence_change', 'no_answer_form', 'ordinary_compact_logistic', 'B_rule',
           'higher_own_likelihood', 'likelihood_margin', 'gbv_margin']
VARIANTS = ['ROA-FULL', 'ROA-NOGBV']
RETRIEVERS = ['bm25', 'dense', 'hybrid']
SEEDS = [20260917, 20260918, 20260919, 20260920, 20260921]
HELDOUT = ['musique', '2wikimultihopqa', 'hotpotqa']
LODO_SEED = 20260922
BASE = dict(C=1.0, solver='lbfgs', class_weight=None, max_iter=5000, penalty='l2', tol=1e-4, fit_intercept=True, random_state=None)
PLATT = dict(C=1e6, solver='lbfgs', class_weight=None, max_iter=2000, penalty='l2', tol=1e-4, fit_intercept=True, random_state=None)
METHODS = VARIANTS + ['HGB', 'GbV', 'V2']

def remainder(prefix, tokens, k):
    return int(hashlib.sha256('|'.join([prefix, *map(str, tokens), k[0], k[2]]).encode('utf-8')).hexdigest(), 16) % 5
def contexts():
    return [dict(stage='primary', seed=s, outer=o, inner=None, id=f'p_{s}_{o}_final') for s in SEEDS for o in range(5)] + [
        dict(stage='lodo', seed=LODO_SEED, heldout=h, inner=None, id=f'l_{h}_final') for h in HELDOUT]
def partition(keys, c):
    if c['stage'] == 'primary':
        test = {k for k in keys if remainder('v3-dhc-outer-v1', [c['seed']], k) == c['outer']}
        prefix, tokens = 'v3-dhc-outer-cal-v1', [c['seed'], c['outer']]
    else:
        test = {k for k in keys if k[0] == c['heldout']}
        prefix, tokens = 'v3-dhc-lodo-final-cal-v1', [LODO_SEED, c['heldout']]
    train = set(keys)-test
    cal = {k for k in train if remainder(prefix, tokens, k) == 0}
    return dict(fit=train-cal, cal=cal, test=test)
def target(y): return int(y['a0_em'] == 0 and y['a1_em'] == 1)
def receipt(parts, rows, ys):
    groups = {p: {(k[0], k[2]) for k in kk} for p, kk in parts.items()}
    require(groups['fit'].isdisjoint(groups['cal']|groups['test']) and groups['cal'].isdisjoint(groups['test']), 'GROUP_LEAKAGE')
    answer = {}
    for p, kk in parts.items():
        eligible = sorted(k for k in kk if rows[k]['eligible'])
        counts = [sum(target(ys[k]) == v for k in eligible) for v in (0, 1)]
        if p in ('fit', 'cal'): require(min(counts) > 0, 'MISSING_RECOVERY_CLASS:'+p)
        answer[p] = dict(N_all=len(kk), N_groups=len(groups[p]), N_eligible=len(eligible),
                         keys_sha256=kh(kk), eligible_keys_sha256=kh(eligible), recovery_target_counts=counts)
    return answer
def top(scores, cap):
    require(all(math.isfinite(v) for v in scores.values()), 'NONFINITE_RANK')
    return set(sorted(scores, key=lambda k: (-scores[k], k))[:cap])
def decision(reps, lodo):
    success = {v: {m: sum(r['pooled']['methods'][v]['net'] > r['pooled']['methods'][m]['net'] and
                          r['pooled']['methods'][v]['damage'] <= r['pooled']['methods'][m]['damage'] for r in reps)
                   for m in ('HGB', 'GbV')} for v in VARIANTS}
    med = {v: {metric: statistics.median(r['pooled']['comparisons'][v]['GbV'][metric] for r in reps)
               for metric in ('delta_em_pp', 'delta_f1_pp')} for v in VARIANTS}
    damage = {v: statistics.median(r['pooled']['methods'][v]['damage'] for r in reps) for v in VARIANTS}
    full_minus_no = statistics.median(r['pooled']['comparisons']['ROA-FULL']['ROA-NOGBV']['delta_em_pp'] for r in reps)
    damage_le = sum(r['pooled']['methods']['ROA-FULL']['damage'] <= r['pooled']['methods']['GbV']['damage'] for r in reps)
    transport = {v: {m: {r['heldout']: r['summary']['comparisons'][v][m]['delta_em_pp'] for r in lodo}
                     for m in ('HGB', 'GbV')} for v in VARIANTS}
    support = dict(condition_1=success['ROA-FULL']['HGB'] >= 4, condition_2=success['ROA-FULL']['GbV'] >= 4,
        condition_3=med['ROA-FULL']['delta_em_pp'] >= .40, condition_4=med['ROA-FULL']['delta_f1_pp'] >= .30,
        condition_5=damage_le >= 4, condition_6=min(transport['ROA-FULL']['GbV'].values()) >= 0,
        condition_7=min(transport['ROA-FULL']['HGB'].values()) >= -.10)
    reject = dict(success_vs_GbV_below_3=success['ROA-FULL']['GbV'] < 3, median_em_nonpositive=med['ROA-FULL']['delta_em_pp'] <= 0)
    independence = dict(condition_1=success['ROA-NOGBV']['GbV'] >= 4, condition_2=med['ROA-NOGBV']['delta_em_pp'] >= .30,
        condition_3=full_minus_no <= .10, condition_4=min(transport['ROA-NOGBV']['GbV'].values()) >= -.10,
        condition_5=damage['ROA-NOGBV'] <= damage['ROA-FULL']+2)
    status = 'ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE' if all(support.values()) else 'ROA_FULL_REJECTED' if any(reject.values()) else 'ROA_FULL_INCONCLUSIVE'
    supported = status == 'ROA_FULL_SUPPORTED_FOR_FINAL_CANDIDATE'
    return dict(decision=status, dependence_label=('BASELINE_INDEPENDENCE_SUPPORTED' if all(independence.values()) else 'GBV_AUGMENTED_ONLY') if supported else None,
        support_conditions=support, rejection_triggers=reject, independence_conditions=independence if supported else None,
        success_counts=success, median_minus_GbV=med, median_damage=damage, full_damage_le_GbV_repetitions=damage_le,
        median_FULL_minus_NOGBV_em_pp=full_minus_no, lodo_em_comparisons=transport,
        failed_support_conditions=[k for k,v in support.items() if not v],
        cohort_role='V3_DEVELOPMENT_ONLY', final_full_development_model_fitted=False, fresh_confirmatory_ID_selection=False)
