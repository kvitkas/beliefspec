"""Controlled MiniGrid Memory episodes for the BeliefSpec pilot.

This module adapts MiniGrid's MemoryEnv into a balanced, scripted dataset.
The model-facing record contains only categorical object observations, agent
direction, previous action, executed actions, and a shared controller phase.
Evaluator-only truth stays in ``Episode.evaluator``.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import product
from typing import Any

import numpy as np
from minigrid.core.actions import Actions
from minigrid.core.constants import OBJECT_TO_IDX
from minigrid.core.world_object import Ball, Key
from minigrid.envs.memory import MemoryEnv

CLUE_KEY = 0
CLUE_BALL = 1
CLUE_UNKNOWN = 2

STAGE_CLUE = 0
STAGE_TRANSIT = 1
STAGE_DECISION = 2

START_PREV_ACTION = 7
DEFAULT_WAITS = (8, 20, 44)
SPLIT_ROUTE_OFFSETS = {"train": 0, "val": 512, "validation": 512, "test": 1024, "dev": 1280}
ROUTE_TEMPLATE_COUNT = 1536

KEY_OBJ = OBJECT_TO_IDX["key"]
BALL_OBJ = OBJECT_TO_IDX["ball"]
UNSEEN_OBJ = OBJECT_TO_IDX["unseen"]


@dataclass
class Episode:
    """One scripted episode with agent-visible arrays and evaluator metadata."""

    images: np.ndarray
    directions: np.ndarray
    prev_actions: np.ndarray
    actions: np.ndarray
    stages: np.ndarray
    observed_clue: int
    top_clue: int
    evaluator: dict[str, Any]


def collect_dataset(
    split: str,
    routes_per_delay: int,
    waits: Iterable[int] = DEFAULT_WAITS,
    seed: int = 0,
) -> list[Episode]:
    """Collect a balanced fixed-geometry controlled Memory dataset.

    Each route template is crossed with hidden clue key/ball, top option key/ball,
    and clue exposure observed/never-observed. Route actions never depend on these
    factors. The fixed geometry is intentional; callers must not report layout
    generalization from this dataset.
    """

    _ = seed  # Route partitions are fixed so different split seeds cannot overlap.
    if routes_per_delay <= 0:
        raise ValueError("routes_per_delay must be positive")

    normalized_split = split.lower()
    route_offset = SPLIT_ROUTE_OFFSETS.get(normalized_split)
    if route_offset is None:
        raise ValueError(f"Unknown split {split!r}; expected one of {sorted(SPLIT_ROUTE_OFFSETS)}")

    episodes: list[Episode] = []
    for wait in waits:
        templates = _route_templates(wait=wait)
        if route_offset + routes_per_delay > len(templates):
            raise ValueError(
                f"wait={wait} has only {len(templates)} route templates; "
                f"split offset {route_offset} plus {routes_per_delay} routes exceeds that"
            )
        for route_index, wait_actions in enumerate(
            templates[route_offset : route_offset + routes_per_delay]
        ):
            route_id = f"{normalized_split}-w{wait}-r{route_index}"
            for hidden_clue in (CLUE_KEY, CLUE_BALL):
                for top_clue in (CLUE_KEY, CLUE_BALL):
                    for clue_observed in (True, False):
                        episodes.append(
                            collect_episode(
                                split=normalized_split,
                                route_id=route_id,
                                wait=wait,
                                wait_actions=wait_actions,
                                hidden_clue=hidden_clue,
                                top_clue=top_clue,
                                clue_observed=clue_observed,
                            )
                        )
    return episodes


def collect_episode(
    *,
    split: str,
    route_id: str,
    wait: int,
    wait_actions: tuple[int, ...],
    hidden_clue: int,
    top_clue: int,
    clue_observed: bool,
) -> Episode:
    """Collect one scripted episode. Route and visibility are clue-independent."""

    env = _make_env(hidden_clue=hidden_clue, top_clue=top_clue)
    images: list[np.ndarray] = []
    directions: list[int] = []
    prev_actions: list[int] = [START_PREV_ACTION]
    stages: list[int] = []
    actions: list[int] = list(_base_actions_to_wait_point()) + list(wait_actions) + [
        int(Actions.forward),
        int(Actions.forward),
    ]

    last_clue_step: int | None = None

    def record(stage: int, step_index: int) -> None:
        nonlocal last_clue_step
        clue_visible = env.agent_sees(1, 5)
        actual_stage = STAGE_CLUE if clue_visible else stage
        object_plane = env.gen_obs()["image"][:, :, 0].astype(np.uint8)
        if not clue_observed and clue_visible:
            object_plane = _mask_world_cell(object_plane, env, 1, 5)
        if clue_observed and clue_visible:
            last_clue_step = step_index
        images.append(object_plane)
        directions.append(int(env.agent_dir))
        stages.append(actual_stage)

    record(STAGE_CLUE, 0)
    for step_index, action in enumerate(actions, start=1):
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            raise RuntimeError(
                f"predecision route terminated early at step {step_index}: "
                f"reward={reward}, info={info}, obs_keys={sorted(obs)}"
            )
        prev_actions.append(action)
        stage = STAGE_DECISION if step_index == len(actions) else STAGE_TRANSIT
        record(stage, step_index)

    image_array = np.stack(images).astype(np.uint8)
    direction_array = np.asarray(directions, dtype=np.uint8)
    prev_action_array = np.asarray(prev_actions, dtype=np.uint8)
    action_array = np.asarray(actions, dtype=np.uint8)
    stage_array = np.asarray(stages, dtype=np.uint8)

    observed_clue = observed_clue_from_history(image_array, stage_array)
    expected_observed_clue = hidden_clue if clue_observed else CLUE_UNKNOWN
    if observed_clue != expected_observed_clue:
        raise RuntimeError(
            f"visible clue parser returned {observed_clue}; expected {expected_observed_clue}"
        )
    visible_top_clue = top_clue_from_final_image(image_array[-1])
    if visible_top_clue != top_clue:
        raise RuntimeError("final observation does not encode the requested top choice")

    delay = None if last_clue_step is None else len(images) - 1 - last_clue_step
    episode_id = _episode_id(split, route_id, hidden_clue, top_clue, clue_observed)
    evaluator = {
        "hidden_clue": hidden_clue,
        "split": split,
        "episode_id": episode_id,
        "route_id": route_id,
        "wait": wait,
        "delay": delay,
        "last_clue_step": last_clue_step,
        "correct_top": hidden_clue == top_clue,
        "clue_observed": clue_observed,
        "visible_hash": visible_history_hash_arrays(
            image_array, direction_array, prev_action_array, action_array, stage_array
        ),
    }
    return Episode(
        images=image_array,
        directions=direction_array,
        prev_actions=prev_action_array,
        actions=action_array,
        stages=stage_array,
        observed_clue=observed_clue,
        top_clue=visible_top_clue,
        evaluator=evaluator,
    )


def replay_choice(episode: Episode, choose_top: bool) -> dict[str, Any]:
    """Replay the hidden evaluator episode in MiniGrid and execute a top/bottom choice."""

    env = _make_env(
        hidden_clue=int(episode.evaluator["hidden_clue"]),
        top_clue=int(episode.top_clue),
    )
    for action in episode.actions:
        obs, reward, terminated, truncated, info = env.step(int(action))
        if terminated or truncated:
            raise RuntimeError(
                f"predecision action terminated during replay: reward={reward}, info={info}, obs={obs}"
            )

    choice_actions = (
        (int(Actions.forward), int(Actions.left), int(Actions.forward))
        if choose_top
        else (int(Actions.forward), int(Actions.right), int(Actions.forward))
    )
    reward = 0.0
    terminated = False
    truncated = False
    for action in choice_actions:
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
    return {
        "reward": float(reward),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "success": bool(reward > 0),
        "choice_top": bool(choose_top),
        "correct_top": bool(episode.evaluator["correct_top"]),
        "final_pos": tuple(int(x) for x in env.agent_pos),
    }


def top_clue_from_final_image(image: np.ndarray) -> int:
    """Return the top option's clue class using only the final object observation."""

    cells: list[tuple[int, int, int]] = []
    for obj_id, clue in ((KEY_OBJ, CLUE_KEY), (BALL_OBJ, CLUE_BALL)):
        for x, y in np.argwhere(image == obj_id):
            cells.append((int(x), int(y), clue))
    if len(cells) != 2:
        raise ValueError(f"Expected exactly two visible choice objects, found {len(cells)}")
    cells.sort(key=lambda item: item[0])
    if cells[0][0] == cells[1][0]:
        raise ValueError("Cannot order final choices from visible observation")
    return cells[0][2]


