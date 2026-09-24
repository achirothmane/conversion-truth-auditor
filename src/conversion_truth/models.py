from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class Source(str, Enum):
    TRUTH = "TRUTH"
    GA4 = "GA4"


class Classification(str, Enum):
    MATCH = "MATCH"
    DUPLICATE = "DUPLICATE"
    MISSING = "MISSING"
    PHANTOM = "PHANTOM"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class ConversionRecord:
    source: Source
    event_type: str
    timestamp: datetime
    value: Decimal
    currency: str
    transaction_id: str | None = None
    event_id: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class Finding:
    key: str
    classification: Classification
    confidence: Confidence
    truth_count: int
    ga4_count: int
    truth_value: Decimal | None = None
    ga4_value: Decimal | None = None
    currency: str | None = None
    subtype: str | None = None
    reason: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["classification"] = self.classification.value
        data["confidence"] = self.confidence.value
        if self.truth_value is not None:
            data["truth_value"] = str(self.truth_value)
        if self.ga4_value is not None:
            data["ga4_value"] = str(self.ga4_value)
        data["evidence_ids"] = list(self.evidence_ids)
        return data
