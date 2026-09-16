"""Frozen Mistral NF4 reader primitives for the prospective reader extension.

The module is deliberately independent of the failed Phi scientific artifacts.
It provides CPU-side prompt admission, exact local model loading, compact
generation/likelihood receipts, and an append-only operation journal.  Importing
it never loads a tokenizer, a model, project data, or CUDA.
"""

from __future__ import annotations

from dataclasses import dataclass
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
from typing import Any, Iterable, Sequence


REPO_ID = "mistralai/Mistral-7B-Instruct-v0.3"
REVISION = "c170c708c41dac9275d15a8fff4eca08d52bab71"
GENERATION_INPUT_GUARD = 8192
LIKELIHOOD_TOTAL_GUARD = 8192
ANSWER_MAX_NEW_TOKENS = 48
REPAIR_QUERY_MAX_NEW_TOKENS = 64
CONTEXT_BUDGET_CHARACTERS = 16_000
SEED = 20260917
OPERATIONS = frozenset({"a0", "repair_query", "repair_retrieval", "a1", "likelihood"})


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def object_sha256(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def ids_sha256(values: Sequence[int]) -> str:
    return object_sha256([int(value) for value in values])


def _shape(value: Any) -> tuple[int, int]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        require(len(shape) == 2, "GENERATION_INPUT_RANK")
        return int(shape[0]), int(shape[1])
    require(
        isinstance(value, Sequence) and len(value) == 1
        and isinstance(value[0], Sequence),
        "SINGLE_GENERATION_INPUT_ROW",
    )
    return 1, len(value[0])


def require_generation_admission(*, stage: str, input_ids: Any, attention_mask: Any) -> int:
    """Reject an unsafe generation request before tensors can reach CUDA."""

    require(stage in {"a0", "repair_query", "a1"}, "UNKNOWN_GENERATION_STAGE")
    row_count, width = _shape(input_ids)
    mask_rows, mask_width = _shape(attention_mask)
    require(row_count == mask_rows == 1 and width == mask_width, "GENERATION_SHAPE")
    require(0 < width <= GENERATION_INPUT_GUARD, "GENERATION_INPUT_EXCEEDS_GUARD")
    mask = attention_mask[0]
    if hasattr(mask, "tolist"):
        mask = mask.tolist()
    require(list(mask) == [1] * width, "GENERATION_ATTENTION_MASK")
    return width


def render_evidence(evidence: Sequence[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    """Render the unchanged five-document Phase-10 context contract."""

    require(len(evidence) == 5, "EXACT_FIVE_EVIDENCE_ROWS")
    require([int(row["rank"]) for row in evidence] == [1, 2, 3, 4, 5], "EVIDENCE_RANKS")
    ids = [str(row["document_id"]) for row in evidence]
    require(len(set(ids)) == 5, "UNIQUE_EVIDENCE_DOCUMENTS")
    headers = [
        f"[Evidence {row['rank']} | id={row['document_id']} | title={row['title']}]\n"
        for row in evidence
    ]
    separators = ["" if index == 0 else "\n\n" for index in range(5)]
    remaining = CONTEXT_BUDGET_CHARACTERS - sum(
        len(separator) + len(header)
        for separator, header in zip(separators, headers, strict=True)
    )
    require(remaining >= 0, "EVIDENCE_HEADERS_EXCEED_BUDGET")
    chunks: list[str] = []
    flags: list[bool] = []
    for separator, header, row in zip(separators, headers, evidence, strict=True):
        body = str(row["text"]).strip()
        included = body[:remaining]
        remaining -= len(included)
        chunks.append(separator + header + included)
        flags.append(len(included) < len(body))
    rendered = "".join(chunks)
    require(len(rendered) <= CONTEXT_BUDGET_CHARACTERS, "EVIDENCE_BUDGET")
    return rendered, {
        "context_budget_characters": CONTEXT_BUDGET_CHARACTERS,
        "rendered_context_characters": len(rendered),
        "context_truncated": any(flags),
        "per_document_truncated": flags,
        "ordered_passed_document_ids": ids,
    }


def render_prompt(
    tokenizer: Any,
    template: str,
    question: str,
    evidence: Sequence[dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    context, metadata = render_evidence(evidence)
    user = template.format(question=question, evidence=context)
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": user}],
        tokenize=False,
        add_generation_prompt=True,
    )
    require(isinstance(prompt, str) and prompt, "EMPTY_RENDERED_PROMPT")
    return prompt, metadata


def prepare_generation(
    tokenizer: Any,
    *,
    stage: str,
    template: str,
    question: str,
    evidence: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Tokenize and admit a generation request entirely on CPU."""

    prompt, render = render_prompt(tokenizer, template, question, evidence)
    encoded = tokenizer([prompt], return_tensors="pt", truncation=False)
    width = require_generation_admission(
        stage=stage,
        input_ids=encoded["input_ids"],
        attention_mask=encoded["attention_mask"],
    )
    ids = [int(value) for value in encoded["input_ids"][0].tolist()]
    mask = [int(value) for value in encoded["attention_mask"][0].tolist()]
    return {
        "stage": stage,
        "prompt": prompt,
        "prompt_sha256": text_sha256(prompt),
        "input_token_ids": ids,
        "input_token_ids_sha256": ids_sha256(ids),
        "attention_mask": mask,
        "input_tokens": width,
        "render": render,
        "encoded": encoded,
    }


def aligned_prompt_answer_ids(tokenizer: Any, prompt: str, answer: str) -> tuple[list[int], list[int]]:
    prompt_ids = [int(value) for value in tokenizer(prompt, add_special_tokens=False)["input_ids"]]
    full_ids = [int(value) for value in tokenizer(prompt + answer, add_special_tokens=False)["input_ids"]]
    require(full_ids[: len(prompt_ids)] == prompt_ids, "PROMPT_TARGET_PREFIX_ALIGNMENT")
    target_ids = full_ids[len(prompt_ids):]
    require(bool(target_ids), "EMPTY_LIKELIHOOD_TARGET")
    return prompt_ids, target_ids


def prepare_likelihood(
    tokenizer: Any,
    *,
    template: str,
    question: str,
    evidence: Sequence[dict[str, Any]],
    answer: str,
) -> dict[str, Any]:
    """Preserve the complete target and rightmost prompt under the 8192 guard."""

    prompt, render = render_prompt(tokenizer, template, question, evidence)
    prompt_ids, target_ids = aligned_prompt_answer_ids(tokenizer, prompt, answer)
    require(len(target_ids) < LIKELIHOOD_TOTAL_GUARD, "TARGET_EXCEEDS_LIKELIHOOD_GUARD")
    original_prompt_tokens = len(prompt_ids)
    keep = LIKELIHOOD_TOTAL_GUARD - len(target_ids)
    token_truncated = len(prompt_ids) > keep
    if token_truncated:
        prompt_ids = prompt_ids[-keep:]
    full_ids = prompt_ids + target_ids
    require(0 < len(prompt_ids) and len(full_ids) <= LIKELIHOOD_TOTAL_GUARD, "LIKELIHOOD_ADMISSION")
    return {
        "prompt_sha256": text_sha256(prompt),
        "prompt_token_ids": prompt_ids,
        "prompt_token_ids_sha256": ids_sha256(prompt_ids),
        "original_prompt_tokens": original_prompt_tokens,
        "prompt_tokens": len(prompt_ids),
        "target_token_ids": target_ids,
        "target_token_ids_sha256": ids_sha256(target_ids),
        "target_tokens": len(target_ids),
        "full_token_ids": full_ids,
        "total_tokens": len(full_ids),
        "token_truncated": token_truncated,
        "render": render,
    }


def parse_answer(raw: str) -> str:
    match = re.search(r"(?im)^\s*final\s+answer\s*:\s*(.*?)\s*$", raw)
    return (match.group(1) if match else raw).strip()


def parse_repair_query(raw: str, question: str) -> tuple[str, bool]:
    matches = [
        value.strip()
        for value in re.findall(r"(?im)^\s*search\s+query\s*:\s*(.*?)\s*$", raw)
        if value.strip()
    ]
    if matches:
        return matches[0], False
    fallback = next((line.strip() for line in reversed(raw.splitlines()) if line.strip()), question)
    return (fallback or question), True


class DurableOperationJournal:
    """Append-only per-call journal with exact-input interruption recovery.

    Completed operation keys are never executed again.  A final unmatched intent
    may be resumed only with the identical operation and input hash; every such
    recovery is written before the repeated deterministic call.
    """

    def __init__(self, path: str | Path, *, resume: bool) -> None:
        self.path = Path(path)
        require(resume or not self.path.exists(), "JOURNAL_EXISTS_WITHOUT_RESUME")
        require(not resume or self.path.is_file(), "RESUME_JOURNAL_MISSING")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rows: list[dict[str, Any]] = []
        if self.path.exists():
            with self.path.open("rb") as handle:
                for raw in handle:
                    require(raw.endswith(b"\n"), "PARTIAL_JOURNAL_LINE")
                    row = json.loads(raw)
                    require(raw == canonical(row) + b"\n", "NONCANONICAL_JOURNAL_ROW")
                    self.rows.append(row)
        self.completed: dict[str, dict[str, Any]] = {}
        self.pending: dict[str, Any] | None = None
        self._validate()
        self.stream = self.path.open("ab")

    def _validate(self) -> None:
        state: dict[str, dict[str, Any]] = {}
        active: str | None = None
        for sequence, row in enumerate(self.rows):
            require(row.get("sequence") == sequence, "JOURNAL_SEQUENCE")
            event = row.get("event")
            key = row.get("operation_key")
            require(isinstance(key, str) and key, "JOURNAL_OPERATION_KEY")
            if event == "intent":
                require(active is None and key not in state, "DUPLICATE_OR_OVERLAPPING_INTENT")
                require(row.get("operation") in OPERATIONS, "JOURNAL_OPERATION")
                require(re.fullmatch(r"[0-9a-f]{64}", str(row.get("input_sha256", ""))) is not None,
                        "JOURNAL_INPUT_HASH")
                state[key] = {"intent": row, "recoveries": 0}
                active = key
            elif event == "resume_pending":
                require(active == key and key in state and "result" not in state[key], "INVALID_PENDING_RESUME")
                require(row.get("input_sha256") == state[key]["intent"]["input_sha256"], "RESUME_INPUT_HASH")
                state[key]["recoveries"] += 1
            elif event == "result":
                require(active == key and key in state and "result" not in state[key], "INVALID_RESULT")
                require(re.fullmatch(r"[0-9a-f]{64}", str(row.get("result_sha256", ""))) is not None,
                        "JOURNAL_RESULT_HASH")
                state[key]["result"] = row
                active = None
            else:
                raise RuntimeError("UNKNOWN_JOURNAL_EVENT")
        self.completed = {key: value for key, value in state.items() if "result" in value}
        self.pending = None if active is None else state[active]["intent"]

    def _append(self, row: dict[str, Any]) -> None:
        payload = {"sequence": len(self.rows), **row}
        raw = canonical(payload) + b"\n"
        self.stream.write(raw)
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.rows.append(payload)

    def begin(self, *, operation_key: str, operation: str, input_sha256: str) -> bool:
        """Return True when the exact completed operation must be skipped."""

        require(operation in OPERATIONS, "UNKNOWN_OPERATION")
        require(re.fullmatch(r"[0-9a-f]{64}", input_sha256) is not None, "INVALID_INPUT_HASH")
        if operation_key in self.completed:
            intent = self.completed[operation_key]["intent"]
            require(intent["operation"] == operation and intent["input_sha256"] == input_sha256,
                    "COMPLETED_OPERATION_INPUT_MISMATCH")
            return True
        if self.pending is not None:
            require(self.pending["operation_key"] == operation_key, "PENDING_OPERATION_KEY_MISMATCH")
            require(self.pending["operation"] == operation and self.pending["input_sha256"] == input_sha256,
                    "PENDING_OPERATION_INPUT_MISMATCH")
            self._append({
                "event": "resume_pending", "operation_key": operation_key,
                "operation": operation, "input_sha256": input_sha256,
            })
            return False
        self._append({
            "event": "intent", "operation_key": operation_key,
            "operation": operation, "input_sha256": input_sha256,
        })
        self.pending = self.rows[-1]
        return False

    def complete(self, *, operation_key: str, result_sha256: str) -> None:
        require(self.pending is not None and self.pending["operation_key"] == operation_key,
                "RESULT_WITHOUT_MATCHING_INTENT")
        require(re.fullmatch(r"[0-9a-f]{64}", result_sha256) is not None, "INVALID_RESULT_HASH")
        self._append({
            "event": "result", "operation_key": operation_key,
            "operation": self.pending["operation"], "result_sha256": result_sha256,
        })
        intent = self.pending
        recoveries = sum(
            row["event"] == "resume_pending" and row["operation_key"] == operation_key
            for row in self.rows
        )
        self.completed[operation_key] = {
            "intent": intent, "result": self.rows[-1], "recoveries": recoveries,
        }
        self.pending = None

    def close(self) -> None:
        if not self.stream.closed:
            self.stream.close()


def frozen_witness_positions(rows: Iterable[dict[str, Any]]) -> list[int]:
    """Choose first and last development position in every dataset/retriever cell."""

    cells: dict[tuple[str, str], list[int]] = {}
    for row in rows:
        require(row.get("cohort") == "development", "WITNESS_REQUIRES_DEVELOPMENT_ROWS")
        key = (str(row["dataset"]), str(row["retriever"]))
        cells.setdefault(key, []).append(int(row["position"]))
    require(len(cells) == 9 and all(values for values in cells.values()), "NINE_NONEMPTY_WITNESS_CELLS")
    selected = sorted({value for values in cells.values() for value in (min(values), max(values))})
    require(len(selected) == 18, "EIGHTEEN_UNIQUE_WITNESS_POSITIONS")
    return selected


@dataclass(frozen=True)
class GenerationResult:
    receipt: dict[str, Any]
    first_step_logits: Any | None


@dataclass(frozen=True)
class LikelihoodResult:
    receipt: dict[str, Any]
    first_target_logits: Any | None


class MistralNF4Reader:
    """Exact local Mistral reader.  Model residency is explicit and exclusive."""

    def __init__(self, *, asset: str | Path, answer_prompt: str | Path, repair_prompt: str | Path) -> None:
        self.asset = Path(asset).resolve()
        self.answer_template = Path(answer_prompt).read_text(encoding="utf-8")
        self.repair_template = Path(repair_prompt).read_text(encoding="utf-8")
        self.tokenizer: Any | None = None
        self.model: Any | None = None
        self.torch: Any | None = None
        self.model_forward_calls = 0
        self._hook: Any | None = None

    def load(self) -> None:
        require(self.model is None and self.tokenizer is None, "READER_ALREADY_LOADED")
        required = {
            "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false",
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        }
        require(all(os.environ.get(key) == value for key, value in required.items()), "FROZEN_ENVIRONMENT")
        import numpy as np
        import torch
        import bitsandbytes as bnb
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        require(torch.cuda.is_available() and torch.cuda.device_count() == 1, "ONE_CUDA_DEVICE")
        require(torch.cuda.is_bf16_supported(), "BF16_REQUIRED")
        random.seed(SEED)
        np.random.seed(SEED)
        torch.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)
        torch.use_deterministic_algorithms(True)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        tokenizer = AutoTokenizer.from_pretrained(
            self.asset, use_fast=True, local_files_only=True,
            trust_remote_code=False, legacy=False,
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        require(tokenizer.is_fast and tokenizer.vocab_size == 32768, "TOKENIZER_IDENTITY")
        quantization = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.asset, local_files_only=True, trust_remote_code=False,
            use_safetensors=True, low_cpu_mem_usage=True, device_map={"": 0},
            quantization_config=quantization, torch_dtype=torch.bfloat16,
            attn_implementation="eager",
        )
        model.eval()
        model.generation_config.temperature = None
        model.generation_config.top_p = None
        model.generation_config.top_k = None
        require(type(model).__name__ == "MistralForCausalLM", "MODEL_CLASS")
        require(getattr(model.config, "_attn_implementation", None) == "eager", "EAGER_ATTENTION")
        require(all(value in (0, "cuda", "cuda:0") for value in model.hf_device_map.values()),
                "NO_CPU_OR_DISK_OFFLOAD")
        linear4 = [module for module in model.modules() if isinstance(module, bnb.nn.Linear4bit)]
        require(len(linear4) == 224, "LINEAR4BIT_COUNT")
        require(all(module.weight.quant_state is not None
                    and module.weight.quant_state.quant_type == "nf4"
                    and bool(module.weight.quant_state.nested) for module in linear4), "NF4_DOUBLE_QUANT")
        self.tokenizer, self.model, self.torch = tokenizer, model, torch

        def count_forward(_module: Any, _args: Any, _kwargs: Any) -> None:
            require(torch.is_inference_mode_enabled() and not torch.is_grad_enabled(), "INFERENCE_MODE")
            self.model_forward_calls += 1

        self._hook = model.register_forward_pre_hook(count_forward, with_kwargs=True)

    def close(self) -> None:
        if self._hook is not None:
            self._hook.remove()
        self._hook = None
        self.model = None
        self.tokenizer = None
        torch = self.torch
        self.torch = None
        gc.collect()
        if torch is not None and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _require_loaded(self) -> tuple[Any, Any, Any]:
        require(self.tokenizer is not None and self.model is not None and self.torch is not None,
                "READER_NOT_LOADED")
        return self.tokenizer, self.model, self.torch

    def generate(
        self,
        *,
        stage: str,
        question: str,
        evidence: Sequence[dict[str, Any]],
        capture_full_vocab_first_step: bool = False,
    ) -> GenerationResult:
        tokenizer, model, torch = self._require_loaded()
        template = self.repair_template if stage == "repair_query" else self.answer_template
        maximum = REPAIR_QUERY_MAX_NEW_TOKENS if stage == "repair_query" else ANSWER_MAX_NEW_TOKENS
        prepared = prepare_generation(
            tokenizer, stage=stage, template=template, question=question, evidence=evidence,
        )
        encoded = {name: value.to("cuda:0") for name, value in prepared.pop("encoded").items()}
        before = self.model_forward_calls
        with torch.inference_mode():
            generated = model.generate(
                **encoded, do_sample=False, max_new_tokens=maximum,
                pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id,
                use_cache=True, return_dict_in_generate=True, output_scores=True,
            )
        output = generated.sequences[0, prepared["input_tokens"]:]
        output_ids = [int(value) for value in output.detach().cpu().tolist()]
        require(len(generated.scores) == len(output_ids) <= maximum, "GENERATION_SCORE_COUNT")
        selected: list[float] = []
        for index, logits in enumerate(generated.scores):
            row = logits[0].float()
            require(bool(torch.isfinite(row).all().item()), "NONFINITE_GENERATION_LOGITS")
            token = output_ids[index]
            value = row[token] - torch.logsumexp(row, dim=0)
            selected.append(float(value.item()))
        require(all(math.isfinite(value) for value in selected), "NONFINITE_GENERATION_LOG_PROBABILITY")
        raw = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        parsed, fallback = (parse_repair_query(raw, question) if stage == "repair_query"
                            else (parse_answer(raw), None))
        receipt = {
            **{key: value for key, value in prepared.items() if key != "prompt"},
            "reader": "mistral_nf4", "revision": REVISION,
            "raw_text": raw, "raw_text_sha256": text_sha256(raw),
            "parsed_text": parsed, "parsed_text_sha256": text_sha256(parsed),
            "parser_fallback": fallback, "generated_token_ids": output_ids,
            "generated_token_ids_sha256": ids_sha256(output_ids),
            "output_tokens": len(output_ids),
            "chosen_log_probabilities": selected,
            "model_forward_calls": self.model_forward_calls - before,
        }
        witness = None
        if capture_full_vocab_first_step and generated.scores:
            witness = generated.scores[0][0].float().detach().cpu().numpy()
            require(tuple(witness.shape) == (32768,), "GENERATION_WITNESS_SHAPE")
        return GenerationResult(receipt=receipt, first_step_logits=witness)

    def likelihood(
        self,
        *,
        question: str,
        evidence: Sequence[dict[str, Any]],
        answer: str,
        capture_full_vocab_first_target: bool = False,
    ) -> LikelihoodResult:
        tokenizer, model, torch = self._require_loaded()
        prepared = prepare_likelihood(
            tokenizer, template=self.answer_template, question=question,
            evidence=evidence, answer=answer,
        )
        input_ids = torch.tensor([prepared["full_token_ids"]], device="cuda:0", dtype=torch.long)
        attention_mask = torch.ones_like(input_ids)
        position_ids = attention_mask.long().cumsum(-1) - 1
        before = self.model_forward_calls
        with torch.inference_mode():
            logits = model(
                input_ids=input_ids, attention_mask=attention_mask,
                position_ids=position_ids, use_cache=False,
            ).logits
        prompt_count = prepared["prompt_tokens"]
        target_count = prepared["target_tokens"]
        positions = torch.arange(
            prompt_count - 1, prompt_count + target_count - 1, device="cuda:0",
        )
        targets = input_ids[0, prompt_count:]
        selected_logits = logits[0, positions, :].float()
        require(tuple(selected_logits.shape) == (target_count, 32768), "LIKELIHOOD_LOGIT_SHAPE")
        require(bool(torch.isfinite(selected_logits).all().item()), "NONFINITE_LIKELIHOOD_LOGITS")
        chosen = selected_logits.gather(1, targets[:, None]).squeeze(1) - torch.logsumexp(
            selected_logits, dim=-1,
        )
        values = [float(value) for value in chosen.detach().cpu().tolist()]
        require(values and all(math.isfinite(value) for value in values), "LIKELIHOOD_VALUES")
        receipt = {
            **{key: value for key, value in prepared.items() if key != "full_token_ids"},
            "reader": "mistral_nf4", "revision": REVISION,
            "answer_sha256": text_sha256(answer),
            "chosen_log_probabilities": values,
            "mean_log_probability": float(sum(values) / len(values)),
            "minimum_log_probability": float(min(values)),
            "model_forward_calls": self.model_forward_calls - before,
        }
        witness = None
        if capture_full_vocab_first_target:
            witness = selected_logits[0].detach().cpu().numpy()
            require(tuple(witness.shape) == (32768,), "LIKELIHOOD_WITNESS_SHAPE")
        return LikelihoodResult(receipt=receipt, first_target_logits=witness)