def observed_clue_from_history(images: np.ndarray, stages: np.ndarray) -> int:
    """Parse the permitted clue-stage observations into key/ball/unknown."""

    seen: list[int] = []
    for image in images[stages == STAGE_CLUE]:
        for obj_id, clue in ((KEY_OBJ, CLUE_KEY), (BALL_OBJ, CLUE_BALL)):
            if np.any(image == obj_id):
                seen.append(clue)
    if not seen:
        return CLUE_UNKNOWN
    if len(set(seen)) != 1:
        raise ValueError("Conflicting clue objects in clue-stage observations")
    return seen[-1]


def visible_history_hash(episode: Episode) -> str:
    """Hash only agent-visible arrays and public labels, never evaluator metadata."""

    return visible_history_hash_arrays(
        episode.images,
        episode.directions,
        episode.prev_actions,
        episode.actions,
        episode.stages,
    )


def visible_history_hash_arrays(
    images: np.ndarray,
    directions: np.ndarray,
    prev_actions: np.ndarray,
    actions: np.ndarray,
    stages: np.ndarray,
) -> str:
    digest = hashlib.sha256()
    for value in (images, directions, prev_actions, actions, stages):
        contiguous = np.ascontiguousarray(value)
        digest.update(str(contiguous.shape).encode("ascii"))
        digest.update(contiguous.dtype.str.encode("ascii"))
        digest.update(contiguous.tobytes())
    return digest.hexdigest()


