"""Full historical inputs reconstructed with original renderer and fixed tokenizer."""
import argparse
import dataclasses
import hashlib
import json
from pathlib import Path
import sys
import traceback
import types


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--config', type=Path, required=True); parser.add_argument('--config-sha256', required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8')); rec = next(e for e in config['controls'] if e['name'] == 'io')
    path = Path(rec['path']); assert hashlib.sha256(path.read_bytes()).hexdigest() == rec['sha256']
    io = types.ModuleType('tokenizer_io'); io.__file__ = str(path); sys.modules[io.__name__] = io; exec(compile(path.read_bytes(), str(path), 'exec'), io.__dict__)
    cfg, out, env, named, state, allowed, result = io.setup(args.config, args.config_sha256, 'producer')
    result['original_physical_root'] = cfg['roots']['original']['physical']
    mismatch = []
    try:
        native = io.namespace('original_tokenizer_render'); records = result['ast_nodes']
        io.take(native, named['contracts'], {'DATASETS', 'READERS', 'RETRIEVERS', 'FROZEN_THRESHOLDS', 'FrozenProtocol'}, records)
        io.take(native, named['adapters'], {'_is_finite_number', 'RankedDocument', 'EvidenceRender', 'render_phase10_evidence'}, records)
        io.take(native, named['parsing'], {'parse_final_answer'}, records)
        io.take(native, named['independent'], {'parsed_query'}, records)
        tokenizer, pre = io.tokenizer(named, result)
        templates = {k: named[k].read_text(encoding='utf-8') for k in ('answer_template', 'repair_template')}
        counts = {}; input_total = output_total = 0
        with (out / 'TOKENIZER_REPLAY_PRIVATE.jsonl').open('x', encoding='utf-8', newline='\n') as target:
            for mode, count in [('canonical', 13500), ('replay', 180)]:
                paths = [named[mode + '_' + role] for role in ('traces', 'branches', 'provenance', 'generations')]
                handles = [p.open(encoding='utf-8') for p in paths]
                try:
                    for i in range(count):
                        trace, branch, provenance = [json.loads(next(f)) for f in handles[:3]]
                        key = {k: trace[k] for k in ('dataset', 'retriever', 'sample_id')}
                        assert all(all(row[k] == v for k, v in key.items()) for row in (branch, provenance))
                        for stage in ('a0', 'repair_query', 'a1'):
                            old = json.loads(next(handles[3])); assert all(old[k] == v for k, v in key.items()) and old['stage'] == stage and old['position'] == trace['position']
                            side = 'e1' if stage == 'a1' else 'e0'; evidence = provenance[side]
                            assert [d['text'] for d in evidence] == branch['evidence1' if side == 'e1' else 'evidence0']
                            docs = [native.RankedDocument(rank=d['rank'], document_id=d['document_id'], content_hash=d['content_hash'], score=d['retrieval_score'], title=d['title'], text=d['text']) for d in evidence]
                            rendered = native.render_phase10_evidence(docs, 16000)
                            user = templates['repair_template' if stage == 'repair_query' else 'answer_template'].format(question=branch['question'], evidence=rendered.text)
                            prompt = tokenizer.apply_chat_template([{'role': 'user', 'content': user}], tokenize=False, add_generation_prompt=True)
                            tokens = tokenizer([prompt], return_tensors='pt', truncation=False)
                            generated_ids = old['generated_token_ids']
                            raw = tokenizer.batch_decode([generated_ids], skip_special_tokens=True)[0].strip()
                            parsed, fallback = native.parsed_query(raw, branch['question']) if stage == 'repair_query' else (native.parse_final_answer(raw), None)
                            output_count = next((j for j, token in enumerate(generated_ids) if token == tokenizer.pad_token_id), len(generated_ids))
                            rebuilt = dict(prompt_sha256=hashlib.sha256(prompt.encode('utf-8')).hexdigest(), input_token_ids=tokens['input_ids'][0].tolist(),
                                attention_mask=tokens['attention_mask'][0].tolist(), raw_text=raw, input_tokens=int(tokens['attention_mask'].sum().item()),
                                output_tokens=output_count, native_output_score_steps=len(generated_ids), render=json.loads(json.dumps(dataclasses.asdict(rendered))),
                                parsed_text=parsed, parser_fallback=fallback)
                            failures = [k for k, v in rebuilt.items() if v != old[k] or type(v) is not type(old[k])]
                            if failures: mismatch.append(dict(mode=mode, position=trace['position'], stage=stage, fields=failures))
                            row = dict(mode=mode, **key, position=trace['position'], stage=stage, rebuilt=rebuilt,
                                archived_observations=dict(generated_token_ids=generated_ids, qwen_forward_calls=old['qwen_forward_calls']),
                                bindings={name: io.jsha(value) for name, value in dict(trace=trace, branch=branch, provenance=provenance, generation=old).items()})
                            target.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n'); target.flush()
                            input_total += rebuilt['input_tokens']; output_total += rebuilt['output_tokens']
                        if (i + 1) % 1500 == 0: print('QWEN_TOKENIZER_REPLAY', mode, i + 1, count, flush=True)
                    assert all(f.readline() == '' for f in handles), 'EXTRA_HISTORICAL_ROWS'
                finally:
                    for f in handles: f.close()
                counts[mode] = dict(traces=count, generations=count * 3)
        assert not mismatch, 'TOKENIZER_OUTPUT_MISMATCHES'
        result.update(status='PASS_FULL_HISTORICAL_QWEN_TOKENIZER_PENDING_INDEPENDENT', coverage=counts,
            input_tokens_checked=input_total, output_tokens_checked=output_total, rebuilt_fields_per_receipt=10, generation_receipts=41040,
            exact_rebuilt_field_comparisons=410400, mismatches=0)
    except Exception as exc: result.update(error=repr(exc), traceback=traceback.format_exc())
    io.write(out / 'MISMATCHES_PRIVATE.json', mismatch)
    io.finish(result, state, allowed, out, 'PRODUCER_RESULT.json')
    print(json.dumps({k: result[k] for k in ('status', 'generation_receipts', 'input_tokens_checked', 'output_tokens_checked') if k in result}, indent=2))
    return 0 if result['status'].startswith('PASS_') else 2


if __name__ == '__main__': raise SystemExit(main())
