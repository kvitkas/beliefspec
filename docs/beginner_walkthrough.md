# Beginner walkthrough

This walkthrough explains the completed BeliefSpec pilot at three levels. It is
grounded in the saved package as of 2026-10-01, especially:

- `src/beliefspec/task.py`
- `src/beliefspec/model.py`
- `src/beliefspec/experiment.py`
- `src/beliefspec/analyze_results.py`
- `results/summary.json`
- `results/final/episodes.csv`
- `results/traces/observed_success.json`
- `results/traces/observed_failure.json`
- `results/traces/unavailable_failure.json`

The short version: the pilot is credible for exploratory lab outreach, but it
does not show that predictive supervision improved memory. In this small task,
the task-only GRU solved the observed-clue decision in all three training seeds.
The predictive GRU solved it in two seeds and failed in one seed, while learning
much better next-view prediction. That is an informative limitation, not a
positive result.

## Level 1: ELI5

Imagine a tiny maze game. At the start, the agent gets a quick glimpse of a
green object. It is either a key or a ball. Then the agent walks down a hallway.
At the end, it sees two objects and must choose the one that matches the object
from the start.

The route through the hallway is scripted. The model does not drive around by
itself. It only answers the final question: should we choose the top branch or
the bottom branch?

BeliefSpec asks whether an agent remembers better if, while learning the final
answer, it also practices predicting what it will see next. The intuition is
simple: if a model must keep track of the world to predict future observations,
maybe its memory will also be more useful for decisions.

In this pilot, that intuition did not get strong support. The predictive model
became much better at predicting the next local view, but that did not reliably
make the final memory decision better. One predictive seed forgot or failed to
decode the clue and guessed `unknown` at the final step. Two predictive seeds
worked. The task-only model worked in all three seeds.

This is still useful. One plausible explanation is that short-horizon next-view
prediction is too local: predicting hallway walls and nearby objects is not the
same as remembering the early clue. This experiment does not establish that
explanation as the cause of the failed training run.

## Level 2: Beginner technical

### What the agent sees

Each episode is a sequence of 7 by 7 MiniGrid object-ID images. The package uses
only the object plane, plus direction, previous action, and a public route phase.
The object IDs that matter most here are:

- `0`: unseen
- `1`: empty
- `2`: wall
- `5`: key
- `6`: ball

The model does not receive mission text, simulator `info`, filenames, episode
IDs, hidden clue labels, full-map renders, rewards, success positions, or
anything from evaluator-only metadata.

The controlled task has two main clue conditions:

- `observed`: the clue is visible near the start.
- `never`: the hidden clue exists in the simulator, but the visible clue cell is
  masked as unseen whenever it would otherwise be visible.

For observed clues, the measured delays are 17, 29, and 53 steps since the last
visible clue observation. These correspond to route waits of 8, 20, and 44
actions. For never-observed clues, delay is undefined because there was no last
clue observation.

### What the model controls

The model does not choose the route. `collect_episode()` in `task.py` records a
fixed clue-independent route. At the end, the model produces probabilities over
three clue states:

- key
- ball
- unknown

`decision_from_memory()` converts those clue probabilities into a top/bottom
choice by comparing them to the top object visible in the final view. Unknown
probability is split evenly between top and bottom; exact ties choose top. This
is forced-choice scoring, not an "unknown is correct" decision score.

That distinction matters. In never-observed episodes, the correct memory label
is `unknown`, so readout accuracy can be 1.0 while forced-choice success is only
0.5. There is no information available to choose key versus ball.

### The six baselines

All methods use the same downstream decision interface: a three-value clue
probability vector is turned into a top/bottom choice.

| Method | What it stores or uses | Expected behavior |
| --- | --- | --- |
| Current view | Only the final observation | Chance on observed clues, because the start clue is gone |
| Recent history | A 32-frame window | Works at shorter delays, fails when the clue is outside the window |
| Structured memory | Parsed fact from all clue-phase observations | Solves observed clues and says unknown when never observed |
| Episodic retrieval | Stores clue-phase frames and retrieves the latest relevant one | Same result as structured memory on this one-fact task |
| GRU task only | Learned recurrent memory trained on final clue label | Can learn to keep the clue in hidden state |
| GRU + prediction | Same GRU plus action-conditioned next-view prediction | Tests whether predictive supervision helps or hurts the learned memory |

