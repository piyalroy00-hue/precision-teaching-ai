"""Optional OpenAI adapter; imported only when explicitly configured."""
import re

from app.ai.prompt_generator import TutorPrompt
from app.ai.tutor import TutorContext, TutorOutput


def _section(content: str, heading: str) -> str:
    heading_pattern = re.compile(
        rf"(?im)^\s*(?:\*\*)?{re.escape(heading)}(?:\*\*)?\s*:?\s*"
    )
    match = heading_pattern.search(content)
    if match is None:
        return ""
    value = content[match.end():]
    next_heading = re.search(r"(?im)^\s*(?:\*\*)?\d+\.(?:\*\*)?\s+", value)
    return (value[:next_heading.start()] if next_heading else value).strip()


class OpenAITutorProvider:
    """Adapter for an explicitly configured OpenAI SDK client."""

    def __init__(self, api_key: str, model: str, client=None):
        self._api_key = api_key
        self._model = model
        self._client = client

    def generate(self, prompt: TutorPrompt, context: TutorContext) -> TutorOutput:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError("Install the 'openai' package to use the OpenAI tutor provider.") from exc
            self._client = OpenAI(api_key=self._api_key)
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": prompt.system_instruction},
                {"role": "user", "content": prompt.user_instruction},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or ""
        practice_heading = f"4. One {context.difficulty.lower()}-level practice question"
        output = TutorOutput(
            explanation=_section(content, "1. Simple explanation"),
            example=_section(content, "2. Small Python example"),
            step_by_step=_section(content, "3. Step-by-step explanation"),
            hint=_section(content, "5. One hint"),
            practice_question=_section(content, practice_heading),
            correct_answer=_section(content, "6. Correct answer"),
            feedback=_section(content, "7. Brief feedback"),
        )
        if not all(
            (
                output.explanation,
                output.example,
                output.step_by_step,
                output.practice_question,
                output.hint,
                output.correct_answer,
                output.feedback,
            )
        ):
            raise ValueError("The tutor provider returned incomplete structured content.")
        return output
