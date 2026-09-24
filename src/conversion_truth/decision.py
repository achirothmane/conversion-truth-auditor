from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Iterable

from .models import Classification, Confidence, Finding


class Decision(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK_TRUST = "BLOCK_TRUST"
    UNKNOWN = "UNKNOWN"


class EvidenceStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True)
class DecisionPolicy:
    """Explicit materiality policy, not an inferred claim about business loss."""

    block_error_rate: Decimal = Decimal("0.05")
    block_value_rate: Decimal = Decimal("0.05")


CONFIRMED_CLASSES = {
    Classification.DUPLICATE,
    Classification.MISSING,
    Classification.PHANTOM,
    Classification.MISMATCH,
}


def _d(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal("0")


def _add(bucket: dict[str, Decimal], currency: str | None, amount: Decimal) -> None:
    if amount <= 0:
        return
    bucket[currency or "UNSPECIFIED"] += amount


def _finding_currency(finding: Finding) -> str | None:
    return finding.currency


def _rates_by_currency(
    findings: Iterable[Finding],
) -> tuple[dict[str, Decimal], dict[str, Decimal], dict[str, Decimal], dict[str, Decimal]]:
    reported: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    over: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    under: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    unresolved: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for f in findings:
        currency = _finding_currency(f)
        truth = _d(f.truth_value)
        ga4 = _d(f.ga4_value)
        _add(reported, currency, ga4)

        if f.classification is Classification.DUPLICATE:
            _add(over, currency, max(ga4 - truth, Decimal("0")))
        elif f.classification is Classification.MISSING:
            _add(under, currency, truth)
        elif f.classification is Classification.PHANTOM:
            _add(over, currency, ga4)
        elif f.classification is Classification.MISMATCH:
            if f.subtype == "VALUE_MISMATCH":
                if ga4 > truth:
                    _add(over, currency, ga4 - truth)
                elif truth > ga4:
                    _add(under, currency, truth - ga4)
        elif f.classification is Classification.UNKNOWN:
            _add(unresolved, currency, ga4 or truth)

    return dict(reported), dict(over), dict(under), dict(unresolved)


def evaluate(findings: list[Finding], policy: DecisionPolicy | None = None) -> dict:
    policy = policy or DecisionPolicy()
    counts = Counter(f.classification for f in findings)

    confirmed = [
        f for f in findings
        if f.classification in CONFIRMED_CLASSES and f.confidence is Confidence.HIGH
    ]
    unknown = [f for f in findings if f.classification is Classification.UNKNOWN]
    evaluable = [f for f in findings if f.classification is not Classification.UNKNOWN]

    error_rate = (
        Decimal(len(confirmed)) / Decimal(len(evaluable))
        if evaluable
        else None
    )

    reported, over, under, unresolved = _rates_by_currency(findings)
    discrepancy = {
        currency: over.get(currency, Decimal("0")) + under.get(currency, Decimal("0"))
        for currency in set(over) | set(under)
    }

    value_rates: dict[str, Decimal] = {}
    for currency, amount in discrepancy.items():
        denominator = reported.get(currency, Decimal("0"))
        if denominator > 0:
            value_rates[currency] = amount / denominator

    material_by_count = error_rate is not None and error_rate >= policy.block_error_rate
    material_by_value = any(rate >= policy.block_value_rate for rate in value_rates.values())

    if not evaluable:
        decision = Decision.UNKNOWN
        reason = "NO_EVALUABLE_TRANSACTION_GROUPS"
    elif not confirmed:
        if unknown:
            decision = Decision.UNKNOWN
            reason = "NO_CONFIRMED_ERRORS_BUT_EVIDENCE_GAPS_REMAIN"
        else:
            decision = Decision.PASS
            reason = "NO_CONFIRMED_MATERIAL_DISCREPANCIES"
    elif material_by_count or material_by_value:
        decision = Decision.BLOCK_TRUST
        reason = "CONFIRMED_DISCREPANCIES_EXCEED_EXPLICIT_MATERIALITY_POLICY"
    else:
        decision = Decision.WARN
        reason = "CONFIRMED_DISCREPANCIES_BELOW_BLOCKING_MATERIALITY_POLICY"

    if not evaluable:
        evidence_status = EvidenceStatus.INSUFFICIENT
    elif unknown:
        evidence_status = EvidenceStatus.PARTIAL
    else:
        evidence_status = EvidenceStatus.COMPLETE

    def decmap(values: dict[str, Decimal]) -> dict[str, str]:
        return {k: str(v) for k, v in sorted(values.items())}

    def ratemap(values: dict[str, Decimal]) -> dict[str, str]:
        return {k: f"{(v * Decimal('100')):.2f}%" for k, v in sorted(values.items())}

    return {
        "decision": decision.value,
        "reason": reason,
        "evidence_status": evidence_status.value,
        "confirmed_discrepancies": len(confirmed),
        "unknown_groups": len(unknown),
        "evaluable_groups": len(evaluable),
        "confirmed_error_rate": f"{(error_rate * Decimal('100')):.2f}%" if error_rate is not None else None,
        "value": {
            "ga4_reported": decmap(reported),
            "confirmed_overreported": decmap(over),
            "confirmed_underreported": decmap(under),
            "confirmed_discrepancy": decmap(discrepancy),
            "unresolved": decmap(unresolved),
            "confirmed_discrepancy_rate_vs_ga4_reported": ratemap(value_rates),
        },
        "policy": {
            "block_error_rate": f"{(policy.block_error_rate * Decimal('100')):.2f}%",
            "block_value_rate": f"{(policy.block_value_rate * Decimal('100')):.2f}%",
        },
        "class_counts": {name.value: counts.get(name, 0) for name in Classification},
    }