The structured and episodic baselines are not "fair neural baselines." They have
hand-designed knowledge about where to look for the clue. They are included as
task-validity checks: if they fail, the task or evaluator is broken.

### Labels, losses, and gradients

The GRU has two different kinds of numbers. Its **weights** are learned rules
shared across episodes. Its **hidden state** is a 32-number working memory for
the current episode. At each step, the encoder turns the current categorical
view, direction, previous action and phase into 48 numbers. The GRU combines
those numbers with its previous 32-number state to create the next state.
The readout turns the final state into three scores; softmax converts those
scores into probabilities summing to one. A hidden-state number is not an
explicit fact such as "key": interpretation comes from the trained readout.

A **loss** is a penalty for a prediction. Cross-entropy penalizes assigning low
probability to the correct category: a probability of 0.9 gives about 0.105 nats,
while 0.1 gives about 2.303 nats. These are illustrative values of -log(p), not
experimental measurements. A **gradient** tells us how a tiny change in each
weight would change the loss. Backpropagation follows that dependency through
all earlier recurrent steps. Adam uses those gradients to adjust the weights;
gradient clipping limits an overly large update. Repeating this on training
batches is learning. During validation and test, weights stay fixed, while the
working-memory state still updates as new observations arrive and resets to
zero for the next episode.

The main task label is not "top" or "bottom." It is the observed-history clue
class:

- `0 = key`
- `1 = ball`
- `2 = unknown`

That label is derived only from permitted visible history. In other words, a
never-observed hidden key and a never-observed hidden ball both get the label
`unknown`.

The task-only GRU minimizes:

```text
cross_entropy(final_clue_logits, observed_clue_label)
```

The predictive GRU minimizes:

```text
task_cross_entropy + 0.1 * next_view_cross_entropy
```

The prediction target is categorical. At time `t`, the GRU state and executed
action predict the object IDs in `images[t+1]`. The code does not treat object
IDs as continuous numbers with meaningful distances.

Both learned variants allocate the same model:

- 56,171 total parameters
- 34,611 shared encoder/GRU/readout parameters
- 21,560 prediction-head parameters

The task-only arm still allocates the prediction head, but its prediction loss
weight is zero, so that head is inactive for training. This keeps the object
layout matched while making the active optimization different.

The tests check important mechanics:

- prediction loss uses the next observation, not the current observation;
- padding is masked;
- future observations do not change prefix hidden states;
- the GRU resets between episodes;
- final task loss has a gradient path back to the visible clue feature;
- prediction loss trains encoder and GRU parameters, not only the prediction
  head;
- saved and reloaded models produce identical logits and predictions;
- a tiny real subset can be fit for key, ball, and unknown labels.

Tiny-subset fitting is a debugging check. It is not evidence of scientific
generalization.

### Training, validation, and test

The splits are separate:

- train: 1,536 episodes
- validation: 384 episodes
- test: 768 episodes

The main learned runs used seeds 11, 22, and 33 for both control and predictive
variants. Each run used 30 epochs and 720 updates on CPU with two Torch threads.
Checkpoint selection used minimum validation task cross-entropy with earliest
tie, not test-set performance.

The final primary comparison was paired by training seed:

| Training seed | Task-only observed success | Predictive observed success | Difference |
| --- | ---: | ---: | ---: |
| 11 | 1.0 | 0.5 | -0.5 |
| 22 | 1.0 | 1.0 | 0.0 |
| 33 | 1.0 | 1.0 | 0.0 |

The mean predictive-minus-control difference was -0.1667. The descriptive 95%
t interval was [-0.8838, 0.5504]. With only three training seeds, this interval
is unstable. It is a seed-level descriptive interval, not a claim that thousands
of test episodes are independent training replications.

For never-observed clues, every method's forced-choice success was 0.5. That is
the intended result: the answer is unavailable from permitted inputs.

### What the figures mean

`results/figures/decision_success.png` plots forced-choice success. In the
observed-clue panel, the x-axis is measured delay, not map size or route wait.
The error bars are training-seed ranges where there are learned seeds. They are
not confidence intervals. The figure shows that current view stays at chance,
recent history fails at the longest delay, structured and episodic solve the
observed condition, task-only solves all observed learned settings, and
predictive seed 11 fails.

