"""Post-hoc audit: when does a next-view target depend on the remote clue?"""

from collections import defaultdict

import numpy as np

from beliefspec.dataio import load_dataset, write_json
from beliefspec.experiment import ROOT


def main():
    episodes = load_dataset(ROOT / "data/test", with_evaluator=True)
    twins = defaultdict(list)
    for episode in episodes:
        if episode.observed_clue != 2:
            twins[(episode.evaluator["route_id"], episode.top_clue)].append(episode)
    records = []
    for (route_id, top_clue), pair in twins.items():
        if len(pair) != 2:
            raise RuntimeError("Missing observed-clue twin")
        a, b = pair
        if not np.array_equal(a.actions, b.actions):
            raise RuntimeError("Unpaired routes")
        differing_observation_steps = np.flatnonzero(np.any(a.images != b.images, axis=(1, 2))).tolist()
        differing_prediction_input_times = [t - 1 for t in differing_observation_steps if t >= 1]
        last = int(a.evaluator["last_clue_step"])
        post_clue_target_count = len(a.images) - 1 - last
        post_clue_differences = sum(t >= last for t in differing_prediction_input_times)
        records.append({"route_id": route_id, "top_clue": int(top_clue),
                        "differing_observation_steps": differing_observation_steps,
                        "differing_prediction_input_times": differing_prediction_input_times,
                        "last_clue_step": last, "post_clue_targets": post_clue_target_count,
                        "post_clue_target_differences": post_clue_differences})
    summary = {"status": "post-hoc deterministic target audit, not primary experimental result",
               "observed_episode_pairs": len(records),
               "prediction_input_times_with_clue_dependent_targets": sorted({
                   t for r in records for t in r["differing_prediction_input_times"]}),
               "post_clue_target_comparisons": sum(r["post_clue_targets"] for r in records),
               "post_clue_target_differences": sum(r["post_clue_target_differences"] for r in records),
               "interpretation": "Only t=0 next-view targets depend on clue identity; this objective does not require retaining clue identity over the measured decision delay",
               "caveat": "Does not identify why optimization failed for one seed or exclude benefits in another task",
               "pairs": records}
    write_json(ROOT / "results/target_dependence_diagnostic.json", summary)
    print({k: v for k, v in summary.items() if k != "pairs"})


if __name__ == "__main__":
    main()
