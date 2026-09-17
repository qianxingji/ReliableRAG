"""Versioned source-only IO bridge; all native scientific definitions stay unchanged."""
from dataclasses import dataclass
import importlib.util
import sys
import types

from scripts.empirical_scoring_io import require


def source_only_import(name, path):
    """Caller authenticates the exact source before this loader executes its bytes."""
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    exec(compile(path.read_bytes(),str(path),"exec"),module.__dict__)
    return module


def native_scoring(root):
    import numpy as np
    folder=root/"outputs/daa_v2_fresh_v1/prelabel_seal_v3"
    support=source_only_import("v3_support",folder/"v3_support.py")
    require(support.ROOT==root,"Original source root cannot be silently rebound")
    # Reviewed IO binding only: no scientific function or original file is patched.
    support.import_file=source_only_import
    wrapper=source_only_import("empirical_authenticated_native_base",folder/"native_base.py")
    native=wrapper.assemble()
    v2=types.ModuleType("src.arbitration.v2_ensemble");v2.__dict__.update(np=np,dataclass=dataclass)
    sys.modules[v2.__name__]=v2
    names={"V2_SCORE_FEATURES","V2_LABELS","V2_LAMBDA_DAMAGE","V2_META_ALPHA","V2_ACTION_RATE",
        "V2_GROUP_FOLDS","V2_GROUP_SEED","V2EnsembleBundle","empirical_cdf","transition_utility","score_unseen","action_budget"}
    v2_nodes=wrapper.take(v2,"src/arbitration/v2_ensemble.py",names)
    eligibility=source_only_import("src.evaluation.answer_normalization",root/"src/evaluation/answer_normalization.py")
    schema=source_only_import("src.evaluation.fresh_schema",root/"src/evaluation/fresh_schema.py")
    return wrapper,native,v2,eligibility,schema,native.source_definitions+v2_nodes
