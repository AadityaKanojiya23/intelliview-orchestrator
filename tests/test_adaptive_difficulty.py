from workers.adaptive_difficulty import get_next_difficulty

import pytest


def test_high_scores_return_hard():
    assert get_next_difficulty(9) == "hard"
    assert get_next_difficulty(10) == "hard"


def test_low_scores_return_easy():
    assert get_next_difficulty(4) == "easy"
    assert get_next_difficulty(0) == "easy"


def test_boundary_scores_return_medium():
    assert get_next_difficulty(5) == "medium"
    assert get_next_difficulty(8) == "medium"


@pytest.mark.parametrize(
    ("current_difficulty", "score", "expected_difficulty"),
    [
        ("medium", 9, "hard"),
        ("hard", 4, "easy"),
        ("easy", 7, "medium"),
        ("medium", 8, "medium"),
        ("medium", 10, "hard"),
    ],
)
def test_difficulty_transitions(
    current_difficulty,
    score,
    expected_difficulty,
):
    assert get_next_difficulty(score) == expected_difficulty