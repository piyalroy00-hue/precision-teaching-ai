import pytest

from app.ai.tutor import (
    TutorContext,
    TutorNotConfiguredError,
    TutorOutput,
    TutorService,
)


class CapturingProvider:
    def __init__(self):
        self.context: TutorContext | None = None

    def generate(self, context: TutorContext) -> TutorOutput:
        self.context = context
        return TutorOutput(
            explanation="An explanation.", example="print('example')", step_by_step="Step one.",
            hint="Try the base case.", practice_question="What stops recursion?",
            correct_answer="A base case.", feedback="Review the stopping condition.",
        )


def test_tutor_service_passes_learner_model_context_to_provider():
    provider = CapturingProvider()
    context = TutorContext(
        subject="Python Programming", topic="Recursion", subtopic="Base case",
        mastery_probability=0.31, mastery_level="Beginner", difficulty="Easy",
        learning_objective="Explain why a recursive function stops.",
        prerequisite_concepts=("Function Definition",), previous_errors=("Missing base case",),
        learning_session_id=12,
    )

    output = TutorService(provider).generate_instruction(context)

    assert provider.context is context
    assert output.correct_answer == "A base case."


def test_tutor_service_requires_an_explicit_provider():
    context = TutorContext(
        subject="Python Programming", topic="Recursion", subtopic=None,
        mastery_probability=0.31, mastery_level="Beginner", difficulty="Easy",
        learning_objective="Explain a base case.",
    )

    with pytest.raises(TutorNotConfiguredError):
        TutorService().generate_instruction(context)


def test_tutor_context_rejects_invalid_mastery():
    with pytest.raises(ValueError):
        TutorContext(
            subject="Python Programming", topic="Recursion", subtopic=None,
            mastery_probability=1.1, mastery_level="Mastered", difficulty="Hard",
            learning_objective="Explain recursion.",
        )