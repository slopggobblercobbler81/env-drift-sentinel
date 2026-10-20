"""Rule evaluators for configuration values, placeholders, secrets, and formats.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# Common placeholder patterns
PLACEHOLDER_REGEXES = [
    re.compile(r"^\$\{[a-zA-Z0-9_:-]+\}$"),                    # ${VARIABLE} or ${VAR:default}
    re.compile(r"^<[a-zA-Z0-9_\s-]+>$"),                       # <YOUR_API_KEY>
    re.compile(r"^\[[a-zA-Z0-9_\s-]+\]$"),                     # [INSERT_KEY]
    re.compile(r"^(?i)change[_-]?me$"),                        # CHANGEME, change_me
    re.compile(r"^(?i)todo$"),                                 # TODO
    re.compile(r"^(?i)fixme$"),                                # FIXME
    re.compile(r"^(?i)xxx+$"),                                 # XXX
    re.compile(r"^(?i)replace[_-]?me.*$"),                     # REPLACE_ME
    re.compile(r"^(?i)your[_-]?(?:api[_-]?key|secret|token|password|name|email|id)[_-]?here$"),
    re.compile(r"^(?i)(?:dummy|example|test|sample)[_-]?(?:key|secret|token|pass.*)$"),
    re.compile(r"^(?i)00000000-0000-0000-0000-000000000000$"), # Null UUID
    re.compile(r"^(?i)https?://example\.com(?:/.*)?$"),       # example.com URLs in prod
]

# Sensitive keys patterns
SECRET_KEY_REGEX = re.compile(
    r"(?i)(password|passwd|pwd|secret|private[_-]?key|api[_-]?key|token|auth[_-]?token|"
    r"jwt|bearer|credential|client[_-]?secret|access[_-]?key|encryption[_-]?key)"
)

# Known high-confidence token prefixes
HIGH_CONFIDENCE_SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN (?:RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY-----"), "Private cryptographic key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token"),
    (re.compile(r"github_pat_[a-zA-Z0-9_]{82}"), "GitHub Fine-Grained Token"),
    (re.compile(r"sk_live_[0-9a-zA-Z]{24,}"), "Stripe Live Secret Key"),
    (re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"), "Slack Token"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "JSON Web Token (JWT)"),
]


def is_unresolved_placeholder(value: str) -> Tuple[bool, Optional[str]]:
    """Checks if a configuration value contains an unresolved placeholder string."""
    if not value:
        return False, None
    val_clean = value.strip().strip('"').strip("'").strip()
    for regex in PLACEHOLDER_REGEXES:
        if regex.match(val_clean):
            return True, f"Value matches placeholder pattern '{regex.pattern}'"
    return False, None


def is_empty_value(value: Optional[str]) -> bool:
    """Checks if a value is None, empty, or whitespace only."""
    if value is None:
        return True
    return len(value.strip()) == 0


def detect_suspicious_secret(key: str, value: str) -> Tuple[bool, Optional[str]]:
    """Detects if a key-value pair exposes a sensitive secret in plaintext."""
    if not value or is_unresolved_placeholder(value)[0]:
        return False, None

    val_clean = value.strip().strip('"').strip("'")
    if len(val_clean) < 6:
        # Values shorter than 6 chars are unlikely to be live sensitive tokens
        return False, None

    # Check for known high-confidence token patterns
    for pattern, desc in HIGH_CONFIDENCE_SECRET_PATTERNS:
        if pattern.search(val_clean):
            return True, f"Contains unmasked credential ({desc})"

    # Check key name and value complexity
    if SECRET_KEY_REGEX.search(key):
        # Ignore obvious local test passwords or placeholders
        test_indicators = {"local", "test", "dev", "default", "none", "null", "false", "true", "mock"}
        if val_clean.lower() in test_indicators:
            return False, None
        if len(val_clean) >= 12:
            return True, f"Key '{key}' matches sensitive keyword and holds a secret value"

    return False, None


def detect_type_mismatch(baseline: str, target: str) -> Tuple[bool, Optional[str]]:
    """Detects if target value diverges in inferred type from baseline value."""
    if not baseline or not target:
        return False, None

    b_val = baseline.strip().strip('"').strip("'")
    t_val = target.strip().strip('"').strip("'")

    # Boolean check
    bool_true = {"true", "1", "yes", "on"}
    bool_false = {"false", "0", "no", "off"}
    b_is_bool = b_val.lower() in (bool_true | bool_false)
    t_is_bool = t_val.lower() in (bool_true | bool_false)
    if b_is_bool and not t_is_bool and not is_unresolved_placeholder(t_val)[0]:
        return True, f"Expected boolean value like '{b_val}', received '{t_val}'"

    # Integer check
    b_is_int = b_val.isdigit() or (b_val.startswith("-") and b_val[1:].isdigit())
    t_is_int = t_val.isdigit() or (t_val.startswith("-") and t_val[1:].isdigit())
    if b_is_int and not t_is_int and not is_unresolved_placeholder(t_val)[0]:
        return True, f"Expected integer value like '{b_val}', received non-numeric '{t_val}'"

    # URL check
    b_is_url = b_val.startswith("http://") or b_val.startswith("https://")
    t_is_url = t_val.startswith("http://") or t_val.startswith("https://")
    if b_is_url and not t_is_url and not is_unresolved_placeholder(t_val)[0]:
        return True, f"Expected URL starting with http:// or https://, received '{t_val}'"

    return False, None
