from app.ai.tutor import TutorContext, TutorOutput
import pytest

from app.services.personalized_tutor_service import (
    InvalidGeneratedContentError,
    PersonalizedTutorService,
)


class RecordingProvider:
    def __init__(self):
        self.prompt = None
        self.context = None

    def generate(self, prompt, context) -> TutorOutput:
        self.prompt = prompt
        self.context = context
        return TutorOutput("explanation", "example", "steps", "hint", "question", "answer", "feedback")


def _context() -> TutorContext:
    return TutorContext(
        subject="Python Programming", topic="Recursion", subtopic="Base case",
        mastery_probability=0.31, mastery_level="Beginner", difficulty="Easy",
        learning_objective="Explain why recursion stops.",
        prerequisite_concepts=("Function Definition",), previous_errors=("No base case",),
    )


def test_personalized_tutor_builds_a_prompt_before_calling_provider():
    provider = RecordingProvider()

    result = PersonalizedTutorService(provider).generate(_context())

    assert result.explanation == "explanation"
    assert provider.context.topic == "Recursion"
    assert provider.prompt.version == "phase3-v1"
    assert "No base case" in provider.prompt.user_instruction


def test_local_provider_personalizes_instruction_to_target_and_difficulty():
    result = PersonalizedTutorService().generate(_context())

    assert "Base case" in result.explanation
    assert "easy lesson" in result.explanation
    assert "Function Definition" in result.explanation


def test_tutor_rejects_a_provider_example_with_invalid_python():
    class InvalidExampleProvider:
        def generate(self, prompt, context) -> TutorOutput:
            return TutorOutput("explanation", "def broken(:", "steps", "hint", "question", "answer", "feedback")

    with pytest.raises(InvalidGeneratedContentError, match="syntax is invalid"):
        PersonalizedTutorService(InvalidExampleProvider()).generate(_context())