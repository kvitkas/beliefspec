"""CPU training, frozen-checkpoint evaluation and fully recorded episode metrics."""

import argparse
import csv
import json
import os
import platform
import random
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch

from beliefspec.dataio import file_sha256, load_dataset, save_dataset, visible_hash, write_json
from beliefspec.model import (
    MemoryModel,
    baseline_probabilities,
    collate,
    decision_from_memory,
    losses,
)

ROOT = Path(__file__).resolve().parents[2]


def setup(seed, threads=2):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)


def evaluate_losses(model, episodes, batch_size=64):
    model.eval()
    task_sum = pred_sum = correct = count = 0
    with torch.no_grad():
        for start in range(0, len(episodes), batch_size):
            batch = collate(episodes[start:start + batch_size])
            output = model(batch)
            task, prediction = losses(output, batch)
            n = len(batch.labels)
            task_sum += task.item() * n
            pred_sum += prediction.item() * n
            correct += (output["logits"].argmax(-1) == batch.labels).sum().item()
            count += n
    return {"task_ce": task_sum / count, "prediction_ce": pred_sum / count,
            "readout_accuracy": correct / count}


def train(config, seed, variant, train_data, validation, destination):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Preserve prior run: {destination}")
    destination.mkdir(parents=True)
    setup(seed, config["threads"])
    model = MemoryModel(config["encoder_size"], config["hidden_size"])
    optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
    order_rng = np.random.default_rng(seed + 10000)
    weight = config["prediction_weight"] if variant == "predictive" else 0.0
    write_json(destination / "config.json", {**config, "seed": seed, "variant": variant})
    best, best_epoch = float("inf"), -1
    started = time.perf_counter()
    history = []
    for epoch in range(config["epochs"]):
        model.train()
        order = order_rng.permutation(len(train_data))
        task_values, pred_values = [], []
        for begin in range(0, len(order), config["batch_size"]):
            batch = collate([train_data[int(i)] for i in order[begin:begin + config["batch_size"]]])
            optimizer.zero_grad(set_to_none=True)
            output = model(batch)
            task_loss, pred_loss = losses(output, batch)
            objective = task_loss + weight * pred_loss if weight else task_loss
            objective.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), config["gradient_clip"])
            optimizer.step()
            task_values.append(task_loss.item())
            pred_values.append(pred_loss.item())
        metrics = evaluate_losses(model, validation, config["batch_size"])
        row = {"epoch": epoch + 1, "train_task_ce": float(np.mean(task_values)),
               "train_prediction_ce": float(np.mean(pred_values)),
               **{f"validation_{k}": v for k, v in metrics.items()},
               "elapsed_seconds": time.perf_counter() - started}
        history.append(row)
        if metrics["task_ce"] < best:
            best, best_epoch = metrics["task_ce"], epoch + 1
            torch.save({"state_dict": model.state_dict(), "config": config,
                        "seed": seed, "variant": variant, "epoch": best_epoch},
                       destination / "best.pt")
        with (destination / "history.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        if epoch == 0 or (epoch + 1) % 10 == 0:
            print(json.dumps({"variant": variant, "seed": seed, **row}), flush=True)
    result = {"status": "complete", "variant": variant, "seed": seed,
              "epochs": config["epochs"], "updates": config["epochs"] *
              int(np.ceil(len(train_data) / config["batch_size"])),
              "best_epoch": best_epoch, "best_validation_task_ce": best,
              "seconds": time.perf_counter() - started, "parameters": model.counts(),
              "active_parameters": model.counts()["allocated"] if weight else model.counts()["shared"],
              "device": "cpu", "checkpoint_sha256": file_sha256(destination / "best.pt")}
    write_json(destination / "result.json", result)
    return result


def load_model(checkpoint):
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model = MemoryModel(payload["config"]["encoder_size"], payload["config"]["hidden_size"])
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, payload


def infer(model, episodes, batch_size=64):
    probabilities, prediction_metrics = [], []
    with torch.no_grad():
        for start in range(0, len(episodes), batch_size):
            batch = collate(episodes[start:start + batch_size])
            output = model(batch)
            probabilities.extend(output["logits"].softmax(-1).numpy().tolist())
            for j, length in enumerate(batch.lengths.tolist()):
                logits = output["prediction_logits"][j, :length - 1]
                targets = batch.images[j, 1:length]
                ce = torch.nn.functional.cross_entropy(logits.reshape(-1, 11), targets.reshape(-1))
                accuracy = (logits.argmax(-1) == targets).float().mean().item()
                copy_accuracy = (batch.images[j, :length - 1] == targets).float().mean().item()
                prediction_metrics.append({"prediction_ce": ce.item(),
                                           "prediction_accuracy": accuracy,
                                           "copy_accuracy": copy_accuracy})
    return probabilities, prediction_metrics


def episode_row(episode, probability, method, seed, prediction=None):
    truth = episode.evaluator
    choice = decision_from_memory({"clue_probabilities": probability}, episode.top_clue)
    decoded = int(np.argmax(probability))
    correct_top = bool(truth["correct_top"])
    success = choice == correct_top
    label = int(episode.observed_clue)
    unavailable = "unavailable_unknown_readout" if decoded == 2 else "unavailable_hallucinated_readout"
    failure = ("success" if success else unavailable if label == 2 else
               "incorrect_or_unknown_readout" if decoded != label else "supplied_but_misused")
    row = {**truth, "method": method, "training_seed": seed,
           "visible_sha256": visible_hash(episode), "observed_clue": label,
           "top_clue": int(episode.top_clue), "length": len(episode.images),
           "p_key": float(probability[0]), "p_ball": float(probability[1]),
           "p_unknown": float(probability[2]), "readout": decoded,
           "readout_correct": int(decoded == label), "choose_top": int(choice),
           "success": int(success), "failure_class": failure}
    if prediction:
        row.update(prediction)
    return row


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)


