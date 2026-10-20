"""Kubernetes ConfigMap and Secret parser supporting YAML/JSON manifests.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config_drift_detector.core.models import ConfigSource
from config_drift_detector.parsers.base import BaseParser

try:
    import yaml
    HAVE_PYYAML = True
except ImportError:
    HAVE_PYYAML = False


class K8sParser(BaseParser):
    """Parser for Kubernetes ConfigMap and Secret manifests."""

    def parse(self, content: str, source_path: Union[str, Path]) -> ConfigSource:
        path_obj = Path(source_path)
        name = path_obj.name

        values: Dict[str, str] = {}
        comments: Dict[str, str] = {}
        line_numbers: Dict[str, int] = {}
        metadata: Dict[str, Any] = {}

        if HAVE_PYYAML:
            try:
                documents = list(yaml.safe_load_all(content))
                for doc in documents:
                    if not isinstance(doc, dict):
                        continue
                    kind = doc.get("kind", "")
                    if kind not in ("ConfigMap", "Secret"):
                        continue

                    doc_meta = doc.get("metadata", {})
                    metadata["k8s_name"] = doc_meta.get("name", name)
                    metadata["k8s_kind"] = kind
                    metadata["k8s_namespace"] = doc_meta.get("namespace", "default")

                    # Extract data
                    data_block = doc.get("data") or {}
                    if isinstance(data_block, dict):
                        for k, v in data_block.items():
                            key_str = str(k)
                            if kind == "Secret" and isinstance(v, str) and self._is_base64(v):
                                try:
                                    decoded = base64.b64decode(v).decode("utf-8", errors="replace")
                                    values[key_str] = decoded
                                except Exception:
                                    values[key_str] = str(v)
                            else:
                                values[key_str] = str(v) if v is not None else ""

                    # Extract stringData (for Secrets)
                    string_data_block = doc.get("stringData") or {}
                    if isinstance(string_data_block, dict):
                        for k, v in string_data_block.items():
                            values[str(k)] = str(v) if v is not None else ""

            except Exception:
                # If PyYAML parse fails, fallback to line-based parser
                values = self._parse_fallback(content)
        else:
            values = self._parse_fallback(content)

        # Compute estimated line numbers
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            for key in values.keys():
                if key not in line_numbers and (stripped.startswith(f"{key}:") or stripped.startswith(f"\"{key}\":") or stripped.startswith(f"'{key}':")):
                    line_numbers[key] = i

        return ConfigSource(
            name=name,
            path=str(path_obj),
            format="k8s_configmap",
            values=values,
            comments=comments,
            line_numbers=line_numbers,
            metadata=metadata,
        )

    @staticmethod
    def _is_base64(s: str) -> bool:
        if not s or len(s) % 4 != 0:
            return False
        import re
        return bool(re.match(r"^[A-Za-z0-9+/]+={0,2}$", s))

    @staticmethod
    def _parse_fallback(content: str) -> Dict[str, str]:
        """Simple pure-Python fallback for extracting data block keys from k8s YAML."""
        values: Dict[str, str] = {}
        in_data = False
        data_indent = 0
        current_multiline_key: Optional[str] = None
        multiline_buffer: List[str] = []
        multiline_indent = 0

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())

            # Check if document resets
            if stripped == "---":
                in_data = False
                continue

            if stripped in ("data:", "stringData:"):
                in_data = True
                data_indent = indent
                continue

            if in_data:
                if indent <= data_indent and not stripped.startswith("-"):
                    # Exited data block
                    in_data = False
                    if current_multiline_key:
                        values[current_multiline_key] = "\n".join(multiline_buffer)
                        current_multiline_key = None
                        multiline_buffer = []
                    continue

                if current_multiline_key:
                    if indent > multiline_indent:
                        multiline_buffer.append(line.strip())
                        continue
                    else:
                        values[current_multiline_key] = "\n".join(multiline_buffer)
                        current_multiline_key = None
                        multiline_buffer = []

                if ":" in stripped:
                    k, rest = stripped.split(":", 1)
                    k = k.strip().strip('"').strip("'")
                    rest = rest.strip()
                    if rest in ("|", ">", "|-", ">-"):
                        current_multiline_key = k
                        multiline_indent = indent
                        multiline_buffer = []
                    else:
                        v = rest.strip('"').strip("'")
                        values[k] = v

        if current_multiline_key:
            values[current_multiline_key] = "\n".join(multiline_buffer)

        return values
