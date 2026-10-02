# Comprehension checklist

Use this checklist before discussing BeliefSpec with Professor Qin or Q-Lab.
The goal is not to memorize every number. The goal is to explain the experiment
honestly, including its negative or mixed evidence.

## One-minute explanation

You should be able to say:

- BeliefSpec asks when predictive supervision makes memory more useful for
  decisions.
- The pilot uses a controlled MiniGrid Memory task where the route is scripted
  and the model only chooses the final top/bottom branch.
- The learned comparison is a task-only GRU versus the same GRU trained with an
  auxiliary next-view prediction loss.
- The predictive model learned better next-view prediction, but it did not
  reliably improve the final memory decision.
- The result is useful because it suggests short-horizon local prediction may
  not force the model to remember the decision-relevant clue.

## Task understanding

Check yourself:

- Can I explain why this is a controlled adaptation of MiniGrid Memory, not an
  unchanged benchmark?
- Can I explain what the model controls and what the scripted controller
  controls?
- Can I name the two clue exposure conditions: observed and never observed?
- Can I explain why observed-clue delays are 17, 29, and 53 steps, not simply
  the wait settings 8, 20, and 44?
- Can I explain why never-observed episodes have `delay = null`?
- Can I explain why fixed geometry means this does not test layout
  generalization?

## Information access

Check yourself:

- Can I list the permitted inputs: object-ID image, direction, previous action,
  stage, and executed action for prediction?
- Can I list excluded inputs: mission text, simulator `info`, episode IDs,
  hidden clue, rewards, success position, full-grid render, and evaluator
  metadata?
- Can I explain why evaluator-only logs are saved separately from visible
  records?
- Can I explain why changing hidden facts with identical visible histories
  should not change model inputs?
- Can I explain why the never-observed condition should produce chance
  forced-choice success?

## Labels and scoring

Check yourself:

- Can I explain the three memory labels: key, ball, unknown?
- Can I explain why the task loss is three-class cross-entropy, not binary
  top/bottom success?
- Can I explain why `unknown` readout can be correct while forced-choice success
  is only chance?
- Can I explain how clue probabilities become a top/bottom choice?
- Can I explain why exact ties choose top and why that makes some successes
  "lucky" rather than evidence of memory?

## Baselines

You should be able to describe each baseline in one sentence:

- Current view: uses only the final observation.
- Recent history: uses a bounded 32-frame window.
- Structured memory: records the parsed clue fact from clue-stage observations.
- Episodic retrieval: stores clue-stage frames and retrieves the latest relevant
  one.
- GRU task only: learns a compact recurrent state from the final clue-label
  objective.
- GRU + prediction: uses the same recurrent model plus 0.1 times next-view
  prediction loss.

Check yourself:

- Can I explain why structured and episodic baselines are task-validity checks,
  not claims of a fair learned architecture?
- Can I explain why recent history works at shorter delays but fails when the
  clue falls outside the window?
- Can I explain why the task-only and predictive GRUs have the same allocated
  parameter count?

## Learned-model details

Check yourself:

- Can I explain what a recurrent model is in plain language?
- Can I explain what the GRU hidden state is supposed to carry?
- Can I explain the difference between model weights and per-episode memory
  state?
- Can I explain the difference between training loss and evaluation success?
- Can I explain what a gradient path from final loss back to the clue means?
- Can I explain why categorical object IDs should not be treated as continuous
  numbers?
- Can I explain why the task-only prediction head is allocated but inactive?

Key numbers to know:

| Quantity | Value |
| --- | ---: |
| Total learned-model parameters | 56,171 |
| Shared parameters | 34,611 |
| Prediction-head parameters | 21,560 |
| Auxiliary prediction weight | 0.1 |
| Main training seeds | 11, 22, 33 |
| Train episodes | 1,536 |
| Validation episodes | 384 |
| Test episodes | 768 |
| Epochs per main run | 30 |
| Updates per main run | 720 |

## Results

You should be able to state:

