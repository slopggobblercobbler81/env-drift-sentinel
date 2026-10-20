import os
import re
import sys
import argparse
<<<<<<< HEAD
from typing import Dict, Any, List, Tuple

def parse_env_file(filepath: str) -> Dict[str, str]:
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                env_vars[key] = val
    return env_vars

def infer_type(val: str) -> str:
    if val.lower() in ('true', 'false', 'yes', 'no', '1', '0'):
        return 'boolean'
    try:
        int(val)
        return 'integer'
    except ValueError:
        pass
    try:
        float(val)
        return 'float'
    except ValueError:
        pass
    if re.match(r'^https?://', val, re.IGNORECASE):
        return 'url'
    if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', val):
        return 'email'
    return 'string'

def compare_environments(base_env: Dict[str, str], target_env: Dict[str, str], target_name: str) -> Dict[str, Any]:
    base_keys = set(base_env.keys())
    target_keys = set(target_env.keys())

    missing = sorted(list(base_keys - target_keys))
    unexpected = sorted(list(target_keys - base_keys))
    common = base_keys.intersection(target_keys)

    format_discrepancies = []
    value_mismatches = []

    for k in sorted(list(common)):
        b_val = base_env[k]
        t_val = target_env[k]
        b_type = infer_type(b_val)
        t_type = infer_type(t_val)

        if b_type != t_type:
            format_discrepancies.append({
                "key": k,
                "base_value": b_val,
                "base_type": b_type,
                "target_value": t_val,
                "target_type": t_type
            })
        elif b_val != t_val:
            value_mismatches.append({
                "key": k,
                "base_value": b_val,
                "target_value": t_val
            })

    return {
        "target": target_name,
        "missing_variables": missing,
        "unexpected_variables": unexpected,
        "format_discrepancies": format_discrepancies,
        "value_mismatches": value_mismatches
    }

