# env-drift-sentinel

<<<<<<< HEAD
`env-drift-sentinel` is a lightweight Python CLI tool that detects configuration drift between environments (staging, production, local), identifying missing variables, value format discrepancies, and unexpected overrides.

## Features

- **Missing Variables**: Detects variables present in the base environment but absent in targets.
- **Unexpected Variables**: Detects extra variables present in targets but absent in the base environment.
- **Format Discrepancies**: Identifies type mismatches (e.g., boolean vs string, integer vs string, URLs, etc.).
- **Value Mismatches**: Flags variables with differing literal values.
- **Multiple Output Formats**: Supports human-readable text and JSON output.

## Installation

```bash
pip install .
```
=======
Audits `.env` files vs `.env.example` vs running OS environment variables for missing keys, secret leakage, and format errors.
>>>>>>> 377ffc359f9f74cb82e0a5c3a225e921395495cc

## Usage

```bash
<<<<<<< HEAD
env-drift-sentinel --base production.env --target staging=staging.env --target local=.env.local
```

## License

[MIT](LICENSE)
=======
python env_drift_sentinel.py --example .env.example --target .env --strict --report-format markdown
```

## Features

- Missing key detection (`.env.example` vs `.env` vs OS environment)
- Extra key warning
- Secret leakage heuristic scanning (API keys, tokens, passwords)
- Strict mode support for CI/CD pipelines
- JSON and Markdown reports
>>>>>>> 377ffc359f9f74cb82e0a5c3a225e921395495cc


Documentation update for release.
