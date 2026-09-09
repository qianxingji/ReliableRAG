from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class RankedTrace:
    """Minimal score record used by post-repair budget selection."""

    sample_id: str
    dataset: str
    retriever: str
    score: float

    @property
    def stratum(self) -> tuple[str, str]:
        return (self.dataset, self.retriever)


@dataclass(frozen=True)
class TransitionOutcome:
    """Gold-derived transition fields for evaluation only, never runtime scoring."""

    a0_em: int
    a1_em: int
    a0_f1: float
    a1_f1: float

    @property
    def recovery(self) -> int:
        return int(self.a0_em == 0 and self.a1_em == 1)

    @property
    def damage(self) -> int:
        return int(self.a0_em == 1 and self.a1_em == 0)

    @property
    def net(self) -> int:
        return self.recovery - self.damage

    @property
    def em_delta(self) -> float:
        return float(self.a1_em - self.a0_em)

    @property
    def f1_delta(self) -> float:
        return float(self.a1_f1 - self.a0_f1)


def deterministic_rank(records: Iterable[RankedTrace]) -> list[RankedTrace]:
    """Rank descending by score with a stable, label-free lexical tie break."""

    return sorted(
        records,
        key=lambda r: (-r.score, r.dataset, r.retriever, r.sample_id),
    )


def select_global_budget(records: Iterable[RankedTrace], budget: int) -> list[RankedTrace]:
    """Select the top-scoring traces under one global action budget."""

    if budget < 0:
        raise ValueError("budget must be non-negative")
    ranked = deterministic_rank(records)
    if budget > len(ranked):
        raise ValueError(f"budget={budget} exceeds scorable record count={len(ranked)}")
    return ranked[:budget]


def select_stratum_budgets(
    records: Iterable[RankedTrace],
    budgets: Mapping[tuple[str, str], int],
) -> list[RankedTrace]:
    """Select top-scoring traces separately within dataset x retriever strata."""

    groups: dict[tuple[str, str], list[RankedTrace]] = {}
    for record in records:
        groups.setdefault(record.stratum, []).append(record)

    selected: list[RankedTrace] = []
    for stratum in sorted(budgets):
        budget = budgets[stratum]
        if budget < 0:
            raise ValueError(f"negative budget for {stratum}: {budget}")
        ranked = deterministic_rank(groups.get(stratum, []))
        if budget > len(ranked):
            raise ValueError(
                f"budget={budget} for {stratum} exceeds scorable count={len(ranked)}"
            )
        selected.extend(ranked[:budget])
    return selected


def two_head_utility(p_recovery: float, p_damage: float, lambda_damage: float) -> float:
    """Expected adoption utility for the proposed V2 two-head selector."""

    if lambda_damage < 0:
        raise ValueError("lambda_damage must be non-negative")
    for name, value in (("p_recovery", p_recovery), ("p_damage", p_damage)):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must lie in [0, 1]")
    return p_recovery - lambda_damage * p_damage


def four_state_utility(
    probabilities: Mapping[str, float],
    lambda_damage: float,
) -> float:
    """Expected utility from transition probabilities over 00, 01, 10, 11.

    Only 01 contributes recovery benefit and 10 contributes damage cost. 00 and 11
    are neutral for normalized exact-match utility, while still being useful states for
    learning whether a replacement is likely to be unproductive.
    """

    required = {"00", "01", "10", "11"}
    if set(probabilities) != required:
        raise ValueError(f"probabilities must contain exactly {sorted(required)}")
    if lambda_damage < 0:
        raise ValueError("lambda_damage must be non-negative")
    total = sum(probabilities.values())
    if any(v < 0.0 or v > 1.0 for v in probabilities.values()):
        raise ValueError("all state probabilities must lie in [0, 1]")
    if abs(total - 1.0) > 1e-8:
        raise ValueError(f"state probabilities must sum to 1, got {total}")
    return probabilities["01"] - lambda_damage * probabilities["10"]


def summarize_selection(
    selected: Sequence[RankedTrace],
    outcomes: Mapping[tuple[str, str, str], TransitionOutcome],
) -> dict[str, float | int]:
    """Summarize selected actions using evaluation-only outcome records."""

    recovery = 0
    damage = 0
    em_delta = 0.0
    f1_delta = 0.0
    for row in selected:
        key = (row.sample_id, row.dataset, row.retriever)
        outcome = outcomes[key]
        recovery += outcome.recovery
        damage += outcome.damage
        em_delta += outcome.em_delta
        f1_delta += outcome.f1_delta
    return {
        "actions": len(selected),
        "recovery": recovery,
        "damage": damage,
        "net": recovery - damage,
        "sum_em_delta": em_delta,
        "sum_f1_delta": f1_delta,
    }
