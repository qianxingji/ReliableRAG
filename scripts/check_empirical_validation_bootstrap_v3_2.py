"""Invented-only isolated-launch gate for the V3.2 bootstrap."""
import argparse,ast,hashlib,json,os,subprocess,sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument("--config",type=Path,required=True);p.add_argument("--config-sha256",required=True);a=p.parse_args()
 raw=a.config.read_bytes();assert hashlib.sha256(raw).hexdigest()==a.config_sha256;cfg=json.loads(raw);out=a.config.parent
 wrapper=Path(cfg["wrapper"]["path"]);entry=Path(cfg["entry_v3_1"]["path"]);binding=Path(cfg["binding_v3_1"]["path"])
 for item in cfg["inputs"]:
  path=Path(item["path"]);assert path.stat().st_size==item["size_bytes"] and hashlib.sha256(path.read_bytes()).hexdigest()==item["sha256"]
 tree=ast.parse(wrapper.read_text(encoding="utf-8"));imports=[]
 for node in tree.body:
  if isinstance(node,ast.Import):imports.extend(alias.name for alias in node.names)
  elif isinstance(node,ast.ImportFrom):imports.append(node.module)
 assert imports==["runpy","sys","pathlib"]
 assert "numpy" not in wrapper.read_text(encoding="utf-8") and "torch" not in wrapper.read_text(encoding="utf-8")
 env={k:v for k,v in os.environ.items() if not k.upper().startswith(("PYTHON","PIP_")) and k not in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")}
 env.update(PYTHONDONTWRITEBYTECODE="1",PYTHONNOUSERSITE="1",CUDA_VISIBLE_DEVICES="-1",HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1")
 prefix=[sys.executable,"-I","-B","-X","utf8",str(wrapper)]
 help_run=subprocess.run(prefix+["--help"],cwd=out,env=env,capture_output=True,text=True,encoding="utf-8")
 assert help_run.returncode==0 and help_run.stderr=="" and "--config-sha256" in help_run.stdout
 wrong=subprocess.run(prefix+["--config",str(a.config),"--config-sha256","0"*64],cwd=out,env=env,capture_output=True,text=True,encoding="utf-8")
 assert wrong.returncode==1 and "V3_BINDING_CONFIG_PIN" in wrong.stderr and "ModuleNotFoundError" not in wrong.stderr
 result={"status":"PASS_C3_VALIDATION_V3_2_BOOTSTRAP_INVENTED_ONLY","cas_q2_status":"NOT READY",
  "isolated_help_exit_code":help_run.returncode,"wrong_pin_exit_code":wrong.returncode,"wrong_pin_reached_v3_1_prepare":True,
  "bootstrap_imports":imports,"v3_1_entry_sha256":hashlib.sha256(entry.read_bytes()).hexdigest(),
  "v3_1_binding_sha256":hashlib.sha256(binding.read_bytes()).hexdigest(),"current_runtime_payloads_read":0,
  "configuration_parsed_in_wrong_pin_case":False,"fresh_gold_values":0,"neural_forwards":0,"scientific_fits":0}
 with (out/"FIXTURE_RESULT.json").open("x",encoding="utf-8",newline="\n") as f:json.dump(result,f,indent=2);f.write("\n")
 print(result["status"]);return 0
if __name__=="__main__":raise SystemExit(main())
