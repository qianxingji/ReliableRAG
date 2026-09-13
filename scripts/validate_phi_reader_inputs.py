"""Independent full reconstruction of the value-blind Phi input freeze."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.phi_reader_input_freeze_common import (
    DATASETS, MAXIMUM_GENERATION_INPUT_TOKENS, PHI_RELATIVE, PHI_REVISION,
    REPO, RETRIEVERS, canonical, digest, load, object_sha, record, require,
    require_generation_admission, seal, text_sha, write_json,
)


PRODUCER = REPO / "outputs/cas_q2/phi_reader_input_freeze_v2"
VALIDATION = REPO / "outputs/cas_q2/phi_reader_input_freeze_validation_v1"
PRODUCER_MANIFEST_SHA256 = "17cb0c29e4d4a5b98991bbebf1368bdff0ebece6221ca163c73327bcf4bcedd9"
PRODUCER_COMMIT = "baf84189d0cc101fee14e0af660570be29187da8"


def json_rows(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def verify_producer() -> list[Path]:
    require(digest(PRODUCER / "SHA256_MANIFEST.json") == PRODUCER_MANIFEST_SHA256, "producer manifest pin")
    manifest = load(PRODUCER / "SHA256_MANIFEST.json")
    expected = {row["path"] for row in manifest["files"]} | {"SHA256_MANIFEST.json"}
    actual = {path.relative_to(PRODUCER).as_posix() for path in PRODUCER.rglob("*") if path.is_file()}
    require(actual == expected, "producer exact namespace")
    paths = [PRODUCER / "SHA256_MANIFEST.json"]
    for row in manifest["files"]:
        path = PRODUCER / row["path"]
        require(path.stat().st_size == row["size_bytes"] and digest(path) == row["sha256"], "producer file pin")
        paths.append(path)
    return paths


def install_boundary(allowed: set[Path], snapshot: Path, output: Path, environment_roots: tuple[Path, ...]) -> dict:
    receipt = {"denied": [], "environment_reads": set(), "weight_reads_denied": 0,
        "outside_reads_denied": 0, "outside_writes_denied": 0}
    allowed = {path.resolve() for path in allowed}; snapshot = snapshot.resolve(); output = output.resolve()
    environment_roots = tuple(path.resolve() for path in environment_roots)

    def hook(event, args):
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "urllib.Request", "subprocess.Popen", "os.system"}:
            raise RuntimeError("independent Phi input validator network/process boundary")
        if event != "open" or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve(); mode, flags = args[1:3]
        writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if not path.is_relative_to(output):
                receipt["outside_writes_denied"] += 1; receipt["denied"].append(str(path)); raise RuntimeError("validator write outside output")
            return
        if path.suffix.lower() in {".safetensors", ".bin", ".pt", ".pth", ".ckpt"}:
            receipt["weight_reads_denied"] += 1; receipt["denied"].append(str(path)); raise RuntimeError("validator model weight read")
        if any(path.is_relative_to(root) for root in environment_roots):
            receipt["environment_reads"].add(str(path)); return
        if path not in allowed and not path.is_relative_to(snapshot) and not path.is_relative_to(output):
            receipt["outside_reads_denied"] += 1; receipt["denied"].append(str(path)); raise RuntimeError(f"validator non-allowlisted read: {path}")

    sys.addaudithook(hook); return receipt


def independent_render(evidence: list[dict]) -> tuple[str, bool, list[bool]]:
    require(len(evidence) == 5 and [row["rank"] for row in evidence] == [1, 2, 3, 4, 5], "validator five evidence rows")
    require(len({row["document_id"] for row in evidence}) == 5, "validator unique evidence")
    headers = ["[Evidence %d | id=%s | title=%s]\n" % (row["rank"], row["document_id"], row["title"]) for row in evidence]
    reserved = sum(len(header) for header in headers) + 8
    require(reserved <= 16000, "validator header budget")
    remaining = 16000 - reserved; chunks, flags = [], []
    for index, (header, row) in enumerate(zip(headers, evidence, strict=True)):
        body = str(row["text"]).strip(); included = body[:remaining]; remaining -= len(included)
        chunks.append(("" if index == 0 else "\n\n") + header + included); flags.append(len(included) < len(body))
    rendered = "".join(chunks)
    require(len(rendered) <= 16000 and all(row["document_id"] in rendered for row in evidence), "validator rendered identity")
    return rendered, any(flags), flags


def independent_prompt(tokenizer, template: str, question: str, evidence: list[dict]) -> tuple[list[int], dict]:
    rendered, truncated, flags = independent_render(evidence)
    user = template.format(question=question, evidence=rendered)
    prompt = tokenizer.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True)
    ids = list(tokenizer(prompt, add_special_tokens=True)["input_ids"])
    return ids, {"prompt_sha256": text_sha(prompt), "input_token_ids_sha256": object_sha(ids), "input_tokens": len(ids),
        "rendered_context_characters": len(rendered), "context_truncated": truncated, "per_document_truncated": flags}


def document(row: dict, rank: int) -> dict:
    return {"rank": rank, "document_id": row["id"], "title": row["title"],
        "text": row["title"] + "\n" + "".join(row["sentences"]), "content_hash": row["content_hash"]}


def assets(original: Path, cohort: str) -> dict:
    if cohort == "development":
        base = original / "outputs/daa_v2_fresh_v1/pool_freeze"
        pp = lambda d: base / "pools" / f"{d}_documents.jsonl"
        rp = lambda d: base / "runtime_projection" / f"{d}_selected_runtime.jsonl"
    else:
        base = REPO / "outputs/cas_q2/empirical_candidate_pool_v2"
        pp = lambda d: base / "pools" / f"{d}.jsonl"
        rp = lambda d: base / "runtime" / f"{d}.jsonl"
    return {dataset: {"documents": {row["id"]: row for row in json_rows(pp(dataset))},
        "questions": {row["id"]: row["question"] for row in json_rows(rp(dataset))}} for dataset in DATASETS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--project-root", type=Path, required=True); args = parser.parse_args()
    original = args.project_root.resolve(); require(not VALIDATION.exists(), "single-use Phi input validation namespace")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip(), "commit validator first")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    producer_paths = verify_producer(); receipt = load(PRODUCER / "BUILD_RECEIPT.json"); freeze = load(PRODUCER / "EXECUTABLE_FREEZE.json")
    require(receipt["status"] == "PASS_VALUE_BLIND_PHI_INPUT_FREEZE_PENDING_INDEPENDENT" and receipt["source_commit"] == PRODUCER_COMMIT,
        "producer status/commit")
    VALIDATION.mkdir(parents=True, exist_ok=False)
    from transformers import AutoTokenizer

    snapshot = original / PHI_RELATIVE
    allowed = set(producer_paths + [Path(row["path"]) for row in freeze["inputs"]] + [Path(row["path"]) for row in freeze["environment_inputs_actually_read"]])
    allowed.update({REPO / "scripts/validate_phi_reader_inputs.py", REPO / "scripts/phi_reader_input_freeze_common.py",
        REPO / "docs/cas_q2/PHI_READER_INPUT_FREEZE_CONTRACT.md", REPO / "docs/cas_q2/PHI_READER_INPUT_FREEZE_V2_AMENDMENT.md"})
    allowed = {path.resolve() for path in allowed}
    boundary = install_boundary(allowed, snapshot, VALIDATION, (Path(sys.prefix), Path(sys.base_prefix)))
    for row in freeze["inputs"] + freeze["environment_inputs_actually_read"]:
        require(record(Path(row["path"])) == row, "producer bound input unchanged")
    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True, trust_remote_code=False)
    require(hashlib.sha256(tokenizer.chat_template.encode("utf-8")).hexdigest() == "78d976a442bcde2f0be15aafbb8e3050e1104f86732266f68403251b89982a90", "pinned Phi chat template")
    answer_template = (original / "prompts/baseline_v1.txt").read_text(encoding="utf-8")
    repair_template = (original / "prompts/repair_missing_v1.txt").read_text(encoding="utf-8")
    dev_traces = list(json_rows(original / "outputs/daa_v2_fresh_v1/runtime_branch_freeze/trace_manifest.jsonl"))
    test_traces = list(json_rows(REPO / "outputs/cas_q2/empirical_runtime_preparation_v1/TRACE_MANIFEST_PRIVATE.jsonl"))
    roles = {(row["dataset"], row["sample_id"]): row["role"] for row in json_rows(REPO / "outputs/cas_q2/empirical_fixed_panel_v1/TRAINING_GROUPS_PRIVATE.jsonl")}
    dev_assets, test_assets = assets(original, "development"), assets(original, "test")
    produced = json_rows(PRODUCER / "INPUT_LENGTHS_PRIVATE.jsonl")
    aggregates = collections.defaultdict(lambda: {"rows": 0, "answer_max": 0, "repair_query_max": 0, "context_truncated": 0})
    maximum = {"input_tokens": -1}; checks = 0
    for cohort, traces, source in (("development", dev_traces, dev_assets), ("test", test_traces, test_assets)):
        for trace in traces:
            dataset, retriever, sid = trace["dataset"], trace["retriever"], trace["sample_id"]; item = source[dataset]
            evidence = [document(item["documents"][doc_id], rank) for rank, doc_id in enumerate(trace["original_top5_ids"], 1)]
            answer_ids, answer = independent_prompt(tokenizer, answer_template, item["questions"][sid], evidence)
            repair_ids, repair = independent_prompt(tokenizer, repair_template, item["questions"][sid], evidence)
            require_generation_admission(stage="a0", input_ids=[answer_ids], attention_mask=[[1] * len(answer_ids)])
            require_generation_admission(stage="repair_query", input_ids=[repair_ids], attention_mask=[[1] * len(repair_ids)])
            expected = {"cohort": cohort, "dataset": dataset, "retriever": retriever, "sample_id": sid,
                "position": trace["position"], "role": roles[(dataset, sid)] if cohort == "development" else "test",
                "original_top5_ids_sha256": object_sha(trace["original_top5_ids"]), "answer": answer, "repair_query": repair}
            require(next(produced) == expected, "independent scalar-ledger row")
            group = aggregates[(cohort, dataset, retriever)]; group["rows"] += 1
            group["answer_max"] = max(group["answer_max"], answer["input_tokens"])
            group["repair_query_max"] = max(group["repair_query_max"], repair["input_tokens"])
            group["context_truncated"] += int(answer["context_truncated"])
            for stage, metadata in (("a0", answer), ("repair_query", repair)):
                if metadata["input_tokens"] > maximum["input_tokens"]:
                    maximum = {"cohort": cohort, "dataset": dataset, "retriever": retriever, "sample_id": sid,
                        "position": trace["position"], "stage": stage, "input_tokens": metadata["input_tokens"],
                        "prompt_sha256": metadata["prompt_sha256"]}
            checks += 2
    try:
        next(produced); raise RuntimeError("producer ledger has trailing row")
    except StopIteration:
        pass
    aggregate_rows = [dict(cohort=k[0], dataset=k[1], retriever=k[2], **v) for k, v in sorted(aggregates.items())]
    require(checks == 63000 and receipt["aggregates"] == aggregate_rows and receipt["maximum"] == maximum, "complete aggregate reconstruction")
    for stage in ("a0", "repair_query", "a1"):
        require(require_generation_admission(stage=stage, input_ids=[[1] * MAXIMUM_GENERATION_INPUT_TOKENS],
            attention_mask=[[1] * MAXIMUM_GENERATION_INPUT_TOKENS]) == MAXIMUM_GENERATION_INPUT_TOKENS, "admission ceiling")
        try:
            require_generation_admission(stage=stage, input_ids=[[1] * (MAXIMUM_GENERATION_INPUT_TOKENS + 1)],
                attention_mask=[[1] * (MAXIMUM_GENERATION_INPUT_TOKENS + 1)])
            raise RuntimeError("overlength guard accepted")
        except RuntimeError as exc:
            require(str(exc) == "Phi generation input exceeds accepted witness", "exact overlength rejection")
    require(not boundary["denied"], "validator boundary denial")
    compact_boundary = {key: (len(value) if key == "environment_reads" else value) for key, value in boundary.items()}
    result = {"status": "PASS_INDEPENDENT_VALUE_BLIND_PHI_INPUT_FREEZE", "cas_q2_status": "NOT READY",
        "source_commit": commit, "producer_source_commit": PRODUCER_COMMIT, "producer_manifest_sha256": PRODUCER_MANIFEST_SHA256,
        "scalar_rows": 31500, "prompt_reconstructions": checks, "development_traces": len(dev_traces), "test_traces": len(test_traces),
        "maximum": maximum, "aggregates": aggregate_rows, "admission_boundary_checks": 6,
        "environment_files_actually_read": len(boundary["environment_reads"]), "execution_boundary": compact_boundary,
        "model_loads": 0, "model_forward_calls": 0, "generation_calls": 0, "scientific_fit_calls": 0,
        "gold_reads": 0, "existing_answer_strings_read": 0, "producer_imported": False,
        "scope": "Independent tokenizer-only full scalar reconstruction; dynamic a1 remains guarded before CUDA at runtime."}
    write_json(VALIDATION / "INDEPENDENT_VALIDATION.json", result); seal(VALIDATION)
    print(result["status"], checks, maximum, flush=True); return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
