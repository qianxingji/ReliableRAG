"""Explicit fixed-object length binding around the unchanged generation validator."""
import builtins
import hashlib
import inspect
import json
from pathlib import Path

ORDINARY_LEN = builtins.len
CARDINALITY = 151665
VOCAB_SHA = '54a4e00eec5a8c5f40d137afdde38da75f4c46ffa802b509cb5fb2157b5a5b0d'
TEMPLATE_SHA = 'cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


class FixedTokenizerLength:
    """Only the bound tokenizer gets a constant; every other object uses builtin len."""
    def __init__(self, tokenizer_source):
        self.tokenizer_source = tokenizer_source
        self.tokenizer = None
        self.specialized_calls = 0
        self.ordinary_calls = 0
        self.successful_generations = 0
        self.generated_ids_checked = 0
        self.failed_generations = 0
        self.vocabulary_rechecks = 0

    def bind(self, tokenizer):
        if self.tokenizer is not None:
            require(tokenizer is self.tokenizer, 'TOKENIZER_INSTANCE_CHANGED')
            return
        cls = type(tokenizer)
        require(cls.__name__ == 'Qwen2TokenizerFast' and
            cls.__module__ == 'transformers.models.qwen2.tokenization_qwen2_fast', 'EXACT_TOKENIZER_CLASS')
        path = Path(inspect.getfile(cls)).resolve()
        require(path == Path(self.tokenizer_source['path']).resolve() and
            hashlib.sha256(path.read_bytes()).hexdigest() == self.tokenizer_source['sha256'], 'ACTUAL_TOKENIZER_SOURCE')
        self.tokenizer = tokenizer
        self.recheck()

    def __call__(self, value):
        if self.tokenizer is not None and value is self.tokenizer:
            self.specialized_calls += 1
            return CARDINALITY
        self.ordinary_calls += 1
        return ORDINARY_LEN(value)

    def recheck(self):
        require(self.tokenizer is not None and builtins.len is ORDINARY_LEN, 'BOUND_TOKENIZER_AND_UNCHANGED_BUILTIN')
        require(ORDINARY_LEN(self.tokenizer) == CARDINALITY, 'TOKENIZER_CARDINALITY_CHANGED')
        require(canonical_hash(self.tokenizer.get_vocab()) == VOCAB_SHA, 'TOKENIZER_VOCABULARY_CHANGED')
        require(hashlib.sha256(self.tokenizer.chat_template.encode('utf-8')).hexdigest() == TEMPLATE_SHA, 'TOKENIZER_TEMPLATE_CHANGED')
        self.vocabulary_rechecks += 1

    def wrap_generation(self, original):
        scope = original.__globals__
        require('len' not in scope, 'ORIGINAL_HELPER_LEN_ALREADY_BOUND')
        scope['len'] = self

        def observed(rec, trace, stage, evidence, question, tokenizer, templates, config):
            self.bind(tokenizer)
            before = self.specialized_calls
            try:
                result = original(rec, trace, stage, evidence, question, tokenizer, templates, config)
            except BaseException:
                self.failed_generations += 1
                raise
            count = ORDINARY_LEN(rec['generated_token_ids'])
            require(self.specialized_calls - before == count, 'EVERY_GENERATED_ID_LENGTH_CHECKED')
            self.successful_generations += 1
            self.generated_ids_checked += count
            if self.successful_generations % 1500 == 0:
                self.recheck()
            return result

        return observed

    def finish(self, expected_generations):
        self.recheck()
        require(self.successful_generations == expected_generations and self.failed_generations == 0,
            'COMPLETE_GENERATION_VALIDATION_COVERAGE')
        require(self.specialized_calls == self.generated_ids_checked, 'EXACT_GENERATED_ID_LENGTH_COVERAGE')
        return self.receipt()

    def receipt(self):
        return dict(global_name='len', scope='one original independent helper namespace',
            specialization='one fixed tokenizer object; all other objects use ordinary builtin len',
            cardinality=CARDINALITY, vocabulary_sha256=VOCAB_SHA, chat_template_sha256=TEMPLATE_SHA,
            specialized_length_calls=self.specialized_calls, ordinary_length_calls=self.ordinary_calls,
            successful_generation_checks=self.successful_generations, generated_ids_checked=self.generated_ids_checked,
            failed_generation_checks=self.failed_generations, complete_vocabulary_rechecks=self.vocabulary_rechecks,
            tokenizer_source=self.tokenizer_source, tokenizer_mutated=False, global_builtins_modified=False,
            original_scientific_helper_bodies_modified=False, literal_unchanged_original_cli=False)
