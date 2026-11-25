"""Provider-neutral boundary for the Phase 3 instruction-generation layer.

The tutor consumes a target chosen by the learner model. It never computes or
persists mastery; BKT remains the sole authority for learner modelling.
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TutorContext:
    """Minimal non-identifying learner context for an instructional request."""

    subject: str
    topic: str
    subtopic: str | None
    mastery_probability: float
    mastery_level: str
    difficulty: str
    learning_objective: str
    prerequisite_concepts: tuple[str, ...] = ()
    previous_errors: tuple[str, ...] = ()
    learning_session_id: int | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.mastery_probability <= 1.0:
            raise ValueError("mastery_probability must be within [0, 1].")


@dataclass(frozen=True)
class TutorOutput:
    """Structured instructional content returned by a configured provider."""

    explanation: str
    example: str
    step_by_step: str
    hint: str
    practice_question: str
    correct_answer: str
    feedback: str


class TutorProvider(Protocol):
    """Adapter contract implemented by a future provider-specific client."""

    def generate(self, context: TutorContext) -> TutorOutput:
        """Generate instructional content for a learner-model-selected target."""


class TutorNotConfiguredError(RuntimeError):
    """Raised until a concrete LLM provider is intentionally configured."""


class DisabledTutorProvider:
    """Safe default that prevents accidental network calls or fabricated tutoring."""

    def generate(self, context: TutorContext) -> TutorOutput:
        raise TutorNotConfiguredError(
            "No AI tutor provider is configured. Stage 2 adds prompt generation and provider setup."
        )


class TutorService:
    """Thin orchestration boundary that delegates instruction generation only."""

    def __init__(self, provider: TutorProvider | None = None):
        self._provider = provider or DisabledTutorProvider()

    def generate_instruction(self, context: TutorContext) -> TutorOutput:
        return self._provider.generate(context)