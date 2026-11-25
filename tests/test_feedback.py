from app.ai.feedback import generate_feedback, generate_hint
from app.ai.tutor import TutorContext


def _context(previous_errors=()) -> TutorContext:
    return TutorContext(
        subject="Python Programming", topic="Recursion", subtopic="Base case",
        mastery_probability=0.31, mastery_level="Beginner", difficulty="Easy",
        learning_objective="Explain why recursion stops.",
        prerequisite_concepts=("Function Definition",), previous_errors=previous_errors,
    )


def test_hint_uses_the_most_recent_recorded_error_when_available():
    hint = generate_hint(_context(("Missing a base case",)))

    assert "Missing a base case" in hint


def test_hint_uses_prerequisite_when_no_error_is_available():
    hint = generate_hint(_context())

    assert "Function Definition" in hint


def test_feedback_changes_with_practice_correctness_without_reporting_mastery():
    correct = generate_feedback(_context(), is_correct=True)
    incorrect = generate_feedback(_context(), is_correct=False)

    assert correct.feedback.startswith("Correct.")
    assert incorrect.feedback.startswith("Not quite.")
    assert "0.31" not in correct.feedback
    assert "mastery" not in incorrect.feedback.lower()