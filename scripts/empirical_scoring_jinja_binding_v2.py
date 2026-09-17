"""Exact-code Jinja compiler allowance around the unchanged composed C4 guard."""
from __future__ import annotations

import hashlib
import importlib.metadata
from pathlib import Path
import sys
import types

from scripts.empirical_scoring_stage_guard import guard as original_stage_guard
from scripts.empirical_scoring_stage_io import require


JINJA_VERSION = "3.1.6"
COMPILER_SHA256 = "f51a42425e57f3c0479652623ec1cf876f791e1d2e029bf0149350baeb542de3"
ENVIRONMENT_SHA256 = "f6786b3fb0a1f8d6c65f4d30bf2af8cb2fae84d1ead8e09ceb48201ab9e2fdf9"
ACTIVE = {}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _all_code(code):
    yield code
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            yield from _all_code(value)


def _source_code(path, function):
    compiled = compile(Path(path).read_bytes(), function.__code__.co_filename, "exec",
                       dont_inherit=True, optimize=sys.flags.optimize)
    matches = [code for code in _all_code(compiled)
               if code.co_name == function.__code__.co_name
               and code.co_firstlineno == function.__code__.co_firstlineno]
    require(len(matches) == 1 and matches[0] == function.__code__,
            "JINJA_LOADED_CODE_MUST_MATCH_AUTHENTICATED_SOURCE")
    return matches[0]


def authenticate_jinja(*, compiler_sha256=COMPILER_SHA256,
                       environment_sha256=ENVIRONMENT_SHA256):
    import jinja2
    import jinja2.compiler as compiler
    import jinja2.environment as environment

    require(importlib.metadata.version("Jinja2") == JINJA_VERSION,
            "JINJA_VERSION")
    compiler_path = Path(compiler.__file__).resolve()
    environment_path = Path(environment.__file__).resolve()
    require(_sha(compiler_path) == compiler_sha256, "JINJA_COMPILER_SOURCE_PIN")
    require(_sha(environment_path) == environment_sha256,
            "JINJA_ENVIRONMENT_SOURCE_PIN")
    _source_code(compiler_path, compiler.generate)
    _source_code(environment_path, environment.Environment._generate)
    require(compiler.__dict__.get("generate") is compiler.generate and
            environment.__dict__.get("generate") is compiler.generate,
            "JINJA_ORIGINAL_FUNCTION_BINDINGS")
    return dict(
        version=jinja2.__version__,
        compiler=dict(path=str(compiler_path), sha256=compiler_sha256,
                      size_bytes=compiler_path.stat().st_size,
                      function="generate",
                      firstlineno=compiler.generate.__code__.co_firstlineno,
                      loaded_code_matches_source=True),
        environment=dict(path=str(environment_path), sha256=environment_sha256,
                         size_bytes=environment_path.stat().st_size,
                         function="Environment._generate",
                         firstlineno=environment.Environment._generate.__code__.co_firstlineno,
                         loaded_code_matches_source=True),
    )


class ExactJinjaCompilerBinding:
    """Admit one exact compiler call event; delegate every other event unchanged."""

    def __init__(self):
        import jinja2.compiler as compiler
        import jinja2.environment as environment

        self.identity = authenticate_jinja()
        self.compiler = compiler
        self.environment = environment
        self.compiler_function = compiler.generate
        self.environment_function = environment.Environment._generate
        self.original_profile = None
        self.profile = None
        self.stats = dict(
            binding_version="C4_JINJA_EXACT_CODE_AND_DIRECT_CALLER_V2",
            authenticated_identity=self.identity,
            admitted_compiler_call_events=0,
            original_profile_delegated_events=0,
            nested_calls_exempted=0,
        )

    def _admitted(self, frame):
        if frame.f_code is not self.compiler_function.__code__:
            return False
        if frame.f_globals is not self.compiler.__dict__:
            return False
        if self.compiler.__dict__.get("generate") is not self.compiler_function:
            return False
        caller = frame.f_back
        if caller is None or caller.f_code is not self.environment_function.__code__:
            return False
        if caller.f_globals is not self.environment.__dict__:
            return False
        if self.environment.__dict__.get("generate") is not self.compiler_function:
            return False
        return caller.f_locals.get("self") is frame.f_locals.get("environment")

    def install(self, root, output, paths, *, stage):
        receipt = original_stage_guard(root, output, paths, stage=stage)
        self.original_profile = sys.getprofile()
        require(callable(self.original_profile), "ORIGINAL_COMPOSED_C4_PROFILE")

        def exact_profile(frame, event, arg):
            if event == "call" and self._admitted(frame):
                self.stats["admitted_compiler_call_events"] += 1
                return
            self.stats["original_profile_delegated_events"] += 1
            self.original_profile(frame, event, arg)

        self.profile = exact_profile
        receipt["jinja_execution_binding_v2"] = self.stats
        sys.setprofile(exact_profile)
        ACTIVE[id(receipt)] = self
        return receipt


def guard(root, output, paths, *, stage):
    binding = ExactJinjaCompilerBinding()
    return binding.install(root, output, paths, stage=stage)


def active_binding(receipt):
    require(id(receipt) in ACTIVE, "ACTIVE_JINJA_BINDING")
    return ACTIVE[id(receipt)]


def release_binding(receipt):
    ACTIVE.pop(id(receipt), None)