def episode_to_jsonable(episode: Episode) -> dict[str, Any]:
    """Convert metadata and arrays to plain objects for simple debugging logs."""

    return {
        "images_shape": list(episode.images.shape),
        "directions": episode.directions.tolist(),
        "prev_actions": episode.prev_actions.tolist(),
        "actions": episode.actions.tolist(),
        "stages": episode.stages.tolist(),
        "observed_clue": episode.observed_clue,
        "top_clue": episode.top_clue,
        "evaluator": json.loads(json.dumps(episode.evaluator)),
    }


def _make_env(*, hidden_clue: int, top_clue: int) -> MemoryEnv:
    env = MemoryEnv(size=13, random_length=False, render_mode=None)
    env.reset(seed=0)
    env.agent_pos = np.array((1, 6), dtype=np.int64)
    env.agent_dir = 3

    for x in range(env.width):
        for y in range(env.height):
            obj = env.grid.get(x, y)
            if obj is not None and obj.type in ("key", "ball"):
                env.grid.set(x, y, None)

    env.grid.set(1, 5, _object_for_clue(hidden_clue))
    env.grid.set(11, 4, _object_for_clue(top_clue))
    bottom_clue = CLUE_BALL if top_clue == CLUE_KEY else CLUE_KEY
    env.grid.set(11, 8, _object_for_clue(bottom_clue))
    env.success_pos = (11, 5) if hidden_clue == top_clue else (11, 7)
    env.failure_pos = (11, 7) if hidden_clue == top_clue else (11, 5)
    env.step_count = 0
    return env


def _object_for_clue(clue: int) -> Key | Ball:
    if clue == CLUE_KEY:
        return Key("green")
    if clue == CLUE_BALL:
        return Ball("green")
    raise ValueError(f"Unknown clue {clue!r}")


def _base_actions_to_wait_point() -> tuple[int, ...]:
    return (int(Actions.right),) + (int(Actions.forward),) * 7


def _route_templates(*, wait: int) -> list[tuple[int, ...]]:
    if wait < 0:
        raise ValueError("wait must be non-negative")
    choices = (int(Actions.left), int(Actions.right), int(Actions.done))
    if wait <= 10:
        templates = [
            tuple(actions)
            for actions in product(choices, repeat=wait)
            if _net_turn(actions) % 4 == 0
        ]
        rng = random.Random(10_000 + wait)
        rng.shuffle(templates)
        return templates

    rng = random.Random(10_000 + wait)
    templates_set: set[tuple[int, ...]] = set()
    attempts = 0
    while len(templates_set) < ROUTE_TEMPLATE_COUNT:
        attempts += 1
        if attempts > ROUTE_TEMPLATE_COUNT * 200:
            raise RuntimeError(f"Could not sample enough route templates for wait={wait}")
        actions = tuple(rng.choice(choices) for _ in range(wait))
        if _net_turn(actions) % 4 == 0:
            templates_set.add(actions)
    templates = list(templates_set)
    rng.shuffle(templates)
    return templates


def _net_turn(actions: tuple[int, ...]) -> int:
    return sum(
        -1 if action == int(Actions.left) else 1 if action == int(Actions.right) else 0
        for action in actions
    )


def _mask_world_cell(object_plane: np.ndarray, env: MemoryEnv, x: int, y: int) -> np.ndarray:
    masked = object_plane.copy()
    vx, vy = env.get_view_coords(x, y)
    if 0 <= vx < masked.shape[0] and 0 <= vy < masked.shape[1]:
        masked[vx, vy] = UNSEEN_OBJ
    return masked


def _episode_id(
    split: str,
    route_id: str,
    hidden_clue: int,
    top_clue: int,
    clue_observed: bool,
) -> str:
    exposure = "seen" if clue_observed else "never"
    return f"{split}:{route_id}:h{hidden_clue}:top{top_clue}:{exposure}"
