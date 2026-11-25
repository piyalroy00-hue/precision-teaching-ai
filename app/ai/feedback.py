"""Context-aware instructional hints and feedback without learner-model mutation."""
from dataclasses import dataclass

from app.ai.tutor import TutorContext


@dataclass(frozen=True)
class PracticeFeedback:
    hint: str
    feedback: str


def generate_hint(context: TutorContext) -> str:
    """Offer one bounded next step without revealing the answer."""
    error_focus = context.previous_errors[-1] if context.previous_errors else None
    if error_focus:
        return f"Before answering, revisit this earlier difficulty: {error_focus}."
    prerequisite = context.prerequisite_concepts[0] if context.prerequisite_concepts else None
    if prerequisite:
        return f"Start by recalling {prerequisite}, then apply it to {context.subtopic or context.topic}."
    return f"Break {context.subtopic or context.topic} into one small {context.difficulty.lower()} step."


def generate_feedback(context: TutorContext, is_correct: bool) -> PracticeFeedback:
    """Respond to practice performance without claiming a mastery change."""
    hint = generate_hint(context)
    target = context.subtopic or context.topic
    if is_correct:
        feedback = (
            f"Correct. You applied {target} appropriately. Try a small variation to reinforce "
            "the same learning objective."
        )
    else:
        feedback = (
            f"Not quite. Revisit {target} and use the hint before attempting a similar "
            f"{context.difficulty.lower()} practice question."
        )
    return PracticeFeedback(hint=hint, feedback=feedback)