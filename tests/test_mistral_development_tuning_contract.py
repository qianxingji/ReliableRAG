from pathlib import Path
import ast
import copy
import unittest

from scripts.run_mistral_development_tuning import (
    EXPECTED_CAL_TRACES,
    EXPECTED_FIT_ATTEMPTS,
    EXPECTED_FIT_TRACES,
    EXPECTED_TRACES,
    METHODS,
    assemble_inputs,
)
from scripts.validate_mistral_development_tuning import (
    comparable,
    compare,
    replay_variant,
    validate_events,
)
from src.arbitration.mistral_reader_runtime import object_sha256
from src.arbitration.reader_development_tuning import tune_recovery_head


def source_rows():
    prelabels = []; outcomes = []; position = 0
    for dataset_index, dataset in enumerate(("hotpotqa", "2wikimultihopqa", "musique")):
        for question in range(1_500):
            role = "fit" if question < 1_200 else "cal"
            for retriever_index, retriever in enumerate(("bm25", "dense", "hybrid")):
                signal = ((question + dataset_index) % 19 - 9) / 10
                hgb = 1 / (1 + pow(2.718281828, -signal))
                margin = signal / 2 + (retriever_index - 1) / 10
                identity = {
                    "dataset": dataset, "retriever": retriever,
                    "sample_id": f"{dataset}-{question:04d}",
                    "position": position, "role": role,
                }
                prelabel = {
                    **identity, "pair_eligible": True,
                    "eligible": (question + dataset_index) % 23 != 0,
                    "forced_keep_reason": None,
                    "hgb_score": hgb, "gbv_F0": 0.4,
                    "gbv_F1": 0.4 + margin, "gbv_margin": margin,
                    "feature_vectors": {
                        "HGB_GBV_R": [hgb, margin],
                        "HGB_ONLY_R": [hgb], "GBV_ONLY_R": [margin],
                    },
                    "source_bindings": {
                        "hgb_signal_row_sha256": "a" * 64,
                        "gbv_row_sha256": "b" * 64,
                    },
                }
                recovery = int(
                    (question + 2 * dataset_index + retriever_index) % 17 == 0
                )
                outcome = {
                    **identity, "prelabel_row_sha256": object_sha256(prelabel),
                    "a0_receipt_sha256": "c" * 64,
                    "a1_receipt_sha256": "d" * 64,
                    "a0_em": 0, "a1_em": recovery,
                    "a0_f1": 0.0, "a1_f1": float(recovery),
                }
                prelabels.append(prelabel); outcomes.append(outcome); position += 1
    return prelabels, outcomes


class MistralDevelopmentTuningContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prelabels, cls.outcomes = source_rows()

    def test_exact_scope_and_common_eligibility(self):
        features, outcomes, parts, counts = assemble_inputs(
            self.prelabels, self.outcomes,
        )
        self.assertEqual(EXPECTED_TRACES, 13_500)
        self.assertEqual(EXPECTED_FIT_TRACES, 10_800)
        self.assertEqual(EXPECTED_CAL_TRACES, 2_700)
        self.assertEqual(EXPECTED_FIT_ATTEMPTS, 84)
        self.assertEqual(set(features), set(METHODS))
        self.assertEqual(len(outcomes), EXPECTED_TRACES)
        self.assertEqual({role: len(keys) for role, keys in parts.items()},
                         {"fit": EXPECTED_FIT_TRACES, "cal": EXPECTED_CAL_TRACES})
        self.assertEqual(len({tuple(value.values()) for value in counts.values()}), 1)

    def test_outcome_to_prelabel_hash_mismatch_fails_closed(self):
        outcomes = copy.deepcopy(self.outcomes)
        outcomes[0]["prelabel_row_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "TUNING_SOURCE_BINDING"):
            assemble_inputs(self.prelabels, outcomes)

    def test_producer_core_and_independent_refit_agree(self):
        features, outcomes, parts, _ = assemble_inputs(self.prelabels, self.outcomes)
        produced = tune_recovery_head(
            features["HGB_ONLY_R"], outcomes, parts, "HGB_ONLY_R",
        )
        independent = replay_variant(
            features["HGB_ONLY_R"], outcomes, parts, "HGB_ONLY_R",
        )
        state = {"maximum_numeric_error": 0.0,
                 "numeric_checks": 0, "exact_checks": 0}
        compare(comparable(produced), comparable(independent), state)
        self.assertLessEqual(state["maximum_numeric_error"], 1e-10)
        self.assertEqual(produced["fit_attempts"], 28)

    def test_complete_event_journal_binds_all_three_methods(self):
        features, outcomes, parts, _ = assemble_inputs(self.prelabels, self.outcomes)
        events = []; produced = {}; independent = {}
        for method in METHODS:
            produced[method] = tune_recovery_head(
                features[method], outcomes, parts, method, events.append,
            )
            independent[method] = replay_variant(
                features[method], outcomes, parts, method,
            )
        events = [{"sequence": index, **event}
                  for index, event in enumerate(events)]
        state = {"maximum_numeric_error": 0.0,
                 "numeric_checks": 0, "exact_checks": 0}
        for method in METHODS:
            compare(comparable(produced[method]), comparable(independent[method]), state)
        validate_events(events, independent, state)
        self.assertEqual(len(events), 168)

    def test_validator_does_not_import_producer_or_tuning_core(self):
        path = (Path(__file__).resolve().parents[1]
                / "scripts/validate_mistral_development_tuning.py")
        source = path.read_text(encoding="utf-8"); tree = ast.parse(source)
        imported = {node.module for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)}
        self.assertNotIn("scripts.run_mistral_development_tuning", imported)
        self.assertNotIn("src.arbitration.reader_development_tuning", imported)
        self.assertIn("PASS_INDEPENDENT_MISTRAL_DEVELOPMENT_TUNING", source)

    def test_test_access_and_action_budget_remain_closed(self):
        root = Path(__file__).resolve().parents[1]
        producer = (root / "scripts/run_mistral_development_tuning.py").read_text(
            encoding="utf-8"
        )
        validator = (root / "scripts/validate_mistral_development_tuning.py").read_text(
            encoding="utf-8"
        )
        for source in (producer, validator):
            self.assertIn('"test_rows_read": 0', source)
            self.assertIn('"action_budget_tuned": False', source)
        self.assertIn('"test_access": "FORBIDDEN"', producer)
        self.assertIn('"action_budget_tuning": "FORBIDDEN"', producer)


if __name__ == "__main__":
    unittest.main()
