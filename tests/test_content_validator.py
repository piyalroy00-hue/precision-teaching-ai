from app.ai.content_validator import validate_python_example


def test_valid_python_example_is_accepted_without_execution():
    result = validate_python_example("def increment(value):\n    return value + 1")

    assert result.is_valid is True
    assert result.message is None


def test_invalid_python_example_is_rejected():
    result = validate_python_example("def increment(:")

    assert result.is_valid is False
    assert "syntax is invalid" in result.message