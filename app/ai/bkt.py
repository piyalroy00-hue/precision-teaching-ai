"""Bayesian Knowledge Tracing (BKT), implemented from first principles.

Standard 4-parameter BKT model:
  P(L0) - p_init      : prior probability the skill is already known
  P(T)  - p_transit    : probability of transitioning from unknown to known
                         after an opportunity to apply the skill
  P(G)  - p_guess      : probability of a correct answer despite not knowing
                         the skill (guessing)
  P(S)  - p_slip       : probability of an incorrect answer despite knowing
                         the skill (a "slip")

On each observed response the posterior mastery is computed via Bayes' rule
conditioned on correctness, and then the learning transition is applied to
obtain the updated mastery estimate to carry into the next opportunity.
"""
from dataclasses import dataclass

from app.config.settings import BKT_DEFAULTS, MASTERY_LEVELS


@dataclass(frozen=True)
class BKTParameters:
    p_init: float = BKT_DEFAULTS["p_init"]
    p_transit: float = BKT_DEFAULTS["p_transit"]
    p_guess: float = BKT_DEFAULTS["p_guess"]
    p_slip: float = BKT_DEFAULTS["p_slip"]

    def __post_init__(self) -> None:
        for name in ("p_init", "p_transit", "p_guess", "p_slip"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within [0, 1], got {value}")


class BKTModel:
    """Stateless BKT calculator: mastery is passed in/out explicitly so callers
    (e.g. the assessment engine) control persistence in the database."""

    def __init__(self, params: BKTParameters | None = None):
        self.params = params or BKTParameters()

    def initial_mastery(self) -> float:
        """P(L0): the starting mastery probability before any evidence."""
        return self.params.p_init

    def _posterior_given_correct(self, prior: float) -> float:
        p_slip = self.params.p_slip
        p_guess = self.params.p_guess
        numerator = prior * (1 - p_slip)
        denominator = numerator + (1 - prior) * p_guess
        return numerator / denominator if denominator > 0 else prior

    def _posterior_given_incorrect(self, prior: float) -> float:
        p_slip = self.params.p_slip
        p_guess = self.params.p_guess
        numerator = prior * p_slip
        denominator = numerator + (1 - prior) * (1 - p_guess)
        return numerator / denominator if denominator > 0 else prior

    def _apply_learning_transition(self, posterior: float) -> float:
        return posterior + (1 - posterior) * self.params.p_transit

    def update_on_correct(self, prior: float) -> float:
        """Bayesian posterior + learning transition after a CORRECT response."""
        posterior = self._posterior_given_correct(prior)
        return self._apply_learning_transition(posterior)

    def update_on_incorrect(self, prior: float) -> float:
        """Bayesian posterior + learning transition after an INCORRECT response."""
        posterior = self._posterior_given_incorrect(prior)
        return self._apply_learning_transition(posterior)

    def update(self, prior: float, is_correct: bool) -> float:
        """Update mastery given one observed response. Returns the new mastery
        probability to use as the prior for the next opportunity."""
        if not 0.0 <= prior <= 1.0:
            raise ValueError(f"prior must be within [0, 1], got {prior}")
        return self.update_on_correct(prior) if is_correct else self.update_on_incorrect(prior)

    def predict_correct_probability(self, prior: float) -> float:
        """P(next response is correct) given current mastery -- NOT the mastery
        probability itself; combines mastery with guess/slip."""
        return prior * (1 - self.params.p_slip) + (1 - prior) * self.params.p_guess


def mastery_level(probability: float) -> str:
    """Convert a raw BKT mastery probability into an interpretable category.

    This app uses contiguous cutoff bands: Beginner < 0.40, Developing < 0.70,
    Proficient < 0.90, and Mastered >= 0.90. The tuple metadata in
    MASTERY_LEVELS is retained for human-readable labels, but the boundary logic
    is implemented with explicit cutoffs because the interpretation is threshold-
    based rather than "exact range match" based.
    """
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"probability must be within [0, 1], got {probability}")

    if probability < 0.40:
        return "Beginner"
    if probability < 0.70:
        return "Developing"
    if probability < 0.90:
        return "Proficient"
    return "Mastered"
