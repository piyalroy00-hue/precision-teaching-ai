"""Optional OpenAI adapter; imported only when explicitly configured."""
from app.ai.prompt_generator import TutorPrompt
from app.ai.tutor import TutorContext, TutorOutput


def _section(content: str, heading: str) -> str:
    marker = f"{heading}:"
    start = content.find(marker)
    if start < 0:
        return ""
    value = content[start + len(marker):]
    next_markers = [f"{number}." for number in range(1, 8)]
    endings = [value.find(candidate) for candidate in next_markers if value.find(candidate) > 0]
    return value[:min(endings) if endings else None].strip()


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
        output = TutorOutput(
            explanation=_section(content, "1. Simple explanation"),
            example=_section(content, "2. Small Python example"),
            step_by_step=_section(content, "3. Step-by-step explanation"),
            hint=_section(content, "5. One hint"),
            practice_question=_section(content, "4. One"),
            correct_answer=_section(content, "6. Correct answer"),
            feedback=_section(content, "7. Brief feedback"),
        )
        if not all((output.explanation, output.example, output.hint, output.correct_answer)):
            raise ValueError("The tutor provider returned incomplete structured content.")
        return output