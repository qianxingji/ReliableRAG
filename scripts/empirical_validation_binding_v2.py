"""Prospective V2 binding for two omitted original helper-scope constants."""
import ast
import builtins
import dis
import hashlib
from pathlib import Path
import types

from scripts.empirical_validation_binding import ValidationBindings, helper_asts
from scripts.empirical_validation_length import require


NATIVE_SHA = '3eb99ad55f93af8beaa0d316d8892ca8747a627bb80671d358312b758638915a'
HELPER_SHA = '12634390df5c76ae30baeb3172778a86fdae87b7ffc06491db4ab57fcb83fd0a'
SUPPORT_SHA = 'd4bacc0112c06df55b924961fb0296204ae8f12e6a19de8020b1feeaca4039c7'
EXPECTED_CONSTANTS = {
    'DATASETS': ('hotpotqa', '2wikimultihopqa', 'musique'),
    'RETRIEVERS': ('bm25', 'dense', 'hybrid'),
}


def source_record(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        size_bytes=path.stat().st_size)


def constant_assignments(path):
    """Read only the two literal assignment ASTs from an authenticated source."""
    found = {}
    for node in ast.parse(Path(path).read_text(encoding='utf-8-sig')).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        name = getattr(node.targets[0], 'id', None)
        if name in EXPECTED_CONSTANTS:
            require(name not in found, 'DUPLICATE_CONSTANT_ASSIGNMENT')
            value = ast.literal_eval(node.value)
            require(type(value) is tuple and all(type(x) is str for x in value), 'LITERAL_STRING_TUPLE_CONSTANT')
            found[name] = dict(value=list(value),
                ast_sha256=hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest())
    require(set(found) == set(EXPECTED_CONSTANTS), 'EXACT_CONSTANT_ASSIGNMENTS')
    return found


def global_reads(code):
    names = {item.argval for item in dis.get_instructions(code)
        if item.opname in {'LOAD_GLOBAL', 'LOAD_NAME'}}
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            names.update(global_reads(value))
    return names


def dependency_inventory(functions):
    """Include nested code objects and distinguish builtins from scope globals."""
    require(type(functions) is dict and functions, 'FUNCTION_DICTIONARY')
    scopes = {id(value.__globals__): value.__globals__ for value in functions.values()
        if isinstance(value, types.FunctionType)}
    require(len(scopes) == 1, 'ONE_ORIGINAL_HELPER_NAMESPACE')
    scope = next(iter(scopes.values()))
    available = set(scope) | set(vars(builtins))
    records = {}
    for name, function in sorted(functions.items()):
        require(isinstance(function, types.FunctionType), 'ORIGINAL_HELPERS_ARE_FUNCTIONS')
        reads = global_reads(function.__code__)
        records[name] = dict(global_reads=sorted(reads), missing=sorted(reads - available))
    missing = sorted(set().union(*(set(value['missing']) for value in records.values())))
    return scope, records, missing