`results/figures/prediction_and_memory.png` compares learned variants. The
left panel shows that the predictive arm learned much lower next-view
cross-entropy than the task-only arm. The task-only prediction head is
untrained, so high prediction loss there is expected. The right panel shows
three-class clue readout accuracy for observed clues. This is where seed 11's
predictive readout failure appears.

`results/figures/learning_curves.png` shows validation learning curves for all
six learned runs. It is useful for diagnosing optimization. Control reached
99% validation readout by epoch 7 in all three seeds. Predictive seeds 22 and
33 reached it at epochs 13 and 15. Predictive seed 11 never reached it, and its
selected checkpoint was epoch 10 because that was the best validation task CE
under the frozen rule.

### What broke during development and how it was fixed

Two important task bugs were found before final test evaluation:

- The clue stayed visible for more than the first frame after the initial turn.
  Masking only frame 0 would leak the hidden clue in the never-observed
  condition. The generator now masks every frame where the clue cell is actually
  visible.
- Delay initially risked being measured from generic key/ball visibility,
  which could confuse final choices with the initial clue. Delay is now tied to
  actual visibility of the original clue cell.

The split partitioning was also made explicit. Route templates now use fixed
disjoint offsets for train, validation, and test. This prevents accidental
train/test overlap from different shuffled split seeds. The geometry still
repeats across splits, so this package does not claim layout generalization.

## Level 3: Code-level map

`task.py` builds and audits the controlled MiniGrid records.

- `collect_dataset()` crosses route, wait, hidden clue, top option, and clue
  exposure into balanced episodes.
- `collect_episode()` runs the scripted predecision route and records visible
  arrays.
- `_make_env()` creates the fixed MiniGrid Memory layout and sets success and
  failure positions.
- `observed_clue_from_history()` derives the three-class label from clue-stage
  visible frames.
- `top_clue_from_final_image()` reads the final top option from visible object
  IDs.
- `replay_choice()` replays a top or bottom decision in the real MiniGrid
  simulator for evaluator-only scoring checks.

`model.py` defines both learned models and nonlearned baselines.

- `collate()` pads episodes and builds tensors.
- `MemoryModel.features()` one-hot encodes images, direction, previous action,
  and stage.
- `MemoryModel.forward()` runs the encoder, GRU, final readout, and prediction
  head.
- `losses()` returns task cross-entropy and next-view prediction
  cross-entropy.
- `baseline_probabilities()` implements current, recent, structured, and
  episodic baselines.
- `clue_to_choice()` and `decision_from_memory()` implement the common
  top/bottom controller contract.

`experiment.py` runs training and evaluation.

- `train()` applies the task-only or predictive objective, saves histories, and
  checkpoints the best validation task CE model.
- `infer()` records clue probabilities and prediction metrics for learned
  models.
- `episode_row()` writes one row per method/seed/episode with probabilities,
  success, prediction error, and failure class.
- `evaluate()` scores baselines and checkpoints on the frozen test episodes,
  writes `results/final/episodes.csv`, writes interventions, and verifies
  structured replay against the MiniGrid simulator.

`analyze_results.py` regenerates summaries, figures, and trace files from saved
records.

- `summarize()` creates `results/summary.json`.
- `figures()` creates `decision_success` and `prediction_and_memory` plots.
- `learning_curves()` creates `learning_curves` and `training_summary.json`.
- `traces()` writes actual saved episode traces for predictive seed 11.

`tests/test_model.py`, `tests/test_task.py`, `tests/test_interface.py`, and
`tests/test_leakage.py` contain the main mechanics and leakage checks.

## One real saved episode

This trace comes from `results/traces/observed_success.json`. It is predictive
model seed 11 on test episode `test:test-w8-r0:h0:top0:seen`.

Important warning: this episode is labeled `success`, but it is not evidence
that predictive seed 11 remembered the clue. The final readout was `unknown`,
and the controller chose top because its residual key probability was slightly
larger than its ball probability. The hidden clue happened to match the top
option, so the forced choice succeeded. The exact-tie rule was not used here.

Episode setup:

