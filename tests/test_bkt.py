import pytest

from app.ai.bkt import BKTModel, BKTParameters, mastery_level


def test_default_parameters_are_used():
    model = BKTModel()
    assert model.params.p_init == pytest.approx(0.20)
    assert model.initial_mastery() == pytest.approx(0.20)


def test_invalid_parameter_raises():
    with pytest.raises(ValueError):
        BKTParameters(p_init=1.5)
    with pytest.raises(ValueError):
        BKTParameters(p_slip=-0.1)


def test_correct_response_increases_mastery():
    model = BKTModel(BKTParameters(p_init=0.3, p_transit=0.1, p_guess=0.2, p_slip=0.1))
    updated = model.update(prior=0.3, is_correct=True)
    assert updated > 0.3
    assert 0.0 <= updated <= 1.0


def test_incorrect_response_decreases_mastery():
    model = BKTModel(BKTParameters(p_init=0.3, p_transit=0.1, p_guess=0.2, p_slip=0.1))
    updated = model.update(prior=0.3, is_correct=False)
    assert updated < 0.3
    assert 0.0 <= updated <= 1.0


def test_repeated_correct_responses_converge_towards_mastery():
    model = BKTModel(BKTParameters(p_init=0.2, p_transit=0.15, p_guess=0.2, p_slip=0.1))
    mastery = model.initial_mastery()
    for _ in range(20):
        mastery = model.update(mastery, is_correct=True)
    assert mastery > 0.9


def test_repeated_incorrect_responses_stay_low():
    model = BKTModel(BKTParameters(p_init=0.5, p_transit=0.05, p_guess=0.1, p_slip=0.05))
    mastery = model.initial_mastery()
    for _ in range(20):
        mastery = model.update(mastery, is_correct=False)
    assert mastery < 0.5


def test_mastery_never_leaves_valid_range_with_random_sequence():
    model = BKTModel()
    mastery = model.initial_mastery()
    sequence = [True, False, True, True, False, False, True, False]
    for is_correct in sequence:
        mastery = model.update(mastery, is_correct)
        assert 0.0 <= mastery <= 1.0


def test_update_rejects_out_of_range_prior():
    model = BKTModel()
    with pytest.raises(ValueError):
        model.update(prior=1.2, is_correct=True)


def test_predict_correct_probability_bounds():
    model = BKTModel(BKTParameters(p_guess=0.25, p_slip=0.1))
    assert model.predict_correct_probability(0.0) == pytest.approx(0.25)
    assert model.predict_correct_probability(1.0) == pytest.approx(0.9)


@pytest.mark.parametrize(
    "probability, expected_label",
    [
        (0.0, "Beginner"),
        (0.39, "Beginner"),
        (0.40, "Developing"),
        (0.69, "Developing"),
        (0.70, "Proficient"),
        (0.89, "Proficient"),
        (0.8903225806451612, "Proficient"),
        (0.90, "Mastered"),
        (1.0, "Mastered"),
    ],
)
def test_mastery_level_bands(probability, expected_label):
    assert mastery_level(probability) == expected_label


def test_mastery_level_rejects_out_of_range():
    with pytest.raises(ValueError):
        mastery_level(-0.01)
    with pytest.raises(ValueError):
        mastery_level(1.01)
