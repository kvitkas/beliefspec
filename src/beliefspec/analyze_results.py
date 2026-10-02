"""Regenerate tables and publication-style plots solely from saved records."""

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from beliefspec.dataio import load_dataset, write_json
from beliefspec.experiment import ROOT, load_model, setup
from beliefspec.model import collate

LABELS = {"current": "Current view", "recent": "Recent 32", "structured": "Structured",
          "episodic": "Episodic", "control": "GRU task only", "predictive": "GRU + prediction"}


def read_csv(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream))


def mean(rows, field):
    return float(np.mean([float(r[field]) for r in rows]))


def summarize(rows):
    table = []
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["method"], row["training_seed"], row["wait"], row["observed_clue"] == "2")].append(row)
    for (method, seed, wait, never), group in grouped.items():
        entry = {"method": method, "training_seed": seed, "wait": int(wait), "never": never,
                 "episodes": len(group), "delay": None if never else int(group[0]["delay"]),
                 "success": mean(group, "success"), "readout_accuracy": mean(group, "readout_correct")}
        if method in ("control", "predictive"):
            entry.update({field: mean(group, field) for field in
                          ("prediction_ce", "prediction_accuracy", "copy_accuracy")})
        table.append(entry)
    seeds = sorted({r["training_seed"] for r in rows if r["method"] == "control"})
    contrasts = []
    for seed in seeds:
        scores = {method: float(np.mean([r["success"] for r in table
                                        if r["method"] == method and r["training_seed"] == seed
                                        and not r["never"]]))
                  for method in ("control", "predictive")}
        contrasts.append({"training_seed": int(seed), **scores,
                          "difference": scores["predictive"] - scores["control"]})
    differences = np.asarray([r["difference"] for r in contrasts])
    sd = float(np.std(differences, ddof=1))
    margin = 4.302652729911275 * sd / np.sqrt(len(differences))
    primary = {"contrast": "predictive_minus_control_observed_equal_delay_weight",
               "seed_results": contrasts, "mean_difference": float(differences.mean()),
               "seed_sd": sd, "descriptive_95_t_interval":
               [float(differences.mean() - margin), float(differences.mean() + margin)],
               "training_replications": len(differences),
               "warning": "df=2, unstable interval; conditional on fixed evaluation routes/layout; not an episode-binomial CI"}
    return table, primary


def figures(table, rows, destination):
    destination.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.dpi": 140, "savefig.bbox": "tight"})
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    colors = {"current": "#777777", "recent": "#a56518", "structured": "#24835c",
              "episodic": "#74ad92", "control": "#236cb4", "predictive": "#b93f67"}
    for method, label in LABELS.items():
        for panel, never in enumerate((False, True)):
            data = [r for r in table if r["method"] == method and r["never"] == never]
            waits = sorted({r["wait"] for r in data})
            x, y, lower, upper = [], [], [], []
            for wait in waits:
                group = [r for r in data if r["wait"] == wait]
                values = [r["success"] for r in group]
                x.append(wait if never else group[0]["delay"])
                y.append(np.mean(values))
                lower.append(np.mean(values) - min(values))
                upper.append(max(values) - np.mean(values))
            axes[panel].errorbar(x, y, yerr=[lower, upper], label=label,
                                color=colors[method], marker="o", capsize=3,
                                linestyle="--" if method == "episodic" else "-", alpha=0.9)
    axes[0].set(xlabel="Steps since last clue observation", ylabel="Forced-choice success",
                title="Clue observed: mean and training-seed range", ylim=(-0.04, 1.04))
    axes[1].set(xlabel="Added wait steps (clue delay undefined)", title="Clue never observed",
                ylim=(-0.04, 1.04))
    for ax in axes:
        ax.axhline(0.5, color="#aaaaaa", linestyle=":", linewidth=1)
    axes[0].legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(destination / "decision_success.png")
    fig.savefig(destination / "decision_success.pdf")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for method in ("control", "predictive"):
        data = [r for r in table if r["method"] == method and not r["never"]]
        seeds = sorted({r["training_seed"] for r in data})
        for panel, metric in enumerate(("prediction_ce", "readout_accuracy")):
            values = [np.mean([r[metric] for r in data if r["training_seed"] == s]) for s in seeds]
            position = 0 if method == "control" else 1
            axes[panel].scatter([position - .07, position, position + .07], values,
                                c=colors[method], s=40, zorder=3)
            axes[panel].plot([position - .18, position + .18], [np.mean(values)] * 2,
                             color=colors[method], linewidth=2)
    for ax in axes:
        ax.set_xticks([0, 1], ["Task only", "+ prediction"])
        ax.set_xlim(-.5, 1.5)
    axes[0].set(ylabel="Next-view cross-entropy (nats/cell)",
                title="Task-only prediction head is untrained")
    axes[1].set(ylabel="Three-class clue readout accuracy", ylim=(-.04, 1.04),
                title="Observed clues; one point per training seed")
    fig.tight_layout()
    fig.savefig(destination / "prediction_and_memory.png")
    fig.savefig(destination / "prediction_and_memory.pdf")
    plt.close(fig)


