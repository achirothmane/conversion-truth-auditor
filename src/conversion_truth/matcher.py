from __future__ import annotations

from collections import defaultdict

from .models import ConversionRecord


def group_by_transaction(records: list[ConversionRecord]) -> tuple[dict[str, list[ConversionRecord]], list[ConversionRecord]]:
    grouped: dict[str, list[ConversionRecord]] = defaultdict(list)
    unmatched: list[ConversionRecord] = []
    for record in records:
        if record.transaction_id:
            grouped[record.transaction_id].append(record)
        else:
            unmatched.append(record)
    return dict(grouped), unmatched
