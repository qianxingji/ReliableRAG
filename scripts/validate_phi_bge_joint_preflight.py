"""Independently authenticate the sealed invented-only Phi/BGE preflight."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

from scripts.phi_reader_preflight_common import REPO, digest, record, require, seal, write_json


PRODUCER = REPO / "outputs/cas_q2/phi_bge_joint_gpu_preflight_v2"
PREDECESSOR = REPO / "outputs/cas_q2/phi_bge_joint_gpu_preflight_v1"
PHI_ONLY = REPO / "outputs/cas_q2/phi_reader_gpu_preflight_v1"
VALIDATION = REPO / "outputs/cas_q2/phi_bge_joint_gpu_preflight_validation_v1"
PRODUCER_MANIFEST = "ecf17a8af6c21fe2887700993bafe53c4aa8ae3c5419112737049db5c91ef2bf"
PRODUCER_COMMIT = "4f9eb32b73d73675e2dec3eedabd3d7728d8ee6a"
PREDECESSOR_MANIFEST = "692c75ac0a625bc3c5aec37562b0be5e73832d7b315df399b044a1b9600464c1"
PREDECESSOR_COMMIT = "f70bcd296a1dfeebeffcdc77ca531e3b7e9205c4"
PHI_REVISION = "2fe192450127e6a83f7441aef6e3ca586c338b77"
BGE_REVISION = "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"
PHI_SNAPSHOT = Path("data/models/huggingface/models--microsoft--Phi-3.5-mini-instruct/snapshots") / PHI_REVISION
WEIGHT_SUFFIXES = {".safetensors", ".bin", ".pt", ".pth", ".ckpt"}
QUESTION = "In the invented toy scene, what color is the paper cog?"


class Checks:
    def __init__(self): self.count = 0
    def require(self, condition, message):
        self.count += 1; require(condition, "independent joint validation: " + message)
    def exact(self, actual, expected, message): self.require(actual == expected, message)


def load(path: Path): return json.loads(path.read_text(encoding="utf-8"))


def text_sha(value: str) -> str: return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_namespace(root: Path, manifest_sha: str, checks: Checks) -> list[Path]:
    manifest_path = root / "SHA256_MANIFEST.json"
    checks.exact(digest(manifest_path), manifest_sha, root.name + " manifest digest")
    manifest = load(manifest_path)
    expected = {row["path"] for row in manifest["files"]} | {"SHA256_MANIFEST.json"}
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    checks.exact(actual, expected, root.name + " exact recursive coverage")
    paths = [manifest_path]
    for row in manifest["files"]:
        path = root / row["path"]
        checks.require(path.stat().st_size == row["size_bytes"] and digest(path) == row["sha256"],
                       root.name + " payload hash " + row["path"])
        paths.append(path)
    return paths


def evidence(long: bool) -> list[dict]:
    rows = []
    for index in range(5):
        body = (" ".join(f"invented_{index}_{token:05d}" for token in range(1500)) if long else
                "In this invented toy scene, the paper cog is silver and rests beside a blue cube.")
        rows.append({"rank": index + 1, "document_id": f"invented-doc-{index}",
                     "title": f"Invented {index}", "text": body})
    return rows


def render(rows: list[dict], budget: int = 16000) -> tuple[str, bool, list[bool]]:
    headers = [f"[Evidence {row['rank']} | id={row['document_id']} | title={row['title']}]\n" for row in rows]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = budget - sum(len(a) + len(b) for a, b in zip(separators, headers, strict=True))
    require(remaining >= 0, "independent joint validation: evidence headers")
    chunks, flags = [], []
    for separator, header, row in zip(separators, headers, rows, strict=True):
        body = row["text"].strip(); included = body[:remaining]; remaining -= len(included)
        chunks.append(separator + header + included); flags.append(len(included) < len(body))
    value = "".join(chunks)
    require(len(value) <= budget and all(row["document_id"] in value for row in rows),
            "independent joint validation: evidence identity")
    return value, any(flags), flags


def parse_query(raw: str) -> tuple[str, bool]:
    found = [value.strip() for value in re.findall(r"(?im)^\s*search\s+query\s*:\s*(.*?)\s*$", raw) if value.strip()]
    if found: return found[0], False
    fallback = next((line.strip() for line in reversed(raw.splitlines()) if line.strip()), QUESTION)
    return fallback or QUESTION, True


def parse_answer(raw: str) -> str:
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    if not lines: return ""
    answer = re.sub(r"^(?:final\s+)?answer\s*:\s*", "", lines[0], flags=re.I)
    return re.sub(r"^the answer is\s+", "", answer, flags=re.I).strip()


def install_boundary(allowed: set[Path], snapshot: Path, output: Path) -> dict:
    allowed = {path.resolve() for path in allowed}; snapshot = snapshot.resolve(); output = output.resolve()
    environment = (Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve())
    receipt = {"weight_reads_denied": 0, "outside_reads_denied": 0, "outside_writes_denied": 0,
               "environment_reads": set(), "denied": []}
    def deny(kind: str, path: Path):
        receipt[kind] += 1; receipt["denied"].append(f"{kind}:{path}")
        raise RuntimeError("independent joint validator boundary")
    def hook(event, args):
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request", "subprocess.Popen", "os.system"}:
            raise RuntimeError("independent joint validator network/process boundary")
        if event != "open" or isinstance(args[0], int): return
        path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output): deny("outside_writes_denied", path)
            return
        if path.suffix.lower() in WEIGHT_SUFFIXES: deny("weight_reads_denied", path)
        if any(path.is_relative_to(root) for root in environment): receipt["environment_reads"].add(str(path)); return
        if path not in allowed and not path.is_relative_to(snapshot) and not path.is_relative_to(output):
            deny("outside_reads_denied", path)
    sys.addaudithook(hook); return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args(); original = args.project_root.resolve(); checks = Checks()
    require(not VALIDATION.exists(), "single-use joint validation namespace")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "commit joint validator first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    producer_paths = verify_namespace(PRODUCER, PRODUCER_MANIFEST, checks)
    predecessor_paths = verify_namespace(PREDECESSOR, PREDECESSOR_MANIFEST, checks)
    produced, failed = load(PRODUCER / "BUILD_RECEIPT.json"), load(PREDECESSOR / "BUILD_RECEIPT.json")
    checks.exact((produced["status"], produced["source_commit"]),
                 ("PASS_PHI_BGE_JOINT_GPU_INVENTED_ONLY", PRODUCER_COMMIT), "producer status/source")
    checks.exact((failed["status"], failed["source_commit"], failed.get("diagnostic")),
                 ("FAIL", PREDECESSOR_COMMIT, "exact joint token admissions"), "preserved predecessor failure")
    for receipt in (produced, failed):
        checks.exact([receipt[key] for key in ("benchmark_rows_read", "generation_calls_on_benchmark", "gold_reads",
                     "existing_answer_strings_read", "scientific_fit_calls")], [0, 0, 0, 0, 0], "zero forbidden counters")
        checks.exact(receipt["execution_boundary"]["denied"], [], "producer boundary denial list")
    checks.exact([produced[key] for key in ("model_loads", "phi_logical_generations", "phi_forward_calls", "bge_forward_calls")],
                 [2, 2, 49, 1], "V2 load/forward counts")
    checks.exact((produced["phi_revision"], produced["bge"]["revision"]), (PHI_REVISION, BGE_REVISION), "model revisions")
    checks.exact(produced["bge"]["embedding_shape"], [1, 768], "BGE embedding shape")
    checks.require(math.isfinite(produced["bge"]["embedding_norm"]) and produced["bge"]["embedding_norm"] > 0, "finite BGE norm")
    checks.exact(produced["admissions"], [{"input_tokens": 353, "position": 0, "stage": "repair_query"},
                                          {"input_tokens": 9472, "position": 0, "stage": "a1"}], "exact admissions")

    freeze = load(PRODUCER / "EXECUTABLE_FREEZE.json")
    phi_pins = load(REPO / "docs/cas_q2/P0_3_READER_AXIS_AVAILABILITY_RESULTS.json")["reader"]["weight_shards"]
    bge_pins = {Path(row["path"]).name: row for row in load(REPO / "docs/cas_q2/PRETRAINED_ASSET_LOCK.json")["files"] if row["model"] == "bge"}
    weight_records = 0
    for row in freeze["inputs"]:
        path = Path(row["path"])
        if path.suffix.lower() in WEIGHT_SUFFIXES:
            pin = phi_pins.get(path.name) if "Phi-3.5-mini-instruct" in str(path) else bge_pins.get(path.name)
            checks.require(pin is not None, "weight has prior accepted pin")
            checks.exact({"size_bytes": row["size_bytes"], "sha256": row["sha256"]},
                         {"size_bytes": pin["size_bytes"], "sha256": pin["sha256"]}, "weight record matches accepted pin")
            weight_records += 1
        else:
            checks.exact(record(path), row, "non-weight producer input unchanged")

    VALIDATION.mkdir(parents=True, exist_ok=False)
    from transformers import AutoTokenizer
    allowed = set(producer_paths + predecessor_paths)
    allowed.update(Path(row["path"]) for row in freeze["inputs"] if Path(row["path"]).suffix.lower() not in WEIGHT_SUFFIXES)
    allowed.update({REPO / "docs/cas_q2/P0_3_READER_AXIS_AVAILABILITY_RESULTS.json", REPO / "docs/cas_q2/PRETRAINED_ASSET_LOCK.json",
                    REPO / "scripts/validate_phi_bge_joint_preflight.py", REPO / "docs/cas_q2/PHI_BGE_JOINT_PREFLIGHT_VALIDATION_CONTRACT.md",
                    PHI_ONLY / "SHA256_MANIFEST.json", PHI_ONLY / "GENERATION_WITNESSES.json"})
    boundary = install_boundary(allowed, original / PHI_SNAPSHOT, VALIDATION)
    tokenizer = AutoTokenizer.from_pretrained(str(original / PHI_SNAPSHOT), local_files_only=True, trust_remote_code=False)
    templates = {"repair_query": (original / "prompts/repair_missing_v1.txt").read_text(encoding="utf-8"),
                 "a1": (original / "prompts/baseline_v1.txt").read_text(encoding="utf-8")}
    phi_observations = load(PHI_ONLY / "GENERATION_WITNESSES.json")["observations"]
    accepted = {"repair_query": next(row["capture"] for row in phi_observations if row["kind"] == "query"),
                "a1": next(row["capture"] for row in phi_observations if row["kind"] == "answer" and row["long_evidence"])}
    for stage, key, is_long in (("repair_query", "short_generation", False), ("a1", "long_generation", True)):
        rows = evidence(is_long); rendered, truncated, flags = render(rows)
        user = templates[stage].format(question=QUESTION, evidence=rendered)
        prompt = tokenizer.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True)
        ids = list(tokenizer(prompt, add_special_tokens=True)["input_ids"]); capture = produced[key]["capture"]
        checks.exact(capture, accepted[stage], stage + " exact accepted Phi-only capture")
        checks.exact(capture["prompt_sha256"], text_sha(prompt), stage + " prompt hash")
        checks.exact(capture["input_token_ids"], ids, stage + " prompt tokens")
        checks.exact(capture["attention_mask"], [1] * len(ids), stage + " attention mask")
        checks.exact(capture["input_tokens"], len(ids), stage + " input length")
        checks.exact(capture["render"], {"text": rendered, "context_truncated": truncated,
                     "context_budget_characters": 16000, "ordered_passed_document_ids": [row["document_id"] for row in rows],
                     "per_document_truncated": flags}, stage + " evidence render")
        decoded = tokenizer.batch_decode([capture["generated_token_ids"]], skip_special_tokens=True)[0].strip()
        checks.exact(capture["raw_text"], decoded, stage + " generated-token decode")
        checks.exact(capture["native_output_score_steps"], len(capture["generated_token_ids"]), stage + " score-step count")
        if stage == "repair_query":
            query, fallback = parse_query(decoded)
            checks.exact(produced[key]["result"], {"search_query": query, "parser_fallback": fallback}, "repair parser")
        else:
            checks.exact(produced[key]["result"], {"parsed_text": parse_answer(decoded)}, "answer parser")

    checks.require(0 < produced["peak_allocated_cuda_bytes"] < produced["nominal_cuda_total_bytes"], "allocated peak below nominal total")
    checks.require(produced["peak_reserved_cuda_bytes"] > produced["nominal_cuda_total_bytes"], "reserved anomaly preserved")
    checks.exact(boundary["denied"], [], "validator boundary denials")
    compact = {key: (len(value) if isinstance(value, set) else value) for key, value in boundary.items()}
    result = {"status": "PASS_INDEPENDENT_PHI_BGE_SAVED_WITNESS_PENDING_CAPACITY_AUDIT", "cas_q2_status": "NOT READY",
              "source_commit": commit, "producer_source_commit": PRODUCER_COMMIT, "producer_manifest_sha256": PRODUCER_MANIFEST,
              "predecessor_source_commit": PREDECESSOR_COMMIT, "predecessor_manifest_sha256": PREDECESSOR_MANIFEST,
              "checks": checks.count, "weight_records_compared_without_weight_reads": weight_records,
              "tokenizer_only": True, "model_loads": 0, "model_forward_calls": 0, "generation_calls": 0,
              "benchmark_rows_read": 0, "gold_reads": 0, "existing_answer_strings_read": 0, "scientific_fit_calls": 0,
              "memory": {"peak_allocated_cuda_bytes": produced["peak_allocated_cuda_bytes"],
                         "peak_reserved_cuda_bytes": produced["peak_reserved_cuda_bytes"],
                         "nominal_cuda_total_bytes": produced["nominal_cuda_total_bytes"],
                         "allocated_fraction": produced["peak_allocated_cuda_bytes"] / produced["nominal_cuda_total_bytes"],
                         "reserved_exceeds_nominal": True}, "execution_boundary": compact,
              "scope": "Saved source/witness authentication only; capacity decision and benchmark authorization remain pending."}
    write_json(VALIDATION / "INDEPENDENT_VALIDATION.json", result); seal(VALIDATION)
    print(result["status"], checks.count, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
