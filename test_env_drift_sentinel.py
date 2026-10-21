import os
import tempfile
import pytest
from env_drift_sentinel import parse_env_file, infer_type, compare_environments

def test_infer_type():
    assert infer_type("true") == "boolean"
    assert infer_type("FALSE") == "boolean"
    assert infer_type("123") == "integer"
    assert infer_type("45.67") == "float"
    assert infer_type("https://example.com") == "url"
    assert infer_type("test@example.com") == "email"
    assert infer_type("hello world") == "string"

def test_parse_env_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.env"
    p.write_text("# Comment\nKEY1=value1\nKEY2=\"quoted\"\n\nKEY3=123\n")
    
    parsed = parse_env_file(str(p))
    assert parsed == {
        "KEY1": ("value1", 2),
        "KEY2": ("quoted", 3),
        "KEY3": ("123", 5)
    }

def test_compare_environments():
    base = {
        "PORT": "8080",
        "DEBUG": "false",
        "URL": "https://api.example.com",
        "SECRET": "abc"
    }
    target = {
        "PORT": "not-an-int",
        "DEBUG": "true",
        "URL": "https://api.example.com",
        "EXTRA": "extra_val"
    }
    
    res = compare_environments(base, target, "staging")
    assert res["target"] == "staging"
    assert res["missing_variables"] == ["SECRET"]
    assert res["unexpected_variables"] == ["EXTRA"]
    assert len(res["format_discrepancies"]) == 1
    assert res["format_discrepancies"][0]["key"] == "PORT"
    assert len(res["value_mismatches"]) == 1
    assert res["value_mismatches"][0]["key"] == "DEBUG"
