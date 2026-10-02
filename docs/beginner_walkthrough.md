# Beginner walkthrough

This walkthrough explains the completed BeliefSpec pilot as a standalone
research artifact. It is grounded in saved records from 2026-10-01 and does not
add new experimental results.

## ELI5

The task is a small memory game. The agent briefly sees a key or a ball, walks
along a scripted route, and later faces two objects. The learned model does not
navigate. It only estimates the remembered clue at the final choice: key, ball,
or unknown. A fixed controller turns that estimate into a top-or-bottom choice.

The question is whether memory becomes more useful if the model also learns to
predict the next observation. In this pilot, next-view prediction got much
better, but final decision success did not improve. The task-only GRU solved
observed clues in all three seeds; the predictive GRU solved two seeds and
failed one.

## What the model sees and controls

Each episode contains 7 by 7 MiniGrid object-ID images, direction, previous
action, and a public route phase. The model does not receive mission text,
simulator `info`, episode IDs, hidden clue labels, rewards, success positions,
full-map renders, or evaluator-only metadata.

There are two clue conditions:

- `observed`: the clue is visible near the start.
- `never`: every frame where the clue cell would be visible is masked.

Observed delays are 17, 29, and 53 steps since the last visible clue. Never
observed episodes have no delay because there is no last visible clue.

The task label is key, ball, or unknown. That is different from binary
top/bottom success. In never-observed episodes, unknown is the correct memory
label, but forced-choice success should remain at chance because the hidden
answer is unavailable from permitted inputs.

## Hidden state versus weights

Weights are the learned checkpoint parameters shared across all episodes. The
recurrent hidden state is a 32-number per-episode working memory. It starts
fresh, updates as frames arrive, and is read at the final decision. A single
hidden-state number is not itself a decoded fact; the trained readout maps the
whole state to key, ball, or unknown.

The experiment therefore asks whether the hidden state for a particular episode
keeps the early clue until the final choice. It does not ask whether the weights
store the answer to a specific test episode.

## Objectives

The task-only GRU minimizes:

```text
cross_entropy(final_clue_logits, observed_clue_label)
```

The predictive GRU minimizes:

```text
task_cross_entropy + 0.1 * next_view_cross_entropy
```

At time `t`, the predictive head uses the recurrent state and executed action
to predict categorical object IDs in `images[t+1]`. Object IDs are not treated
as continuous values.

Both learned variants allocate 56,171 parameters: 34,611 shared
encoder/GRU/readout parameters and 21,560 prediction-head parameters. In the
task-only arm, the prediction-head loss weight is zero, so that head is
allocated but untrained.

During training, a gradient measures how changing each weight would change the
loss; the optimizer uses those gradients to update weights. Gradients pass back
through the recurrent sequence, so the final task loss can train the processing
of the early clue. Validation data select a checkpoint without updating its
weights. Test evaluation uses the selected checkpoint with fixed weights on
held-out trajectories; only the episode's hidden state changes.

## Baselines

All methods output a key/ball/unknown probability vector before the same
top/bottom controller runs.

| Method | Why it is included |
| --- | --- |
| Current view | Checks whether the final observation alone leaks the clue. |
| Recent history | Checks whether a 32-frame window still contains the clue. |
| Structured memory | Parses observed clue facts; validates task solvability. |
| Episodic retrieval | Stores clue-stage frames and retrieves the relevant one. |
| GRU task only | Tests learned recurrent memory from the task loss. |
| GRU + prediction | Tests the matched GRU with auxiliary prediction. |

Structured and episodic baselines are task-validity checks, not fair learned
architectures. They should solve observed clues and remain at chance when the
clue is unavailable.

## Main result

| Training seed | Task-only observed success | Predictive observed success | Difference |
| --- | ---: | ---: | ---: |
| 11 | 1.0 | 0.5 | -0.5 |
| 22 | 1.0 | 1.0 | 0.0 |
| 33 | 1.0 | 1.0 | 0.0 |

The paired predictive-minus-control mean was -0.1667, with descriptive 95% t
interval [-0.8838, 0.5504]. This is a seed-level description over three
training replications, not an episode-binomial confidence interval.

Every method scored 0.5 forced-choice success when the clue was never observed.
The predictive arm learned the auxiliary target: observed-clue prediction
cross-entropies were about 0.53, 0.43, and 0.43 across seeds, versus about
2.49, 2.52, and 2.49 for the untrained task-only prediction head. Better local
prediction did not imply better delayed decision memory.

## Figures

`decision_success.png` reports forced-choice success by measured delay for
observed clues and chance behavior for never-observed clues. Learned-method
points average three seeds; vertical ranges are seed minima and maxima, not
confidence intervals. The never-observed panel uses added wait steps because
clue delay is undefined there.
`prediction_and_memory.png` separates prediction quality from clue readout
quality: dots are seed means and horizontal lines are averages, not uncertainty
intervals. `learning_curves.png` shows validation dynamics: task-only seeds
reached 99% validation readout by epoch 7, predictive seeds 22 and 33 reached it
later, and predictive seed 11 never did. Each curve is one training run, not an
uncertainty band. The task illustration shows saved partial views, not a map
available to the agent.

