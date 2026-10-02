import json
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from beliefspec.experiment import load_model
from beliefspec.model import N_OBJECTS, MemoryModel, collate, losses
from beliefspec.task import CLUE_KEY, CLUE_UNKNOWN, KEY_OBJ, collect_dataset


def _episode(images, *, label=CLUE_KEY, directions=None, actions=None, stages=None):
    images = np.asarray(images, dtype=np.uint8)
    length = len(images)
    if directions is None:
        directions = np.zeros(length, dtype=np.uint8)
    if actions is None:
        actions = np.zeros(length - 1, dtype=np.uint8)
    if stages is None:
        stages = np.ones(length, dtype=np.uint8)
        stages[0] = 0
        stages[-1] = 2
    prev_actions = np.full(length, 7, dtype=np.uint8)
    if length > 1:
        prev_actions[1:] = actions
    return SimpleNamespace(
        images=images,
        directions=np.asarray(directions, dtype=np.uint8),
        prev_actions=prev_actions,
        actions=np.asarray(actions, dtype=np.uint8),
        stages=np.asarray(stages, dtype=np.uint8),
        observed_clue=label,
        top_clue=CLUE_KEY,
        evaluator={},
    )


def _frame(object_id, *, x=3, y=3):
    image = np.zeros((7, 7), dtype=np.uint8)
    image[x, y] = object_id
    return image


def _filled_frame(object_id):
    return np.full((7, 7), object_id, dtype=np.uint8)


def _prediction_logits_for(batch, target_mode):
    logits = torch.full((*batch.images.shape, N_OBJECTS), -8.0)
    for row, length in enumerate(batch.lengths.tolist()):
        for t in range(length - 1):
            if target_mode == "next":
                target = batch.images[row, t + 1]
            elif target_mode == "current":
                target = batch.images[row, t]
            else:
                raise ValueError(target_mode)
            logits[row, t].scatter_(-1, target[..., None], 8.0)
    return logits


def _prediction_loss(batch, target_mode):
    output = {
        "logits": torch.zeros(len(batch.labels), 3),
        "prediction_logits": _prediction_logits_for(batch, target_mode),
    }
    return losses(output, batch)[1].item()


def test_prediction_loss_uses_action_conditioned_state_to_predict_exact_next_observation():
    episode = _episode([_filled_frame(1), _filled_frame(2), _filled_frame(3)], actions=[0, 1])
    batch = collate([episode])

    next_loss = _prediction_loss(batch, "next")
    current_loss = _prediction_loss(batch, "current")

    assert next_loss < 0.001
    assert current_loss > 10.0


def test_prediction_loss_masks_padding_when_padded_observation_values_change():
    short = _episode([_frame(1), _frame(2), _frame(3)], actions=[0, 1])
    long = _episode([_frame(4), _frame(5), _frame(6), _frame(7), _frame(8)], actions=[1, 2, 3, 4])
    batch = collate([short, long])
    output = {
        "logits": torch.zeros(len(batch.labels), 3),
        "prediction_logits": _prediction_logits_for(batch, "next"),
    }
    original = losses(output, batch)[1].item()

    changed = collate([short, long])
    changed.images[0, 3:] = 10
    changed_output = {
        "logits": output["logits"],
        "prediction_logits": output["prediction_logits"].clone(),
    }
    changed_value = losses(changed_output, changed)[1].item()

    assert changed_value == pytest.approx(original)


def test_future_observations_do_not_change_prefix_hidden_states():
    torch.manual_seed(11)
    model = MemoryModel()
    model.eval()
    shared_prefix = [_frame(1), _frame(2), _frame(3)]
    episode_a = _episode(shared_prefix + [_frame(4), _frame(5)], actions=[0, 1, 2, 3])
    episode_b = _episode(shared_prefix + [_frame(7), _frame(8)], actions=[0, 1, 4, 5])

    out_a = model(collate([episode_a]))
    out_b = model(collate([episode_b]))

    torch.testing.assert_close(out_a["states"][0, :3], out_b["states"][0, :3])


def test_gru_memory_resets_between_episodes_in_the_same_batch():
    torch.manual_seed(12)
    model = MemoryModel()
    model.eval()
    first = _episode([_frame(1), _frame(2), _frame(3)], actions=[0, 1])
    second = _episode([_frame(4), _frame(5), _frame(6)], actions=[1, 2])

    batched = model(collate([first, second]))
    alone = model(collate([second]))

    torch.testing.assert_close(batched["states"][1], alone["states"][0])
    torch.testing.assert_close(batched["logits"][1], alone["logits"][0])


