import hashlib
import sys
import tempfile
from pathlib import Path
import unittest

from scripts.empirical_scoring_import_v2 import source_only_import


class SourceImportTests(unittest.TestCase):
    def test_existing_bytecode_is_never_read_and_class_identity_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'toy.py'
            source.write_text('class Saved:\n    value = 17\n',encoding='utf-8')
            cache=root/'__pycache__';cache.mkdir();cached=cache/('toy.'+sys.implementation.cache_tag+'.pyc')
            cached.write_bytes(b'Untrusted invented bytecode must never be opened')
            before=hashlib.sha256(source.read_bytes()).hexdigest()
            def audit(event,args):
                if event=='open' and isinstance(args[0],str) and Path(args[0]).resolve()==cached.resolve():
                    raise AssertionError('Bytecode read')
            sys.addaudithook(audit)
            module=source_only_import('synthetic_saved_source_only',source)
            self.assertEqual(module.Saved.value,17)
            self.assertEqual(module.Saved.__module__,'synthetic_saved_source_only')
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)
            self.assertIs(sys.modules['synthetic_saved_source_only'],module)


if __name__=='__main__':unittest.main()