class V2ValidationBindings(ValidationBindings):
    """Add only authenticated DATASETS/RETRIEVERS to the extracted helper scope."""
    def __init__(self, native, frozen, payloads, **kwargs):
        super().__init__(native, frozen, payloads, **kwargs)
        self.helper_scope_receipt = None

    def _authenticate_constants(self, root):
        native_path = Path(self.native.__file__).resolve()
        helper_path = Path(root).resolve() / 'outputs/daa_v2_fresh_v1/runtime_branch_freeze/independent_validate.py'
        support_path = helper_path.with_name('runtime_support.py')
        expected = self.frozen['constant_sources']
        actual = dict(native=source_record(native_path), helper=source_record(helper_path), support=source_record(support_path))
        require(actual == expected, 'FROZEN_CONSTANT_SOURCE_RECORDS')
        require(actual['native']['sha256'] == NATIVE_SHA, 'CURRENT_VALIDATOR_SOURCE_PIN')
        require(actual['helper']['sha256'] == HELPER_SHA, 'ORIGINAL_HELPER_SOURCE_PIN')
        require(actual['support']['sha256'] == SUPPORT_SHA, 'ORIGINAL_SUPPORT_SOURCE_PIN')
        current = constant_assignments(native_path)
        historical = constant_assignments(support_path)
        require(current == historical == self.frozen['constant_assignments'], 'CONSTANT_ASSIGNMENT_AST_AND_VALUES')
        require({name: tuple(value['value']) for name, value in current.items()} == EXPECTED_CONSTANTS,
            'EXACT_ORIGINAL_CONSTANT_VALUES')
        return actual, current

    def load_functions(self, root):
        require(self.loader_calls == 0, 'SINGLE_ORIGINAL_HELPER_LOAD')
        paths, assignments = self._authenticate_constants(root)
        helper_path = Path(root) / 'outputs/daa_v2_fresh_v1/runtime_branch_freeze/independent_validate.py'
        found = helper_asts(helper_path)
        require(found == self.frozen['original_helper_asts'], 'FROZEN_HELPER_AST_PINS')
        functions = self.original_loader(root)
        require(set(functions) == set(found) - {'FORBIDDEN'}, 'EXACT_ORIGINAL_HELPER_FUNCTION_SET')
        scope, before, missing_before = dependency_inventory(functions)
        require(missing_before == ['DATASETS', 'RETRIEVERS'], 'EXACT_PREBIND_MISSING_GLOBALS')
        require(set(name for name, value in before.items() if value['missing']) == {'validate_branch'},
            'ONLY_VALIDATE_BRANCH_AFFECTED')
        require(all(name not in scope for name in EXPECTED_CONSTANTS), 'HELPER_CONSTANT_ALREADY_BOUND')
        saved = dict(scope)
        original_objects = dict(functions)
        for name, value in EXPECTED_CONSTANTS.items():
            scope[name] = value
        require(set(scope) == set(saved) | set(EXPECTED_CONSTANTS) and
            all(scope[name] is value for name, value in saved.items()), 'ONLY_TWO_SCOPE_ADDITIONS')
        _, after, missing_after = dependency_inventory(functions)
        require(not missing_after, 'UNRESOLVED_HELPER_GLOBALS_AFTER_BINDING')
        original = functions['validate_generation']
        original_codes = {name: hashlib.sha256(value.__code__.co_code).hexdigest() for name, value in functions.items()}
        functions['validate_generation'] = self.length.wrap_generation(original)
        require(all(functions[name] is value and functions[name].__code__ is value.__code__
            for name, value in original_objects.items() if name != 'validate_generation'),
            'ORIGINAL_HELPER_CODE_OBJECTS_CHANGED')
        self.original_helper_records = found
        self.helper_scope_receipt = dict(status='PASS_TWO_ORIGINAL_CONSTANTS_BOUND',
            source_records=paths, constant_assignments=assignments,
            constants={name:list(value) for name, value in EXPECTED_CONSTANTS.items()},
            missing_before=missing_before, missing_after=missing_after,
            affected_helpers_before=sorted(name for name, value in before.items() if value['missing']),
            dependency_inventory_before=before, dependency_inventory_after=after,
            original_function_code_hashes=original_codes, added_names=sorted(EXPECTED_CONSTANTS),
            other_scope_entries_identity_preserved=True, original_helper_code_objects_preserved=True)
        self.loader_calls += 1
        return functions

    def binding_receipt(self):
        value = super().binding_receipt()
        value.update(binding_version='V2_HELPER_CONSTANTS', helper_scope=self.helper_scope_receipt,
            v1_length_and_finalization_reused=True,
            v1_actual_failure_never_upgraded=True,
            scientific_checks_thresholds_and_helper_bodies_changed=False)
        value['entry_bindings'].insert(1,
            'helper namespace: authenticate and bind original DATASETS/RETRIEVERS constants')
        return value
