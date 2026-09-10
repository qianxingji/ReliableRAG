"""Single supplementary HGB-only control: original ROA recipe, selected columns.

Derived verbatim from authenticated ROA learning.py except the explicit control
width mapping and entry-point name. No optimization/fitting settings changed.
Initialize the original controls/design import bridge before importing this file.
"""
import hashlib
import warnings
import numpy as np
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from controls import require, kh, now
from design import BASE, PLATT, RETRIEVERS, target

def ah(a): return hashlib.sha256(np.asarray(a, dtype='<f8').tobytes()).hexdigest()
def numeric(rows, keys, width):
    return np.array([[np.nan if v is None else v for v in rows[k]['numeric'][:width]] for k in keys], dtype=np.float64)
def matrix(x, keys, median, mean, std):
    missing = ~np.isfinite(x)
    hot = np.array([[float(k[1] == r) for r in RETRIEVERS] for k in keys])
    return np.concatenate([(np.where(missing, median, x)-mean)/std, missing.astype(float), hot], axis=1)
def fit_control(rows, training_outcomes, parts, variant, job_id, event):
    """Caller passes only fit/cal labels; this function cannot inspect test outcomes."""
    kk = {p: sorted(k for k in keys if rows[k]['eligible']) for p, keys in parts.items()}
    require(set(training_outcomes) == parts['fit']|parts['cal'], 'TRAINING_LABEL_SCOPE')
    width = {'HGB_ONLY_R': 1}[variant]
    require(all(len(r['numeric']) == width for r in rows.values()), 'CONTROL_FEATURE_WIDTH')
    x = {p:numeric(rows, keys, width) for p,keys in kk.items()}
    require(np.isfinite(x['fit']).any(axis=0).all(), 'ALL_MISSING_FIT_COLUMN')
    median = np.nanmedian(x['fit'],axis=0)
    filled = np.where(np.isfinite(x['fit']),x['fit'],median)
    mean = filled.mean(axis=0); std = filled.std(axis=0,ddof=0); std = np.where(std==0,1,std)
    xx = {p:matrix(x[p], kk[p], median, mean, std) for p in kk}
    yy = {p:np.array([target(training_outcomes[k]) for k in kk[p]],dtype=int) for p in ('fit','cal')}
    require(all(set(y)=={0,1} for y in yy.values()), 'MISSING_CLASS')
    def run(stage, values, labels, parameters):
        entry = dict(job_id=job_id, variant=variant, head='R', stage=stage, started_utc=now(), parameters=parameters,
            sample_count=len(labels), class_counts=np.bincount(labels,minlength=2).tolist(), design_sha256=ah(values),
            target_sha256=hashlib.sha256(np.asarray(labels,dtype=np.uint8).tobytes()).hexdigest(),
            keys_sha256=kh(kk['fit' if stage=='base' else 'cal']))
        event(dict(event='fit_started',**entry))
        model = LogisticRegression(**parameters)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always'); model.fit(values,labels)
        require(not any(issubclass(w.category,ConvergenceWarning) for w in captured), 'FIT_NONCONVERGENCE')
        require(np.isfinite(model.coef_).all() and np.isfinite(model.intercept_).all(), 'NONFINITE_COEFFICIENTS')
        event(dict(event='fit_completed', **entry, completed_utc=now(), iterations=model.n_iter_.tolist(), warnings=[str(w.message) for w in captured]))
        return model
    base = run('base',xx['fit'],yy['fit'],BASE)
    calibration_logits = xx['cal']@base.coef_[0]+base.intercept_[0]
    platt = run('platt',calibration_logits.reshape(-1,1),yy['cal'],PLATT)
    raw = xx['test']@base.coef_[0]+base.intercept_[0]
    prob = expit(raw*platt.coef_[0,0]+platt.intercept_[0])
    model = dict(job_id=job_id,variant=variant,head='R', feature_dimension=2*width+3,
        preprocessing=dict(median=median.tolist(),mean=mean.tolist(),std=std.tolist()),
        coef=base.coef_[0].tolist(),intercept=float(base.intercept_[0]),
        platt_slope=float(platt.coef_[0,0]),platt_intercept=float(platt.intercept_[0]),
        base_iterations=base.n_iter_.tolist(),platt_iterations=platt.n_iter_.tolist(),
        partition_key_hashes={p:kh(kk[p]) for p in kk}, design_hashes={p:ah(xx[p]) for p in kk},
        target_counts={p:np.bincount(yy[p],minlength=2).tolist() for p in yy})
    predictions = {k:dict(logit_R=float(raw[i]),pR=float(prob[i])) for i,k in enumerate(kk['test'])}
    # Ties are exempt; compare raw-logit ranges across strictly ordered calibrated blocks.
    ordered = sorted(predictions,key=lambda k:(predictions[k]['pR'],k))
    previous_max = float('-inf'); reversals = 0; tied_blocks = 0
    import itertools
    for _, group in itertools.groupby(ordered,key=lambda k:predictions[k]['pR']):
        block = list(group); logits = [predictions[k]['logit_R'] for k in block]
        if len(block)>1: tied_blocks += 1
        if min(logits)<previous_max: reversals += 1
        previous_max=max(previous_max,max(logits))
    ranking = dict(platt_slope=model['platt_slope'], strict_order_reversal_blocks=reversals,
        calibrated_tie_blocks=tied_blocks, ranking_unchanged_except_ties=reversals==0,
        calibrated_ranking_always_used=True)
    return model,predictions,ranking
