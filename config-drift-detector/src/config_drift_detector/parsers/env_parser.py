"""Dotenv (.env) parser supporting quotes, exports, multiline strings, and inline comments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from config_drift_detector.core.models import ConfigSource
from config_drift_detector.parsers.base import BaseParser


class EnvParser(BaseParser):
    """Parser for .env and environment template files."""

    def parse(self, content: str, source_path: Union[str, Path]) -> ConfigSource:
        path_obj = Path(source_path)
        name = path_obj.name

        values: Dict[str, str] = {}
        comments: Dict[str, str] = {}
        line_numbers: Dict[str, int] = {}

        lines = content.splitlines()
        pending_comment: List[str] = []
        i = 0
        total_lines = len(lines)

        while i < total_lines:
            raw_line = lines[i]
            line_no = i + 1
            stripped = raw_line.strip()

            if not stripped:
                i += 1
                continue

            if stripped.startswith("#"):
                # Collect comment
                comment_text = stripped.lstrip("#").strip()
                pending_comment.append(comment_text)
                i += 1
                continue

            # Check if this line is an export or key=value
            line_to_parse = stripped
            if line_to_parse.startswith("export "):
                line_to_parse = line_to_parse[7:].strip()

            if "=" in line_to_parse:
                key_part, rest = line_to_parse.split("=", 1)
                key = key_part.strip()

                if not key or not self._is_valid_key(key):
                    i += 1
                    continue

                value, lines_consumed = self._extract_value(rest, lines, i)
                values[key] = value
                line_numbers[key] = line_no
                if pending_comment:
                    comments[key] = " ".join(pending_comment)
                    pending_comment = []

                i += lines_consumed
            else:
                # Key without assignment (e.g. KEY)
                key = line_to_parse.strip()
                if self._is_valid_key(key):
                    values[key] = ""
                    line_numbers[key] = line_no
                    if pending_comment:
                        comments[key] = " ".join(pending_comment)
                        pending_comment = []
                i += 1

        return ConfigSource(
            name=name,
            path=str(path_obj),
            format="env",
            values=values,
            comments=comments,
            line_numbers=line_numbers,
        )

    @staticmethod
    def _is_valid_key(key: str) -> bool:
        """Validates key syntax (standard shell / env var identifier)."""
        if not key:
            return False
        # Allow alphanumeric, underscore, dot, dash
        return all(c.isalnum() or c in ("_", ".", "-") for c in key)

    @classmethod
    def _extract_value(cls, initial_val: str, all_lines: List[str], current_index: int) -> Tuple[str, int]:
        """Extracts value, handling single/double quotes, multiline values, and inline comments."""
        val = initial_val.strip()

        # Check for quoted string
        if val.startswith('"'):
            # Double quoted
            return cls._consume_quoted(val, '"', all_lines, current_index)
        elif val.startswith("'"):
            # Single quoted
            return cls._consume_quoted(val, "'", all_lines, current_index)
        else:
            # Unquoted value: strip trailing inline comments if present
            # Format: KEY=val # comment
            if "#" in val:
                val = val.split("#", 1)[0].strip()
            return val, 1

    @classmethod
    def _consume_quoted(cls, first_line_val: str, quote_char: str, all_lines: List[str], start_index: int) -> Tuple[str, int]:
        """Consumes a quoted string across one or multiple lines."""
        # Check if closed on first line
        content = first_line_val[1:]  # strip leading quote
        if quote_char in content:
            # Closing quote on the same line
            end_idx = content.find(quote_char)
            # Verify it's not escaped
            while end_idx > 0 and content[end_idx - 1] == "\\":
                next_search = content.find(quote_char, end_idx + 1)
                if next_search == -1:
                    break
                end_idx = next_search

            if end_idx != -1 and (end_idx == 0 or content[end_idx - 1] != "\\"):
                extracted = content[:end_idx]
                return cls._unescape(extracted, quote_char), 1

        # Multiline quote
        collected = [content]
        lines_consumed = 1
        curr = start_index + 1
        while curr < len(all_lines):
            line = all_lines[curr]
            lines_consumed += 1
            if quote_char in line:
                end_idx = line.find(quote_char)
                collected.append(line[:end_idx])
                full_val = "\n".join(collected)
                return cls._unescape(full_val, quote_char), lines_consumed
            else:
                collected.append(line)
            curr += 1

        # If not terminated, return whatever was collected
        return cls._unescape("\n".join(collected), quote_char), lines_consumed

    @staticmethod
    def _unescape(val: str, quote_char: str) -> str:
        if quote_char == '"':
            return val.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        elif quote_char == "'":
            return val.replace("\\'", "'").replace('\\\\', '\\')
        return val
