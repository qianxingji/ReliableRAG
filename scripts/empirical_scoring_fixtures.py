"""Invented evidence and independently evaluated saved-estimator arithmetic."""
import math
import numpy as np
from scipy.special import expit, softmax


def invented_trace(index, retriever):
    e0 = [dict(rank=i+1,document_id="invented-"+str(i),content_hash=str(i)*64,score=float(5-i),
               title="Toy passage",text="The invented silver cog rests near a paper wheel.") for i in range(5)]
    e1 = [dict(r) for r in e0[:4]] + [dict(rank=5,document_id="invented-new",content_hash="a"*64,
        score=1.25,title="Toy repair",text="An invented blue cog rests near a wooden wheel.")]
    return dict(dataset="hotpotqa",retriever=retriever,sample_id="invented-scoring-"+str(index),
        question="What color is the invented cog?",a0="silver",a1="blue",E0=e0,E1=e1,
        split="invented_only",answer_semantic_agreement=.125+index*.125)


def invented_cells(index):
    return {name:dict(mean_log_probability=value-index*.125) for name,value in
            zip(("L00","L01","L10","L11"),(-2.,-3.,-4.,-1.5))}


def direct_base(models, pairs, ordinary_names):
    """Bypass native selector/matrix wrappers; HGB still uses its saved estimator."""
    answer = {}
    for name, selector in models.items():
        if name == "ordinary_compact_logistic":
            rows = [{**p["diagnostics"],**p["invariant_features"],**p["features"]} for p in pairs]
            x = np.array([[r[k] for k in ordinary_names] for r in rows],dtype=float)
            scaler, model = selector.model.steps[0][1], selector.model.steps[1][1]
            x = (x-scaler.mean_)/scaler.scale_
            values = expit(x @ model.coef_[0]+model.intercept_[0])
        else:
            x = np.array([[p["features"][k] for k in selector.feature_names] for p in pairs],dtype=float)
            model = selector.model
            if selector.family == "logistic":
                if selector.scaler is not None:
                    if selector.scaler.with_mean: x = x-selector.scaler.mean_
                    if selector.scaler.with_std: x = x/selector.scaler.scale_
                values = expit(x @ model.coef_[0]+model.intercept_[0])
            else:
                positive = model.predict_proba(x)[:,1]; negative = model.predict_proba(-x)[:,1]
                eps = np.finfo(np.float64).eps
                values = np.clip((positive+1.-negative)/2,eps,1.-eps)
        answer[name] = values
    answer.update(B_rule=np.array([p["diagnostics"]["B_repair"] for p in pairs]),
        higher_own_likelihood=np.array([p["diagnostics"]["L11"]-p["diagnostics"]["L00"] for p in pairs]),
        likelihood_margin=np.array([p["diagnostics"]["m1"] for p in pairs]))
    return answer


def direct_v2(bundle, x):
    """Independent linear/softmax/ECDF arithmetic; no native score_unseen call."""
    probabilities = np.zeros((len(x),len(bundle.class_names)))
    for pipeline in bundle.models:
        scaler, model = pipeline.steps[0][1], pipeline.steps[1][1]
        design = (x-scaler.mean_)/scaler.scale_
        local = softmax(design @ model.coef_.T+model.intercept_,axis=1)
        for j,label in enumerate(bundle.class_names): probabilities[:,j] += local[:,list(model.classes_).index(label)]
    probabilities /= len(bundle.models)
    utility = probabilities[:,list(bundle.class_names).index("recovery")]-bundle.lambda_damage*probabilities[:,list(bundle.class_names).index("damage")]
    # Explicit counts, not the native np.searchsorted implementation.
    h = np.array([np.count_nonzero(bundle.hgb_reference <= value)/len(bundle.hgb_reference) for value in x[:,0]])
    u = np.array([np.count_nonzero(bundle.utility_reference <= value)/len(bundle.utility_reference) for value in utility])
    return h+bundle.meta_alpha*u


def scalar_panel(model, retriever, numeric):
    indices = model["numeric_indices"]; prep = model["preprocessing"]
    missing = [numeric[i] is None or not math.isfinite(numeric[i]) for i in indices]
    values = [prep["median"][j] if missing[j] else numeric[i] for j,i in enumerate(indices)]
    design = [(v-prep["mean"][j])/prep["std"][j] for j,v in enumerate(values)]
    design += [float(x) for x in missing] + [float(retriever==r) for r in ("bm25","dense","hybrid")]
    logit = math.fsum(a*b for a,b in zip(design,model["coef"]))+model["intercept"]
    calibrated = logit*model["platt_slope"]+model["platt_intercept"]
    probability = 1/(1+math.exp(-calibrated)) if calibrated >= 0 else math.exp(calibrated)/(1+math.exp(calibrated))
    return logit,probability