## One saved episode

The trace `results/traces/observed_success.json` is predictive seed 11,
checkpoint epoch 10, episode `test:test-w8-r0:h0:top0:seen`.

Saved facts: hidden clue key (`0`), observed label key (`0`), top option key
(`0`), route wait 8, last clue step 1, measured delay 17, episode length 19
frames, and final probabilities key 0.2507379, ball 0.2498507, unknown
0.4994114.

At `t=0`, the clue is visible as object ID `5`, the MiniGrid key ID. The
predicted next-view cell accuracy is 45/49 = 0.9184. At `t=1`, the clue is
still visible; this is why never-observed episodes must mask more than frame 0.
After that, the clue is gone. At `t=17`, the model predicts the final view with
47/49 = 0.9592 next-cell accuracy.

At `t=18`, both choices are visible. The final readout is `unknown`, so memory
readout is wrong for an observed key clue. The controller still chooses top:

```text
p_top = p_key + 0.5 * p_unknown
      = 0.2507379 + 0.2497057
      = 0.5004436
```

Top is correct in this episode, so binary success is 1. This is a lucky success,
not evidence that seed 11 remembered the clue. The paired trace
`results/traces/observed_failure.json` uses the same seed and route but has
hidden clue ball with top option key. The probabilities are effectively the
same, the controller again chooses top, and success is 0.

The trace `results/traces/unavailable_failure.json` is an information-limit
case. The clue was never observed, so unknown readout is correct even though the
forced top/bottom choice can fail.

This row contributes one success to the predictive seed-11, wait-8,
observed-clue group: 1 of 128 episodes in that delay condition. Across all
observed delays, predictive seed 11 has 192 successes out of 384 observed
episodes.

## Bugs and safeguards

The pre-final checks fixed clue masking after the first turn, measured delay
from the original clue cell rather than generic key/ball sightings, and used
disjoint train/validation/test route offsets. Tests cover next-observation
alignment, padding masks, no future leakage, memory reset, save/load
consistency, tiny-set fitting, and metadata leakage. Geometry still repeats, so
layout generalization is not claimed.

## Post-hoc target audit

After primary evaluation, an audit compared 192 observed key/ball episode pairs
with identical routes and choice placements. Prediction targets differed only at
the transition from `t=0` to frame 1. There were zero differences in 6,336
post-clue target comparisons.

This shows that the chosen next-view target did not require retaining the clue
after it disappeared. It does not prove why predictive seed 11 failed.

## Evidence and code map

The pilot supports a narrow conclusion: in this controlled supervised task,
better local next-view prediction did not reliably improve delayed clue memory.
It cannot establish that predictive supervision generally helps or harms memory
and does not evaluate autonomous navigation, RL, LLM agents, AgentSpec, or
layout generalization. Code map: [task.py](../src/beliefspec/task.py) builds data
and labels; [model.py](../src/beliefspec/model.py) defines the GRU, losses,
baselines, and controller; [experiment.py](../src/beliefspec/experiment.py)
trains and writes episode rows. The original `analyze_results.py` generated the
summaries and figures. Use the [README commands](../README.md) for review outputs
that do not overwrite original evidence.

## Ten technical questions

1. What is the exact claim? In this pilot, next-view prediction improved
   prediction metrics but not reliable delayed decision success.
2. Why key/ball/unknown instead of top/bottom? It separates memory availability
   from forced-choice scoring.
3. Could the final view leak the clue? Current-view success is 0.5, so final
   view alone does not solve the observed-clue task.
4. Why include structured and episodic baselines? They verify that observed
   clue information is sufficient and the controller is usable.
5. Why are three seeds weak? There are only three independently trained runs per
   variant. Test episodes and multiple checkpoints from one run are not
   independent training replications.
6. Why might prediction fail to help? The post-clue target does not depend on
   the clue, but that is not a proven cause of seed 11's failure.
7. Is the task too easy? The task-only GRU is at ceiling, so improvement is hard
   to detect.
8. Is this reinforcement learning? No. Trajectories are scripted and training is
   supervised.
9. What would strengthen the result? A fresh non-ceiling protocol with a
   clue-relevant prediction target and more seeds.
10. What should readers inspect first? `results/summary.json`,
    `results/final/episodes.csv`, saved traces, and the target audit.

## Comprehension checklist

You should be able to explain the scripted route, observed versus never-observed
conditions, unknown readout, hidden state versus weights, both training losses,
the matched learned variants, the mixed/negative result, the post-hoc target
audit, and why the pilot is not autonomous navigation, RL, LLM-agent evaluation,
AgentSpec reproduction, or layout generalization.
