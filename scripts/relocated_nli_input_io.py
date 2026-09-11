"""NLI tokenizer factory/ownership and fixture utilities; no neural scorer."""
import hashlib
import json
from pathlib import Path
import sys


MODEL_ID = 'MoritzLaurer/deberta-v3-large-zeroshot-v2.0'
REVISION = '5a4338ab2151dc8db04ad53b42b6153382bf4f99'


def key(row): return tuple(row[k] for k in ('dataset', 'retriever', 'sample_id'))


def factory(cfg, named, io, result):
    target = Path(cfg['sentencepiece_target']).resolve()
    assert target == Path('E:/paper/ReliableRAG-neural-targets-v1/sentencepiece').resolve()
    sys.path.insert(0, str(target))
    import torch
    import transformers
    import sentencepiece
    from transformers import AutoConfig, AutoTokenizer
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized()
    assert sentencepiece.__version__ == '0.2.1' and transformers.__version__ == '4.53.2'
    snapshot = named['nli_config'].parent
    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), revision=REVISION, use_fast=False, local_files_only=True, trust_remote_code=False)
    model_config = AutoConfig.from_pretrained(str(snapshot), revision=REVISION, local_files_only=True, trust_remote_code=False)
    assert not tokenizer.is_fast and type(tokenizer).__name__ == 'DebertaV2Tokenizer'
    assert tokenizer.model_max_length == model_config.max_position_embeddings == 512
    assert {int(k):v for k,v in model_config.id2label.items()} == {0:'entailment',1:'not_entailment'}
    module = sys.modules['sentencepiece._sentencepiece']
    for path in (Path(sentencepiece.__file__).resolve(), Path(module.__file__).resolve()): assert path.is_relative_to(target)
    source = Path(cfg['warning_source']['path']); assert io.sha(source) == cfg['warning_source']['sha256']
    result['tokenizer'] = dict(model_id=MODEL_ID, revision=REVISION, class_name=type(tokenizer).__name__, physical_snapshot=str(snapshot),
        use_fast=False, local_files_only=True, trust_remote_code=False, model_max_length=512, entailment_index=0,
        vocab_size=len(tokenizer), versions=dict(sentencepiece=sentencepiece.__version__, torch=torch.__version__, transformers=transformers.__version__),
        core_paths={m.__name__:str(Path(m.__file__).resolve()) for m in (torch, transformers, sentencepiece, module)},
        sentencepiece_native_binary_sha256=io.sha(Path(module.__file__).resolve()), warning_source=cfg['warning_source'])
    return tokenizer, model_config


def native_sources(named, io, records):
    module = io.namespace('original_nli_preparation')
    io.take(module, named['nli_source'], {'GBV_MODEL_ID','GBV_MODEL_REVISION','GBV_HYPOTHESIS_TEMPLATE','GBV_WORD_OVERLAP',
        'format_hypothesis','resolve_entailment_index','pair_token_length','split_passage_to_fit','effective_model_max_length'}, records)
    return module


def independent_sources(named, io, records):
    module = io.namespace('independent_nli_preparation')
    io.take(module, named['independent_source'], {'hypothesis','length','chunks','positive_index'}, records)
    return module


def fixtures(tokenizer, hypothesis, chunker, indexer, length):
    claim = hypothesis('Which token?', 'alpha')
    short, long = 'alpha beta', 'alpha ' * 800
    short_chunks = chunker(tokenizer, short, claim, max_length=512)
    assert short_chunks == [short]
    assert length(tokenizer, long, claim) > 512
    long_chunks = chunker(tokenizer, long, claim, max_length=512)
    assert len(long_chunks) > 1 and all(length(tokenizer, chunk, claim) <= 512 for chunk in long_chunks)
    impossible = hypothesis('Which token?', 'alpha ' * 800)
    try: chunker(tokenizer, short, impossible, max_length=512)
    except ValueError as exc: assert str(exc) == 'hypothesis does not fit the NLI context window'
    else: raise AssertionError('IMPOSSIBLE_HYPOTHESIS_ACCEPTED')
    try: indexer({0:'not_entailment',1:'not_entailment'})
    except ValueError: pass
    else: raise AssertionError('MISSING_POSITIVE_ENTAILMENT_ACCEPTED')
    return dict(short_chunks=short_chunks, long_chunks=long_chunks, impossible_hypothesis_rejected=True,
        invalid_entailment_labels_rejected=True, fixture_count=4, historical_rows=0)


def archive_metadata(named, io):
    provenance = json.loads(named['gbv_provenance'].read_text(encoding='utf-8'))
    execution = json.loads(named['gbv_execution'].read_text(encoding='utf-8'))
    assert provenance['model_id'] == MODEL_ID and provenance['model_revision'] == REVISION
    assert provenance['input_sha256'] == io.sha(named['branches']) and provenance['scores_sha256'] == io.sha(named['gbv_scores'])
    assert provenance['script_sha256'] == io.sha(named['original_scoring_script'])
    assert provenance['counts'] == dict(scored=3202, normalized_answers_equal=10296, a1_empty=2)
    assert provenance['model_max_length'] == 512 and provenance['entailment_index'] == 0 and provenance['batch_size'] == 8
    assert execution['exit_code'] == 0 and execution['error'] is None and execution['boundary_denials'] == []
    assert execution['call_counters'] == dict(gbv_nli_forward_calls=6404, gbv_nli_pairs=32174)
    return provenance, execution


def source_pair(branch, scores):
    assert set(branch) == {'dataset','retriever','sample_id','question','a0','a1','evidence0','evidence1'}
    assert all(type(branch[k]) is str for k in ('dataset','retriever','sample_id','question','a0','a1'))
    assert all(type(branch[k]) is list and len(branch[k]) == 5 and all(type(v) is str for v in branch[k]) for k in ('evidence0','evidence1'))
    assert set(scores) == {'dataset','retriever','sample_id','eligible','forced_keep_reason','F0','F1','gbv_margin',
        'e0_premise_count','e1_premise_count','e0_chunk_count','e1_chunk_count','model_id','model_revision'}
    assert key(branch) == key(scores) and scores['model_id'] == MODEL_ID and scores['model_revision'] == REVISION


def binary_ownership(cfg, io, allowed):
    import psutil
    env, target, base = Path(cfg['environment']).resolve(), Path(cfg['sentencepiece_target']).resolve(), Path(sys.base_prefix).resolve()
    result = []
    for path in sorted({m.path for m in psutil.Process().memory_maps(grouped=False) if m.path and Path(m.path).suffix.lower() in {'.dll','.pyd','.exe'}}):
        p = Path(path).resolve(); assert allowed(p), ('BINARY_OUTSIDE_ALLOWED_ROOT',str(p))
        owner = 'new_sentencepiece_target' if p.is_relative_to(target) else 'new_environment' if p.is_relative_to(env) else 'base_python' if p.is_relative_to(base) else 'reused_windows'
        entry = dict(path=str(p),owner=owner)
        if owner != 'reused_windows': entry.update(sha256=io.sha(p),size_bytes=p.stat().st_size)
        result.append(entry)
    assert any(e['owner'] == 'new_sentencepiece_target' and Path(e['path']).suffix.lower() == '.pyd' for e in result)
    return result
