import copy

import numpy as np
import torch

from beliefspec.dataio import load_dataset, save_dataset, visible_hash
from beliefspec.model import MemoryModel, collate
from beliefspec.task import collect_dataset, visible_history_hash


def test_model_outputs_do_not_change_when_evaluator_metadata_changes():
    torch.manual_seed(21)
    model = MemoryModel()
    model.eval()
    episode = collect_dataset("train", routes_per_delay=1, waits=(8,), seed=12)[0]
    altered = copy.deepcopy(episode)
    altered.evaluator = {
        "episode_id": "leaky-answer-id",
        "hidden_clue": 1 - int(episode.evaluator["hidden_clue"]),
        "correct_top": not bool(episode.evaluator["correct_top"]),
        "route_id": "metadata-should-not-enter-model",
    }

    original = model(collate([episode]))
    changed = model(collate([altered]))

    torch.testing.assert_close(original["logits"], changed["logits"])
    torch.testing.assert_close(original["prediction_logits"], changed["prediction_logits"])


def test_collated_model_inputs_ignore_info_fields_and_episode_ids():
    episode = collect_dataset("train", routes_per_delay=1, waits=(8,), seed=13)[0]
    altered = copy.deepcopy(episode)
    altered.evaluator["episode_id"] = "contains-key-answer"
    altered.evaluator["info"] = {"mission": "go to the hidden correct object"}
    altered.evaluator["filename"] = "ball_is_correct.npy"

    original = collate([episode])
    changed = collate([altered])

    for field in ("images", "directions", "prev_actions", "actions", "stages", "lengths", "labels"):
        torch.testing.assert_close(getattr(original, field), getattr(changed, field))


def test_saving_and_loading_without_evaluator_keeps_hidden_logs_out_of_visible_records(tmp_path):
    episodes = collect_dataset("train", routes_per_delay=1, waits=(8,), seed=14)
    save_dataset(tmp_path, episodes)

    visible = load_dataset(tmp_path, with_evaluator=False)
    with_hidden = load_dataset(tmp_path, with_evaluator=True)

    assert all(ep.evaluator == {} for ep in visible)
    assert any(ep.evaluator for ep in with_hidden)
    assert [visible_hash(ep) for ep in visible] == [visible_hash(ep) for ep in with_hidden]


def test_identical_visible_histories_have_identical_model_inputs_despite_hidden_truth_swap():
    episodes = collect_dataset("train", routes_per_delay=1, waits=(8,), seed=15)
    pair = [
        ep
        for ep in episodes
        if not ep.evaluator["clue_observed"] and ep.top_clue == episodes[0].top_clue
    ][:2]
    assert len(pair) == 2
    assert pair[0].evaluator["hidden_clue"] != pair[1].evaluator["hidden_clue"]
    assert pair[0].evaluator["correct_top"] != pair[1].evaluator["correct_top"]
    assert visible_history_hash(pair[0]) == visible_history_hash(pair[1])

    first = collate([pair[0]])
    second = collate([pair[1]])

    np.testing.assert_array_equal(pair[0].images, pair[1].images)
    for field in ("images", "directions", "prev_actions", "actions", "stages", "labels"):
        torch.testing.assert_close(getattr(first, field), getattr(second, field))
