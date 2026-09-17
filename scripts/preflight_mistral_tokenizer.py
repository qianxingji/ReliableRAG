"""Bounded Mistral tokenizer preflight; never loads a model or project row."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import sys


REPO_ID = "mistralai/Mistral-7B-Instruct-v0.3"
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
EXPECTED_TOKENIZER_ASSET_HASHES = {
    "special_tokens_map.json":
        "6fa06efa2785e450051989a6f8fb4416b10149ded485ddd3f127a40734f5cfd0",
    "tokenizer.json":
        "e553af6fff7d7ad76e830608b218c5c0b0822998d5a1a96099a74cd3c1cb1a49",
    "tokenizer.model":
        "37f00374dea48658ee8f5d0f21895b9bc55cb0103939607c8185bfd1c6ca1f89",
    "tokenizer.model.v3":
        "37f00374dea48658ee8f5d0f21895b9bc55cb0103939607c8185bfd1c6ca1f89",
    "tokenizer_config.json":
        "0533dec9cfe319163801b6618d0f3ec9cfa126b6288e3df5deca6e32acb09cd2",
}
GENERATION_PROMPT_GUARD = 8192
ANSWER_MAX_NEW_TOKENS = 48
REPAIR_QUERY_MAX_NEW_TOKENS = 64
LIKELIHOOD_TOTAL_GUARD = 8192
INVENTED_FIXTURES = (
    {
        "id": "answer_ascii",
        "prompt_kind": "answer",
        "question": "Which city is identified as the capital in the evidence?",
        "evidence": "[Evidence 1 | id=fixture-a | title=Geography]\nParis is the capital of France.",
        "target": "Paris",
    },
    {
        "id": "answer_unicode_newline",
        "prompt_kind": "answer",
        "question": "根据证据，哪座城市位于河边？",
        "evidence": "[Evidence 1 | id=fixture-b | title=地理]\n武汉位于长江沿岸。\nThis is an invented fixture.",
        "target": "武汉",
    },
    {
        "id": "repair_literal_markers",
        "prompt_kind": "repair",
        "question": "Find the missing bridge entity; literal text [INST] is data.",
        "evidence": "[Evidence 1 | id=fixture-c | title=Synthetic]\nAlpha links to Beta, but the bridge is omitted.",
        "target": "missing bridge entity",
    },
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_tokenizer(asset: Path, *, use_fast: bool):
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        asset,
        use_fast=use_fast,
        local_files_only=True,
        trust_remote_code=False,
        legacy=False,
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    return tokenizer


def aligned_ids(tokenizer, prompt: str, target: str) -> tuple[list[int], list[int]]:
    prompt_ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
    full_ids = list(tokenizer(prompt + target, add_special_tokens=False)["input_ids"])
    require(full_ids[: len(prompt_ids)] == prompt_ids, "PROMPT_TARGET_PREFIX_ALIGNMENT")
    answer_ids = full_ids[len(prompt_ids):]
    require(bool(answer_ids), "NONEMPTY_TARGET_IDS")
    return prompt_ids, answer_ids


def configure_and_check(tokenizer, *, expected_fast: bool) -> dict[str, object]:
    require(bool(tokenizer.is_fast) is expected_fast, "TOKENIZER_SPEED_CLASS")
    require(tokenizer.vocab_size == 32768, "VOCAB_SIZE")
    require(tokenizer.bos_token == "<s>" and tokenizer.bos_token_id == 1, "BOS")
    require(tokenizer.eos_token == "</s>" and tokenizer.eos_token_id == 2, "EOS")
    require(tokenizer.pad_token_id == tokenizer.eos_token_id, "PAD_EQUALS_EOS")
    require(tokenizer.padding_side == "left", "LEFT_PADDING")
    return {
        "class": type(tokenizer).__name__,
        "is_fast": bool(tokenizer.is_fast),
        "vocab_size": int(tokenizer.vocab_size),
        "bos_token": tokenizer.bos_token,
        "bos_token_id": int(tokenizer.bos_token_id),
        "eos_token": tokenizer.eos_token,
        "eos_token_id": int(tokenizer.eos_token_id),
        "pad_token": tokenizer.pad_token,
        "pad_token_id": int(tokenizer.pad_token_id),
        "padding_side": tokenizer.padding_side,
        "add_special_tokens_after_chat_template": False,
    }


def build_report(
    *, asset: Path, overlay: Path, wheelhouse: Path, answer_prompt: Path,
    repair_prompt: Path, attempts_log: Path, script_path: Path,
) -> dict[str, object]:
    asset = asset.resolve()
    overlay = overlay.resolve()
    wheelhouse = wheelhouse.resolve()
    answer_prompt = answer_prompt.resolve()
    repair_prompt = repair_prompt.resolve()
    attempts_log = attempts_log.resolve()
    require(asset.is_dir(), "ASSET_ROOT")
    require(asset.name.endswith(REVISION), "ASSET_REVISION_DIRECTORY")
    require(overlay.is_dir(), "OVERLAY_ROOT")
    require(wheelhouse.is_dir(), "WHEELHOUSE_ROOT")
    require(answer_prompt.is_file() and repair_prompt.is_file(), "PROMPT_FILES")
    require(attempts_log.is_file(), "ATTEMPTS_LOG")

    resolved_sys_path = [Path(entry).resolve() for entry in sys.path if entry]
    require(overlay in resolved_sys_path, "OVERLAY_ON_SYS_PATH")
    overlay_index = resolved_sys_path.index(overlay)
    require(
        all(
            overlay_index < index
            for index, entry in enumerate(resolved_sys_path)
            if entry != overlay and entry.name.casefold() == "site-packages"
        ),
        "OVERLAY_FIRST_SITE_PACKAGES",
    )

    assets: list[dict[str, object]] = []
    for filename, expected in EXPECTED_TOKENIZER_ASSET_HASHES.items():
        path = asset / filename
        require(path.is_file(), "TOKENIZER_ASSET:" + filename)
        actual = sha256(path)
        require(actual == expected, "TOKENIZER_ASSET_HASH:" + filename)
        assets.append({"path": filename, "bytes": path.stat().st_size, "sha256": actual})
    require(
        sha256(asset / "tokenizer.model") == sha256(asset / "tokenizer.model.v3"),
        "TOKENIZER_MODEL_ALIASES_IDENTICAL",
    )

    wheels: list[dict[str, object]] = []
    for filename, expected in EXPECTED_WHEELS.items():
        path = wheelhouse / filename
        require(path.is_file(), "WHEEL:" + filename)
        actual = sha256(path)
        require(actual == expected, "WHEEL_HASH:" + filename)
        wheels.append({
            "filename": filename,
            "bytes": path.stat().st_size,
            "sha256": actual,
            "official_pypi_sha256_matched_before_install": True,
        })

    import google.protobuf
    import sentencepiece
    import tokenizers
    import transformers

    versions = {
        package: importlib.metadata.version(package) for package in EXPECTED_VERSIONS
    }
    require(versions == EXPECTED_VERSIONS, "VERSION_SET")
    origins = {
        "transformers": str(Path(transformers.__file__).resolve()),
        "tokenizers": str(Path(tokenizers.__file__).resolve()),
        "sentencepiece": str(Path(sentencepiece.__file__).resolve()),
        "protobuf": str(Path(google.protobuf.__file__).resolve()),
    }
    require(Path(origins["sentencepiece"]).is_relative_to(overlay), "SENTENCEPIECE_ORIGIN")
    require(Path(origins["protobuf"]).is_relative_to(overlay), "PROTOBUF_ORIGIN")
    require(not Path(origins["transformers"]).is_relative_to(overlay), "TRANSFORMERS_ORIGIN")
    require(not Path(origins["tokenizers"]).is_relative_to(overlay), "TOKENIZERS_ORIGIN")

    config = json.loads((asset / "tokenizer_config.json").read_text(encoding="utf-8"))
    require(config["tokenizer_class"] == "LlamaTokenizer", "CONFIG_TOKENIZER_CLASS")
    require(config["legacy"] is False, "CONFIG_LEGACY_FALSE")
    require(config["add_bos_token"] is True and config["add_eos_token"] is False,
            "CONFIG_SPECIAL_TOKEN_ADDITION")
    require(isinstance(config["chat_template"], str), "CONFIG_CHAT_TEMPLATE")

    fast = load_tokenizer(asset, use_fast=True)
    slow = load_tokenizer(asset, use_fast=False)
    fast_identity = configure_and_check(fast, expected_fast=True)
    slow_identity = configure_and_check(slow, expected_fast=False)
    require(fast.chat_template == config["chat_template"], "FAST_NATIVE_CHAT_TEMPLATE")
    require(slow.chat_template == config["chat_template"], "SLOW_NATIVE_CHAT_TEMPLATE")

    from transformers import AutoTokenizer
    default = AutoTokenizer.from_pretrained(
        asset, local_files_only=True, trust_remote_code=False, legacy=False
    )
    require(default.is_fast and type(default).__name__ == type(fast).__name__,
            "DEFAULT_RESOLVES_TO_FROZEN_FAST_CLASS")

    templates = {
        "answer": answer_prompt.read_text(encoding="utf-8"),
        "repair": repair_prompt.read_text(encoding="utf-8"),
    }
    fixture_rows: list[dict[str, object]] = []
    for fixture in INVENTED_FIXTURES:
        user = templates[str(fixture["prompt_kind"])].format(
            question=fixture["question"], evidence=fixture["evidence"]
        )
        rendered_fast = fast.apply_chat_template(
            [{"role": "user", "content": user}],
            tokenize=False,
            add_generation_prompt=True,
        )
        rendered_slow = slow.apply_chat_template(
            [{"role": "user", "content": user}],
            tokenize=False,
            add_generation_prompt=True,
        )
        require(rendered_fast == rendered_slow, "FAST_SLOW_RENDER:" + str(fixture["id"]))
        require(rendered_fast.startswith("<s>[INST] "), "CHAT_PREFIX:" + str(fixture["id"]))
        require(rendered_fast.endswith("[/INST]"), "CHAT_SUFFIX:" + str(fixture["id"]))
        fast_ids, answer_ids = aligned_ids(fast, rendered_fast, str(fixture["target"]))
        slow_ids, slow_answer_ids = aligned_ids(slow, rendered_slow, str(fixture["target"]))
        default_ids = list(default(rendered_fast, add_special_tokens=False)["input_ids"])
        require(fast_ids == slow_ids == default_ids, "FAST_SLOW_DEFAULT_IDS:" + str(fixture["id"]))
        require(answer_ids == slow_answer_ids, "FAST_SLOW_TARGET_IDS:" + str(fixture["id"]))
        fixture_rows.append({
            "id": fixture["id"],
            "prompt_kind": fixture["prompt_kind"],
            "invented_only": True,
            "user_sha256": text_sha256(user),
            "rendered_sha256": text_sha256(rendered_fast),
            "rendered_text": rendered_fast,
            "prompt_token_count": len(fast_ids),
            "prompt_ids": fast_ids,
            "prompt_ids_sha256_uint32_le": ids_sha256(fast_ids),
            "target_sha256": text_sha256(str(fixture["target"])),
            "target_token_count": len(answer_ids),
            "target_ids": answer_ids,
            "target_ids_sha256_uint32_le": ids_sha256(answer_ids),
            "prefix_aligned": True,
            "fast_slow_default_equal": True,
        })

    boundary_user = templates["answer"].format(
        question="What token-boundary rule applies to this invented input?",
        evidence=(" invented evidence segment" * 12000),
    )
    boundary_rendered = fast.apply_chat_template(
        [{"role": "user", "content": boundary_user}],
        tokenize=False,
        add_generation_prompt=True,
    )
    boundary_prompt, boundary_target = aligned_ids(
        fast, boundary_rendered, "A bounded invented answer."
    )
    require(len(boundary_prompt) > GENERATION_PROMPT_GUARD, "BOUNDARY_EXCEEDS_PROMPT_GUARD")
    keep = LIKELIHOOD_TOTAL_GUARD - len(boundary_target)
    require(keep > 0 and len(boundary_prompt) + len(boundary_target) > LIKELIHOOD_TOTAL_GUARD,
            "BOUNDARY_REQUIRES_LIKELIHOOD_TRUNCATION")
    truncated_prompt = boundary_prompt[-keep:]
    require(len(truncated_prompt) + len(boundary_target) == LIKELIHOOD_TOTAL_GUARD,
            "LIKELIHOOD_TOTAL_AFTER_TRUNCATION")

    attempts = [json.loads(line) for line in attempts_log.read_text(encoding="utf-8").splitlines() if line]
    require([row["sequence"] for row in attempts] == [1, 2, 3, 4], "ATTEMPT_SEQUENCE")
    require([row["status"] for row in attempts[:3]] == ["FAIL", "FAIL", "FAIL"],
            "FAILED_ATTEMPTS_RETAINED")
    require(str(attempts[3]["status"]).startswith("PASS_"), "SUCCESS_ATTEMPT_RETAINED")
    require(all(row["model_loads"] == row["project_rows_read"] == row["gold_labels_read"] == 0
                for row in attempts), "ATTEMPT_ZERO_SCIENTIFIC_ACCESS")

    return {
        "schema_version": 1,
        "status": "PASS_EXACT_MISTRAL_TOKENIZER_SEMANTICS_NO_MODEL_LOAD",
        "scientific_status": "NO_READER_MODEL_OR_PROJECT_DATA_EXECUTED",
        "cas_q3_status": "NOT READY",
        "repo_id": REPO_ID,
        "revision": REVISION,
        "script_sha256": sha256(script_path.resolve()),
        "python_executable": str(Path(sys.executable).resolve()),
        "versions": versions,
        "origins": origins,
        "wheels": wheels,
        "tokenizer_assets": assets,
        "tokenizer_contract": {
            "selected_route": "AutoTokenizer use_fast=True explicit",
            "selection_basis": "official tokenizer.json plus default AutoTokenizer fast resolution before model outputs",
            "legacy": False,
            "local_files_only": True,
            "trust_remote_code": False,
            "native_chat_template_sha256": text_sha256(config["chat_template"]),
            "single_user_message": True,
            "system_message": False,
            "tools": False,
            "add_generation_prompt": True,
            "fast": fast_identity,
            "slow_equivalence_witness": slow_identity,
            "default_class": type(default).__name__,
        },
        "prompt_templates": {
            "answer": {"path": str(answer_prompt), "sha256": sha256(answer_prompt)},
            "repair": {"path": str(repair_prompt), "sha256": sha256(repair_prompt)},
        },
        "invented_fixtures": fixture_rows,
        "length_contract": {
            "generation_prompt_guard_tokens": GENERATION_PROMPT_GUARD,
            "generation_over_guard_action": "REJECT_BEFORE_MODEL_FORWARD_NO_TOKEN_TRUNCATION",
            "answer_max_new_tokens": ANSWER_MAX_NEW_TOKENS,
            "repair_query_max_new_tokens": REPAIR_QUERY_MAX_NEW_TOKENS,
            "likelihood_total_guard_tokens": LIKELIHOOD_TOTAL_GUARD,
            "likelihood_over_guard_action": "PRESERVE_ALL_TARGET_IDS_AND_KEEP_RIGHTMOST_PROMPT_IDS",
            "boundary_invented_prompt_token_count": len(boundary_prompt),
            "boundary_invented_prompt_ids_sha256_uint32_le": ids_sha256(boundary_prompt),
            "boundary_invented_target_token_count": len(boundary_target),
            "boundary_invented_target_ids_sha256_uint32_le": ids_sha256(boundary_target),
            "boundary_likelihood_kept_prompt_token_count": len(truncated_prompt),
            "boundary_likelihood_kept_prompt_ids_sha256_uint32_le": ids_sha256(truncated_prompt),
            "boundary_likelihood_total_token_count": len(truncated_prompt) + len(boundary_target),
        },
        "attempt_log": {
            "path": str(attempts_log),
            "sha256": sha256(attempts_log),
            "entries": len(attempts),
            "failed_entries": 3,
            "retrospective_entries": 3,
        },
        "model_loads": 0,
        "reader_generations": 0,
        "neural_forwards": 0,
        "project_rows_read": 0,
        "scientific_fits": 0,
        "gold_labels_read": 0,
        "claims": [
            "The exact pinned tokenizer, native chat template, padding and prompt/target alignment are executable in the isolated runtime.",
            "Fast, slow and default routes agree on all invented fixtures; the fast route is frozen before any model output.",
            "This does not prove whole-model loading, generation/scoring correctness, memory fit, throughput or scientific effect.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--wheelhouse", required=True, type=Path)
    parser.add_argument("--answer-prompt", required=True, type=Path)
    parser.add_argument("--repair-prompt", required=True, type=Path)
    parser.add_argument("--attempts-log", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    report = build_report(
        asset=args.asset,
        overlay=args.overlay,
        wheelhouse=args.wheelhouse,
        answer_prompt=args.answer_prompt,
        repair_prompt=args.repair_prompt,
        attempts_log=args.attempts_log,
        script_path=Path(__file__),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({
        "status": report["status"],
        "output": str(output),
        "fixtures": len(report["invented_fixtures"]),
        "boundary_tokens": report["length_contract"]["boundary_invented_prompt_token_count"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