def test_final_task_loss_has_gradient_path_back_to_visible_clue_feature():
    torch.manual_seed(13)
    model = MemoryModel()
    episode = next(ep for ep in collect_dataset("train", routes_per_delay=1, waits=(8,), seed=7)
                   if ep.observed_clue == CLUE_KEY)
    batch = collate([episode])

    output = model(batch, retain_input_grad=True)
    task_loss = losses(output, batch)[0]
    task_loss.backward()

    clue_x, clue_y = np.argwhere(episode.images[0] == KEY_OBJ)[0]
    clue_feature_index = (int(clue_x) * 7 + int(clue_y)) * N_OBJECTS + KEY_OBJ
    assert output["features"].grad[0, 0, clue_feature_index].abs().item() > 0.0


def test_prediction_loss_trains_encoder_and_gru_not_only_prediction_head():
    torch.manual_seed(14)
    model = MemoryModel()
    episodes = collect_dataset("train", routes_per_delay=1, waits=(8,), seed=8)[:4]
    batch = collate(episodes)

    prediction_loss = losses(model(batch), batch)[1]
    prediction_loss.backward()

    encoder_grad = sum(p.grad.abs().sum().item() for p in model.encoder.parameters() if p.grad is not None)
    gru_grad = sum(p.grad.abs().sum().item() for p in model.gru.parameters() if p.grad is not None)
    predictor_grad = sum(
        p.grad.abs().sum().item() for p in model.predictor.parameters() if p.grad is not None
    )
    readout_grad = sum(
        p.grad.abs().sum().item() for p in model.readout.parameters() if p.grad is not None
    )

    assert encoder_grad > 0.0
    assert gru_grad > 0.0
    assert predictor_grad > 0.0
    assert readout_grad == 0.0


def test_saved_model_reload_produces_identical_logits_and_predictions(tmp_path):
    torch.manual_seed(15)
    model = MemoryModel()
    episodes = collect_dataset("train", routes_per_delay=1, waits=(8,), seed=9)[:3]
    batch = collate(episodes)
    before = model(batch)
    checkpoint = tmp_path / "model.pt"
    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": {"encoder_size": model.encoder_size, "hidden_size": model.hidden_size},
            "seed": 15,
            "variant": "control",
            "epoch": 1,
        },
        checkpoint,
    )

    restored, payload = load_model(checkpoint)
    after = restored(batch)

    assert payload["seed"] == 15
    torch.testing.assert_close(before["logits"], after["logits"])
    torch.testing.assert_close(before["prediction_logits"], after["prediction_logits"])


def _fit_tiny_subset(variant):
    torch.manual_seed(777)
    np.random.seed(777)
    torch.set_num_threads(2)
    episodes = []
    for target in (CLUE_KEY, 1, CLUE_UNKNOWN):
        episode = next(
            ep
            for ep in collect_dataset("train", routes_per_delay=2, waits=(8,), seed=10)
            if ep.observed_clue == target
        )
        episodes.append(episode)
    batch = collate(episodes)
    model = MemoryModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    prediction_weight = 0.1 if variant == "predictive" else 0.0
    started = time.perf_counter()
    result = {"variant": variant, "seed": 777, "updates": 0, "fit_accuracy": 0.0}
    for update in range(1, 501):
        optimizer.zero_grad(set_to_none=True)
        output = model(batch)
        task_loss, prediction_loss = losses(output, batch)
        objective = task_loss + prediction_weight * prediction_loss
        objective.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        with torch.no_grad():
            accuracy = (model(batch)["logits"].argmax(-1) == batch.labels).float().mean().item()
        result = {
            "variant": variant,
            "seed": 777,
            "updates": update,
            "fit_accuracy": accuracy,
            "task_ce": task_loss.item(),
            "prediction_ce": prediction_loss.item(),
            "seconds": time.perf_counter() - started,
        }
        if accuracy >= 0.98:
            break
    return result


def test_tiny_actual_dataset_subset_fit_check_records_control_and_predictive_results():
    control = _fit_tiny_subset("control")
    predictive = _fit_tiny_subset("predictive")
    result = {
        "tiny_subset_fit": [control, predictive],
        "criterion": "fit_accuracy >= 0.98 within 500 updates on labels key, ball, unknown",
        "criterion_met": {
            "control": control["fit_accuracy"] >= 0.98,
            "predictive": predictive["fit_accuracy"] >= 0.98,
        },
    }
    path = Path("artifacts/verification/model_checks.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")

    assert {row["variant"] for row in result["tiny_subset_fit"]} == {"control", "predictive"}
    assert all(row["updates"] <= 500 for row in result["tiny_subset_fit"])
    assert all(result["criterion_met"].values()), "Tiny-subset fitting failed; inspect saved artifact"
