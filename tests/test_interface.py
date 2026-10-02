import pytest

from beliefspec.model import clue_to_choice, decision_from_memory


def test_forced_choice_and_decoded_memory_interventions():
    known = {"clue_probabilities": [1, 0, 0], "nuisance_note": "wall A"}
    changed = {"clue_probabilities": [1, 0, 0], "nuisance_note": "wall B"}
    assert decision_from_memory(known, 0)
    assert decision_from_memory(changed, 0)
    assert not decision_from_memory({"clue_probabilities": [0, 1, 0]}, 0)
    assert decision_from_memory({"clue_probabilities": [0, 0, 1]}, 0)
    assert decision_from_memory({"clue_probabilities": [0, 0, 1]}, 1)


def test_invalid_memory_probabilities_fail_loudly():
    for probability in ([0, 0, 0], [-1, 1, 1], [1, 0], [float("nan"), 0, 0]):
        with pytest.raises(ValueError):
            clue_to_choice(probability, 0)
