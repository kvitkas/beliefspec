# Defending the work

This note is for public-review conversations: lab meetings, professor feedback,
or a private manuscript discussion. It explains what the pilot is, what it is
not, and how to answer likely technical questions without overstating the work.

## Core defense

The original BeliefSpec pilot is a small supervised memory diagnostic, not an
autonomous agent benchmark. The environment is a controlled adaptation of
MiniGrid Memory. A scripted route carries the agent from an early clue to a final
top/bottom choice. The learned model controls only the final decision through a
three-class clue readout: key, ball, or unknown.

The comparison is intentionally narrow:

- same visible observations and actions;
- same compact recurrent architecture;
- same training, validation, and test splits;
- same validation-based checkpoint rule;
- same final controller interface;
- task-only objective versus task objective plus 0.1 times next-view prediction.

The pilot does not show that predictive supervision improved memory. The
task-only GRU solved observed clues in all three training seeds. The predictive
GRU solved two seeds and failed one seed. The informative result is that
next-view prediction can improve local prediction metrics without reliably
improving decision-relevant memory.

## Recurrent hidden state versus weights

A beginner-friendly distinction matters here.

The model weights are the learned parameters saved in the checkpoint. They
encode general behavior learned from the training set. They are shared across
all episodes.

The recurrent hidden state is the per-episode memory vector produced while a
specific episode unfolds. It starts fresh for each episode, updates after each
observation/action frame, and is what the final readout uses to guess key, ball,
or unknown.

So the question is not "did the weights contain the answer?" The question is
"after seeing this particular episode's clue and hallway, did the hidden state
retain decision-relevant information until the final view?"

## Objectives

The task-only GRU trains on:

```text
cross_entropy(final_clue_logits, observed_clue_label)
```

The predictive GRU trains on:

```text
task_cross_entropy + 0.1 * next_view_cross_entropy
```

The prediction target is categorical next-view object IDs. At time `t`, the
state and executed action predict `images[t+1]`. It is not a continuous
regression over arbitrary object numbers.

Both variants allocate 56,171 parameters: 34,611 shared parameters plus a
21,560-parameter prediction head. In the task-only arm, the prediction head is
allocated but inactive because the prediction weight is zero. This makes the
untrained-head prediction metric a contrast, not a claim that the task-only arm
was supposed to predict well.

## Why the baselines exist

The nonlearned baselines are not decoration. Each one checks a different failure
mode.

| Baseline | What it checks |
| --- | --- |
| Current view | Whether the final observation alone leaks the clue |
| Recent history | Whether a bounded window can bridge the delay |
| Structured memory | Whether the intended observed fact is enough to solve the task |
| Episodic retrieval | Whether storing and retrieving clue-stage frames solves this one-fact memory task |
| Task-only GRU | Whether recurrent supervised memory can solve the same interface |
| Predictive GRU | Whether adding next-view prediction changes that memory result |

Structured and episodic memory reaching 1.0 success on observed clues is a task
validity check. Their 0.5 success on never-observed clues is also required:
when the clue is unavailable, no permitted method should beat chance in forced
choice.

## Figures and uncertainty

`decision_success.png` reports forced-choice success. For observed clues, the
x-axis is measured delay since last clue observation: 17, 29, and 53 steps. For
never-observed clues, delay is undefined, so the plot uses the added wait
setting. The error bars are training-seed ranges where multiple learned seeds
exist. They are not confidence intervals.

`prediction_and_memory.png` separates prediction quality from memory readout.
The task-only prediction head is untrained, so its next-view prediction error is
expected to be high. The key comparison is not "which untrained head predicts."
It is whether the predictive arm's lower next-view cross-entropy is accompanied
by higher clue readout or decision success. In this pilot, it was not.

`learning_curves.png` is a diagnostic. It shows that all task-only seeds reached
99% validation readout by epoch 7, predictive seeds 22 and 33 reached it later,
and predictive seed 11 never reached it. This establishes a design limitation:
the original auxiliary target and budget produced at least one learned-memory
failure. It does not prove why that seed failed.

The primary interval in `results/summary.json` is a descriptive seed-level
t interval over three paired training seeds. It is deliberately not an
episode-binomial confidence interval. Many test episodes from one trained model
do not create many independent training replications.

## Actual saved episode

The trace `results/traces/observed_success.json` is predictive seed 11,
checkpoint epoch 10, episode `test:test-w8-r0:h0:top0:seen`.

Episode facts:

- hidden clue: key (`0`);
- top option: key (`0`);
- clue observed: true;
- route wait: 8;
- measured delay: 17;
- length: 19 frames;
- final simulator-correct choice: top.

At `t=0`, the clue is visible and the executed action is `1`. The diagnostic
readout is:

```text
key 0.2971, ball 0.2368, unknown 0.4661
```

The next-view target is the actual object-ID frame at `t=1`; the model's
predicted object IDs match 45 of 49 cells, so `next_cell_accuracy = 0.9184`.

At `t=1`, the clue is still visible after the first turn. The executed action
is `2`, and the readout is:

```text
key 0.2886, ball 0.2171, unknown 0.4943
```

At `t=17`, one step before the final decision frame, the executed action is
`2`. The readout is:

