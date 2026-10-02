"""Independent record-level checks on the completed frozen evaluation."""

import csv
import json
from collections import defaultdict

import numpy as np

from beliefspec.dataio import file_sha256, write_json
from beliefspec.experiment import ROOT


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    freeze = json.loads((ROOT / "artifacts/freeze.json").read_text())
    mismatches = [name for name, digest in freeze["files"].items()
                  if file_sha256(ROOT / name) != digest]
    require(not mismatches, f"Frozen evidence changed: {mismatches}")
    with (ROOT / "results/final/episodes.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    groups = defaultdict(list)
    for row in rows:
        groups[(row["method"], row["training_seed"])].append(row)
    require(len(groups) == 10, "Expected four deterministic baselines and six trained models")
    id_sets = [{row["episode_id"] for row in group} for group in groups.values()]
    require(all(ids == id_sets[0] for ids in id_sets), "Methods did not share evaluation episodes")
    require(len(id_sets[0]) == 768, "Expected 768 evaluation episodes")
    require(all(len(group) == 768 for group in groups.values()), "Duplicate/missing rows")
    hidden_swap_checks = 0
    independent_scores = {}
    for (method, seed), group in groups.items():
        observed = [r for r in group if r["observed_clue"] != "2"]
        never = [r for r in group if r["observed_clue"] == "2"]
        observed_success = sum(int(r["success"]) for r in observed) / len(observed)
        never_success = sum(int(r["success"]) for r in never) / len(never)
        require(never_success == .5, f"Never-observed balance failed: {method}/{seed}")
        independent_scores[f"{method}:{seed}"] = {"observed": observed_success,
                                                    "never": never_success}
        twins = defaultdict(list)
        for row in never:
            twins[(row["route_id"], row["top_clue"])].append(row)
        for pair in twins.values():
            require(len(pair) == 2, "Expected balanced hidden-truth twins")
            require(pair[0]["visible_sha256"] == pair[1]["visible_sha256"], "Hidden clue leaked")
            for field in ("p_key", "p_ball", "p_unknown"):
                require(abs(float(pair[0][field]) - float(pair[1][field])) < 1e-7,
                        "Identical histories changed predictions")
            hidden_swap_checks += 1
    contrasts = [independent_scores[f"predictive:{seed}"]["observed"] -
                 independent_scores[f"control:{seed}"]["observed"] for seed in (11, 22, 33)]
    summary = json.loads((ROOT / "results/summary.json").read_text())["primary"]
    require(np.isclose(np.mean(contrasts), summary["mean_difference"]), "Primary summary mismatch")
    replay = json.loads((ROOT / "results/final/simulator_replay.json").read_text())
    require(len(replay) == 768, "Missing terminal action replays")
    require(all(r["terminated"] and not r["truncated"] and
                r["success"] == bool(r["expected_success"]) for r in replay), "Replay disagreement")
    with (ROOT / "results/final/interventions.csv").open() as stream:
        interventions = list(csv.DictReader(stream))
    require(len(interventions) == 4 * len(rows), "Missing decoded-memory interventions")
    intervention_lookup = {(r["method"], r["training_seed"], r["episode_id"], r["intervention"]): r
                           for r in interventions}
    for row in rows:
        key = (row["method"], row["training_seed"], row["episode_id"])
        require(intervention_lookup[(*key, "original")]["success"] == row["success"],
                "Original intervention disagrees")
        require(intervention_lookup[(*key, "irrelevant")]["success"] == row["success"],
                "Nuisance changed controller decision")
    reproduction = json.loads((ROOT / "runs/reproduction/verification.json").read_text())
    require(reproduction["runs"][0]["exact_checkpoint_tensors"], "Fresh reproduction not exact")
    result = {"frozen_files_verified": len(freeze["files"]), "episode_rows": len(rows),
              "paired_method_seed_groups": len(groups), "hidden_swap_output_checks": hidden_swap_checks,
              "simulator_replays": len(replay), "intervention_rows": len(interventions),
              "independently_computed_scores": independent_scores,
              "independent_primary_seed_differences": contrasts,
              "fresh_environment_reproduction": reproduction, "passed": True}
    write_json(ROOT / "artifacts/verification/package_checks.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in
                      ("independently_computed_scores", "fresh_environment_reproduction")}, indent=2))


if __name__ == "__main__":
    main()
