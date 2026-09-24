from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .classify import classify_group, classify_unmatched_ga4
from .decision import DecisionPolicy, evaluate
from .matcher import group_by_transaction
from .models import Classification, Confidence, Finding
from .normalize import load_ga4, load_truth


def audit(
    truth_path: str | Path,
    ga4_path: str | Path,
    policy: DecisionPolicy | None = None,
) -> dict[str, Any]:
    truth = load_truth(truth_path)
    ga4 = load_ga4(ga4_path)

    truth_groups, truth_unkeyed = group_by_transaction(truth)
    ga4_groups, ga4_unkeyed = group_by_transaction(ga4)

    findings: list[Finding] = []
    all_keys = sorted(set(truth_groups) | set(ga4_groups))
    for key in all_keys:
        findings.append(
            classify_group(key, truth_groups.get(key, []), ga4_groups.get(key, []))
        )

    for i, record in enumerate(ga4_unkeyed, start=1):
        findings.append(classify_unmatched_ga4(record, i))

    for i, record in enumerate(truth_unkeyed, start=1):
        findings.append(
            Finding(
                key=f"UNKEYED-TRUTH-{i}",
                classification=Classification.UNKNOWN,
                confidence=Confidence.LOW,
                truth_count=1,
                ga4_count=0,
                truth_value=record.value,
                currency=record.currency,
                reason="TRUTH_RECORD_WITHOUT_TRANSACTION_ID",
            )
        )

    counts = Counter(f.classification.value for f in findings)
    summary = {name.value: counts.get(name.value, 0) for name in Classification}
    decision = evaluate(findings, policy)

    return {
        "summary": summary,
        "decision": decision,
        "findings": [f.to_dict() for f in findings],
    }