```text
key 0.2420, ball 0.2399, unknown 0.5181
```

The predicted next-view target is the final decision frame at `t=18`; the trace
records `next_cell_accuracy = 0.9592`.

At `t=18`, both final choices are visible. The final readout is:

```text
key 0.2507379, ball 0.2498507, unknown 0.4994114
```

The argmax class is `unknown`, so the memory readout is wrong for an observed
key clue. But the final controller computes top score as:

```text
p_top = p_key + 0.5 * p_unknown
      = 0.2507379 + 0.2497057
      = 0.5004436
```

This is not an exact tie. The residual key probability makes top slightly more
likely than bottom. Because the hidden clue and top option are both key, the
simulator success is true. That success is therefore not evidence that seed 11
remembered the clue well.

The paired trace `results/traces/observed_failure.json` uses the same model
seed and route but hidden clue ball with top option key. Its final probabilities
are effectively the same:

```text
key 0.2507379, ball 0.2498507, unknown 0.4994114
```

The controller again chooses top. In that episode top is wrong, so success is
false. Together, the two traces show a failure to recover the decision-relevant
clue, not a meaningful success/failure mechanism difference.

This one episode contributes one row to the predictive seed-11, wait-8,
observed-clue group. That group contains 128 episodes in `results/summary.json`
and has success 0.5 with readout accuracy 0.0. Across all observed-clue delays,
predictive seed 11 contributes 384 observed episodes and its seed-level observed
success is 0.5, which is the seed-11 point in the primary paired contrast.

## Code-level map

The implementation is small enough to defend at the function level:

- `task.collect_dataset()` and `task.collect_episode()` build balanced scripted
  MiniGrid Memory episodes.
- `task.observed_clue_from_history()` derives key, ball, or unknown from
  permitted clue-stage observations.
- `task.replay_choice()` replays the final top/bottom choice in MiniGrid for
  evaluator-only scoring checks.
- `model.MemoryModel` defines the shared encoder, GRU, readout, and prediction
  head.
- `model.losses()` defines the final clue-label cross-entropy and next-view
  categorical prediction cross-entropy.
- `model.baseline_probabilities()` implements current-view, recent-window,
  structured-memory, and episodic-retrieval baselines.
- `experiment.train()` trains one learned run and saves the validation-selected
  checkpoint.
- `experiment.evaluate()` writes per-episode rows and controller interventions.
- `analyze_results.summarize()` creates the seed-level primary contrast and
  `analyze_results.traces()` creates the saved real-episode traces.

## Ten likely PI questions

1. **What is the claim?**

   The claim is narrow: in this controlled pilot, short-horizon next-view
   prediction improved prediction metrics but did not reliably improve
   decision-relevant memory. It is a diagnostic result, not a general theory.

2. **Why is this related to belief states?**

   The recurrent hidden state is a compact summary of partial observations and
   actions. The task tests whether that summary preserves an early hidden-world
   fact that matters later.

3. **Why not train directly on top/bottom?**

   The three-class key/ball/unknown label separates memory quality from final
   forced-choice scoring. It lets never-observed episodes be correctly labeled
   unknown instead of pretending one hidden answer was observable.

4. **Could the route phase leak the answer?**

   The phase is public and shared across methods, and route choices are crossed
   independently of clue identity and choice placement. It can help locate when
   clue observations occur, but it should not identify key versus ball.

5. **Why did prediction not help?**

   The established limitation is target mismatch: the local next-view objective
   can be mostly hallway geometry and may not require retaining the initial
   clue. That is a design limitation of the pilot and a follow-up hypothesis,
   not a proven cause of seed 11's failure.

6. **Is the task too easy?**

   For the task-only GRU, yes, the observed condition hit ceiling in all three
   seeds. That makes the pilot weak for detecting improvements. The useful
   failure is that predictive seed 11 did worse despite better prediction.

7. **Are the seeds enough?**

   Three seeds are enough for an outreach pilot and for discovering failure
   modes. They are not enough for a strong public statistical claim.

8. **What did you personally do?**

   Use only facts the student can verify from their own work. Template answer:
   "This was AI-assisted engineering. My verified contribution was [insert only
   what I personally did: for example, reviewed the code, reproduced command X,
   inspected trace Y, wrote summary Z]. I should not claim implementation or
   research experience I cannot personally demonstrate."

9. **What is your background or availability?**

   Use only supplied, verified personal facts. Do not invent a major, GPA,
   coursework, prior lab experience, weekly hours, or schedule. If not yet
   verified, say: "I can provide my current major, preparation, and availability
   in the application materials after checking them."

10. **What would change your mind?**

   A follow-up where the predictive target is forced to depend on the clue,
   where task-only does not already hit ceiling, and where predictive models
   improve held-out decision success across fresh seeds under a frozen protocol.

## Provenance and readiness

This package is AI-assisted. That is acceptable for exploratory outreach if it
is stated plainly and the student personally understands and can reproduce the
work before discussing it as their own preparation.

Readiness verdict:

- Exploratory lab outreach: ready, with honest limitations.
- Private working draft: reasonable after source audit and advisor feedback.
- Public preprint: not ready. It needs a non-ceiling follow-up, stronger seed
  evidence, and a clearer mechanism-distinguishing experiment.
