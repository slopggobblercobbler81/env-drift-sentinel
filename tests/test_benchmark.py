"""Benchmark tests for large .env file scanning and audit latency."""

import os
import tempfile
import time
from env_drift_sentinel import parse_env_file, audit, compare_environments


def _generate_large_env_content(entry_count: int) -> str:
    """Generate mock .env content with diverse variable types and occasional secrets."""
    lines = [
        "# Large benchmark environment configuration file",
        "# Auto-generated for performance testing",
    ]
    for i in range(entry_count):
        if i % 10 == 0:
            lines.append(f"# Section {i // 10}")
        if i % 25 == 0:
            lines.append(f"SERVICE_{i}_API_KEY=ghp_{'A' * 36}")
        elif i % 5 == 0:
            lines.append(f"SERVICE_{i}_ENABLED=true")
        elif i % 3 == 0:
            lines.append(f"SERVICE_{i}_PORT={3000 + (i % 1000)}")
        elif i % 2 == 0:
            lines.append(f"SERVICE_{i}_URL=https://api.internal.service{i}.net/v1")
        else:
            lines.append(f"SERVICE_{i}_NAME='microservice-worker-{i}'")
    return "\n".join(lines) + "\n"


def test_large_env_parse_latency():
    """Verify that parsing a large .env file with 5,000 entries executes within 1.0 second."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = os.path.join(tmpdir, ".env.large")
        content = _generate_large_env_content(5000)
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)

        start_time = time.perf_counter()
        parsed = parse_env_file(env_path)
        elapsed = time.perf_counter() - start_time

        assert len(parsed) == 5000
        # Parsing 5,000 lines should easily complete under 1.0s
        assert elapsed < 1.0


def test_large_env_audit_latency():
    """Verify that scanning and auditing drift between large .env files executes efficiently."""
    with tempfile.TemporaryDirectory() as tmpdir:
        example_path = os.path.join(tmpdir, ".env.example")
        target_path = os.path.join(tmpdir, ".env.target")

        example_content = _generate_large_env_content(3000)
        # Target has 3000 entries plus extra entries
        target_content = _generate_large_env_content(3200)

        with open(example_path, "w", encoding="utf-8") as f:
            f.write(example_content)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(target_content)

        start_time = time.perf_counter()
        report = audit(example_path, target_path)
        elapsed = time.perf_counter() - start_time

        assert isinstance(report, dict)
        assert len(report["extra_in_target"]) == 200
        assert len(report["missing_in_target"]) == 0
        assert len(report["leakage"]) > 0
        # Auditing 3,000+ entries with secret scans should finish in under 2.0s
        assert elapsed < 2.0


def test_large_env_comparison_throughput():
    """Verify compare_environments throughput on 2,000 pairs of environment variables."""
    base_env = {f"KEY_{i}": (f"value_{i}", i) for i in range(2000)}
    target_env = {f"KEY_{i}": (f"value_{i}" if i % 4 != 0 else f"modified_{i}", i) for i in range(2000)}

    start_time = time.perf_counter()
    diff = compare_environments(base_env, target_env, "production")
    elapsed = time.perf_counter() - start_time

    assert diff["target"] == "production"
    assert len(diff["missing_variables"]) == 0
    assert len(diff["unexpected_variables"]) == 0
    # Modified entries should be in value_mismatches (every 4th entry = 500 entries)
    assert len(diff["value_mismatches"]) == 500
    assert elapsed < 1.0
