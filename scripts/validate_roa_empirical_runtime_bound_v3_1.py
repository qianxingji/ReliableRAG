"""V3.1 entry: NumPy target plus frozen auxiliary numerical runtimes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import site
import sys

from scripts.validate_roa_empirical_runtime_bound_v2 import profile_execution


def validate_evidence_pins(cfg, census, audit):
    assert cfg["census_task_manifest_sha256"] == census["source_task_manifest_sha256"], "V3_CENSUS_TASK_PIN"
    assert cfg["census_client_audit_manifest_sha256"] == census["client_audit_manifest_sha256"], "V3_CENSUS_AUDIT_PIN"
    assert audit["source_task_manifest_sha256"] == cfg["census_task_manifest_sha256"], "V3_AUDIT_SOURCE_PIN"
    assert cfg["environment_anomaly_audit_manifest_sha256"] == "bb4f4f04a8a96759edfade612bc32a12dbf6a7f6df17f194a4e24fc1fdd8a4db", "V3_1_ENVIRONMENT_AUDIT_PIN"


def prepare(config, pin):
    raw=config.read_bytes(); assert hashlib.sha256(raw).hexdigest()==pin, "V3_BINDING_CONFIG_PIN"
    cfg=json.loads(raw); root=Path(cfg["project_root"]).resolve(); repo=Path(cfg["engineering_root"]).resolve()
    assert root==Path("E:/paper/ReliableRAG").resolve() and repo==Path("E:/paper/ReliableRAG-cas-q2-p0-1").resolve()
    assert Path(sys.prefix).resolve()==root/".venv" and sys.flags.isolated and sys.dont_write_bytecode and site.ENABLE_USER_SITE is False
    assert os.environ["CUDA_VISIBLE_DEVICES"]=="-1"
    assert all(name not in os.environ for name in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS"))
    payloads={};controls={}
    for entry in cfg["controls"]:
        path=Path(entry["path"]);data=path.read_bytes()
        assert hashlib.sha256(data).hexdigest()==entry["sha256"] and len(data)==entry["size_bytes"]
        assert Path(entry["filename"]).name==entry["filename"] and entry["filename"] not in payloads
        payloads[entry["filename"]]=data;controls[entry["name"]]=entry
    assert Path(controls["entry_v3_1"]["path"]).resolve()==Path(__file__).resolve()
    assert json.loads(payloads[controls["v2_client_acceptance"]["filename"]])["status"]=="ACCEPTED_C3_VALIDATION_V2_FOR_ONE_FULL_RUN"
    census=json.loads(payloads[controls["census_results"]["filename"]])
    assert census["status"]=="ACCEPTED_COMPLETE_CENSUS_AND_BOUNDED_THREAD_DEPENDENCE" and census["default_12_thread_mode"]["exact_saved_rows"]==18180
    audit=json.loads(payloads[controls["census_client_audit"]["filename"]])
    assert audit["status"]=="ACCEPTED_COMPLETE_CENSUS_AND_BOUNDED_THREAD_DEPENDENCE"
    validate_evidence_pins(cfg,census,audit)
    if "v3_1_fixture_acceptance" in controls:
        fixture=json.loads(payloads[controls["v3_1_fixture_acceptance"]["filename"]])
        assert fixture["status"]=="ACCEPTED_C3_VALIDATION_V3_1_INVENTED_ONLY"
    sys.path.insert(0,str(repo))
    for expected in cfg["original_sources"].values():
        path=Path(expected["path"]);assert hashlib.sha256(path.read_bytes()).hexdigest()==expected["sha256"] and path.stat().st_size==expected["size_bytes"]
    frozen=dict(cfg,freeze_sha256=pin)
    frozen["embedded_controls"]=[{k:e[k] for k in ("filename","sha256","size_bytes")} for e in cfg["controls"]]
    frozen["embedded_controls"].append({"filename":"EXECUTION_FREEZE.json","sha256":pin,"size_bytes":len(raw)})
    payloads["EXECUTION_FREEZE.json"]=raw
    return root,repo,frozen,payloads


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--config",type=Path,required=True);parser.add_argument("--config-sha256",required=True)
    args=parser.parse_args();root,repo,frozen,payloads=prepare(args.config,args.config_sha256)
    from scripts.empirical_validation_binding_v3_1 import V31ValidationBindings,observe_native_default
    environment_start=observe_native_default(frozen,"start")
    events=[];profile_execution(events)
    from scripts import validate_roa_empirical_runtime as native
    assert Path(native.__file__).resolve()==Path(frozen["original_sources"]["current_validator"]["path"]).resolve()
    assert not (native.OUT/"INDEPENDENT_VALIDATION.json").exists()
    assert not (native.OUT/"SEAL.json").exists() and not (native.OUT/"SHA256_MANIFEST.json").exists() and not (native.OUT/"validation_execution").exists()
    for mode,folder in (("canonical",native.OUT),("replay",native.OUT/"replay")):
        assert hashlib.sha256((folder/"EXECUTION_MANIFEST.json").read_bytes()).hexdigest()==frozen["runtime_execution_manifests"][mode]
    binding=V31ValidationBindings(native,frozen,payloads,environment_start=environment_start,forbidden_events=events);binding.install()
    sys.argv=[str(Path(native.__file__)),"--project-root",str(root),"--preparation-manifest-sha256","7ecc9c22d3a400fcafdf51a4d5ce09adbbb7e30d5bef180d046ead70ba2bb258"]
    return native.main()


if __name__=="__main__":raise SystemExit(main())
