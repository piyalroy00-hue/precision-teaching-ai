"""Non-executing validation helpers for generated instructional content."""
import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    message: str | None = None


@dataclass(frozen=True)
class GeneratedPracticeQuestion:
    question: str
    options: tuple[str, ...]
    correct_answer: str
    explanation: str
    difficulty: str


def validate_python_example(example: str) -> ValidationResult:
    """Parse generated Python without executing it on the application host."""
    if not example.strip():
        return ValidationResult(False, "Generated Python example is empty.")
    try:
        ast.parse(example)
    except SyntaxError as exc:
        return ValidationResult(False, f"Generated Python syntax is invalid: {exc.msg}")
    return ValidationResult(True)


def validate_practice_question(question: GeneratedPracticeQuestion) -> ValidationResult:
    """Validate structured educational questions without executing supplied code."""
    if not question.question.strip() or not question.explanation.strip():
        return ValidationResult(False, "Question text and explanation are required.")
    if question.difficulty not in {"Easy", "Medium", "Hard"}:
        return ValidationResult(False, "Question difficulty must be Easy, Medium, or Hard.")
    if len(question.options) < 2 or len(set(question.options)) != len(question.options):
        return ValidationResult(False, "Question options must contain at least two unique choices.")
    if question.correct_answer not in question.options:
        return ValidationResult(False, "Correct answer must match exactly one provided option.")
    return ValidationResult(True)