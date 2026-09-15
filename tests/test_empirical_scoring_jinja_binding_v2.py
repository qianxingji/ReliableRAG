"""CPU-only positive/negative gate for the prospective C4 Jinja V2 binding."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
ROOT = Path(r"E:\paper\ReliableRAG")
PYTHON = ROOT / ".venv/Scripts/python.exe"
SOURCE_PINS = {
    "scripts/empirical_scoring_guard.py": "10330b7a464e859b816f55569de423b9802f2ca45faf6a0f830dae7a4ebdfb3e",
    "scripts/empirical_scoring_stage_guard.py": "71074048e9979032f777e1c38aab8575ecb1139cead026c2c4c18eb51a0b3ac3",
    "scripts/empirical_scoring_stage_run.py": "c9624604d46eeb1b7fb8340083c274922b1916268d287ef2671044f245035987",
    "scripts/preflight_roa_empirical_scoring_gpu.py": "fd38feb973c849dcdc1a66b636593f2f09b51a4f7c797f26b6d01ac710d01fe6",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def child_output(value):
    print(json.dumps(value, ensure_ascii=False))


def child_guard(case, output):
    from scripts.empirical_scoring_jinja_binding_v2 import guard

    output.mkdir(parents=True)
    paths = []
    stage = "gpu_preflight"
    sentinel = output / "sentinel.txt"
    if case == "raw_read":
        target = ROOT / "data/raw/invented-never-read.json"
        action = target.read_bytes
    elif case == "unlisted_read":
        target = ROOT / "invented-unlisted-never-read.txt"
        action = target.read_bytes
    elif case == "external_write":
        target = output.parent / "outside.txt"
        action = lambda: target.write_text("bad")
    elif case == "wrong_stage_weight":
        stage = "independent"
        target = ROOT / "data/models/huggingface/models--Qwen--Qwen2.5-3B-Instruct/invented.safetensors"
        paths = [target]
        action = target.read_bytes
    elif case == "cpu_forward":
        stage = "independent"
        class Toy:
            def parameters(self): return []
            def forward(self): sentinel.write_text("bad")
        action = Toy().forward
    elif case in {"fit", "partial_fit", "fit_transform", "standalone_generate"}:
        name = "generate" if case == "standalone_generate" else case
        scope = {"sentinel": sentinel}
        exec(compile("def %s():\n sentinel.write_text('bad')\n" % name,
                     str(REPO / "invented_model.py"), "exec"), scope)
        action = scope[name]
    elif case == "method_generate":
        class Toy:
            def generate(self): sentinel.write_text("bad")
        action = Toy().generate
    elif case == "forged_compiler_path":
        import jinja2.compiler
        scope = {"sentinel": sentinel}
        exec(compile("def generate():\n sentinel.write_text('bad')\n",
                     str(Path(jinja2.compiler.__file__).resolve()), "exec"), scope)
        action = scope["generate"]
    elif case == "new_retrieval":
        scope = {"sentinel": sentinel}
        exec(compile("def retrieve():\n sentinel.write_text('bad')\n",
                     str(ROOT / "src/retrieval/invented.py"), "exec"), scope)
        action = scope["retrieve"]
    elif case == "socket":
        action = lambda: sys.audit("socket.connect", None, None)
    elif case == "subprocess":
        action = lambda: sys.audit("subprocess.Popen", "invented", [], None, None)
    else:
        raise AssertionError(case)
    receipt = guard(ROOT, output, paths, stage=stage)
    try:
        action()
    except RuntimeError as exc:
        child_output(dict(case=case, diagnostic=str(exc), sentinel=sentinel.exists(),
                          denials=receipt["denied"], profile_cleared=sys.getprofile() is None))
        return 0
    raise AssertionError("negative body was not denied: " + case)


def child_jinja(mode, output):
    import jinja2
    if mode == "jinja_original":
        from scripts.empirical_scoring_stage_guard import guard
    else:
        from scripts.empirical_scoring_jinja_binding_v2 import guard
    output.mkdir(parents=True)
    sentinel = output / "sentinel.txt"
    receipt = guard(ROOT, output, [], stage="gpu_preflight")
    if mode == "jinja_direct":
        import jinja2.compiler
        environment = jinja2.Environment()
        node = environment.parse("Hello {{ name }}")
        action = lambda: jinja2.compiler.generate(node, environment, None, None)
    elif mode == "jinja_nested":
        import jinja2.compiler
        def generate(): sentinel.write_text("bad")
        class Nested(jinja2.compiler.CodeGenerator):
            def __init__(self, *args, **kwargs):
                generate()
                super().__init__(*args, **kwargs)
        environment = jinja2.Environment()
        environment.code_generator_class = Nested
        action = lambda: environment.from_string("Hello {{ name }}").render(name="invented")
    else:
        action = lambda: jinja2.Environment().from_string("Hello {{ name }}").render(name="invented")
    try:
        rendered = action()
    except RuntimeError as exc:
        child_output(dict(mode=mode, diagnostic=str(exc), denials=receipt["denied"],
                          sentinel=sentinel.exists(), profile_cleared=sys.getprofile() is None,
                          admitted=receipt.get("jinja_execution_binding_v2", {}).get(
                              "admitted_compiler_call_events", 0)))
        return 0
    assert mode == "jinja_bound" and rendered == "Hello invented"
    child_output(dict(mode=mode, rendered=rendered, denials=receipt["denied"],
                      admitted=receipt["jinja_execution_binding_v2"]["admitted_compiler_call_events"],
                      active_profile=sys.getprofile() is not None))
    return 0


def child_tokenizer(mode, output):
    from transformers import AutoTokenizer
    snapshot = ROOT / "data/models/huggingface/models--Qwen--Qwen2.5-3B-Instruct/snapshots/aa8e72537993ba99e69dfaafa59ed015b17504d1"
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True,
                                               trust_remote_code=False)
    messages = [{"role": "system", "content": "Answer from invented evidence."},
                {"role": "user", "content": "What color is the invented cog?"}]
    output.mkdir(parents=True)
    receipt = None
    if mode == "tokenizer_bound":
        from scripts.empirical_scoring_jinja_binding_v2 import guard
        receipt = guard(ROOT, output, [], stage="gpu_preflight")
    rendered = tokenizer.apply_chat_template(messages, tokenize=False,
                                             add_generation_prompt=True)
    token_ids = tokenizer.apply_chat_template(messages, tokenize=True,
                                              add_generation_prompt=True)
    child_output(dict(mode=mode, rendered_sha256=hashlib.sha256(rendered.encode()).hexdigest(),
                      token_ids_sha256=hashlib.sha256(json.dumps(token_ids,
                          separators=(",", ":")).encode()).hexdigest(),
                      token_count=len(token_ids), model_load_calls=0,
                      model_forward_calls=0, fresh_gold_values_materialized=0,
                      admitted=(receipt["jinja_execution_binding_v2"]["admitted_compiler_call_events"]
                                if receipt else None), denials=(receipt["denied"] if receipt else [])))
    return 0


def child_main(argv):
    case, output = argv[0], Path(argv[1]).resolve()
    if case.startswith("jinja_"):
        return child_jinja(case, output)
    if case.startswith("tokenizer_"):
        return child_tokenizer(case, output)
    if case == "changed_pin":
        from scripts.empirical_scoring_jinja_binding_v2 import authenticate_jinja
        try:
            authenticate_jinja(compiler_sha256="0" * 64)
        except RuntimeError as exc:
            child_output(dict(case=case, diagnostic=str(exc)))
            return 0
        raise AssertionError("changed source pin accepted")
    return child_guard(case, output)


class JinjaBindingV2Tests(unittest.TestCase):
    def run_child(self, case):
        with tempfile.TemporaryDirectory() as tmp:
            command = [str(PYTHON), "-B", "-X", "utf8", str(Path(__file__).resolve()),
                       "--child", case, str(Path(tmp) / "out")]
            env = os.environ.copy()
            env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(REPO),
                       CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1",
                       TRANSFORMERS_OFFLINE="1")
            run = subprocess.run(command, cwd=REPO, env=env, capture_output=True,
                                 text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, "")
        return json.loads(run.stdout)

    def test_authenticated_cold_jinja_and_original_failure(self):
        original = self.run_child("jinja_original")
        self.assertEqual(original["diagnostic"], "C4 boundary: forbidden call generate")
        bound = self.run_child("jinja_bound")
        self.assertEqual(bound["rendered"], "Hello invented")
        self.assertGreater(bound["admitted"], 0)
        self.assertEqual(bound["denials"], [])

    def test_real_qwen_tokenizer_cold_template_equivalence(self):
        reference = self.run_child("tokenizer_reference")
        bound = self.run_child("tokenizer_bound")
        for field in ("rendered_sha256", "token_ids_sha256", "token_count"):
            self.assertEqual(bound[field], reference[field])
        self.assertGreater(bound["admitted"], 0)
        self.assertEqual(bound["denials"], [])
        self.assertEqual(bound["model_load_calls"], bound["model_forward_calls"])
        self.assertEqual(bound["model_forward_calls"], bound["fresh_gold_values_materialized"])

    def test_exact_identity_and_descendant_negative_cases(self):
        expected = {
            "standalone_generate": "forbidden call generate",
            "method_generate": "forbidden call generate",
            "forged_compiler_path": "forbidden call generate",
            "jinja_direct": "forbidden call generate",
            "jinja_nested": "forbidden call generate",
            "fit": "forbidden call fit",
            "partial_fit": "forbidden call partial_fit",
            "fit_transform": "forbidden call fit_transform",
            "new_retrieval": "new retrieval/query embedding in scoring",
            "raw_read": "raw benchmark read",
            "unlisted_read": "unlisted project input",
            "external_write": "write outside output",
            "wrong_stage_weight": "neural weight loading outside stage",
            "cpu_forward": "neural forward in CPU",
            "socket": "socket.connect",
            "subprocess": "subprocess.Popen",
        }
        profile_denials = {
            "standalone_generate", "method_generate", "forged_compiler_path",
            "jinja_direct", "jinja_nested", "fit", "partial_fit",
            "fit_transform", "new_retrieval", "cpu_forward",
        }
        for case, reason in expected.items():
            with self.subTest(case=case):
                result = self.run_child(case)
                self.assertIn(reason, result["diagnostic"])
                self.assertFalse(result["sentinel"])
                self.assertEqual(result["profile_cleared"], case in profile_denials)
        self.assertEqual(self.run_child("changed_pin")["diagnostic"],
                         "JINJA_COMPILER_SOURCE_PIN")

    def test_original_sources_and_v1_failure_remain_exact(self):
        for relative, expected in SOURCE_PINS.items():
            self.assertEqual(digest(REPO / relative), expected)
        v1 = REPO / "outputs/cas_q2/empirical_scoring_gpu_preflight_v1"
        self.assertEqual(digest(v1 / "SHA256_MANIFEST.json"),
                         "c03555a4a3562be34345bd79b35abb11c8b6bb913a4c812e24837cfb8c88f3b6")
        manifest = json.loads((v1 / "SHA256_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["files"]), 5)
        self.assertEqual({p.relative_to(v1).as_posix() for p in v1.rglob("*") if p.is_file()},
                         {"SHA256_MANIFEST.json", *[x["path"] for x in manifest["files"]]})

    def test_all_five_fixed_path_maps_and_aliases(self):
        from scripts import empirical_scoring_stage_io as stage_io
        from scripts import empirical_scoring_stage_run as stage_run
        from scripts.run_roa_empirical_scoring_bound_v2 import apply_stage_paths, fixed_stage_maps
        before, after = fixed_stage_maps()
        original = stage_io.STAGES
        try:
            for stage in before:
                with self.subTest(stage=stage):
                    mapping = {key: Path(value) for key, value in before.items()}
                    stage_io.STAGES = mapping
                    stage_run.STAGES = mapping
                    config = dict(stage=stage, stage_paths_before=before,
                                  stage_paths_after=after)
                    if stage == "gpu_preflight":
                        context = patch("pathlib.Path.exists", return_value=False)
                    else:
                        context = patch("pathlib.Path.is_dir", return_value=True)
                    with context:
                        apply_stage_paths(config)
                    self.assertIs(stage_io.STAGES, stage_run.STAGES)
                    self.assertEqual({k: str(v.resolve()) for k, v in mapping.items()}, after)
        finally:
            stage_io.STAGES = original
            stage_run.STAGES = original

    def test_config_pin_and_existing_output_fail_closed(self):
        from scripts.run_roa_empirical_scoring_bound_v2 import (
            apply_stage_paths, fixed_stage_maps, parse_binding)
        before, after = fixed_stage_maps()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "CONFIG_PIN"):
                parse_binding(["--config", str(path), "--config-sha256", "0" * 64,
                               "--", "--project-root", str(ROOT)])
        from scripts import empirical_scoring_stage_io as stage_io
        old = stage_io.STAGES
        try:
            stage_io.STAGES = {k: Path(v) for k, v in before.items()}
            with patch("pathlib.Path.exists", return_value=True), self.assertRaisesRegex(
                    RuntimeError, "MUST_START_ABSENT"):
                apply_stage_paths(dict(stage="gpu_preflight", stage_paths_before=before,
                                       stage_paths_after=after))
        finally:
            stage_io.STAGES = old

    def test_versioned_stage_run_adds_controls_and_preserves_result_fields(self):
        from scripts import empirical_scoring_stage_run as stage_run
        from scripts.run_roa_empirical_scoring_bound_v2 import (
            bound_stage_run, canonical_hash, fixed_stage_maps)

        before_map, after_map = fixed_stage_maps()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            config_path = folder / "CONFIG.json"
            control_path = folder / "CONTROL.txt"
            config_path.write_text("{}", encoding="utf-8")
            control_path.write_text("invented control", encoding="utf-8")
            control = dict(path=str(control_path.resolve()), sha256=digest(control_path),
                           size_bytes=control_path.stat().st_size)
            config = dict(stage="gpu_preflight", entry_module=
                          "scripts.preflight_roa_empirical_scoring_gpu",
                          stage_paths_before=before_map, stage_paths_after=after_map,
                          controls=[control])
            output = folder / "output"
            output.mkdir()
            profile = lambda frame, event, arg: None
            binding = types.SimpleNamespace(profile=profile, stats=dict(
                binding_version="C4_JINJA_EXACT_CODE_AND_DIRECT_CALLER_V2",
                admitted_compiler_call_events=3))

            class FakeStageRun:
                def __init__(self, root, stage, pins):
                    self.paths = []
                    self.result = {"status": "ORIGINAL", "scientific_value": 7}
                    self.out = output
                    self.boundary = {"invented": True}
                def finish(self, success_status=None, *, acceptance=None):
                    self.parent_arguments = (success_status, acceptance)
                    sys.setprofile(None)
                    return 0

            original_class, original_guard = stage_run.StageRun, stage_run.guard
            try:
                stage_run.StageRun = FakeStageRun
                with patch("scripts.empirical_scoring_jinja_binding_v2.active_binding",
                           return_value=binding), patch(
                           "scripts.empirical_scoring_jinja_binding_v2.release_binding") as release:
                    Bound = bound_stage_run(config, config_path, "a" * 64,
                                           [folder / "authenticated"])
                    run = Bound(ROOT, "gpu_preflight", {"runtime": "b" * 64})
                    sys.setprofile(profile)
                    original = dict(run.result)
                    self.assertEqual(run.finish("PASS"), 0)
                    release.assert_called_once_with(run.boundary)
                receipt = json.loads((output / "EXECUTION_BINDING_V2.json").read_text(
                    encoding="utf-8"))
                self.assertEqual(receipt["original_result_before_binding_sha256"],
                                 canonical_hash(original))
                self.assertEqual(receipt["original_result_fields"], list(original))
                self.assertEqual(receipt["controls_added"], [
                    dict(path=str(config_path.resolve()), sha256=digest(config_path),
                         size_bytes=config_path.stat().st_size), control])
                self.assertTrue(receipt["active_profile_before_finalization"])
                self.assertEqual(run.parent_arguments, ("PASS", None))
                self.assertEqual(run.result["status"], "ORIGINAL")
                self.assertIn("execution_binding_v2", run.result)
            finally:
                sys.setprofile(None)
                stage_run.StageRun = original_class
                stage_run.guard = original_guard


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        raise SystemExit(child_main(sys.argv[2:]))
    unittest.main()
