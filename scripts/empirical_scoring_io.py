"""Fixed scoring asset authentication and unchanged historical definition assembly."""
import ast
from dataclasses import dataclass
from pathlib import Path
import sys
import types

from scripts.empirical_pool_io import REPO, load, record, checked, require, verify_namespace
from scripts.empirical_retrieval_io import import_file

AUDIT = REPO / "outputs/cas_q2/empirical_scoring_input_audit_v1"
AUDIT_SHA = "1027d9e0c062c11bca3c6427d2c2db6403b42e25880d34777d5e32b6adae8ebc"
PANEL = REPO / "outputs/cas_q2/empirical_fixed_panel_v1"
FIELDS = {"ROA-FULL":list(range(11)), "ROA-NOGBV":list(range(10)), "HGB_GBV_R":[0,10], "HGB_ONLY_R":[0], "GBV_ONLY_R":[10]}


def inputs(root, *, neural=False):
    paths = verify_namespace(AUDIT, AUDIT_SHA)
    audit = load(AUDIT / "SCORING_INPUT_AUDIT.json")
    require(audit["status"] == "PASS_SCORING_INPUT_INVENTORY_ONLY", "Accepted scoring inventory")
    for entry in audit["checked_files"]:
        paths.append(checked(Path(entry["path"]), entry["sha256"], entry["size_bytes"]))
    if neural:
        from scripts.empirical_retrieval_io import AUDIT as ACQUISITION, AUDIT_SHA as ACQUISITION_SHA
        paths += verify_namespace(ACQUISITION, ACQUISITION_SHA)
        for entry in load(ACQUISITION / "ACQUISITION_INPUT_AUDIT.json")["checked_files"]:
            paths.append(checked(Path(entry["path"]), entry["sha256"], entry["size_bytes"]))
    learning = REPO / "src/arbitration/roa_original/learning.py"
    paths.append(checked(learning, "1ee2f9bacfe8f2cb9bed79aa450f679ded6d8d4d18c6b99fa105eaf5c6da664f"))
    original = root / "outputs/daa_v2_fresh_v1/prelabel_seal_v3"
    pre = load(original / "preflight/PREFLIGHT_INPUT_VERIFICATION.json")
    require(any(Path(e["path"]).resolve() == (original / "native_base.py").resolve() for e in audit["checked_files"]), "Native source inventoried")
    return audit, pre, sorted(set(paths))


def native_scoring(root):
    """Original assembler, original selected ASTs, no original main/fit/evaluation."""
    import numpy as np
    folder = root / "outputs/daa_v2_fresh_v1/prelabel_seal_v3"
    support = import_file("v3_support", folder / "v3_support.py")
    require(support.ROOT == root, "Original source root cannot be silently rebound")
    wrapper = import_file("empirical_authenticated_native_base", folder / "native_base.py")
    native = wrapper.assemble()
    v2 = types.ModuleType("src.arbitration.v2_ensemble")
    v2.__dict__.update(np=np, dataclass=dataclass)
    sys.modules[v2.__name__] = v2
    names = {"V2_SCORE_FEATURES","V2_LABELS","V2_LAMBDA_DAMAGE","V2_META_ALPHA","V2_ACTION_RATE",
             "V2_GROUP_FOLDS","V2_GROUP_SEED","V2EnsembleBundle","empirical_cdf","transition_utility","score_unseen","action_budget"}
    v2_nodes = wrapper.take(v2, "src/arbitration/v2_ensemble.py", names)
    eligibility = import_file("src.evaluation.answer_normalization", root / "src/evaluation/answer_normalization.py")
    schema = import_file("src.evaluation.fresh_schema", root / "src/evaluation/fresh_schema.py")
    return wrapper, native, v2, eligibility, schema, native.source_definitions + v2_nodes


def saved_models(root, native, v2):
    import joblib
    historical = root / "outputs/mars_full"
    method = load(historical / "method_freeze.json")
    names = tuple(v2.V2_SCORE_FEATURES[:7])
    models = {name: joblib.load(historical / "models" / (name + ".joblib")) for name in names}
    for name, model in models.items():
        if name != "ordinary_compact_logistic":
            require(tuple(model.feature_names) == tuple(method["model_manifest"][name]["feature_names"]), "Original feature order")
            require(type(model) is native.symmetric.SymmetricSelector, "Original selector class identity")
        else:
            require(type(model) is native.ordinary.OrdinarySelector, "Original ordinary class identity")
    bundle = joblib.load(root / "outputs/daa_v2_fresh_v1/prelabel_seal_v3/models/daa_v2.joblib")
    require(type(bundle) is v2.V2EnsembleBundle and len(bundle.models) == 5, "Original V2 saved ensemble")
    require(tuple(bundle.feature_names) == tuple(v2.V2_SCORE_FEATURES) and tuple(bundle.class_names) == tuple(v2.V2_LABELS), "V2 feature/class order")
    require(bundle.action_rate == .05 and bundle.meta_alpha == 2 and bundle.lambda_damage == 1, "V2 scientific constants")
    panel = load(PANEL / "MODELS.json")
    require(set(panel) == set(FIELDS), "Fixed five-model panel")
    for name, indices in FIELDS.items():
        require(panel[name]["numeric_indices"] == indices and panel[name]["feature_dimension"] == 2*len(indices)+3, "Fixed panel columns")
    return models, bundle, panel


def original_panel_math():
    """Only the byte-pinned original numeric/matrix functions, with no fitter import."""
    import numpy as np
    path = REPO / "src/arbitration/roa_original/learning.py"
    module = types.ModuleType("empirical_original_panel_math")
    module.__dict__.update(np=np, RETRIEVERS=("bm25","dense","hybrid"))
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"numeric","matrix"}]
    require({n.name for n in nodes} == {"numeric","matrix"}, "Original panel arithmetic functions")
    exec(compile(ast.Module(body=nodes,type_ignores=[]), str(path), "exec"), module.__dict__)
    return module


def panel_scores(panel, keys, numeric):
    import numpy as np
    from scipy.special import expit
    require(np.asarray(numeric).shape == (len(keys),11), "Eleven numeric scores")
    require(len(keys) == len(set(keys)) and all(k[1] in ("bm25","dense","hybrid") for k in keys), "Unique valid trace keys")
    math = original_panel_math(); answer = {}
    for name, indices in FIELDS.items():
        model = panel[name]; x = np.asarray(numeric, dtype=np.float64)[:,indices]
        transform = {k:np.asarray(v,dtype=np.float64) for k,v in model["preprocessing"].items()}
        require(set(transform) == {"median","mean","std"} and all(np.isfinite(v).all() for v in transform.values()), "Finite saved preprocessing")
        require(all(v.shape == (len(indices),) for v in transform.values()) and np.all(transform["std"] > 0), "Fixed preprocessing shape/scale")
        matrix = math.matrix(x, keys, **transform)
        raw = matrix @ np.asarray(model["coef"], dtype=np.float64) + model["intercept"]
        probabilities = expit(raw*model["platt_slope"]+model["platt_intercept"])
        require(np.isfinite(raw).all() and np.isfinite(probabilities).all(), "Finite panel outputs")
        answer[name] = dict(logit_R=raw, pR=probabilities)
    return answer