- Hidden clue: key (`hidden_clue = 0`)
- Clue exposure: observed
- Top option: key (`top_clue = 0`)
- Correct top choice: true
- Route wait: 8
- Measured delay: 17 steps since last clue observation
- Episode length: 19 frames
- Selected checkpoint: epoch 10

At `t=0`, the agent saw a 7 by 7 object-ID image with a key visible in the
clue area. The trace records one row containing `5`, the key object ID:

```text
[[0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0],
 [0,0,0,0,2,2,2],
 [0,0,0,0,2,5,1],
 [0,0,0,0,2,1,1],
 [0,0,0,0,2,1,1],
 [0,0,0,0,2,2,1]]
```

The diagnostic readout probabilities at `t=0` were:

```text
key 0.2971, ball 0.2368, unknown 0.4661
```

The executed action was `1` (turn right from north to east), and the predicted
next-view cell accuracy was 0.9184, or 45 of 49 cells. At array coordinate
`[2,6]`, it predicted `1` (empty), but the actual next observation contained
`5` (key). Good average pixel/category accuracy already hid a clue error.
The trace saves every predicted next grid, so this comparison is inspectable.

The recurrent state changed as input arrived: its recorded vector norm was
4.0866 at t=0, 4.6141 at t=1, and 4.1180 at the final step. A norm only shows
that numerical state exists and changes; it does not tell us what is remembered.
The intermediate readouts below apply the final trained readout to earlier
states for inspection. Only the final step received task supervision, so those
intermediate probabilities are not separately validated belief estimates.

At `t=1`, the clue was still visible. This matters because it was the bug that
had to be fixed for never-observed episodes: masking only the first frame would
have leaked the clue here. In this observed episode, seeing it is allowed. The
readout was:

```text
key 0.2886, ball 0.2171, unknown 0.4943
```

After `t=1`, the clue was no longer visible. At `t=2`, phase changed to transit.
The readout had already moved to:

```text
key 0.2797, ball 0.2112, unknown 0.5092
```

At `t=8`, still in transit, the readout was:

```text
key 0.2672, ball 0.2619, unknown 0.4709
```

At `t=17`, one step before the final decision frame, the readout was:

```text
key 0.2420, ball 0.2399, unknown 0.5181
```

After action `2` (forward), the predicted final grid matched 47 of 49 cells
(0.9592). Its two errors were the choice objects: at `[1,5]` it predicted ball
instead of key, and at `[5,5]` it predicted unseen instead of ball. This is a
concrete example of high next-view accuracy missing the cells relevant to a
decision. The controller used the actual final observation's options, not these
predictions, so these prediction errors did not directly choose the branch.

At `t=18`, the final frame, both choices were visible. The top object was key
and the bottom object was ball. The final diagnostic readout was:

```text
key 0.2507, ball 0.2499, unknown 0.4994
```

The argmax readout was `unknown`, so `readout_correct = 0` because the observed
clue label was key. The controller still chose top:

```text
p_top = p_key + 0.5 * p_unknown
      = 0.2507 + 0.2497
      = about 0.5004
```

Because p_top exceeds 0.5, `choose_top = 1`. In this particular
episode, the top option was the correct simulator choice, so `success = 1`.

The saved simulator replay then executed forward, left, forward (`[2,0,2]`),
ending at world position `(11,5)`. MiniGrid terminated successfully with reward
0.9776331361. This shaped reward is different from our binary success score of
1. Replaying the paired ball-clue failure with the same top choice terminated
at the same position with reward 0.0. Both are in
`results/traces/simulator_replays.json`; neither was a navigation timeout.

This row contributes one success to 64 successes out of 128 observed episodes
at delay 17 for predictive seed 11, and one to 192 out of 384 observed episodes
for that seed across all delays. It is one paired evaluation episode, not an
additional independent training seed. See `results/final/episodes.csv` for the
record and `results/summary.json` for the aggregated counts and rates.

The paired failure trace `results/traces/observed_failure.json` uses the same
route and model seed but has hidden clue ball while the top option is key. It
has almost the same final probabilities:

```text
key 0.2507, ball 0.2499, unknown 0.4994
```

The controller again chose top, but top was wrong, so `success = 0`. That pair
is the cleanest beginner lesson in the package: the seed-11 predictive model
learned local prediction but did not recover the decision-relevant clue.

