# env-drift-sentinel

`env-drift-sentinel` is a lightweight Python CLI tool that audits `.env` files against `.env.example` templates and active OS environment variables for configuration drift, missing keys, format discrepancies, and secret leakage.

## Features

- **Missing Key Detection**: Detects variables present in example or base configurations but absent in target environments.
- **Extra Key Detection**: Detects unexpected variables present in target environments.
- **Format Discrepancies**: Identifies type mismatches (e.g., boolean vs string, integer, float, URL, email).
- **Secret Leakage Scanning**: Scans for potential secrets (API keys, tokens, passwords) using security heuristics.
- **Strict Mode Support**: Returns non-zero exit code on drift or errors for CI/CD integration.
- **Multiple Output Formats**: Supports human-readable Markdown and structured JSON reporting.

## Installation

```bash
pip install .
```

## Usage

Run audit using Python script:

```bash
python env_drift_sentinel.py --example .env.example --target .env --strict --report-format markdown
```

Or via installed CLI entry point:

```bash
env-drift-sentinel --example .env.example --target .env
```

## License

[MIT](LICENSE)
