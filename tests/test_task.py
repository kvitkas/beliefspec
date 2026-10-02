import numpy as np

from beliefspec.model import baseline_probabilities, clue_to_choice
from beliefspec.task import (
    CLUE_BALL,
    CLUE_KEY,
    CLUE_UNKNOWN,
    DEFAULT_WAITS,
    STAGE_CLUE,
    STAGE_DECISION,
    collect_dataset,
    replay_choice,
    visible_history_hash,
)


def test_collect_dataset_balances_full_factorial_and_delays():
    episodes = collect_dataset("train", routes_per_delay=2, waits=(8,), seed=123)

    assert len(episodes) == 2 * 2 * 2 * 2
    combos = {
        (
            episode.evaluator["route_id"],
            episode.evaluator["hidden_clue"],
            episode.top_clue,
            episode.evaluator["clue_observed"],
        )
        for episode in episodes
    }
    assert len(combos) == len(episodes)
    assert {episode.evaluator["wait"] for episode in episodes} == {8}
    assert {episode.evaluator["delay"] for episode in episodes if episode.observed_clue != 2} == {17}
    assert all(episode.evaluator["delay"] is None for episode in episodes if episode.observed_clue == 2)


def test_agent_visible_contract_shapes_and_stages():
    episode = collect_dataset("train", routes_per_delay=1, waits=(8,), seed=0)[0]

    assert episode.images.shape == (len(episode.actions) + 1, 7, 7)
    assert episode.images.dtype == np.uint8
    assert episode.directions.shape == (len(episode.images),)
    assert episode.prev_actions.shape == (len(episode.images),)
    assert episode.prev_actions[0] == 7
    assert episode.stages[0] == STAGE_CLUE
    assert np.count_nonzero(episode.stages == STAGE_CLUE) == 2
    assert episode.stages[-1] == STAGE_DECISION
    assert episode.top_clue in (CLUE_KEY, CLUE_BALL)
    assert episode.observed_clue in (CLUE_KEY, CLUE_BALL, CLUE_UNKNOWN)


def test_never_observed_hidden_swap_keeps_visible_history_identical():
    episodes = collect_dataset("train", routes_per_delay=1, waits=(8,), seed=1)
    pair = [
        episode
        for episode in episodes
        if episode.top_clue == CLUE_KEY and not episode.evaluator["clue_observed"]
    ]
    assert {episode.evaluator["hidden_clue"] for episode in pair} == {CLUE_KEY, CLUE_BALL}
    assert pair[0].evaluator["correct_top"] is not pair[1].evaluator["correct_top"]
    assert visible_history_hash(pair[0]) == visible_history_hash(pair[1])
    np.testing.assert_array_equal(pair[0].images, pair[1].images)
    np.testing.assert_array_equal(pair[0].actions, pair[1].actions)


def test_routes_are_invariant_to_hidden_clue_and_placement():
    episodes = collect_dataset("train", routes_per_delay=1, waits=DEFAULT_WAITS, seed=2)
    by_route = {}
    for episode in episodes:
        by_route.setdefault((episode.evaluator["wait"], episode.evaluator["route_id"]), []).append(
            episode.actions
        )
    for action_sequences in by_route.values():
        first = action_sequences[0]
        for actions in action_sequences[1:]:
            np.testing.assert_array_equal(first, actions)


def test_splits_have_disjoint_visible_histories_for_same_generation_plan():
    train = collect_dataset("train", routes_per_delay=4, waits=(8,), seed=3)
    val = collect_dataset("val", routes_per_delay=4, waits=(8,), seed=3)
    test = collect_dataset("test", routes_per_delay=4, waits=(8,), seed=3)

    train_hashes = {visible_history_hash(episode) for episode in train}
    val_hashes = {visible_history_hash(episode) for episode in val}
    test_hashes = {visible_history_hash(episode) for episode in test}

    assert train_hashes.isdisjoint(val_hashes)
    assert train_hashes.isdisjoint(test_hashes)
    assert val_hashes.isdisjoint(test_hashes)


def test_structured_and_episodic_solve_observed_cases_with_real_replay():
    episodes = collect_dataset("train", routes_per_delay=2, waits=(8,), seed=4)
    observed = [episode for episode in episodes if episode.evaluator["clue_observed"]]

    for episode in observed:
        for method in ("structured", "episodic"):
            probabilities = baseline_probabilities(episode, method)
            choose_top = clue_to_choice(probabilities, episode.top_clue)
            result = replay_choice(episode, choose_top=choose_top)
            assert result["terminated"]
            assert not result["truncated"]
            assert result["success"]


def test_current_and_recent_do_not_read_clue_after_recent_window():
    episode = next(
        ep
        for ep in collect_dataset("train", routes_per_delay=1, waits=(44,), seed=5)
        if ep.evaluator["clue_observed"]
    )

    assert episode.evaluator["delay"] > 32
    np.testing.assert_array_equal(baseline_probabilities(episode, "current"), np.eye(3)[2])
    np.testing.assert_array_equal(baseline_probabilities(episode, "recent", window=32), np.eye(3)[2])


def test_final_replay_rewards_match_correct_top_metadata():
    episodes = collect_dataset("train", routes_per_delay=1, waits=(8,), seed=6)

    for episode in episodes:
        top_result = replay_choice(episode, choose_top=True)
        bottom_result = replay_choice(episode, choose_top=False)
        assert top_result["terminated"]
        assert bottom_result["terminated"]
        assert top_result["success"] == episode.evaluator["correct_top"]
        assert bottom_result["success"] != episode.evaluator["correct_top"]