The never-observed trace `results/traces/unavailable_failure.json` is different.
There the correct observed-history label is `unknown`, so the readout can be
correct while the forced top/bottom decision is still chance. That is an
information-availability failure, not forgetting.

## Interventions and what they do not prove

The intervention file changes decoded clue probabilities before the deterministic
controller chooses top or bottom:

- original: use the recorded probability vector;
- remove: replace it with `[0, 0, 1]`, all unknown;
- swap: swap key and ball probabilities;
- irrelevant: change a nuisance note that `decision_from_memory()` ignores.

This checks the controller interface. It asks, "If the decoded memory says a
different clue, does the scripted final choice change as expected?" It does not
prove which internal neural dimensions caused the decision. It also does not
say anything about an LLM's actual use of memory, because no LLM agent was
evaluated.

For structured and episodic observed episodes, original success was 1.0, remove
fell to 0.5, swap fell to 0.0, and irrelevant stayed 1.0. That is the intended
controller audit. Learned models follow the same interface, but their decoded
probabilities can be uncertain or wrong.

## What the evidence supports

A separate check after primary evaluation compared 192 observed-clue key/ball
episode pairs with identical routes and option placements. Only the very first
next-view target depended on the clue. None of 6,336 target comparisons after
the clue disappeared differed. See `results/target_dependence_diagnostic.json`.
This is explicitly a post-hoc audit of the dataset, not another trained result.
It proves the chosen target did not *require* remembering the clue over the
decision delay; it does not prove why predictive seed 11 failed to optimize.

This package supports these careful claims:

- The controlled MiniGrid Memory pipeline can separate observed clues from
  never-observed clues.
- The six baselines share a common downstream forced-choice interface.
- The structured and episodic baselines solve observed clues and fall to chance
  when information is unavailable.
- The task-only GRU solved the observed-clue test condition in all three main
  training seeds.
- The predictive GRU learned substantially better next-view prediction.
- In this pilot, better next-view prediction did not reliably improve
  decision-relevant clue memory.
- The failure mode is plausible: short-horizon local view prediction can be
  satisfied by hallway geometry without preserving the early clue.

It does not support these stronger claims:

- Predictive memory is new.
- Predictive supervision improves memory in general.
- Predictive supervision harms memory in general.
- The result generalizes to new layouts.
- The experiment evaluates autonomous navigation, reinforcement learning, or
  LLM agents.
- The package is ready for a public preprint without further review and
  stronger evidence.

The work is AI-assisted engineering. Before presenting it as part of your own
research skills, personally reproduce the key commands, read the code paths
above, and practice explaining the result without overstating it.

## Likely professor questions and honest answers

**What exactly is your research question?**

Under what conditions does predictive supervision make an agent's memory more
useful for decisions? This pilot tested a narrow first condition: short-horizon,
action-conditioned next-view prediction in a controlled MiniGrid Memory task.

**What did the predictive objective predict?**

At each valid time step, the GRU state plus the executed action predicted the
next 7 by 7 object-ID observation. The loss was categorical cross-entropy over
object IDs.

**Did prediction help?**

Not in this pilot. It improved next-view prediction, but the predictive arm did
not outperform the task-only GRU on decision success. One predictive seed failed
to recover the observed clue.

**Why might prediction fail to help?**

The target is mostly local hallway geometry. Predicting the next frame can be
solved without storing the start clue until the final decision.

**Why include structured and episodic baselines?**

They verify the task. If a method with explicit observed-fact memory cannot
solve observed clues, the experiment is invalid.

**Why are never-observed readouts sometimes "correct" but decisions chance?**

Because the correct memory state is unknown. Knowing "I never saw the clue" is
not enough to choose key versus ball.

**What is the biggest limitation?**

The pilot has only one fixed geometry, three training seeds, supervised final
choice rather than autonomous RL, and a short-horizon predictive target that may
be misaligned with the decision-relevant memory.

**What would you run next?**

First check additional seeds and a prespecified loss-weight/budget comparison
to understand optimization. Then specify a predictive target that requires
retaining the clue, add a non-ceiling task and new-layout evaluation, and test
whether the effect survives after removing hand-designed route phase cues.
Keep the original result and label each follow-up separately.
