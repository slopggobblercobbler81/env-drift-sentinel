import pytest
from env_drift_sentinel import infer_type

def test_case_insensitive_booleans():
    assert infer_type("TRUE") == "boolean"
    assert infer_type("True") == "boolean"
    assert infer_type("true") == "boolean"
    assert infer_type("FALSE") == "boolean"
    assert infer_type("False") == "boolean"
    assert infer_type("false") == "boolean"
    assert infer_type("YES") == "boolean"
    assert infer_type("Yes") == "boolean"
    assert infer_type("NO") == "boolean"
    assert infer_type("No") == "boolean"
