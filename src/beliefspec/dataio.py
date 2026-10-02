"""Visible data and evaluator-only ground truth are stored in separate files."""

import hashlib
import json
from pathlib import Path

import numpy as np


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def visible_hash(episode):
    digest = hashlib.sha256()
    for field in ("images", "directions", "prev_actions", "actions", "stages"):
        digest.update(np.asarray(getattr(episode, field), dtype=np.int64).tobytes())
    return digest.hexdigest()


def save_dataset(directory, episodes):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    arrays = {}
    visible_index, evaluator = [], []
    for i, episode in enumerate(episodes):
        for field in ("images", "directions", "prev_actions", "actions", "stages"):
            arrays[f"{i}_{field}"] = getattr(episode, field)
        visible_index.append({"index": i, "observed_clue": int(episode.observed_clue),
                              "top_clue": int(episode.top_clue),
                              "visible_sha256": visible_hash(episode)})
        evaluator.append(episode.evaluator)
    np.savez_compressed(directory / "visible.npz", **arrays)
    write_json(directory / "visible_index.json", visible_index)
    write_json(directory / "evaluator_only.json", evaluator)


def load_dataset(directory, with_evaluator=False):
    from beliefspec.task import Episode
    directory = Path(directory)
    index = json.loads((directory / "visible_index.json").read_text())
    # Training/validation never open the evaluator-only file.
    evaluator = (json.loads((directory / "evaluator_only.json").read_text())
                 if with_evaluator else [{} for _ in index])
    episodes = []
    with np.load(directory / "visible.npz", allow_pickle=False) as arrays:
        for i, row in enumerate(index):
            kwargs = {name: arrays[f"{i}_{name}"] for name in
                      ("images", "directions", "prev_actions", "actions", "stages")}
            episodes.append(Episode(**kwargs, observed_clue=row["observed_clue"],
                                    top_clue=row["top_clue"], evaluator=evaluator[i]))
    return episodes


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
