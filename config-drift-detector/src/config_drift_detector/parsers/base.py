"""Base parser interface for configuration sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from config_drift_detector.core.models import ConfigSource


class BaseParser(ABC):
    """Abstract base class for all configuration source parsers."""

    @abstractmethod
    def parse(self, content: str, source_path: Union[str, Path]) -> ConfigSource:
        """Parses content string into a ConfigSource."""
        pass

    def parse_file(self, file_path: Union[str, Path]) -> ConfigSource:
        """Reads file and invokes parse."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        content = p.read_text(encoding="utf-8", errors="replace")
        return self.parse(content, p)