def main():
    parser = argparse.ArgumentParser(description="Detect configuration drift between environment files.")
    parser.add_argument("--base", required=True, help="Base environment file (e.g., production.env)")
    parser.add_argument("--target", required=True, action='append', help="Target environment file to compare, format name=filepath (e.g., staging=staging.env)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()

    base_env = parse_env_file(args.base)
    if not base_env and not os.path.exists(args.base):
        print(f"Error: Base environment file '{args.base}' not found.", file=sys.stderr)
        sys.exit(1)

    results = []
    for t_arg in args.target:
        if "=" not in t_arg:
            print(f"Error: Target format must be name=filepath, got '{t_arg}'", file=sys.stderr)
            sys.exit(1)
        name, filepath = t_arg.split("=", 1)
        target_env = parse_env_file(filepath)
        if not target_env and not os.path.exists(filepath):
            print(f"Error: Target environment file '{filepath}' not found.", file=sys.stderr)
            sys.exit(1)
        
        res = compare_environments(base_env, target_env, name)
        results.append(res)

    if args.format == "json":
        import json
        print(json.dumps(results, indent=2))
    else:
        has_drift = False
        for res in results:
            print(f"=== Drift Analysis for: {res['target']} ===")
            if not res['missing_variables'] and not res['unexpected_variables'] and not res['format_discrepancies'] and not res['value_mismatches']:
                print("  No drift detected! Environments are fully synchronized.\n")
                continue
            
            has_drift = True
            if res['missing_variables']:
                print("  Missing Variables (present in base, absent in target):")
                for m in res['missing_variables']:
                    print(f"    - {m}")
            
            if res['unexpected_variables']:
                print("  Unexpected Variables (present in target, absent in base):")
                for u in res['unexpected_variables']:
                    print(f"    - {u}")

            if res['format_discrepancies']:
                print("  Format Discrepancies (type mismatch):")
                for f in res['format_discrepancies']:
                    print(f"    - {f['key']}: base type '{f['base_type']}' ({f['base_value']}) vs target type '{f['target_type']}' ({f['target_value']})")

            if res['value_mismatches']:
                print("  Value Mismatches:")
                for v in res['value_mismatches']:
                    print(f"    - {v['key']}: base '{v['base_value']}' vs target '{v['target_value']}'")
            print()

        if has_drift:
            sys.exit(2)

if __name__ == '__main__':
=======
import json

# Heuristics for potential secret leakage
SECRET_PATTERNS = [
    re.compile(r'sk-[a-zA-Z0-9]{20,}', re.IGNORECASE),
    re.compile(r'ghp_[a-zA-Z0-9]{36}', re.IGNORECASE),
    re.compile(r'aws_[a-zA-Z0-9]{20,}', re.IGNORECASE),
    re.compile(r'bearer\s+[a-zA-Z0-9_\-\.]{20,}', re.IGNORECASE),
    re.compile(r'password\s*=\s*[\"\']?[^\s\"\'\n]{4,}[\"\']?', re.IGNORECASE),
]

def parse_env_file(path):
    keys = {}
    if not os.path.exists(path):
        return keys
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                raise ValueError(f"Format error in {path} at line {line_num}: missing '='")
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            keys[key] = (val, line_num)
    return keys

def check_secrets(key, val):
    issues = []
    combined = f"{key}={val}"
    for pattern in SECRET_PATTERNS:
        if pattern.search(combined):
            issues.append(f"Potential secret leakage detected in key '{key}': matches security pattern")
    return issues

def audit(example_path, target_path, strict=False):
    example_keys = parse_env_file(example_path)
    target_keys = parse_env_file(target_path)
    os_env = os.environ

    missing_in_target = []
    extra_in_target = []
    missing_in_os = []
    leakage = []
    format_errors = []

    for k in example_keys:
        if k not in target_keys:
            missing_in_target.append(k)

    for k in target_keys:
        if k not in example_keys:
            extra_in_target.append(k)
        else:
            val, _ = target_keys[k]
            leaks = check_secrets(k, val)
            if leaks:
                leakage.extend(leaks)

    for k in example_keys:
        if k not in os_env and k not in target_keys:
            missing_in_os.append(k)

    return {
        "missing_in_target": missing_in_target,
        "extra_in_target": extra_in_target,
        "missing_in_os": missing_in_os,
        "leakage": leakage,
        "format_errors": format_errors
    }

def main():
    parser = argparse.ArgumentParser(description="Audit .env files for drift, leaks, and missing keys.")
    parser.add_argument("--example", default=".env.example", help="Path to example env file")
    parser.add_argument("--target", default=".env", help="Path to target env file")
    parser.add_argument("--strict", action="store_true", help="Fail with non-zero exit code on any drift/issue")
    parser.add_argument("--report-format", choices=["json", "markdown"], default="markdown", help="Report output format")

    args = parser.parse_args()

    try:
        report = audit(args.example, args.target, strict=args.strict)
    except Exception as e:
        print(f"Error during audit: {e}", file=sys.stderr)
        sys.exit(1)

    has_issues = bool(report["missing_in_target"] or report["extra_in_target"] or report["missing_in_os"] or report["leakage"] or report["format_errors"])

    if args.report_format == "json":
        print(json.dumps(report, indent=2))
    else:
        print("# Env Drift Sentinel Report\n")
        print(f"- **Example File**: `{args.example}`")
        print(f"- **Target File**: `{args.target}`")
        print(f"- **Strict Mode**: `{args.strict}`\n")

        print("## Summary of Findings")
        print(f"- **Missing in Target**: {len(report['missing_in_target'])}")
        print(f"- **Extra in Target**: {len(report['extra_in_target'])}")
        print(f"- **Missing in OS Env**: {len(report['missing_in_os'])}")
        print(f"- **Potential Leakages**: {len(report['leakage'])}")
        print(f"- **Format Errors**: {len(report['format_errors'])}\n")

        if report['missing_in_target']:
            print("### Missing Keys in Target")
            for k in report['missing_in_target']:
                print(f"- `{k}`")
            print()

        if report['leakage']:
            print("### Secret Leakages")
            for l in report['leakage']:
                print(f"- {l}")
            print()

    if args.strict and has_issues:
        sys.exit(1)

if __name__ == "__main__":
>>>>>>> 377ffc359f9f74cb82e0a5c3a225e921395495cc
    main()
