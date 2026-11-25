from app.ai.prompt_generator import PROMPT_VERSION, build_tutor_prompt
from app.ai.tutor import TutorContext


def test_prompt_is_built_from_the_learner_model_target_and_context():
    context = TutorContext(
        subject="Python Programming", topic="Recursion", subtopic="Base case",
        mastery_probability=0.31, mastery_level="Beginner", difficulty="Easy",
        learning_objective="Explain why a recursive function stops.",
        prerequisite_concepts=("Function Definition", "Return Values"),
        previous_errors=("Missing a base case",),
    )

    prompt = build_tutor_prompt(context)

    assert prompt.version == PROMPT_VERSION
    assert "Topic: Recursion" in prompt.user_instruction
    assert "Mastery level: Beginner" in prompt.user_instruction
    assert "Instructional difficulty: Easy" in prompt.user_instruction
    assert "Missing a base case" in prompt.user_instruction
    assert "Simple explanation" in prompt.user_instruction
    assert "Correct answer" in prompt.user_instruction


def test_prompt_does_not_expose_raw_mastery_probability_to_student_facing_content():
    context = TutorContext(
        subject="Python Programming", topic="Loops", subtopic=None,
        mastery_probability=0.31, mastery_level="Beginner", difficulty="Easy",
        learning_objective="Use a loop.",
    )

    prompt = build_tutor_prompt(context)

    assert "0.31" not in prompt.user_instruction
    assert "Do not estimate, alter, or discuss learner-model probabilities" in prompt.system_instruction