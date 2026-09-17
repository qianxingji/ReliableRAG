"""Independent replay of the bounded Mistral tokenizer preflight report."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import sys


REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
EXPECTED_VERSIONS = {
    "transformers": "4.53.2",
    "tokenizers": "0.21.4",
    "sentencepiece": "0.2.1",
    "protobuf": "7.36.1",
}
EXPECTED_WHEELS = {
    "protobuf-7.36.1-cp310-abi3-win_amd64.whl":
        "51139351435d9b43d88a55eaa49fb6f737fbb478fb0cbf2cf694d1a04a9d3363",
    "sentencepiece-0.2.1-cp310-cp310-win_amd64.whl":
        "e52144670738b4b477fade6c2a9b6af71a8d0094514c9853ac9f6fc1fcfabae7",
}
EXPECTED_ASSETS = {
    "special_tokens_map.json": "6fa06efa2785e450051989a6f8fb4416b10149ded485ddd3f127a40734f5cfd0",
    "tokenizer.json": "e553af6fff7d7ad76e830608b218c5c0b0822998d5a1a96099a74cd3c1cb1a49",
    "tokenizer.model": "37f00374dea48658ee8f5d0f21895b9bc55cb0103939607c8185bfd1c6ca1f89",
    "tokenizer.model.v3": "37f00374dea48658ee8f5d0f21895b9bc55cb0103939607c8185bfd1c6ca1f89",
    "tokenizer_config.json": "0533dec9cfe319163801b6618d0f3ec9cfa126b6288e3df5deca6e32acb09cd2",
}
FIXTURES = (
    ("answer_ascii", "answer", "Which city is identified as the capital in the evidence?",
     "[Evidence 1 | id=fixture-a | title=Geography]\nParis is the capital of France.", "Paris"),
    ("answer_unicode_newline", "answer", "根据证据，哪座城市位于河边？",
     "[Evidence 1 | id=fixture-b | title=地理]\n武汉位于长江沿岸。\nThis is an invented fixture.", "武汉"),
    ("repair_literal_markers", "repair", "Find the missing bridge entity; literal text [INST] is data.",
     "[Evidence 1 | id=fixture-c | title=Synthetic]\nAlpha links to Beta, but the bridge is omitted.",
     "missing bridge entity"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def ids_sha256(values: list[int]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(struct.pack("<I", value))
    return digest.hexdigest()


def require(condition: bool, label: str, checks: list[str]) -> None:
    if not condition:
        raise RuntimeError(label)
    checks.append(label)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-report", required=True, type=Path)
    parser.add_argument("--producer-script", required=True, type=Path)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--wheelhouse", required=True, type=Path)
    parser.add_argument("--answer-prompt", required=True, type=Path)
    parser.add_argument("--repair-prompt", required=True, type=Path)
    parser.add_argument("--attempts-log", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report_path = args.producer_report.resolve()
    script_path = args.producer_script.resolve()
    asset = args.asset.resolve()
    overlay = args.overlay.resolve()
    wheelhouse = args.wheelhouse.resolve()
    answer_prompt = args.answer_prompt.resolve()
    repair_prompt = args.repair_prompt.resolve()
    attempts_log = args.attempts_log.resolve()
    output = args.output.resolve()
    checks: list[str] = []

    require(not output.exists(), "OUTPUT_ABSENT", checks)
    require(report_path.is_file(), "PRODUCER_REPORT_EXISTS", checks)
    require(script_path.is_file(), "PRODUCER_SCRIPT_EXISTS", checks)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    require(report["status"] == "PASS_EXACT_MISTRAL_TOKENIZER_SEMANTICS_NO_MODEL_LOAD",
            "PRODUCER_STATUS", checks)
    require(report["cas_q3_status"] == "NOT READY", "NOT_READY_PRESERVED", checks)
    require(report["revision"] == REVISION, "EXACT_REVISION", checks)
    require(sha256(script_path) == report["script_sha256"], "PRODUCER_SCRIPT_HASH", checks)
    for field in ("model_loads", "reader_generations", "neural_forwards",
                  "project_rows_read", "scientific_fits", "gold_labels_read"):
        require(report[field] == 0, "ZERO_" + field.upper(), checks)

    resolved_sys_path = [Path(entry).resolve() for entry in sys.path if entry]
    require(overlay in resolved_sys_path, "OVERLAY_ON_SYS_PATH", checks)
    overlay_index = resolved_sys_path.index(overlay)
    require(all(overlay_index < index for index, entry in enumerate(resolved_sys_path)
                if entry != overlay and entry.name.casefold() == "site-packages"),
            "OVERLAY_FIRST_SITE_PACKAGES", checks)

    versions = {name: importlib.metadata.version(name) for name in EXPECTED_VERSIONS}
    require(versions == EXPECTED_VERSIONS == report["versions"], "VERSION_SET", checks)
    import google.protobuf
    import sentencepiece
    import tokenizers
    import transformers
    origins = {
        "transformers": str(Path(transformers.__file__).resolve()),
        "tokenizers": str(Path(tokenizers.__file__).resolve()),
        "sentencepiece": str(Path(sentencepiece.__file__).resolve()),
        "protobuf": str(Path(google.protobuf.__file__).resolve()),
    }
    require(origins == report["origins"], "ORIGIN_SET", checks)
    require(Path(origins["sentencepiece"]).is_relative_to(overlay), "SENTENCEPIECE_OVERLAY", checks)
    require(Path(origins["protobuf"]).is_relative_to(overlay), "PROTOBUF_OVERLAY", checks)
    require(not Path(origins["transformers"]).is_relative_to(overlay), "TRANSFORMERS_BASE", checks)
    require(not Path(origins["tokenizers"]).is_relative_to(overlay), "TOKENIZERS_BASE", checks)

    reported_wheels = {row["filename"]: row for row in report["wheels"]}
    require(set(reported_wheels) == set(EXPECTED_WHEELS), "WHEEL_NAME_SET", checks)
    for filename, expected in EXPECTED_WHEELS.items():
        path = wheelhouse / filename
        require(path.is_file(), "WHEEL_EXISTS:" + filename, checks)
        actual = sha256(path)
        require(actual == expected, "WHEEL_HASH:" + filename, checks)
        require(reported_wheels[filename]["sha256"] == actual,
                "PRODUCER_WHEEL_HASH:" + filename, checks)
        require(reported_wheels[filename]["official_pypi_sha256_matched_before_install"] is True,
                "OFFICIAL_HASH_FLAG:" + filename, checks)

    reported_assets = {row["path"]: row for row in report["tokenizer_assets"]}
    require(set(reported_assets) == set(EXPECTED_ASSETS), "TOKENIZER_ASSET_NAME_SET", checks)
    for filename, expected in EXPECTED_ASSETS.items():
        path = asset / filename
        require(path.is_file(), "ASSET_EXISTS:" + filename, checks)
        actual = sha256(path)
        require(actual == expected, "ASSET_HASH:" + filename, checks)
        require(reported_assets[filename]["sha256"] == actual,
                "PRODUCER_ASSET_HASH:" + filename, checks)

    attempts = [json.loads(line) for line in attempts_log.read_text(encoding="utf-8").splitlines() if line]
    require(sha256(attempts_log) == report["attempt_log"]["sha256"], "ATTEMPT_LOG_HASH", checks)
    require(len(attempts) == report["attempt_log"]["entries"] == 4, "ATTEMPT_COUNT", checks)
    require([row["status"] for row in attempts[:3]] == ["FAIL", "FAIL", "FAIL"],
            "FAILURES_RETAINED", checks)
    require(all(row["model_loads"] == row["project_rows_read"] == row["gold_labels_read"] == 0
                for row in attempts), "ATTEMPT_ZERO_ACCESS", checks)

    config = json.loads((asset / "tokenizer_config.json").read_text(encoding="utf-8"))
    require(config["tokenizer_class"] == "LlamaTokenizer", "CONFIG_CLASS", checks)
    require(config["legacy"] is False, "CONFIG_LEGACY_FALSE", checks)
    require(text_sha256(config["chat_template"]) ==
            report["tokenizer_contract"]["native_chat_template_sha256"],
            "CHAT_TEMPLATE_HASH", checks)

    from transformers import AutoTokenizer
    fast = AutoTokenizer.from_pretrained(
        asset, use_fast=True, local_files_only=True, trust_remote_code=False, legacy=False
    )
    slow = AutoTokenizer.from_pretrained(
        asset, use_fast=False, local_files_only=True, trust_remote_code=False, legacy=False
    )
    for tokenizer in (fast, slow):
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        require(tokenizer.vocab_size == 32768, "VOCAB_32768:" + type(tokenizer).__name__, checks)
        require(tokenizer.bos_token_id == 1 and tokenizer.eos_token_id == 2,
                "BOS_EOS_IDS:" + type(tokenizer).__name__, checks)
        require(tokenizer.pad_token_id == 2 and tokenizer.padding_side == "left",
                "PAD_LEFT:" + type(tokenizer).__name__, checks)
    require(type(fast).__name__ == report["tokenizer_contract"]["fast"]["class"],
            "FAST_CLASS", checks)
    require(type(slow).__name__ == report["tokenizer_contract"]["slow_equivalence_witness"]["class"],
            "SLOW_CLASS", checks)

    templates = {
        "answer": answer_prompt.read_text(encoding="utf-8"),
        "repair": repair_prompt.read_text(encoding="utf-8"),
    }
    require(sha256(answer_prompt) == report["prompt_templates"]["answer"]["sha256"],
            "ANSWER_PROMPT_HASH", checks)
    require(sha256(repair_prompt) == report["prompt_templates"]["repair"]["sha256"],
            "REPAIR_PROMPT_HASH", checks)
    reported_fixtures = {row["id"]: row for row in report["invented_fixtures"]}
    require(set(reported_fixtures) == {row[0] for row in FIXTURES}, "FIXTURE_ID_SET", checks)
    for fixture_id, kind, question, evidence, target in FIXTURES:
        user = templates[kind].format(question=question, evidence=evidence)
        rendered = fast.apply_chat_template(
            [{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True
        )
        slow_rendered = slow.apply_chat_template(
            [{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True
        )
        require(rendered == slow_rendered, "RENDER_EQUAL:" + fixture_id, checks)
        prompt_ids = list(fast(rendered, add_special_tokens=False)["input_ids"])
        slow_ids = list(slow(rendered, add_special_tokens=False)["input_ids"])
        full_ids = list(fast(rendered + target, add_special_tokens=False)["input_ids"])
        require(prompt_ids == slow_ids, "PROMPT_IDS_EQUAL:" + fixture_id, checks)
        require(full_ids[:len(prompt_ids)] == prompt_ids, "PREFIX_ALIGNMENT:" + fixture_id, checks)
        target_ids = full_ids[len(prompt_ids):]
        row = reported_fixtures[fixture_id]
        require(rendered == row["rendered_text"], "RENDERED_TEXT:" + fixture_id, checks)
        require(text_sha256(user) == row["user_sha256"], "USER_HASH:" + fixture_id, checks)
        require(text_sha256(rendered) == row["rendered_sha256"],
                "RENDER_HASH:" + fixture_id, checks)
        require(prompt_ids == row["prompt_ids"], "PROMPT_IDS:" + fixture_id, checks)
        require(ids_sha256(prompt_ids) == row["prompt_ids_sha256_uint32_le"],
                "PROMPT_IDS_HASH:" + fixture_id, checks)
        require(target_ids == row["target_ids"], "TARGET_IDS:" + fixture_id, checks)
        require(ids_sha256(target_ids) == row["target_ids_sha256_uint32_le"],
                "TARGET_IDS_HASH:" + fixture_id, checks)

    boundary_user = templates["answer"].format(
        question="What token-boundary rule applies to this invented input?",
        evidence=(" invented evidence segment" * 12000),
    )
    boundary_rendered = fast.apply_chat_template(
        [{"role": "user", "content": boundary_user}], tokenize=False, add_generation_prompt=True
    )
    boundary_prompt = list(fast(boundary_rendered, add_special_tokens=False)["input_ids"])
    boundary_full = list(fast(boundary_rendered + "A bounded invented answer.",
                              add_special_tokens=False)["input_ids"])
    require(boundary_full[:len(boundary_prompt)] == boundary_prompt,
            "BOUNDARY_PREFIX_ALIGNMENT", checks)
    boundary_target = boundary_full[len(boundary_prompt):]
    contract = report["length_contract"]
    require(contract["generation_prompt_guard_tokens"] == 8192, "GENERATION_GUARD", checks)
    require(len(boundary_prompt) > 8192, "BOUNDARY_OVER_GUARD", checks)
    require(len(boundary_prompt) == contract["boundary_invented_prompt_token_count"],
            "BOUNDARY_PROMPT_COUNT", checks)
    require(ids_sha256(boundary_prompt) ==
            contract["boundary_invented_prompt_ids_sha256_uint32_le"],
            "BOUNDARY_PROMPT_HASH", checks)
    require(ids_sha256(boundary_target) ==
            contract["boundary_invented_target_ids_sha256_uint32_le"],
            "BOUNDARY_TARGET_HASH", checks)
    kept = boundary_prompt[-(8192 - len(boundary_target)):]
    require(len(kept) + len(boundary_target) == 8192, "LIKELIHOOD_TOTAL_GUARD", checks)
    require(ids_sha256(kept) == contract["boundary_likelihood_kept_prompt_ids_sha256_uint32_le"],
            "LIKELIHOOD_RIGHT_PROMPT_HASH", checks)

    validation = {
        "schema_version": 1,
        "status": "PASS_INDEPENDENT_MISTRAL_TOKENIZER_REPLAY",
        "cas_q3_status": "NOT READY",
        "producer_report_sha256": sha256(report_path),
        "producer_script_sha256": sha256(script_path),
        "validator_script_sha256": sha256(Path(__file__).resolve()),
        "checks": len(checks),
        "check_labels": checks,
        "versions": versions,
        "fixture_count": len(FIXTURES),
        "model_loads": 0,
        "reader_generations": 0,
        "neural_forwards": 0,
        "project_rows_read": 0,
        "scientific_fits": 0,
        "gold_labels_read": 0,
        "scope_limit": "Tokenizer and prompt-boundary replay only; no model load, generation, scoring, resource fit or scientific effect is established.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(validation, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": validation["status"], "checks": len(checks),
                      "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
