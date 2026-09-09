from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


V2_SCORE_FEATURES = (
    "state_symmetric_hgb",
    "state_symmetric_logistic",
    "no_cross_state",
    "no_B",
    "no_evidence_change",
    "no_answer_form",
    "ordinary_compact_logistic",
    "B_rule",
    "higher_own_likelihood",
    "likelihood_margin",
)

V2_LABELS = ("recovery", "damage", "neutral")
V2_LAMBDA_DAMAGE = 1.0
V2_META_ALPHA = 2.0
V2_ACTION_RATE = 0.05
V2_GROUP_FOLDS = 5
V2_GROUP_SEED = 20260909


@dataclass
class V2EnsembleBundle:
    """Cross-fitted damage-aware meta ensemble used to rank post-repair actions."""

    models: list[object]
    feature_names: tuple[str, ...]
    class_names: tuple[str, ...]
    lambda_damage: float
    meta_alpha: float
    action_rate: float
    hgb_reference: np.ndarray
    utility_reference: np.ndarray
    group_folds: int
    group_seed: int


def _build_meta_model() -> object:
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=4000,
            class_weight="balanced",
            C=1.0,
        ),
    )


def empirical_cdf(reference: np.ndarray, values: np.ndarray) -> np.ndarray:
    ordered = np.sort(np.asarray(reference, dtype=float))
    if len(ordered) == 0:
        raise ValueError("reference distribution cannot be empty")
    return np.searchsorted(
        ordered,
        np.asarray(values, dtype=float),
        side="right",
    ) / len(ordered)


def transition_utility(
    probabilities: np.ndarray,
    classes: Sequence[str],
    lambda_damage: float = V2_LAMBDA_DAMAGE,
) -> np.ndarray:
    class_names = list(classes)
    return (
        probabilities[:, class_names.index("recovery")]
        - lambda_damage * probabilities[:, class_names.index("damage")]
    )


def fit_crossfitted_ensemble(
    x: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    *,
    hgb_scores: np.ndarray,
    n_splits: int = V2_GROUP_FOLDS,
    seed: int = V2_GROUP_SEED,
    lambda_damage: float = V2_LAMBDA_DAMAGE,
    meta_alpha: float = V2_META_ALPHA,
    action_rate: float = V2_ACTION_RATE,
) -> tuple[V2EnsembleBundle, np.ndarray]:
    """Fit grouped fold models and return bundle plus out-of-fold fused scores.

    Each development question is scored by a model that did not train on that question.
    The same fold models are retained as an ensemble for future unseen examples, which
    avoids the old refit-then-transfer score-scale mismatch.
    """

    x = np.asarray(x, dtype=float)
    labels = np.asarray(labels)
    groups = np.asarray(groups)
    hgb_scores = np.asarray(hgb_scores, dtype=float)
    if not (len(x) == len(labels) == len(groups) == len(hgb_scores)):
        raise ValueError("x, labels, groups, and hgb_scores must have equal length")

    splitter = GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof_probabilities = np.zeros((len(x), len(V2_LABELS)), dtype=float)
    models: list[object] = []

    for train_index, valid_index in splitter.split(x, labels, groups):
        model = _build_meta_model()
        model.fit(x[train_index], labels[train_index])
        probability = model.predict_proba(x[valid_index])
        classes = list(model[-1].classes_)
        for target_column, label in enumerate(V2_LABELS):
            oof_probabilities[valid_index, target_column] = probability[
                :, classes.index(label)
            ]
        models.append(model)

    utility = transition_utility(
        oof_probabilities,
        V2_LABELS,
        lambda_damage=lambda_damage,
    )
    hgb_reference = np.sort(hgb_scores.copy())
    utility_reference = np.sort(utility.copy())
    fused = empirical_cdf(hgb_reference, hgb_scores) + meta_alpha * empirical_cdf(
        utility_reference,
        utility,
    )

    bundle = V2EnsembleBundle(
        models=models,
        feature_names=V2_SCORE_FEATURES,
        class_names=V2_LABELS,
        lambda_damage=lambda_damage,
        meta_alpha=meta_alpha,
        action_rate=action_rate,
        hgb_reference=hgb_reference,
        utility_reference=utility_reference,
        group_folds=n_splits,
        group_seed=seed,
    )
    return bundle, fused


def score_unseen(bundle: V2EnsembleBundle, x: np.ndarray) -> np.ndarray:
    """Return V2 fused ranking scores for unseen, label-free score records."""

    x = np.asarray(x, dtype=float)
    if not bundle.models:
        raise ValueError("bundle contains no fitted models")

    probabilities = np.zeros((len(x), len(bundle.class_names)), dtype=float)
    for model in bundle.models:
        model_probability = model.predict_proba(x)
        model_classes = list(model[-1].classes_)
        for target_column, label in enumerate(bundle.class_names):
            probabilities[:, target_column] += model_probability[
                :, model_classes.index(label)
            ]
    probabilities /= len(bundle.models)

    utility = transition_utility(
        probabilities,
        bundle.class_names,
        lambda_damage=bundle.lambda_damage,
    )
    hgb = x[:, bundle.feature_names.index("state_symmetric_hgb")]
    return empirical_cdf(bundle.hgb_reference, hgb) + bundle.meta_alpha * empirical_cdf(
        bundle.utility_reference,
        utility,
    )


def action_budget(trace_count: int, action_rate: float = V2_ACTION_RATE) -> int:
    if trace_count < 0:
        raise ValueError("trace_count must be non-negative")
    if not 0.0 <= action_rate <= 1.0:
        raise ValueError("action_rate must be in [0, 1]")
    return int(round(trace_count * action_rate))
