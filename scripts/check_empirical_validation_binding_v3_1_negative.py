"""Invented negative cases for the V3.1 numerical-runtime boundary."""
import argparse,copy,hashlib,json,os
from pathlib import Path

def invoke(fn,*args):
 try:return {"status":"PASS","value":fn(*args)}
 except Exception as exc:return {"status":"REJECTED","reason":str(exc),"type":type(exc).__name__}

def runtime_pool(expected):
 return {"user_api":expected.get("user_api"),"internal_api":expected.get("internal_api"),
  "num_threads":expected.get("num_threads"),"version":expected.get("version"),
  "threading_layer":expected.get("threading_layer"),"architecture":expected.get("architecture"),
  "filepath":expected["path"]}

def rejected(cases,label,value,reason):
 cases[label]=value;assert value["status"]=="REJECTED" and value["reason"]==reason

def main():
 p=argparse.ArgumentParser();p.add_argument("--config",type=Path,required=True);p.add_argument("--config-sha256",required=True);a=p.parse_args()
 raw=a.config.read_bytes();assert hashlib.sha256(raw).hexdigest()==a.config_sha256;cfg=json.loads(raw);repo=Path(cfg["engineering_root"])
 import sys;sys.path.insert(0,str(repo))
 import numpy as np
 from threadpoolctl import threadpool_info
 import scripts.empirical_validation_binding_v3_1 as v31
 pools=threadpool_info();target=cfg["v3_blas"];aux=cfg["v3_auxiliary_pools"];cases={}
 assert invoke(v31.validate_native_default,pools,target,aux,np.__version__,os.environ,"start")["status"]=="PASS"
 os.environ["OMP_NUM_THREADS"]="1"
 rejected(cases,"override_present",invoke(v31.validate_native_default,pools,target,aux,np.__version__,os.environ,"start"),"V3_1_THREAD_OVERRIDES_MUST_BE_ABSENT")
 del os.environ["OMP_NUM_THREADS"]
 rejected(cases,"wrong_numpy",invoke(v31.validate_native_default,pools,target,aux,"0.0",os.environ,"start"),"V3_1_NUMPY_VERSION")
 rejected(cases,"missing_target",invoke(v31.validate_native_default,[],target,aux,np.__version__,os.environ,"start"),"V3_1_EXACTLY_ONE_TARGET_NUMPY_BLAS_POOL")
 rejected(cases,"duplicate_target",invoke(v31.validate_native_default,pools+pools,target,aux,np.__version__,os.environ,"start"),"V3_1_EXACTLY_ONE_TARGET_NUMPY_BLAS_POOL")
 for label,field,value in (("wrong_target_threads","num_threads",11),("wrong_target_version","version","0.0"),
  ("wrong_target_architecture","architecture","Invented"),("wrong_target_layer","threading_layer","openmp"),
  ("wrong_target_api","internal_api","mkl")):
  changed=copy.deepcopy(pools);changed[0][field]=value
  rejected(cases,label,invoke(v31.validate_native_default,changed,target,aux,np.__version__,os.environ,"start"),"V3_1_TARGET_NUMPY_BLAS_IDENTITY")
 changed_target=copy.deepcopy(target);changed_target["sha256"]="0"*64
 rejected(cases,"wrong_target_dll_bytes",invoke(v31.validate_native_default,pools,changed_target,aux,np.__version__,os.environ,"start"),"V3_1_TARGET_NUMPY_BLAS_IDENTITY")
 aux_pools=[runtime_pool(item) for item in aux];complete=pools+aux_pools
 assert invoke(v31.validate_native_default,complete,target,aux,np.__version__,os.environ,"end")["status"]=="PASS"
 rejected(cases,"auxiliary_at_start",invoke(v31.validate_native_default,complete,target,aux,np.__version__,os.environ,"start"),"V3_1_AUXILIARY_POOL_AT_START")
 rejected(cases,"missing_auxiliary_at_end",invoke(v31.validate_native_default,complete[:-1],target,aux,np.__version__,os.environ,"end"),"V3_1_AUXILIARY_POOL_SET")
 duplicate=complete+[copy.deepcopy(aux_pools[0])]
 rejected(cases,"duplicate_auxiliary_at_end",invoke(v31.validate_native_default,duplicate,target,aux,np.__version__,os.environ,"end"),"V3_1_AUXILIARY_POOL_SET")
 unknown=copy.deepcopy(aux_pools[0]);unknown["filepath"]=str(Path(aux[0]["path"]).with_name("invented.dll"))
 rejected(cases,"unknown_auxiliary_at_end",invoke(v31.validate_native_default,complete+[unknown],target,aux,np.__version__,os.environ,"end"),"V3_1_AUXILIARY_POOL_SET")
 changed=copy.deepcopy(complete);changed[1]["num_threads"]+=1
 rejected(cases,"wrong_auxiliary_identity",invoke(v31.validate_native_default,changed,target,aux,np.__version__,os.environ,"end"),"V3_1_AUXILIARY_POOL_IDENTITY")
 changed_aux=copy.deepcopy(aux);changed_aux[0]["sha256"]="0"*64
 rejected(cases,"wrong_auxiliary_dll_bytes",invoke(v31.validate_native_default,complete,target,changed_aux,np.__version__,os.environ,"end"),"V3_1_AUXILIARY_POOL_IDENTITY")
 assert cfg["environment_anomaly_audit_manifest_sha256"]=="bb4f4f04a8a96759edfade612bc32a12dbf6a7f6df17f194a4e24fc1fdd8a4db"
 result={"status":"PASS_C3_VALIDATION_V3_1_NEGATIVE_INVENTED_ONLY","cas_q2_status":"NOT READY","cases":cases,
  "negative_cases":sorted(cases),"valid_start_and_end_cases_passed":True,
  "changed_census_audit_and_environment_pin_cases_are_exercised_by_main_fixture":True,
  "current_runtime_payloads_read":0,"fresh_gold_values":0,"neural_forwards":0,"scientific_fits":0}
 out=a.config.parent/"NEGATIVE_RESULT.json"
 with out.open("x",encoding="utf-8",newline="\n") as f:json.dump(result,f,indent=2);f.write("\n")
 print(result["status"]);return 0
if __name__=="__main__":raise SystemExit(main())
