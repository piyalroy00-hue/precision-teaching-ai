"""Research metrics for labelled experimental data; no results are fabricated."""
from dataclasses import dataclass


@dataclass(frozen=True)
class LearningOutcome:
    pretest_score: float
    posttest_score: float
    learning_gain: float
    normalized_gain: float | None


def calculate_learning_outcome(pretest_score: float, posttest_score: float) -> LearningOutcome:
    if not 0.0 <= pretest_score <= 100.0 or not 0.0 <= posttest_score <= 100.0:
        raise ValueError("Scores must be percentages within [0, 100].")
    gain = posttest_score - pretest_score
    normalized_gain = None if pretest_score == 100.0 else gain / (100.0 - pretest_score)
    return LearningOutcome(pretest_score, posttest_score, gain, normalized_gain)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def prediction_metrics(predictions: list[bool], actuals: list[bool]) -> dict[str, float]:
    if len(predictions) != len(actuals) or not actuals:
        raise ValueError("Predictions and actuals must be non-empty and the same length.")
    true_positive = sum(prediction and actual for prediction, actual in zip(predictions, actuals))
    false_positive = sum(prediction and not actual for prediction, actual in zip(predictions, actuals))
    false_negative = sum(not prediction and actual for prediction, actual in zip(predictions, actuals))
    accuracy = sum(prediction == actual for prediction, actual in zip(predictions, actuals)) / len(actuals)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}