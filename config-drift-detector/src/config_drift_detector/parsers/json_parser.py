"""JSON configuration file parser with key flattening support.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from config_drift_detector.core.models import ConfigSource
from config_drift_detector.parsers.base import BaseParser


class JsonParser(BaseParser):
    """Parser for JSON configuration files."""

    def __init__(self, flatten_delimiter: str = "_", uppercase: bool = True):
        self.flatten_delimiter = flatten_delimiter
        self.uppercase = uppercase

    def parse(self, content: str, source_path: Union[str, Path]) -> ConfigSource:
        path_obj = Path(source_path)
        name = path_obj.name

        try:
            data = json.loads(content)
        except Exception as e:
            raise ValueError(f"Invalid JSON in {source_path}: {e}")

        values: Dict[str, str] = {}
        line_numbers: Dict[str, int] = {}

        if isinstance(data, dict):
            self._flatten_dict(data, "", values)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    self._flatten_dict(item, f"ITEM_{idx}", values)
                else:
                    values[f"ITEM_{idx}"] = str(item)

        # Estimate line numbers
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            for key in values.keys():
                if key not in line_numbers and f'"{key}"' in stripped:
                    line_numbers[key] = i

        return ConfigSource(
            name=name,
            path=str(path_obj),
            format="json",
            values=values,
            line_numbers=line_numbers,
            metadata={"raw_type": type(data).__name__},
        )

    def _flatten_dict(self, d: Dict[str, Any], prefix: str, out: Dict[str, str]) -> None:
        for k, v in d.items():
            key_name = f"{prefix}{self.flatten_delimiter}{k}" if prefix else str(k)
            if self.uppercase:
                key_name = key_name.upper()

            if isinstance(v, dict):
                self._flatten_dict(v, key_name, out)
            elif isinstance(v, list):
                out[key_name] = json.dumps(v)
            elif v is None:
                out[key_name] = ""
            elif isinstance(v, bool):
                out[key_name] = "true" if v else "false"
            else:
                out[key_name] = str(v)
