"""Regenerate review figures from original records, without changing originals."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

from beliefspec.analyze_results import figures, summarize
from beliefspec.dataio import load_dataset

ROOT = Path(__file__).resolve().parents[2]


def task_illustration(destination):
    episodes = load_dataset(ROOT / "data/test", with_evaluator=True)
    episode_id = "test:test-w8-r0:h0:top0:seen"
    episode = next(e for e in episodes if e.evaluator["episode_id"] == episode_id)
    colors = ["#edf0f3", "#ffffff", "#596674", "#e5c07b", "#e5c07b",
              "#e5ae32", "#56a9c7", "#eeeeee", "#eeeeee", "#eeeeee", "#eeeeee"]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(-0.5, 11.5), cmap.N)
    fig, axes = plt.subplots(1, 4, figsize=(10, 3.2))
    frames = (0, 1, 10, 18)
    titles = ("t = 0: clue visible", "t = 1: last clue view",
              "t = 10: clue absent", "t = 18: final options")
    for ax, t, title in zip(axes, frames, titles):
        # MiniGrid arrays use (x, y), so transpose for horizontal x plotting.
        ax.imshow(episode.images[t].T, cmap=cmap, norm=norm, interpolation="nearest")
        for object_id, letter in ((5, "K"), (6, "B")):
            for x, y in np.argwhere(episode.images[t] == object_id):
                ax.text(x, y, letter, ha="center", va="center", weight="bold", fontsize=11)
        ax.set_xticks(np.arange(-0.5, 7, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 7, 1), minor=True)
        ax.grid(which="minor", color="#d2d7dc", linewidth=0.5)
        ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
        ax.set_title(title, fontsize=10)
    fig.suptitle("Saved 7×7 partial views: scripted movement, learned final choice", fontsize=12)
    fig.legend(handles=[Patch(color=colors[i], label=label) for i, label in
                        ((0, "unseen"), (1, "empty"), (2, "wall"),
                         (5, "K: key"), (6, "B: ball"))],
               loc="lower center", ncol=5, frameon=False)
    fig.tight_layout(rect=(0, 0.12, 1, 0.95))
    for extension in ("png", "pdf"):
        fig.savefig(destination / f"task_illustration.{extension}", dpi=160)
    plt.close(fig)
    return {"episode_id": episode_id, "frames": frames,
            "measured_delay": 17, "source": "data/test/visible.npz",
            "note": "Actual categorical partial observations, not a full-map agent input"}


def learning_curves(destination):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    for variant, color in (("control", "#236cb4"), ("predictive", "#b93f67")):
        for seed, style in zip((11, 22, 33), ("-", "--", ":")):
            path = ROOT / f"runs/main/{variant}_{seed}/history.jsonl"
            history = [json.loads(line) for line in path.read_text().splitlines()]
            for ax, metric in zip(axes, ("validation_readout_accuracy", "validation_prediction_ce")):
                ax.plot([r["epoch"] for r in history], [r[metric] for r in history],
                        color=color, linestyle=style, label=f"{variant}, seed {seed}")
    axes[0].set(xlabel="Training epoch", ylabel="Validation readout accuracy", ylim=(-.04, 1.04))
    axes[1].set(xlabel="Training epoch", ylabel="Validation next-view CE (nats/cell)")
    axes[0].legend(fontsize=7)
    fig.suptitle("All main training seeds; selection uses validation task CE")
    fig.tight_layout()
    for extension in ("png", "pdf"):
        fig.savefig(destination / f"learning_curves.{extension}", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New, unused output directory")
    args = parser.parse_args()
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    with (ROOT / "results/final/episodes.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    table, primary = summarize(rows)
    figures(table, rows, destination)
    learning_curves(destination)
    illustration = task_illustration(destination)
    (destination / "figure_inputs.json").write_text(json.dumps(
        {"source_rows": len(rows), "primary": primary, "by_condition": table,
         "task_illustration": illustration}, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "source_rows": len(rows),
                      "primary": primary}, indent=2))


if __name__ == "__main__":
    main()
