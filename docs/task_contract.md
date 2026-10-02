# Controlled MiniGrid Memory task contract

Written 2026-10-01 for the BeliefSpec pilot.

This task is a controlled adaptation of MiniGrid Memory, not an unchanged
MiniGrid benchmark. The underlying simulator and terminal success/failure
checks are MiniGrid's `MemoryEnv`, but the data generator fixes the map size,
start pose, object placement, balancing, and route policy so memory can be
tested separately from autonomous navigation.

## Geometry and control

- Environment: `MemoryEnv(size=13, random_length=False)`, view size 7.
- Start: agent at `(1, 6)`, facing north, with the clue at `(1, 5)`.
- Choices: top option at `(11, 4)`, bottom option at `(11, 8)`.
- Decision positions: top is reached at `(11, 5)`, bottom at `(11, 7)`.
- The scripted controller executes all predecision movement. Models only choose
  top or bottom at the final decision view.
- The final observation has both choices visible. The top option is derived from
  the visible object-plane observation, not from evaluator truth.

The predecision route is independent of hidden clue and option placement:
turn east, move to hallway `x=8`, execute a route-template wait sequence using
left/right/no-op actions that returns to facing east, then move to the final
decision view. Candidate extra waits are 8, 20, and 44 simulator steps. Actual
delay is recorded as steps since the last visible clue; because the clue remains
visible for one frame after the initial turn, the current route measures delays
of 17, 29, and 53 for observed clues. Never-observed clues have
`delay = null`.

## Agent-visible record

`Episode` has these fields:

- `images`: `uint8[T, 7, 7]`, MiniGrid object IDs only.
- `directions`: `uint8[T]`, agent direction.
- `prev_actions`: `uint8[T]`, with `7` marking the first frame.
- `actions`: `uint8[T-1]`, executed predecision actions.
- `stages`: `uint8[T]`, `0=clue`, `1=transit`, `2=decision`.
- `observed_clue`: `0=key`, `1=ball`, `2=unknown`.
- `top_clue`: `0=key`, `1=ball`, derived from final visible observation.
- `evaluator`: hidden metadata kept out of models.

Every frame in which the initial clue location is actually visible is
`stage==0`. If the clue is never observed, key or ball pixels at that clue
location are replaced by MiniGrid's `unseen` object ID in those frames. Choice
objects are not marked as clue-stage observations, so
structured and episodic baselines cannot mistake the final choices for the
initial clue.

Permitted model inputs are `images`, `directions`, `prev_actions`, `stages`,
and for the prediction head the executed current action. Mission text, `info`,
seed, episode ID, hidden clue, success position, reward, full-grid render, and
all evaluator metadata are excluded.

## Balancing and splits

For each route template and delay, the generator crosses:

- hidden clue: key or ball;
- top option: key or ball;
- exposure: clue observed or never observed.

Routes are selected from split-specific offsets in a deterministic shuffled
route-template list. Route partitions do not depend on the public `seed`
argument, so accidental different split seeds cannot reshuffle train,
validation, and test into overlap. With the default plan, train/validation/test
visible histories are disjoint. The geometry repeats across all splits, so this
dataset does not test layout generalization.

## Prediction target

The prediction target for recurrent models is the next observation's object
plane: state/action at time `t` predicts `images[t+1]`. Targets are categorical
object IDs, not distances between arbitrary identifiers. Padding and final steps
without a successor are excluded by the model loss.

## Replay

`replay_choice(episode, choose_top)` rebuilds the hidden simulator episode,
replays the predecision actions, then executes the top or bottom choice in the
real environment. This verifies that metadata, final choice mapping, and
MiniGrid terminal rewards agree. It is evaluator code; models do not receive its
hidden fields.
