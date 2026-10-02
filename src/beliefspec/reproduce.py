"""Fresh-process training reproduction without overwriting original results."""

import argparse
import csv
import json

import numpy as np
import torch

from beliefspec.dataio import load_dataset, visible_hash, write_json
from beliefspec.experiment import ROOT, episode_row, infer, load_model, train
from beliefspec.task import collect_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Retrain all six runs instead of control seed11")
    parser.add_argument("--output", default="runs/reproduction")
    args = parser.parse_args()
    destination = ROOT / args.output
    config = json.loads((ROOT / "configs/frozen.json").read_text())
    training = load_dataset(ROOT / "data/train")
    validation = load_dataset(ROOT / "data/validation")
    test = load_dataset(ROOT / "data/test", with_evaluator=True)
    regeneration = {}
    for split in ("train", "validation", "test"):
        fresh = collect_dataset(split, config["routes_per_delay"][split], config["waits"],
                                config["data_seeds"][split])
        saved = load_dataset(ROOT / f"data/{split}")
        identical = [visible_hash(e) for e in fresh] == [visible_hash(e) for e in saved]
        if not identical:
            raise RuntimeError(f"Data regeneration mismatch: {split}")
        regeneration[split] = {"episodes": len(fresh), "ordered_visible_hashes_match": identical}
    with (ROOT / "results/final/episodes.csv").open() as stream:
        expected_rows = list(csv.DictReader(stream))
    selected = [(s, v) for s in config["seeds"] for v in ("control", "predictive")]
    if not args.all:
        selected = [(11, "control")]
    results = []
    for seed, variant in selected:
        output = destination / f"{variant}_{seed}"
        train(config, seed, variant, training, validation, output)
        model, _ = load_model(output / "best.pt")
        original, _ = load_model(ROOT / f"runs/main/{variant}_{seed}/best.pt")
        exact_weights = all(torch.equal(v, original.state_dict()[k]) for k, v in model.state_dict().items())
        probabilities, metrics = infer(model, test)
        actual = [episode_row(e, p, variant, seed, m) for e, p, m in zip(test, probabilities, metrics)]
        expected = [r for r in expected_rows if r["method"] == variant and r["training_seed"] == str(seed)]
        by_id = {r["episode_id"]: r for r in expected}
        max_error = max(abs(float(row[field]) - float(by_id[row["episode_id"]][field]))
                        for row in actual for field in ("p_key", "p_ball", "p_unknown", "prediction_ce"))
        equal_decisions = all(row["success"] == int(by_id[row["episode_id"]]["success"]) for row in actual)
        result = {"seed": seed, "variant": variant, "exact_checkpoint_tensors": exact_weights,
                  "max_probability_or_prediction_ce_difference": max_error,
                  "all_episode_successes_identical": equal_decisions,
                  "observed_success": float(np.mean([r["success"] for r in actual if r["observed_clue"] != 2])),
                  "never_success": float(np.mean([r["success"] for r in actual if r["observed_clue"] == 2]))}
        results.append(result)
        if not equal_decisions or max_error >= 1e-6:
            raise RuntimeError(f"Reproduction mismatch: {result}")
    write_json(destination / "verification.json", {"data_regeneration": regeneration, "runs": results})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
