"""Execute the frozen six-run plan sequentially and preserve failures."""

import json
import resource
import time
import traceback
from datetime import UTC, datetime

from beliefspec.dataio import file_sha256, load_dataset, write_json
from beliefspec.experiment import ROOT, train


def main():
    config_path = ROOT / "configs/frozen.json"
    config = json.loads(config_path.read_text())
    if (ROOT / "runs/main").exists() or (ROOT / "artifacts/settings_freeze.json").exists():
        raise FileExistsError("Original main execution exists; use beliefspec.reproduce")
    write_json(ROOT / "artifacts/settings_freeze.json", {
        "utc": datetime.now(UTC).isoformat(), "config_sha256": file_sha256(config_path),
        "main_seeds": config["seeds"], "heldout_model_outcomes_inspected": False,
        "note": "Main settings fixed after seed101 development and before main training"})
    training = load_dataset(ROOT / "data/train")
    validation = load_dataset(ROOT / "data/validation")
    started = time.perf_counter()
    runs = []
    for seed in config["seeds"]:
        for variant in ("control", "predictive"):
            destination = ROOT / f"runs/main/{variant}_{seed}"
            try:
                result = train(config, seed, variant, training, validation, destination)
                runs.append(result)
            except FileExistsError:
                raise
            except Exception as error:
                failure = {"status": "failed", "seed": seed, "variant": variant,
                           "error": repr(error), "traceback": traceback.format_exc()}
                runs.append(failure)
                write_json(destination / "failure.json", failure)
                write_json(ROOT / "artifacts/main_execution.json", {"runs": runs})
                raise
    usage = resource.getrusage(resource.RUSAGE_SELF)
    write_json(ROOT / "artifacts/main_execution.json", {
        "runs": runs, "total_wall_seconds": time.perf_counter() - started,
        "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
        "peak_rss_bytes_macos": usage.ru_maxrss, "device": "cpu", "torch_threads": 2})


if __name__ == "__main__":
    main()
