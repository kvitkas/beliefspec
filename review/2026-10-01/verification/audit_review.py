"""Independent review audit for the BeliefSpec pilot package.

This script intentionally reads raw saved records and frozen files directly.
It does not import or trust existing summary JSON files for the values it
recomputes here.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

from beliefspec.dataio import load_dataset, visible_hash
from beliefspec.experiment import infer, load_model
from beliefspec.model import MemoryModel, baseline_probabilities, clue_to_choice
from beliefspec.task import visible_history_hash


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def relative_to_root(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def freeze_check(root: Path) -> dict[str, Any]:
    publication_helper = root / "review/2026-10-02/verify_publication.py"
    if not publication_helper.exists():
        raise FileNotFoundError(
            "publication provenance helper is required at review/2026-10-02/verify_publication.py"
        )
    spec = importlib.util.spec_from_file_location("verify_publication", publication_helper)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    report = module.verify_publication(root)
    report["mode"] = "publication_copy"
    return report


def audit_splits(root: Path) -> dict[str, Any]:
    datasets = {
        split: load_dataset(root / "data" / split, with_evaluator=True)
        for split in ("train", "validation", "test")
    }
    visible_sets = {split: {visible_hash(ep) for ep in episodes} for split, episodes in datasets.items()}
    overlap = {}
    for first, second in (("train", "validation"), ("train", "test"), ("validation", "test")):
        overlap[f"{first}:{second}"] = len(visible_sets[first] & visible_sets[second])

    split_reports = {}
    label_mismatches = []
    for split, episodes in datasets.items():
        balanced = Counter()
        observed_success = []
        never_success = []
        delays = set()
        for episode in episodes:
            structured = baseline_probabilities(episode, "structured")
            structured_label = int(np.argmax(structured))
            if structured_label != int(episode.observed_clue):
                label_mismatches.append(
                    {
                        "split": split,
                        "episode_id": episode.evaluator["episode_id"],
                        "structured_label": structured_label,
                        "observed_clue": int(episode.observed_clue),
                    }
                )
            choice = clue_to_choice(structured, episode.top_clue)
            success = int(choice == bool(episode.evaluator["correct_top"]))
            if int(episode.observed_clue) == 2:
                never_success.append(success)
            else:
                observed_success.append(success)
                delays.add(int(episode.evaluator["delay"]))
            balanced[
                (
                    int(episode.evaluator["wait"]),
                    int(episode.observed_clue) == 2,
                    int(episode.evaluator["hidden_clue"]),
                    int(episode.top_clue),
                )
            ] += 1
        split_reports[split] = {
            "episodes": len(episodes),
            "unique_visible_hashes": len(visible_sets[split]),
            "delays": sorted(delays),
            "factorial_cell_counts": sorted(set(balanced.values())),
            "structured_observed_success": float(np.mean(observed_success)),
            "structured_never_success": float(np.mean(never_success)),
        }
    return {
        "splits": split_reports,
        "overlap": overlap,
        "label_mismatch_count": len(label_mismatches),
        "label_mismatches": label_mismatches[:20],
    }


def summarize_episode_rows(root: Path) -> dict[str, Any]:
    rows = read_csv(root / "results/final/episodes.csv")
    episodes = load_dataset(root / "data/test", with_evaluator=True)
    by_episode = {episode.evaluator["episode_id"]: episode for episode in episodes}
    by_method_seed = defaultdict(list)
    for row in rows:
        by_method_seed[(row["method"], row["training_seed"])].append(row)

    expected_groups = {
        ("current", ""),
        ("recent", ""),
        ("structured", ""),
        ("episodic", ""),
        ("control", "11"),
        ("predictive", "11"),
        ("control", "22"),
        ("predictive", "22"),
        ("control", "33"),
        ("predictive", "33"),
    }
    missing_groups = sorted(expected_groups - set(by_method_seed))
    extra_groups = sorted(set(by_method_seed) - expected_groups)

    row_mismatches = []
    seen_row_keys = set()
    for row in rows:
        episode = by_episode.get(row["episode_id"])
        if episode is None:
            row_mismatches.append({"episode_id": row["episode_id"], "reason": "missing test episode"})
            continue
        row_key = (row["method"], row["training_seed"], row["episode_id"])
        if row_key in seen_row_keys:
            row_mismatches.append({"episode_id": row["episode_id"], "reason": "duplicate method/seed row"})
        seen_row_keys.add(row_key)
        probabilities = [float(row["p_key"]), float(row["p_ball"]), float(row["p_unknown"])]
        readout = int(np.argmax(probabilities))
        choose_top = int(clue_to_choice(probabilities, int(row["top_clue"])))
        success = int(bool(choose_top) == bool(episode.evaluator["correct_top"]))
        expected_values = {
            "hidden_clue": int(episode.evaluator["hidden_clue"]),
            "split": episode.evaluator["split"],
            "route_id": episode.evaluator["route_id"],
            "wait": int(episode.evaluator["wait"]),
            "correct_top": str(bool(episode.evaluator["correct_top"])),
            "clue_observed": str(bool(episode.evaluator["clue_observed"])),
            "observed_clue": int(episode.observed_clue),
            "top_clue": int(episode.top_clue),
            "length": len(episode.images),
            "visible_hash": visible_history_hash(episode),
            "visible_sha256": visible_hash(episode),
            "readout": readout,
            "readout_correct": int(readout == int(episode.observed_clue)),
            "choose_top": choose_top,
            "success": success,
        }
        if episode.evaluator["delay"] is None:
            expected_values["delay"] = ""
            expected_values["last_clue_step"] = ""
        else:
            expected_values["delay"] = int(episode.evaluator["delay"])
            expected_values["last_clue_step"] = int(episode.evaluator["last_clue_step"])
        for field, expected in expected_values.items():
            actual = row[field]
            if isinstance(expected, int):
                matches = actual != "" and int(actual) == expected
            else:
                matches = actual == expected
            if not matches:
                row_mismatches.append(
                    {
                        "episode_id": row["episode_id"],
                        "method": row["method"],
                        "training_seed": row["training_seed"],
                        "field": field,
                        "expected": expected,
                        "actual": actual,
                    }
                )
                break

    expected_ids = set(by_episode)
    group_integrity = {}
    paired_visible_reference = None
    paired_visible_mismatches = []
    for key, group in sorted(by_method_seed.items()):
        ids = [row["episode_id"] for row in group]
        visible_hashes = {row["episode_id"]: row["visible_sha256"] for row in group}
        key_name = f"{key[0]}:{key[1]}"
        group_integrity[key_name] = {
            "rows": len(group),
            "unique_episode_ids": len(set(ids)),
            "matches_test_episode_set": set(ids) == expected_ids,
        }
        if paired_visible_reference is None:
            paired_visible_reference = visible_hashes
        elif visible_hashes != paired_visible_reference:
            paired_visible_mismatches.append(key_name)

    scores = {}
    delay_scores = {}
    readout_prediction_means = {}
    for key, group in sorted(by_method_seed.items()):
        observed = [row for row in group if row["observed_clue"] != "2"]
        never = [row for row in group if row["observed_clue"] == "2"]
        key_name = f"{key[0]}:{key[1]}"
        scores[f"{key[0]}:{key[1]}"] = {
            "rows": len(group),
            "observed_success": float(np.mean([int(row["success"]) for row in observed])),
            "never_success": float(np.mean([int(row["success"]) for row in never])),
        }
        delay_scores[key_name] = {
            wait: float(np.mean([int(row["success"]) for row in observed if row["wait"] == wait]))
            for wait in sorted({row["wait"] for row in observed}, key=int)
        }
        readout_prediction_means[key_name] = {
            "observed_readout_accuracy": float(
                np.mean([int(row["readout_correct"]) for row in observed])
            ),
            "never_readout_accuracy": float(np.mean([int(row["readout_correct"]) for row in never])),
        }
        if key[0] in ("control", "predictive"):
            readout_prediction_means[key_name].update(
                {
                    "observed_prediction_ce": float(
                        np.mean([float(row["prediction_ce"]) for row in observed])
                    ),
                    "observed_prediction_accuracy": float(
                        np.mean([float(row["prediction_accuracy"]) for row in observed])
                    ),
                    "observed_copy_accuracy": float(
                        np.mean([float(row["copy_accuracy"]) for row in observed])
                    ),
                }
            )

    primary_seed_differences = []
    for seed in ("11", "22", "33"):
        control_delays = delay_scores[f"control:{seed}"]
        predictive_delays = delay_scores[f"predictive:{seed}"]
        control_mean = float(np.mean(list(control_delays.values())))
        predictive_mean = float(np.mean(list(predictive_delays.values())))
        primary_seed_differences.append(
            {
                "training_seed": int(seed),
                "control": control_mean,
                "predictive": predictive_mean,
                "difference": predictive_mean - control_mean,
            }
        )
    diffs = [row["difference"] for row in primary_seed_differences]
    seed_sd = float(np.std(diffs, ddof=1))
    t_critical_df2_95 = 4.302652729911275
    margin = t_critical_df2_95 * seed_sd / np.sqrt(len(diffs))
    return {
        "episode_rows": len(rows),
        "method_seed_group_count": len(by_method_seed),
        "missing_groups": missing_groups,
        "extra_groups": extra_groups,
        "row_integrity_mismatch_count": len(row_mismatches),
        "row_integrity_mismatches": row_mismatches[:20],
        "group_integrity": group_integrity,
        "paired_visible_hash_mismatches": paired_visible_mismatches,
        "scores": scores,
        "success_by_observed_delay": delay_scores,
        "readout_prediction_means": readout_prediction_means,
        "primary_seed_differences": primary_seed_differences,
        "primary_mean_difference": float(np.mean(diffs)),
        "primary_seed_sd": seed_sd,
        "primary_descriptive_95_t_interval": [
            float(np.mean(diffs) - margin),
            float(np.mean(diffs) + margin),
        ],
    }


def audit_runs(root: Path) -> dict[str, Any]:
    frozen_config = read_json(root / "configs/frozen.json")
    run_reports = []
    state_shapes = None
    shape_mismatches = []
    for seed in frozen_config["seeds"]:
        for variant in ("control", "predictive"):
            run = root / f"runs/main/{variant}_{seed}"
            config = read_json(run / "config.json")
            result = read_json(run / "result.json")
            history = [json.loads(line) for line in (run / "history.jsonl").read_text().splitlines()]
            validation_losses = [row["validation_task_ce"] for row in history]
            min_loss = min(validation_losses)
            expected_epoch = next(
                row["epoch"] for row in history if row["validation_task_ce"] == min_loss
            )
            model, payload = load_model(run / "best.pt")
            shapes = {name: list(value.shape) for name, value in model.state_dict().items()}
            if state_shapes is None:
                state_shapes = shapes
            elif shapes != state_shapes:
                shape_mismatches.append({"variant": variant, "seed": seed})
            expected_config = {**frozen_config, "seed": seed, "variant": variant}
            run_reports.append(
                {
                    "variant": variant,
                    "seed": seed,
                    "config_matches_frozen_plus_run_fields": config == expected_config,
                    "selected_epoch": result["best_epoch"],
                    "validation_min_epoch": expected_epoch,
                    "selected_epoch_matches_validation_min": result["best_epoch"] == expected_epoch,
                    "checkpoint_epoch": payload["epoch"],
                    "checkpoint_epoch_matches_result": payload["epoch"] == result["best_epoch"],
                    "parameter_counts": model.counts(),
                }
            )
    reference_model = MemoryModel(frozen_config["encoder_size"], frozen_config["hidden_size"])
    return {
        "runs": run_reports,
        "all_configs_match": all(row["config_matches_frozen_plus_run_fields"] for row in run_reports),
        "all_selected_epochs_match_validation_min": all(
            row["selected_epoch_matches_validation_min"] for row in run_reports
        ),
        "all_checkpoint_epochs_match_results": all(
            row["checkpoint_epoch_matches_result"] for row in run_reports
        ),
        "state_shape_mismatches": shape_mismatches,
        "reference_parameter_counts": reference_model.counts(),
    }


def audit_target_dependence(root: Path) -> dict[str, Any]:
    episodes = load_dataset(root / "data/test", with_evaluator=True)
    twins = defaultdict(list)
    for episode in episodes:
        if int(episode.observed_clue) != 2:
            twins[(episode.evaluator["route_id"], int(episode.top_clue))].append(episode)

    pair_reports = []
    bad_pairs = []
    for key, pair in sorted(twins.items()):
        if len(pair) != 2:
            bad_pairs.append({"key": list(key), "count": len(pair)})
            continue
        first, second = pair
        if not np.array_equal(first.actions, second.actions):
            bad_pairs.append({"key": list(key), "reason": "actions differ"})
            continue
        differing_observation_steps = np.flatnonzero(
            np.any(first.images != second.images, axis=(1, 2))
        ).tolist()
        differing_prediction_input_times = [
            step - 1 for step in differing_observation_steps if step >= 1
        ]
        last_clue_step = int(first.evaluator["last_clue_step"])
        post_clue_targets = len(first.images) - 1 - last_clue_step
        post_clue_differences = sum(
            time_index >= last_clue_step for time_index in differing_prediction_input_times
        )
        pair_reports.append(
            {
                "route_id": key[0],
                "top_clue": key[1],
                "differing_observation_steps": differing_observation_steps,
                "differing_prediction_input_times": differing_prediction_input_times,
                "last_clue_step": last_clue_step,
                "post_clue_targets": post_clue_targets,
                "post_clue_target_differences": post_clue_differences,
            }
        )
    return {
        "observed_episode_pairs": len(pair_reports),
        "bad_pairs": bad_pairs,
        "differing_observation_step_sets": sorted(
            {tuple(row["differing_observation_steps"]) for row in pair_reports}
        ),
        "prediction_input_times_with_clue_dependent_targets": sorted(
            {
                time_index
                for row in pair_reports
                for time_index in row["differing_prediction_input_times"]
            }
        ),
        "post_clue_target_comparisons": sum(row["post_clue_targets"] for row in pair_reports),
        "post_clue_target_differences": sum(
            row["post_clue_target_differences"] for row in pair_reports
        ),
    }


def reinfer_all_checkpoints(root: Path) -> dict[str, Any]:
    rows = read_csv(root / "results/final/episodes.csv")
    episodes = load_dataset(root / "data/test", with_evaluator=True)
    by_run_rows = {
        (variant, str(seed)): {
            row["episode_id"]: row
            for row in rows
            if row["method"] == variant and row["training_seed"] == str(seed)
        }
        for seed in (11, 22, 33)
        for variant in ("control", "predictive")
    }
    run_reports = []
    mismatch_examples = []
    started = time.perf_counter()
    with torch.no_grad():
        for seed in (11, 22, 33):
            for variant in ("control", "predictive"):
                model, _ = load_model(root / f"runs/main/{variant}_{seed}/best.pt")
                probabilities, metrics = infer(model, episodes)
                expected = by_run_rows[(variant, str(seed))]
                max_probability_difference = 0.0
                max_metric_difference = 0.0
                success_mismatches = 0
                readout_mismatches = 0
                for episode, probability, metric in zip(episodes, probabilities, metrics):
                    row = expected[episode.evaluator["episode_id"]]
                    for field, actual in (
                        ("p_key", probability[0]),
                        ("p_ball", probability[1]),
                        ("p_unknown", probability[2]),
                    ):
                        diff = abs(float(row[field]) - float(actual))
                        max_probability_difference = max(max_probability_difference, diff)
                    for field in ("prediction_ce", "prediction_accuracy", "copy_accuracy"):
                        diff = abs(float(row[field]) - float(metric[field]))
                        max_metric_difference = max(max_metric_difference, diff)
                    readout = int(np.argmax(probability))
                    choose_top = int(clue_to_choice(probability, int(episode.top_clue)))
                    success = int(bool(choose_top) == bool(episode.evaluator["correct_top"]))
                    if readout != int(row["readout"]):
                        readout_mismatches += 1
                    if success != int(row["success"]):
                        success_mismatches += 1
                        if len(mismatch_examples) < 10:
                            mismatch_examples.append(
                                {
                                    "variant": variant,
                                    "seed": seed,
                                    "episode_id": episode.evaluator["episode_id"],
                                    "expected_success": int(row["success"]),
                                    "actual_success": success,
                                }
                            )
                run_reports.append(
                    {
                        "variant": variant,
                        "seed": seed,
                        "episodes": len(episodes),
                        "max_probability_difference": max_probability_difference,
                        "max_prediction_metric_difference": max_metric_difference,
                        "readout_mismatches": readout_mismatches,
                        "success_mismatches": success_mismatches,
                    }
                )
    return {
        "seconds": time.perf_counter() - started,
        "runs": run_reports,
        "mismatch_examples": mismatch_examples,
    }


def compare_reproduction(root: Path, reproduction: Path | None) -> dict[str, Any]:
    if reproduction is None:
        return {"provided": False}
    verification = reproduction / "verification.json"
    if not verification.exists():
        return {"provided": True, "exists": False, "path": relative_to_root(root, verification)}
    data = read_json(verification)
    expected_rows = read_csv(root / "results/final/episodes.csv")
    checked_runs = []
    for run in data["runs"]:
        expected = [
            row
            for row in expected_rows
            if row["method"] == run["variant"] and row["training_seed"] == str(run["seed"])
        ]
        checked_runs.append(
            {
                **run,
                "expected_episode_rows_for_run": len(expected),
            }
        )
    return {
        "provided": True,
        "exists": True,
        "path": relative_to_root(root, verification),
        "data_regeneration": data["data_regeneration"],
        "runs": checked_runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stage", required=True, choices=["before", "after"])
    parser.add_argument("--reproduction", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    reproduction = Path(args.reproduction).resolve() if args.reproduction else None

    audit_started = time.perf_counter()
    before = freeze_check(root)
    report = {
        "stage": args.stage,
        "root": ".",
        "output": relative_to_root(root, output),
        "frozen_sha_check_before": before,
        "split_audit": audit_splits(root),
        "raw_episode_results": summarize_episode_rows(root),
        "run_audit": audit_runs(root),
        "target_dependence_audit": audit_target_dependence(root),
        "re_inference_audit": reinfer_all_checkpoints(root),
        "representative_reproduction": compare_reproduction(root, reproduction),
        "frozen_sha_check_after": freeze_check(root),
        "verified_here": [
            "frozen file hashes",
            "split visible-hash overlap",
            "labels derived from structured observed history and evaluator metadata",
            "raw episode-level readout, choice, and success recomputation",
            "six run configs, architecture shapes, and validation-min checkpoint epochs",
            "all six saved checkpoints re-inferred on 768 held-out episodes",
            "descriptive seed-level t interval, readout means, and prediction means",
            "saved test NPZ target dependence",
            "representative reproduction verification when supplied",
        ],
        "supplied_not_reverified_here": [
            "source-paper claims",
            "PDF rendering fidelity",
            "public GitHub upload state",
            "all-six-run retraining reproduction",
        ],
    }
    failures = []
    if (
        before["mismatch_count"]
        or report["frozen_sha_check_after"]["mismatch_count"]
        or not before["passed"]
        or not report["frozen_sha_check_after"]["passed"]
    ):
        failures.append("frozen_sha_mismatch")
    if any(report["split_audit"]["overlap"].values()):
        failures.append("split_visible_hash_overlap")
    expected_split_counts = {
        "train": {"episodes": 1536, "unique_visible_hashes": 1152},
        "validation": {"episodes": 384, "unique_visible_hashes": 288},
        "test": {"episodes": 768, "unique_visible_hashes": 576},
    }
    for split, expected in expected_split_counts.items():
        actual = report["split_audit"]["splits"][split]
        if any(actual[field] != expected[field] for field in expected):
            failures.append("split_count_mismatch")
            break
    if report["split_audit"]["label_mismatch_count"]:
        failures.append("label_mismatch")
    if report["raw_episode_results"]["episode_rows"] != 7680:
        failures.append("episode_row_count")
    if report["raw_episode_results"]["missing_groups"] or report["raw_episode_results"]["extra_groups"]:
        failures.append("method_seed_groups")
    if report["raw_episode_results"]["row_integrity_mismatch_count"]:
        failures.append("row_integrity_mismatch")
    bad_group_counts = [
        name
        for name, group in report["raw_episode_results"]["group_integrity"].items()
        if group["rows"] != 768
        or group["unique_episode_ids"] != 768
        or not group["matches_test_episode_set"]
    ]
    if bad_group_counts:
        failures.append("method_seed_group_episode_pairing")
    if report["raw_episode_results"]["paired_visible_hash_mismatches"]:
        failures.append("paired_visible_hash_mismatch")
    if not report["run_audit"]["all_configs_match"]:
        failures.append("run_config_mismatch")
    if not report["run_audit"]["all_selected_epochs_match_validation_min"]:
        failures.append("checkpoint_selection_mismatch")
    if not report["run_audit"]["all_checkpoint_epochs_match_results"]:
        failures.append("checkpoint_epoch_mismatch")
    if report["run_audit"]["state_shape_mismatches"]:
        failures.append("architecture_shape_mismatch")
    reinfer_bad = [
        row
        for row in report["re_inference_audit"]["runs"]
        if row["episodes"] != 768
        or row["max_probability_difference"] > 1e-6
        or row["max_prediction_metric_difference"] > 1e-6
        or row["readout_mismatches"]
        or row["success_mismatches"]
    ]
    if reinfer_bad:
        failures.append("checkpoint_reinference_mismatch")
    target = report["target_dependence_audit"]
    if target["observed_episode_pairs"] != 192:
        failures.append("target_pair_count")
    if target["bad_pairs"]:
        failures.append("target_bad_pairs")
    if target["differing_observation_step_sets"] != [(0, 1)]:
        failures.append("target_differing_observation_steps")
    if target["prediction_input_times_with_clue_dependent_targets"] != [0]:
        failures.append("target_prediction_times")
    if target["post_clue_target_comparisons"] != 6336:
        failures.append("post_clue_target_comparison_count")
    if target["post_clue_target_differences"] != 0:
        failures.append("post_clue_target_differences")
    reproduction_report = report["representative_reproduction"]
    if reproduction_report["provided"]:
        if not reproduction_report.get("exists", False):
            failures.append("reproduction_missing")
        for split, row in reproduction_report.get("data_regeneration", {}).items():
            expected_episodes = expected_split_counts[split]["episodes"]
            if row["episodes"] != expected_episodes or not row["ordered_visible_hashes_match"]:
                failures.append("reproduction_data_regeneration_mismatch")
        for row in reproduction_report.get("runs", []):
            if not row["exact_checkpoint_tensors"] or not row["all_episode_successes_identical"]:
                failures.append("reproduction_mismatch")
            if row["expected_episode_rows_for_run"] != 768:
                failures.append("reproduction_expected_row_count")
    report["passed"] = not failures
    report["failures"] = failures
    report["audit_runtime_seconds"] = time.perf_counter() - audit_started
    write_json(output, report)
    print(
        json.dumps(
            {
                "output": relative_to_root(root, output),
                "passed": report["passed"],
                "failures": failures,
                "audit_runtime_seconds": report["audit_runtime_seconds"],
            },
            indent=2,
        )
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
