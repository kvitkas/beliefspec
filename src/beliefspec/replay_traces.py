"""Execute the selected real model trace choices in the simulator."""

import json

from beliefspec.dataio import load_dataset, write_json
from beliefspec.experiment import ROOT
from beliefspec.task import replay_choice


def main():
    episodes = {e.evaluator["episode_id"]: e for e in load_dataset(ROOT / "data/test", with_evaluator=True)}
    results = []
    for name in ("observed_success", "observed_failure", "unavailable_failure"):
        path = ROOT / f"results/traces/{name}.json"
        trace = json.loads(path.read_text())
        row = trace["result"]
        replay = replay_choice(episodes[row["episode_id"]], bool(int(row["choose_top"])))
        if replay["success"] != bool(int(row["success"])) or not replay["terminated"]:
            raise RuntimeError(f"Trace replay mismatch: {name}")
        results.append({"trace": str(path.relative_to(ROOT)), "episode_id": row["episode_id"],
                        "method": row["method"], "training_seed": row["training_seed"],
                        "postdecision_actions": [2, 0, 2] if int(row["choose_top"]) else [2, 1, 2],
                        **replay})
    write_json(ROOT / "results/traces/simulator_replays.json", results)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
