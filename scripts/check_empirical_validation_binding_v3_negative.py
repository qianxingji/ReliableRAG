"""Invented negative cases for the V3 native-default environment gate."""
import argparse,copy,hashlib,json,os
from pathlib import Path

def invoke(fn,*args):
 try:return {"status":"PASS","value":fn(*args)}
 except Exception as exc:return {"status":"REJECTED","reason":str(exc),"type":type(exc).__name__}

def main():
 p=argparse.ArgumentParser();p.add_argument("--config",type=Path,required=True);p.add_argument("--config-sha256",required=True);a=p.parse_args()
 raw=a.config.read_bytes();assert hashlib.sha256(raw).hexdigest()==a.config_sha256;cfg=json.loads(raw);repo=Path(cfg["engineering_root"])
 import sys;sys.path.insert(0,str(repo))
 import numpy as np
 from threadpoolctl import threadpool_info
 import scripts.empirical_validation_binding_v3 as v3
 pools=threadpool_info();expected=cfg["v3_blas"];cases={}
 os.environ["OMP_NUM_THREADS"]="1";cases["override_present"]=invoke(v3.validate_native_default,pools,expected,np.__version__,os.environ);del os.environ["OMP_NUM_THREADS"]
 assert cases["override_present"]["reason"]=="V3_THREAD_OVERRIDES_MUST_BE_ABSENT"
 mutations=(("wrong_threads","num_threads",11,"V3_EXACTLY_TWELVE_THREADS"),("wrong_version","version","0.0","V3_OPENBLAS_VERSION"),
  ("wrong_architecture","architecture","Invented","V3_OPENBLAS_ARCHITECTURE"),("wrong_layer","threading_layer","openmp","V3_OPENBLAS_THREADING_LAYER"),
  ("wrong_api","internal_api","mkl","V3_OPENBLAS_REQUIRED"),("wrong_path","filepath",str(Path(expected["path"]).with_name("invented.dll")),"V3_OPENBLAS_DLL_PATH"))
 for label,field,value,reason in mutations:
  changed=copy.deepcopy(pools);changed[0][field]=value;cases[label]=invoke(v3.validate_native_default,changed,expected,np.__version__,os.environ);assert cases[label]["reason"]==reason
 cases["multiple_pools"]=invoke(v3.validate_native_default,pools+pools,expected,np.__version__,os.environ);assert cases["multiple_pools"]["reason"]=="V3_EXACTLY_ONE_BLAS_POOL"
 cases["wrong_numpy"]=invoke(v3.validate_native_default,pools,expected,"0.0",os.environ);assert cases["wrong_numpy"]["reason"]=="V3_NUMPY_VERSION"
 changed=copy.deepcopy(expected);changed["sha256"]="0"*64;cases["wrong_dll_bytes"]=invoke(v3.validate_native_default,pools,changed,np.__version__,os.environ);assert cases["wrong_dll_bytes"]["reason"]=="V3_OPENBLAS_DLL_BYTES"
 assert cfg["census_task_manifest_sha256"]=="5fd10e9c1582bfd55e401255399faef635d854f61f5bdd02c15ac545863a2321"
 assert cfg["census_client_audit_manifest_sha256"]=="8c8d897312cedda7679be5e689a65aa84f62a6c42b8b9b8052246c80ffce6f33"
 result={"status":"PASS_C3_VALIDATION_V3_NEGATIVE_INVENTED_ONLY","cas_q2_status":"NOT READY","cases":cases,
  "negative_cases":sorted(cases),"changed_census_and_audit_pin_cases_are_exercised_by_main_fixture":True,
  "current_runtime_payloads_read":0,"fresh_gold_values":0,"neural_forwards":0,"scientific_fits":0}
 out=a.config.parent/"NEGATIVE_RESULT.json"
 with out.open("x",encoding="utf-8",newline="\n") as f:json.dump(result,f,indent=2);f.write("\n")
 print(result["status"]);return 0
if __name__=="__main__":raise SystemExit(main())
