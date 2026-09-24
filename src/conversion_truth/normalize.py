from __future__ import annotations

import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import ConversionRecord, Source


PAID_STATUSES = {"paid", "completed", "captured", "settled"}


def normalize_id(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value.upper() if value else None


def normalize_currency(value: str | None) -> str:
    value = (value or "").strip().upper()
    if len(value) != 3:
        raise ValueError(f"Invalid currency: {value!r}")
    return value


def normalize_event_type(value: str | None) -> str:
    value = (value or "").strip().lower()
    aliases = {
        "purchase": "purchase",
        "purchased": "purchase",
        "order": "purchase",
        "sale": "purchase",
        "lead": "lead",
    }
    if value not in aliases:
        raise ValueError(f"Unsupported event_type: {value!r}")
    return aliases[value]


def parse_timestamp(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid decimal value: {value!r}") from exc


def load_truth(path: str | Path) -> list[ConversionRecord]:
    records: list[ConversionRecord] = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            status = (row.get("status") or "").strip().lower()
            if status and status not in PAID_STATUSES:
                continue
            records.append(
                ConversionRecord(
                    source=Source.TRUTH,
                    transaction_id=normalize_id(row.get("transaction_id")),
                    event_id=None,
                    event_type=normalize_event_type(row.get("event_type")),
                    timestamp=parse_timestamp(row["timestamp"]),
                    value=parse_decimal(row["value"]),
                    currency=normalize_currency(row.get("currency")),
                    status=status or None,
                )
            )
    return records


def load_ga4(path: str | Path) -> list[ConversionRecord]:
    records: list[ConversionRecord] = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            records.append(
                ConversionRecord(
                    source=Source.GA4,
                    transaction_id=normalize_id(row.get("transaction_id")),
                    event_id=normalize_id(row.get("event_id")),
                    event_type=normalize_event_type(row.get("event_type")),
                    timestamp=parse_timestamp(row["timestamp"]),
                    value=parse_decimal(row["value"]),
                    currency=normalize_currency(row.get("currency")),
                )
            )
    return records
