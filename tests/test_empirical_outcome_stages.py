"""D controller gates and real import/CLI entrypoints, without fresh data access."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.empirical_outcome_stage_run import OutcomeRun
from scripts import empirical_outcome_stage_io as io


class OutcomeStageTests(unittest.TestCase):
    def test_missing_accepted_prelabel_creates_no_namespace_or_reference_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'not_started'
            with patch('scripts.empirical_outcome_stage_run.STAGES', {'mapping':out}), \
                patch('scripts.empirical_outcome_stage_run.subprocess.check_output', side_effect=['', 'inventedcommit']), \
                patch('scripts.empirical_outcome_stage_run.prerequisites', side_effect=RuntimeError('missing complete prelabel')), \
                patch('scripts.empirical_outcome_stage_run.inputs') as source_reader:
                with self.assertRaisesRegex(RuntimeError, 'missing complete prelabel'):
                    OutcomeRun(Path(tmp), 'mapping', {'prelabel':'a'*64})
                source_reader.assert_not_called()
            self.assertFalse(out.exists())

    def test_exact_D_argument_sets_reject_omitted_or_extra_predecessors(self):
        for stage, pins in (('mapping', {}), ('mapping', {'prelabel':'a'*64, 'mapping':'b'*64}),
            ('analysis', {'prelabel':'a'*64, 'mapping':'b'*64}), ('analysis_validation', {'prelabel':'a'*64})):
            with self.subTest(stage=stage), self.assertRaisesRegex(RuntimeError, 'Exact D predecessor'):
                io.prerequisites(stage, pins)

    def test_invented_C4_gate_rejects_CPU_status_missing_scope_or_prior_gold(self):
        pins = {'prelabel':'a'*64}
        seal = dict(status='PASS_COMPLETE_FROZEN_PRELABEL_ONLY', independent_sha256='f'*64, predecessor_manifests={'runtime':'b'*64})
        report = dict(status=seal['status'], traces=18000, questions=6000, cap=900, model_forward_calls=0,
            scientific_fit_calls=0, fresh_gold_values_materialized=0, predecessor_manifests=seal['predecessor_manifests'])
        build = dict(status=seal['status'], source_inputs_unchanged=True)
        def load(path):
            return {'SEAL.json':seal, 'INDEPENDENT_VALIDATION.json':report, 'BUILD_RECEIPT.json':build,
                'EXECUTABLE_FREEZE.json':{'inputs':[], 'predecessor_manifests':seal['predecessor_manifests']}}[path.name]
        with patch.object(io, 'verify_namespace', return_value=[]), patch.object(io, 'load', side_effect=load), \
            patch.object(io, 'record', return_value={'sha256':'f'*64}), patch.object(io, 'scoring_prerequisites', return_value=[]):
            self.assertEqual(io.prerequisites('mapping', pins), [])
            for field, value in (('status', 'PASS_CPU_ENGINEERING_TESTS_ONLY'), ('traces', 17999), ('fresh_gold_values_materialized', 1)):
                original = report[field]; report[field] = value
                with self.subTest(field=field), self.assertRaises(RuntimeError): io.prerequisites('mapping', pins)
                report[field] = original

    def test_all_real_D_cli_imports_and_source_freeze_paths_exist(self):
        self.assertTrue(all(p.is_file() for p in io.source_paths()))
        for name in ('map_roa_empirical_outcomes', 'validate_roa_empirical_outcomes', 'analyze_roa_empirical_results', 'validate_roa_empirical_analysis'):
            with self.subTest(module=name):
                result = subprocess.run([sys.executable, '-B', '-m', 'scripts.'+name, '--help'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('--prelabel-manifest-sha256', result.stdout)


if __name__ == '__main__':
    unittest.main()