- Current-view success was 0.5 because the start clue was gone.
- Structured and episodic memory solved observed clues and stayed at 0.5 when
  the clue was never observed.
- Task-only GRU observed-clue success was 1.0 for seeds 11, 22, and 33.
- Predictive GRU observed-clue success was 0.5 for seed 11 and 1.0 for seeds
  22 and 33.
- The primary mean predictive-minus-control difference was -0.1667 with a very
  unstable descriptive 95% t interval of [-0.8838, 0.5504].
- Predictive models had much lower next-view cross-entropy than task-only
  models, but that did not guarantee better memory.

Check yourself:

- Can I explain why the interval is seed-level and not an episode-binomial
  confidence interval?
- Can I explain why three seeds are enough for a pilot but not enough for a
  strong general claim?
- Can I explain why a negative or mixed result can still be informative?

## Real trace

Practice explaining `results/traces/observed_success.json`:

- The episode is `test:test-w8-r0:h0:top0:seen`.
- The hidden clue is key, and the top option is key.
- The clue is visible at the start and again after the first turn.
- The measured delay is 17 steps since last clue observation.
- Predictive seed 11 ends with probabilities about key 0.2507, ball 0.2499,
  unknown 0.4994.
- The readout is `unknown`, so memory readout is wrong for an observed key.
- The controller chooses top because unknown mass is split and the top score is
  just over 0.5.
- The simulator success is true only because top happened to be the correct
  branch.

Now practice explaining the paired failure:

- `results/traces/observed_failure.json` uses the same model seed and route but
  hidden clue ball with top option key.
- The final probabilities are almost identical.
- The controller again chooses top.
- This time top is wrong, so success is false.
- This shows seed 11 did not reliably use the decision-relevant clue.

## Figures

Check yourself:

- Can I explain that `decision_success.png` shows forced-choice success versus
  measured delay for observed clues and versus wait setting for never-observed
  clues?
- Can I explain that the figure's error bars are training-seed ranges, not
  confidence intervals?
- Can I explain that `prediction_and_memory.png` separates prediction quality
  from clue readout quality?
- Can I explain that `learning_curves.png` is a development diagnostic over all
  six main learned runs?

## Bugs and safeguards

You should be able to say:

- A masking bug was found before final evaluation: the clue stayed visible after
  the first turn, so every actually visible clue frame needed masking in
  never-observed episodes.
- Delay measurement was tied to the original clue cell, not generic key/ball
  sightings, so final choices would not be mistaken for clue observations.
- Split partitioning was fixed with deterministic disjoint route offsets.
- Tests check padding masks, next-observation alignment, no future leakage,
  memory reset between episodes, save/load consistency, tiny-subset fitting, and
  metadata leakage.

## Related work positioning

Check yourself:

- Can I say that predictive memory itself is not new?
- Can I connect the pilot to belief-state shaping and world-model work without
  claiming it reproduces those papers?
- Can I explain that AgentSpec was inspected and smoke-tested, but this pilot is
  standalone and not an AgentSpec integration?
- Can I explain that no LLM agent was evaluated?

## Outreach honesty

Before contacting Q-Lab, make sure you can say:

- The project was AI-assisted, and I am using it as a learning and outreach
  package.
- I personally understand the code paths, results, and limitations.
- I can reproduce at least the representative analysis or training check on my
  machine.
- I am not claiming publication, novelty, lab membership, or a positive result.
- I am asking for feedback and possible day-to-day mentorship on a narrow next
  experiment.

## Red flags

Do not say:

- "Prediction improved memory."
- "This proves the hypothesis."
- "This is an autonomous navigation result."
- "This is an RL result."
- "This is an LLM-agent evaluation."
- "This generalizes to new layouts."
- "The test episodes are thousands of independent replications."
- "I built all of this without assistance."

Safer wording:

- "In this pilot, next-view prediction improved prediction metrics but did not
  reliably improve decision success."
- "The result suggests the auxiliary target may be too local for the
  decision-relevant memory."
- "The strongest next step is to use a predictive target or task condition that
  actually requires retaining the clue."

