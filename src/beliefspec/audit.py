"""Dataset validity gates, run before opening held-out model outcomes."""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from beliefspec.dataio import load_dataset, visible_hash, write_json
from beliefspec.model import baseline_probabilities, clue_to_choice


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def audit(root, splits):
    root = Path(root)
    datasets = {split: load_dataset(root / "data" / split, with_evaluator=True) for split in splits}
    sets = {split: {visible_hash(e) for e in episodes} for split, episodes in datasets.items()}
    report = {"splits": {}, "overlap": {}, "fixed_geometry": True,
              "layout_generalization_claim": False}
    for i, first in enumerate(splits):
        for second in splits[i + 1:]:
            overlap = len(sets[first] & sets[second])
            report["overlap"][f"{first}:{second}"] = overlap
            require(overlap == 0, f"Visible history overlap {first}/{second}: {overlap}")
    for split, episodes in datasets.items():
        balanced = Counter()
        observed_success, unknown_success = [], []
        delays = set()
        for e in episodes:
            require(np.array_equal(e.actions, e.prev_actions[1:]), "Previous-action misalignment")
            require(len(e.actions) + 1 == len(e.images), "Transition count mismatch")
            require(e.prev_actions[0] == 7, "Missing start marker")
            expected = int(np.argmax(baseline_probabilities(e, "structured")))
            require(expected == e.observed_clue, "Task label must follow permitted history")
            choice = clue_to_choice(baseline_probabilities(e, "structured"), e.top_clue)
            correct = int(choice == e.evaluator["correct_top"])
            target = unknown_success if e.observed_clue == 2 else observed_success
            target.append(correct)
            if e.evaluator["delay"] is not None:
                delays.add(int(e.evaluator["delay"]))
            balanced[(e.evaluator["wait"], e.observed_clue == 2,
                      e.evaluator["hidden_clue"], e.top_clue)] += 1
        require(len(set(balanced.values())) == 1, "Unequal factorial counts")
        require(np.mean(observed_success) == 1, "Structured memory must solve observed cases")
        require(np.mean(unknown_success) == 0.5, "Unavailable clues must give chance success")
        report["splits"][split] = {"episodes": len(episodes), "unique_visible": len(sets[split]),
                                    "delays": sorted(delays),
                                    "factorial_cell_counts": sorted(set(balanced.values())),
                                    "structured_observed_success": float(np.mean(observed_success)),
                                    "structured_never_success": float(np.mean(unknown_success)),
                                    "duplicate_explanation": "Never-observed hidden-clue twins intentionally have identical histories"}
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--splits", nargs="+", default=["train", "validation", "test"])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    report = audit(root, args.splits)
    write_json(root / "artifacts" / ("audit_" + "_".join(args.splits) + ".json"), report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
