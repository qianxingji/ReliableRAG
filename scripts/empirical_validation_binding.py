"""Add explicit execution metadata/control bytes to the original C3 final seal."""
import ast
import hashlib
import json
from pathlib import Path
import sys

from scripts.empirical_validation_length import FixedTokenizerLength, canonical_hash, require


def helper_asts(path):
    names = {'FORBIDDEN', 'no_forbidden_fields', 'parsed_answer', 'parsed_query', 'render', 'validate_branch',
        'rank_entries', 'bm25_scores', 'rrf', 'validate_rank', 'replacement', 'validate_generation', 'expected_evidence'}
    found = {}
    for node in ast.parse(path.read_text(encoding='utf-8-sig')).body:
        name = getattr(node, 'name', None)
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            name = getattr(node.targets[0], 'id', None)
        if name in names:
            require(name not in found, 'DUPLICATE_ORIGINAL_HELPER_AST')
            found[name] = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
    require(set(found) == names, 'EXACT_ORIGINAL_HELPER_AST_SET')
    return found


class ValidationBindings:
    """Preserve original validator control flow; disclose three entry bindings."""
    def __init__(self, native, frozen, payloads, *, expected_generations=54540, forbidden_events=None):
        self.native = native
        self.frozen = frozen
        self.payloads = payloads
        self.expected_generations = expected_generations
        self.length = FixedTokenizerLength(frozen['tokenizer_source'])
        self.original_loader = native.load_independent_functions
        self.original_writer = native.write_json
        self.original_seal = native.seal
        self.loader_calls = 0
        self.report_writes = 0
        self.control_artifacts = []
        self.original_helper_records = None
        self.forbidden_events = forbidden_events if forbidden_events is not None else []

    def install(self):
        self.native.load_independent_functions = self.load_functions
        self.native.write_json = self.write_result
        self.native.seal = self.seal_with_controls

    def load_functions(self, root):
        require(self.loader_calls == 0, 'SINGLE_ORIGINAL_HELPER_LOAD')
        path = Path(root) / 'outputs/daa_v2_fresh_v1/runtime_branch_freeze/independent_validate.py'
        require(hashlib.sha256(path.read_bytes()).hexdigest() ==
            '12634390df5c76ae30baeb3172778a86fdae87b7ffc06491db4ab57fcb83fd0a', 'ORIGINAL_HELPER_SOURCE_PIN')
        found = helper_asts(path)
        require(found == self.frozen['original_helper_asts'], 'FROZEN_HELPER_AST_PINS')
        functions = self.original_loader(root)
        original = functions['validate_generation']
        require(all(f.__globals__ is original.__globals__ for f in functions.values()), 'ONE_ORIGINAL_HELPER_NAMESPACE')
        functions['validate_generation'] = self.length.wrap_generation(original)
        self.original_helper_records = found
        self.loader_calls += 1
        return functions

    def binding_receipt(self):
        return dict(status='OBSERVED_NOT_YET_ACCEPTED',
            entry_bindings=['load_independent_functions: original helper ASTs plus scoped len and generation observation',
                'write_json: add execution_binding at the first independent-result creation',
                'seal: exclusively include preloaded controls before the original final namespace seal'],
            fixed_length=self.length.receipt(), original_helper_asts=self.original_helper_records,
            freeze_sha256=self.frozen['freeze_sha256'], controls=self.frozen['embedded_controls'],
            original_main_and_validate_all_bodies_unchanged=True, original_guard_unchanged=True,
            forbidden_execution_events=list(self.forbidden_events),
            control_writes_after_original_computation_boundary=True, literal_unchanged_original_cli=False)

    def write_result(self, path, value):
        if Path(path).resolve() == (self.native.OUT / 'INDEPENDENT_VALIDATION.json').resolve():
            require(self.report_writes == 0 and 'execution_binding' not in value, 'FIRST_INDEPENDENT_RESULT_ONLY')
            self.report_writes += 1
            original_hash = canonical_hash(value)
            original_status = value.get('status')
            binding = self.binding_receipt()
            if original_status == 'PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY':
                try:
                    require(self.loader_calls == 1, 'ONE_COMPLETE_ORIGINAL_HELPER_LOAD')
                    require(not self.forbidden_events, 'NO_FORBIDDEN_EXECUTION')
                    binding['fixed_length'] = self.length.finish(self.expected_generations)
                    torch = sys.modules.get('torch')
                    require(torch is None or not torch.cuda.is_initialized(), 'NO_CUDA_INITIALIZATION')
                    binding['status'] = 'PASS_COMPLETE_DECLARED_EXECUTION_BINDING_PENDING_FINAL_SEAL'
                except Exception as exc:
                    value.update(status='FAIL', execution_binding_error_type=type(exc).__name__, execution_binding_error=str(exc))
                    binding.update(status='FAIL', diagnostic=str(exc))
            else:
                binding['status'] = 'ORIGINAL_VALIDATION_FAILED_NOT_UPGRADED'
            binding.update(original_result_before_binding_sha256=original_hash, original_result_status=original_status)
            value['execution_binding'] = binding
        return self.original_writer(path, value)

    def seal_with_controls(self, output, name='SHA256_MANIFEST.json'):
        require(Path(output).resolve() == self.native.OUT.resolve() and name == 'SHA256_MANIFEST.json', 'EXACT_FINAL_RUNTIME_SEAL')
        report = json.loads((output / 'INDEPENDENT_VALIDATION.json').read_text(encoding='utf-8'))
        require(report['status'] == 'PASS_INDEPENDENT_RUNTIME_AND_BOUNDED_REPLAY' and
            report['execution_binding']['status'] == 'PASS_COMPLETE_DECLARED_EXECUTION_BINDING_PENDING_FINAL_SEAL', 'ACCEPTED_BINDING_BEFORE_SEAL')
        directory = output / 'validation_execution'
        require(not directory.exists(), 'NO_EXECUTION_CONTROL_OVERWRITE')
        directory.mkdir()
        for entry in self.frozen['embedded_controls']:
            name = entry['filename']
            require(Path(name).name == name and name not in {'.', '..'}, 'CONTROL_BASENAME_ONLY')
            data = self.payloads[name]
            require(hashlib.sha256(data).hexdigest() == entry['sha256'] and len(data) == entry['size_bytes'], 'PRELOADED_CONTROL_PIN')
            path = directory / name
            with path.open('xb') as stream:
                stream.write(data)
            require(hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], 'WRITTEN_EXECUTION_CONTROL_PIN')
            self.control_artifacts.append(path)
        return self.original_seal(output)
