import os
import tempfile
import json
from env_drift_sentinel import audit

def test_json_schema_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        ex_path = os.path.join(tmpdir, ".env.example")
        tar_path = os.path.join(tmpdir, ".env")

        with open(ex_path, "w") as f:
            f.write("KEY1=value1\n")
        with open(tar_path, "w") as f:
            f.write("KEY1=value1\nKEY2=value2\n")

        report = audit(ex_path, tar_path)
        
        # Verify schema structure (keys and types)
        expected_keys = {"missing_in_target", "extra_in_target", "missing_in_os", "leakage", "format_errors"}
        assert set(report.keys()) == expected_keys
        
        for k in expected_keys:
            assert isinstance(report[k], list)

        # Test JSON serialization
        json_output = json.dumps(report)
        parsed_back = json.loads(json_output)
        assert set(parsed_back.keys()) == expected_keys
