"""Data models for configuration drift detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DriftType(str, Enum):
    """Types of configuration drift and anomalies."""
    MISSING_IN_TARGET = "MISSING_IN_TARGET"
    EXTRA_IN_TARGET = "EXTRA_IN_TARGET"
    UNRESOLVED_PLACEHOLDER = "UNRESOLVED_PLACEHOLDER"
    EMPTY_VALUE = "EMPTY_VALUE"
    VALUE_DRIFT = "VALUE_DRIFT"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    SUSPICIOUS_SECRET = "SUSPICIOUS_SECRET"


class Severity(str, Enum):
    """Severity levels for drift findings."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ConfigSource:
    """Represents a loaded configuration source (.env, k8s configmap, json, etc.)."""
    name: str
    path: str
    format: str
    values: Dict[str, str] = field(default_factory=dict)
    comments: Dict[str, str] = field(default_factory=dict)
    line_numbers: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.values.get(key, default)

    def contains(self, key: str) -> bool:
        return key in self.values

    @property
    def keys(self) -> List[str]:
        return sorted(self.values.keys())

    @property
    def count(self) -> int:
        return len(self.values)


@dataclass
class DriftItem:
    """Represents an individual drift occurrence or config issue."""
    key: str
    drift_type: DriftType
    severity: Severity
    message: str
    baseline_value: Optional[str] = None
    target_value: Optional[str] = None
    baseline_source: str = ""
    target_source: str = ""
    line_number: Optional[int] = None
    recommendation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "drift_type": self.drift_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "baseline_value": self.baseline_value,
            "target_value": self.target_value,
            "baseline_source": self.baseline_source,
            "target_source": self.target_source,
            "line_number": self.line_number,
            "recommendation": self.recommendation,
        }


@dataclass
class DriftReport:
    """Result of comparing a baseline configuration to a target configuration."""
    baseline: ConfigSource
    target: ConfigSource
    items: List[DriftItem] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return len(self.items) > 0

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.items if item.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.items if item.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for item in self.items if item.severity == Severity.INFO)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0

    def by_type(self, drift_type: DriftType) -> List[DriftItem]:
        return [item for item in self.items if item.drift_type == drift_type]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline": {
                "name": self.baseline.name,
                "path": self.baseline.path,
                "format": self.baseline.format,
                "total_keys": self.baseline.count,
            },
            "target": {
                "name": self.target.name,
                "path": self.target.path,
                "format": self.target.format,
                "total_keys": self.target.count,
            },
            "summary": {
                "total_drift_items": len(self.items),
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
                "has_drift": self.has_drift,
            },
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class MatrixReport:
    """Comparison matrix across multiple configuration sources."""
    sources: List[ConfigSource]
    all_keys: List[str]
    matrix: Dict[str, Dict[str, Optional[str]]]
    status_per_key: Dict[str, str]
    items: List[DriftItem] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return any(status != "OK" for status in self.status_per_key.values()) or len(self.items) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "environments": [s.name for s in self.sources],
            "total_keys": len(self.all_keys),
            "keys": self.all_keys,
            "matrix": self.matrix,
            "status_per_key": self.status_per_key,
            "items": [item.to_dict() for item in self.items],
            "has_drift": self.has_drift,
        }


@dataclass
class AuditReport:
    """Audit report for a single configuration file."""
    source: ConfigSource
    items: List[DriftItem] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.items if item.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.items if item.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for item in self.items if item.severity == Severity.INFO)

    @property
    def has_issues(self) -> bool:
        return len(self.items) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": {
                "name": self.source.name,
                "path": self.source.path,
                "format": self.source.format,
                "total_keys": self.source.count,
            },
            "summary": {
                "total_issues": len(self.items),
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
                "has_issues": self.has_issues,
            },
            "items": [item.to_dict() for item in self.items],
        }
