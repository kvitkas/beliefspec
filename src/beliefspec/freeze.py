"""Hash selected checkpoints, sources and evaluation data before final scoring."""

import json
from datetime import UTC, datetime

from beliefspec.dataio import file_sha256, write_json
from beliefspec.experiment import ROOT


def main():
    destination = ROOT / "artifacts/freeze.json"
    if destination.exists():
        raise FileExistsError("Freeze exists; preserve the original decision record")
    config = json.loads((ROOT / "configs/frozen.json").read_text())
    paths = [ROOT / "configs/frozen.json", ROOT / "docs/protocol.md"]
    paths += list((ROOT / "src/beliefspec").glob("*.py"))
    for split in ("train", "validation", "test"):
        paths += list((ROOT / f"data/{split}").glob("*"))
    for seed in config["seeds"]:
        for variant in ("control", "predictive"):
            run = ROOT / f"runs/main/{variant}_{seed}"
            paths.extend(run / name for name in ("best.pt", "config.json", "result.json", "history.jsonl"))
    paths.extend(ROOT / name for name in (
        "artifacts/main_execution.json", "artifacts/settings_freeze.json",
        "artifacts/environment.json", "requirements.lock.txt",
        "artifacts/audit_train_validation_test.json"))
    if (ROOT / "results/final").exists():
        raise RuntimeError("Final outcomes already exist")
    write_json(destination, {"utc": datetime.now(UTC).isoformat(),
                             "model_outcomes_on_test_inspected": False,
                             "primary": "paired seed difference on observed clues, equal delay weight",
                             "episodes": config["routes_per_delay"]["test"] * 3 * 8,
                             "files": {str(p.relative_to(ROOT)): file_sha256(p) for p in sorted(paths)}})
    print(f"Frozen {len(paths)} files before final model evaluation")


if __name__ == "__main__":
    main()
