"""config-drift-detector: A fast CLI that detects configuration drift between environment templates, staging/prod .env files, and Kubernetes configmaps.
"""

__version__ = "0.1.0"
__author__ = "slopggobblercobbler81"

from config_drift_detector.core.models import (
    ConfigSource,
    DriftItem,
    DriftReport,
    DriftType,
    MatrixReport,
    Severity,
)
from config_drift_detector.core.engine import DriftEngine
from config_drift_detector.parsers import parse_config_file

__all__ = [
    "__version__",
    "ConfigSource",
    "DriftItem",
    "DriftReport",
    "DriftType",
    "MatrixReport",
    "Severity",
    "DriftEngine",
    "parse_config_file",
]