def evaluate(config, freeze_path, destination):
    from beliefspec.task import replay_choice
    freeze = json.loads(Path(freeze_path).read_text())
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Preserve final evaluation: {destination}")
    destination.mkdir(parents=True)
    episodes = load_dataset(ROOT / "data/test", with_evaluator=True)
    for relative, expected in freeze["files"].items():
        if file_sha256(ROOT / relative) != expected:
            raise RuntimeError(f"Freeze mismatch: {relative}")
    setup(0, config["threads"])
    rows, timing, replay_rows = [], [], []
    for method in ("current", "recent", "structured", "episodic"):
        begin = time.perf_counter()
        method_rows = []
        for episode in episodes:
            p = baseline_probabilities(episode, method, config["recent_window"])
            row = episode_row(episode, p, method, "")
            rows.append(row)
            method_rows.append(row)
        timing.append({"method": method, "seconds": time.perf_counter() - begin,
                       "episodes": len(episodes), "includes_simulator_replay": False})
        if method == "structured":
            for episode, row in zip(episodes, method_rows):
                replay = replay_choice(episode, bool(row["choose_top"]))
                if not replay["terminated"] or replay["truncated"]:
                    raise RuntimeError("Controller did not finish")
                if bool(replay["success"]) != bool(row["success"]):
                    raise RuntimeError("Scoring/replay disagreement")
                replay_rows.append({"episode_id": episode.evaluator["episode_id"],
                                    "expected_success": row["success"], **replay})
    for seed in config["seeds"]:
        for variant in ("control", "predictive"):
            model, _ = load_model(ROOT / f"runs/main/{variant}_{seed}/best.pt")
            begin = time.perf_counter()
            probabilities, metrics = infer(model, episodes, config["batch_size"])
            timing.append({"method": variant, "training_seed": seed,
                           "seconds": time.perf_counter() - begin, "episodes": len(episodes),
                           "includes_simulator_replay": False})
            rows.extend(episode_row(e, p, variant, seed, m)
                        for e, p, m in zip(episodes, probabilities, metrics))
    write_csv(destination / "episodes.csv", rows)
    write_json(destination / "evaluation_cost.json", timing)
    write_json(destination / "simulator_replay.json", replay_rows)
    # Intervene on the decoded probability interface, not neural coordinates.
    interventions = []
    for row in rows:
        p = [row["p_key"], row["p_ball"], row["p_unknown"]]
        for intervention, changed in (("original", p), ("remove", [0, 0, 1]),
                                      ("swap", [p[1], p[0], p[2]]), ("irrelevant", p)):
            note = "unrelated wall note B" if intervention == "irrelevant" else "unrelated wall note A"
            memory_record = {"clue_probabilities": changed, "nuisance_note": note}
            choice = decision_from_memory(memory_record, int(row["top_clue"]))
            interventions.append({"episode_id": row["episode_id"], "method": row["method"],
                                  "training_seed": row["training_seed"],
                                  "observed_clue": row["observed_clue"],
                                  "intervention": intervention,
                                  "nuisance_note": note,
                                  "success": int(choice == bool(row["correct_top"]))})
    write_csv(destination / "interventions.csv", interventions)
    print(json.dumps({"evaluated_rows": len(rows), "destination": str(destination)}))


def environment_record():
    return {"utc": datetime.now(UTC).isoformat(), "platform": platform.platform(),
            "python": platform.python_version(), "torch": torch.__version__,
            "cpu_count": os.cpu_count(), "device_used": "cpu",
            "mps_available": torch.backends.mps.is_available(),
            "cuda_available": torch.cuda.is_available(),
            "physical_memory_bytes": int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]))
            if platform.system() == "Darwin" else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate", "train", "evaluate", "environment"])
    parser.add_argument("--config", default="configs/frozen.json")
    parser.add_argument("--split", choices=["train", "validation", "test"], default="train")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--variant", choices=["control", "predictive"], default="control")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    if args.command == "environment":
        write_json(ROOT / "artifacts/environment.json", environment_record())
        print(json.dumps(environment_record(), indent=2))
        return
    config = json.loads((ROOT / args.config).read_text())
    if args.command == "generate":
        from beliefspec.task import collect_dataset
        path = ROOT / f"data/{args.split}"
        if path.exists():
            raise FileExistsError(f"Preserve dataset: {path}")
        episodes = collect_dataset(args.split, config["routes_per_delay"][args.split],
                                   config["waits"], config["data_seeds"][args.split])
        save_dataset(path, episodes)
        print(json.dumps({"split": args.split, "episodes": len(episodes),
                          "unique_visible_histories": len({visible_hash(e) for e in episodes})}))
    elif args.command == "train":
        train(config, args.seed, args.variant, load_dataset(ROOT / "data/train"),
              load_dataset(ROOT / "data/validation"),
              ROOT / (args.output or f"runs/main/{args.variant}_{args.seed}"))
    else:
        evaluate(config, ROOT / "artifacts/freeze.json", ROOT / (args.output or "results/final"))


if __name__ == "__main__":
    main()
