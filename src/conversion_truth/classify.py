from __future__ import annotations

from decimal import Decimal

from .models import Classification, Confidence, ConversionRecord, Finding


def _sum_values(records: list[ConversionRecord]) -> Decimal:
    return sum((r.value for r in records), Decimal("0"))


def classify_group(
    key: str,
    truth: list[ConversionRecord],
    ga4: list[ConversionRecord],
) -> Finding:
    truth_count = len(truth)
    ga4_count = len(ga4)
    truth_value = _sum_values(truth) if truth else None
    ga4_value = _sum_values(ga4) if ga4 else None
    evidence_ids = tuple(r.event_id for r in ga4 if r.event_id)
    currencies = {r.currency for r in [*truth, *ga4]}
    currency = next(iter(currencies)) if len(currencies) == 1 else None

    if truth_count and not ga4_count:
        return Finding(
            key=key,
            classification=Classification.MISSING,
            confidence=Confidence.HIGH,
            truth_count=truth_count,
            ga4_count=0,
            truth_value=truth_value,
            currency=currency,
            reason="TRUTH_TRANSACTION_WITHOUT_GA4_PURCHASE",
        )

    if ga4_count and not truth_count:
        return Finding(
            key=key,
            classification=Classification.PHANTOM,
            confidence=Confidence.HIGH,
            truth_count=0,
            ga4_count=ga4_count,
            ga4_value=ga4_value,
            currency=currency,
            reason="GA4_TRANSACTION_WITHOUT_TRUTH_TRANSACTION",
            evidence_ids=evidence_ids,
        )

    if truth_count != 1:
        return Finding(
            key=key,
            classification=Classification.UNKNOWN,
            confidence=Confidence.LOW,
            truth_count=truth_count,
            ga4_count=ga4_count,
            truth_value=truth_value,
            ga4_value=ga4_value,
            currency=currency,
            reason="NON_UNIQUE_TRUTH_TRANSACTION_ID",
            evidence_ids=evidence_ids,
        )

    if ga4_count > 1:
        return Finding(
            key=key,
            classification=Classification.DUPLICATE,
            confidence=Confidence.HIGH,
            truth_count=truth_count,
            ga4_count=ga4_count,
            truth_value=truth_value,
            ga4_value=ga4_value,
            currency=currency,
            reason="MULTIPLE_GA4_PURCHASES_FOR_ONE_TRUTH_TRANSACTION",
            evidence_ids=evidence_ids,
        )

    if ga4_count == 1:
        t, g = truth[0], ga4[0]
        if t.currency != g.currency:
            return Finding(
                key=key,
                classification=Classification.MISMATCH,
                confidence=Confidence.HIGH,
                truth_count=1,
                ga4_count=1,
                truth_value=t.value,
                ga4_value=g.value,
                currency=None,
                subtype="CURRENCY_MISMATCH",
                reason=f"TRUTH={t.currency};GA4={g.currency}",
                evidence_ids=evidence_ids,
            )
        if t.value != g.value:
            return Finding(
                key=key,
                classification=Classification.MISMATCH,
                confidence=Confidence.HIGH,
                truth_count=1,
                ga4_count=1,
                truth_value=t.value,
                ga4_value=g.value,
                currency=t.currency,
                subtype="VALUE_MISMATCH",
                reason="TRANSACTION_VALUES_DIFFER",
                evidence_ids=evidence_ids,
            )
        if t.event_type != g.event_type:
            return Finding(
                key=key,
                classification=Classification.MISMATCH,
                confidence=Confidence.HIGH,
                truth_count=1,
                ga4_count=1,
                truth_value=t.value,
                ga4_value=g.value,
                currency=t.currency,
                subtype="EVENT_TYPE_MISMATCH",
                reason=f"TRUTH={t.event_type};GA4={g.event_type}",
                evidence_ids=evidence_ids,
            )
        return Finding(
            key=key,
            classification=Classification.MATCH,
            confidence=Confidence.HIGH,
            truth_count=1,
            ga4_count=1,
            truth_value=t.value,
            ga4_value=g.value,
            currency=t.currency,
            evidence_ids=evidence_ids,
        )

    raise AssertionError("Unreachable classification state")


def classify_unmatched_ga4(record: ConversionRecord, index: int) -> Finding:
    key = record.event_id or f"UNKEYED-GA4-{index}"
    return Finding(
        key=key,
        classification=Classification.UNKNOWN,
        confidence=Confidence.LOW,
        truth_count=0,
        ga4_count=1,
        ga4_value=record.value,
        currency=record.currency,
        reason="NO_TRANSACTION_ID",
        evidence_ids=(record.event_id,) if record.event_id else (),
    )
