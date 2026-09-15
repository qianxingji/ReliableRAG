"""Exercise actual Python read guards using invented files in a temporary root."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class RuntimeGuardTests(unittest.TestCase):
    def test_raw_other_model_and_tokenizer_weight_boundaries(self):
        code = '''
from pathlib import Path
import sys
from scripts.empirical_runtime_guard import guard
from scripts.verify_roa_artifacts import digest
root=Path(sys.argv[1]);out=root/'new';out.mkdir()
raw=root/'data/raw/toy.json'
qwen=root/'data/models/huggingface/models--Qwen--Qwen2.5-3B-Instruct/toy.safetensors'
other=root/'data/models/huggingface/models--Other/toy.safetensors'
for p in (raw,qwen,other):p.parent.mkdir(parents=True,exist_ok=True);p.write_text('invented')
scope=guard(root,out,[raw,qwen,other],tokenizer_only=sys.argv[2]=='tokenizer')
for p in (raw,other):
    try:p.read_text()
    except RuntimeError:pass
    else:raise AssertionError('forbidden file decoded')
if sys.argv[2]=='tokenizer':
    try:qwen.read_bytes()
    except RuntimeError:pass
    else:raise AssertionError('weight read in tokenizer mode')
    assert len(digest(qwen))==64
else:assert qwen.read_text()=='invented'
outside=root/'not_an_output.txt'
try:outside.write_text('invented')
except RuntimeError:pass
else:raise AssertionError('external write')
assert not outside.exists()
print('PASS')
'''
        for mode in ("joint", "tokenizer"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                run = subprocess.run([sys.executable, "-B", "-c", code, folder, mode], capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(run.stdout.strip(), "PASS")


if __name__ == "__main__":
    unittest.main()
