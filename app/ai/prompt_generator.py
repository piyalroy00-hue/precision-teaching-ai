"""Programmatic, versioned prompts for the instruction-generation provider."""
from dataclasses import dataclass

from app.ai.tutor import TutorContext

PROMPT_VERSION = "phase3-v1"


@dataclass(frozen=True)
class TutorPrompt:
    version: str
    system_instruction: str
    user_instruction: str


def build_tutor_prompt(context: TutorContext) -> TutorPrompt:
    """Create a bounded instructional request from learner-model output.

    The learner model selects target, readiness, and difficulty before this
    function runs. The prompt explicitly prevents the provider from revising
    that model or introducing content beyond the selected difficulty.
    """
    prerequisites = ", ".join(context.prerequisite_concepts) or "None required"
    previous_errors = "; ".join(context.previous_errors) or "No recorded errors"
    subtopic = context.subtopic or context.topic
    system_instruction = (
        "You are an adaptive educational tutor. Generate accurate, concise Python "
        "instruction using only the supplied learning target and difficulty. Do not "
        "estimate, alter, or discuss learner-model probabilities. Do not introduce "
        "concepts beyond the requested difficulty. Return all requested sections."
    )
    user_instruction = f"""Subject: {context.subject}
Topic: {context.topic}
Subtopic: {subtopic}
Mastery level: {context.mastery_level}
Instructional difficulty: {context.difficulty}
Learning objective: {context.learning_objective}
Prerequisite concepts: {prerequisites}
Previous errors: {previous_errors}

Generate these labelled sections:
1. Simple explanation
2. Small Python example
3. Step-by-step explanation
4. One {context.difficulty.lower()}-level practice question
5. One hint
6. Correct answer
7. Brief feedback
"""
    return TutorPrompt(
        version=PROMPT_VERSION,
        system_instruction=system_instruction,
        user_instruction=user_instruction,
    )