def traces(rows, destination):
    import torch
    episodes = load_dataset(ROOT / "data/test", with_evaluator=True)
    lookup = {e.evaluator["episode_id"]: e for e in episodes}
    candidates = [r for r in rows if r["method"] == "predictive" and r["training_seed"] == "11"]
    selected = []
    for tag, predicate in (("observed_success", lambda r: r["observed_clue"] != "2" and r["success"] == "1"),
                           ("observed_failure", lambda r: r["observed_clue"] != "2" and r["success"] == "0"),
                           ("unavailable_failure", lambda r: r["observed_clue"] == "2" and r["success"] == "0")):
        match = next((r for r in candidates if predicate(r)), None)
        if match:
            selected.append((tag, match))
    model, checkpoint = load_model(ROOT / "runs/main/predictive_11/best.pt")
    setup(0)
    for tag, row in selected:
        episode = lookup[row["episode_id"]]
        batch = collate([episode])
        with torch.no_grad():
            output = model(batch)
            readout_over_time = model.readout(output["states"])[0].softmax(-1).numpy()
            predicted_views = output["prediction_logits"][0].argmax(-1).numpy()
        steps = []
        for t in range(len(episode.images)):
            step = {"t": t, "image_object_ids": episode.images[t].tolist(),
                    "direction": int(episode.directions[t]), "phase": int(episode.stages[t]),
                    "previous_action": int(episode.prev_actions[t]),
                    "readout_probabilities": readout_over_time[t].tolist(),
                    "state_l2": float(output["states"][0, t].norm())}
            if t < len(episode.actions):
                step["action"] = int(episode.actions[t])
                step["predicted_next_image"] = predicted_views[t].tolist()
                step["next_cell_accuracy"] = float(np.mean(predicted_views[t] == episode.images[t + 1]))
            steps.append(step)
        write_json(destination / f"{tag}.json", {"selection": tag, "result": row,
                                                 "checkpoint_epoch": checkpoint["epoch"], "steps": steps,
                                                 "caution": "Intermediate readout is diagnostic; trained at final step only"})


def learning_curves(destination):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    diagnostics = []
    for variant, color in (("control", "#236cb4"), ("predictive", "#b93f67")):
        for seed in (11, 22, 33):
            run = ROOT / f"runs/main/{variant}_{seed}"
            history = [json.loads(line) for line in (run / "history.jsonl").read_text().splitlines()]
            result = json.loads((run / "result.json").read_text())
            for panel, metric in enumerate(("validation_readout_accuracy", "validation_prediction_ce")):
                axes[panel].plot([r["epoch"] for r in history], [r[metric] for r in history],
                                 color=color, alpha=.6, label=LABELS[variant] if seed == 11 else None)
            diagnostics.append({"variant": variant, "training_seed": seed,
                                "first_validation_readout_99_epoch": next(
                                    (r["epoch"] for r in history if r["validation_readout_accuracy"] >= .99), None),
                                "selected_epoch": result["best_epoch"],
                                "seconds": result["seconds"], "parameters": result["parameters"]})
    axes[0].set(xlabel="Training epoch", ylabel="Validation readout accuracy", ylim=(-.04, 1.04))
    axes[1].set(xlabel="Training epoch", ylabel="Validation next-view CE (nats/cell)")
    axes[0].legend(fontsize=8)
    fig.suptitle("Development-set learning curves: all three main training seeds")
    fig.tight_layout()
    fig.savefig(destination / "learning_curves.png")
    fig.savefig(destination / "learning_curves.pdf")
    plt.close(fig)
    write_json(ROOT / "results/training_summary.json", diagnostics)


def main():
    rows = read_csv(ROOT / "results/final/episodes.csv")
    table, primary = summarize(rows)
    write_json(ROOT / "results/summary.json", {"primary": primary, "by_condition": table})
    figures(table, rows, ROOT / "results/figures")
    learning_curves(ROOT / "results/figures")
    traces(rows, ROOT / "results/traces")
    intervention_rows = read_csv(ROOT / "results/final/interventions.csv")
    grouped = defaultdict(list)
    for row in intervention_rows:
        grouped[(row["method"], row["training_seed"], row["observed_clue"] == "2",
                 row["intervention"])].append(row)
    write_json(ROOT / "results/intervention_summary.json", [
        {"method": k[0], "seed": k[1], "never": k[2], "intervention": k[3],
         "success": mean(v, "success"), "episodes": len(v)} for k, v in grouped.items()])
    print(json.dumps(primary, indent=2))


if __name__ == "__main__":
    main()
