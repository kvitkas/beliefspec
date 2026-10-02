# Follow-up plan

This document proposes next experiments only. It does not report executed work.
The priority is to distinguish mechanisms more clearly than the original pilot:
does predictive supervision help because the prediction target requires the
decision-relevant fact, or does it merely improve local world modeling without
useful memory?

Before running any follow-up, write a fresh protocol, freeze train/validation
tuning rules, and keep final evaluation seeds untouched until settings are
fixed. Avoid a ceiling task where the task-only GRU already reaches perfect
observed-clue success.

## Shared design rules

Use the original pilot as the baseline package:

- same controlled MiniGrid-style memory setting unless a modification is named;
- same six method families where feasible;
- same three-class key/ball/unknown memory label;
- same forced-choice controller contract;
- same separation of evaluator-only metadata from model-visible records;
- same train, validation, and held-out test discipline.

Changes should be minimal. Each follow-up should change one reason the original
pilot may have been insensitive, while preserving enough of the original
pipeline for comparison.

Fresh evaluation rule:

- tune architecture, budgets, prediction weight, and task difficulty on
  train/validation only;
- freeze seeds, episode counts, checkpoint rules, and primary metrics before
  held-out test scoring;
- if a held-out result influences design, relabel that set as development and
  generate a fresh held-out set.

Primary metrics should stay seed-level:

- forced-choice success on observed clues by measured delay;
- three-class clue readout accuracy;
- next-view or auxiliary-target cross-entropy;
- never-observed forced-choice success near 0.5;
- structured/episodic sanity checks;
- per-seed paired predictive-minus-control differences.

## Priority 1: Target relevance

Question: Does predictive supervision help when the prediction target actually
requires the decision-relevant clue?

Hypothesis: The original next-view target was too local. A target that cannot be
predicted without the start clue should create a better test of predictive
memory.

Concrete mechanism:

- After the original memory delay, add a scripted neutral reveal panel that
  becomes visible only after the model has already formed the pre-reveal hidden
  state used for the auxiliary prediction.
- The panel's future sensory content depends on the earlier observed clue. For
  example, after a key clue the future panel contains a key-shaped marker; after
  a ball clue it contains a ball-shaped marker; after an unknown clue it contains
  an uninformative neutral marker.
- The auxiliary head predicts the future panel from the pre-reveal state, before
  the reveal panel enters the model input.
- The final decision readout is evaluated before the revealed panel is allowed
  to influence the decision state, or on a separate branch where the panel is a
  training-only sensory target and not part of the decision input.

Minimal modification:

- Keep the same route and final forced-choice interface.
- Add the clue-dependent future panel as a sensory prediction target near the
  final decision point.
- Preserve the original short-horizon next-view objective as a comparison arm:
  task-only, local-prediction, clue-relevant-prediction.

Controls:

- Match recurrent capacity and task-label access.
- Keep the same number of task updates across learned arms.
- Report extra auxiliary-head parameters and compute.
- Include structured and episodic baselines to verify the clue is sufficient.
- Include never-observed episodes with a neutral observed future target. Do not
  train the auxiliary head on hidden simulator labels when the clue was never
  observed.
- Mark the future-panel target as training-only sensory supervision. At
  evaluation, distinguish decision performance from auxiliary prediction.

Privileged-target pitfalls:

- If the future panel is generated from hidden simulator truth when the clue was
  not observed, the auxiliary label is privileged supervision. That can be a
  deliberately labeled separate experiment, but not the main fair comparison.
- If the decision readout sees the revealed panel before choosing, the task no
  longer tests memory.
- If the panel is deterministic from route timing rather than clue identity, it
  does not test target relevance.
- If never-observed examples are assigned key/ball panel labels from hidden
  truth, the supervision contract changes and must be reported. Balanced,
  identical test histories still cannot identify the hidden answer: extra
  training labels alone do not remove that information limit.

Primary metric:

- predictive-minus-control observed-clue forced-choice success by training seed,
  with clue readout accuracy as the mechanism metric.

Counterevidence:

- local and clue-relevant prediction both improve prediction loss but neither
  improves clue readout or decision success;
- clue-relevant prediction improves only its auxiliary metric while final memory
  remains unchanged;
- gains disappear on fresh held-out routes.

Alternative explanations to check:

- the auxiliary target leaks the answer through labels rather than visible
  history;
- the task is still at ceiling for the task-only GRU;
- improvements come from extra gradient steps or active parameters rather than
  target relevance;
- a clue-shaped panel simply duplicates the existing clue classification loss.
  Include a matched extra clue-readout loss control before attributing a gain
  specifically to future-observation prediction;
- the model exploits route timing instead of remembering clue identity.

Best competing-mechanism distinction:

- If clue-relevant prediction helps while local next-view prediction does not,
  the evidence points to target relevance.
- If both help equally, the benefit may be generic auxiliary regularization.
- If neither helps, the bottleneck may be architecture, optimization, or task
  sensitivity rather than predictive supervision.

## Priority 2: Information gathering

Question: Does predictive supervision help more when the agent must decide what
information to gather, not merely remember information supplied by a script?

Hypothesis: Prediction may matter more when actions determine whether useful
evidence will be observed.

Minimal modification:

- Add one explicit query point before the final choice. The model must choose
  `inspect` or `commit`.
- `inspect` has a modest known cost, such as one extra step or a small utility
  penalty, and reveals a small observation panel that can disambiguate the
  currently relevant clue.
- `commit` skips the query and proceeds directly to the final top/bottom
  decision.
- Optionally include an unreliable-initial-cue condition where the early clue is
  sometimes absent, masked, or visibly noisy. In that condition, inspection
  should be useful only when the current memory state is uncertain.

Controls:

- Always-inspect baseline: pays the cost and receives the query observation.
- Never-inspect baseline: never pays the cost and relies on memory.
- Threshold policy baseline: uses only permitted model-visible uncertainty, not
  hidden truth, to inspect when confidence is below a fixed validation-tuned
  threshold.
- Task-only versus auxiliary-prediction learned arms must be capacity matched.
- Balance clue identity, top option, initial-cue reliability, and query result.
- Keep query cost known and independent of clue identity.
- Keep final decision scoring compatible with the original key/ball/unknown
  contract.

Primary metric:

- cost-adjusted decision utility: final success value minus inspect cost;
- targeted query rate: how often the model inspects when the permitted visible
  history is uncertain versus when it is already sufficient.

Counterevidence:

- no cost-adjusted gain over never-inspect or always-inspect;
- indiscriminate querying that pays the cost even when memory is confident;
- low query rate in genuinely uncertain or unreliable-cue cases;
- improved prediction loss without improved query targeting or utility.

Alternative explanations to check:

- the inspect panel is too cheap, making always-inspect optimal;
- the inspect panel is too expensive, making never-inspect optimal;
- uncertainty calibration, not predictive memory, explains query behavior;
- query observations leak final choice position rather than resolving the clue.

Limitations:

- A threshold policy based on permitted uncertainty is a calibration baseline,
  not a human-level policy.
- This follow-up would introduce an action choice absent from the original
  pilot, so it should be reported as a new task variant, not a direct rerun.

## Priority 3: Stale-clue adaptation

Question: Can predictive supervision help when early information becomes stale
and the agent must update its belief?

Hypothesis: A useful belief state should not only remember; it should revise
memory when later evidence contradicts or supersedes the initial clue.

Minimal modification:

- Add a condition where the initial clue can be changed or invalidated by a
  later visible event cue before the final decision.
- Keep a no-change condition so the original memory requirement remains.
- Preserve the key/ball/unknown readout contract. The label remains the latest
  supported observed clue, or unknown when the visible history does not support
  either object.
- Include at least three event types: reliable change cue, explicit no-change
  cue, and cued-unknown/refresh-needed cue.

Controls:

- Balance changed versus unchanged episodes.
- Make later evidence visible under the same masking and leakage rules.
- Ensure the final choices do not reveal whether the clue changed.
- Keep route timing independent of clue identity and change condition.
- Add initial-only, latest-fact, and recency baselines. Initial-only should fail
  changed cases; latest-fact should solve reliably observed updates; recency
  tests whether simple "use the last cue" behavior explains performance.

Primary metric:

- success and readout accuracy split by unchanged, changed, and never-observed
  conditions.

Counterevidence:

- models keep using the first clue after a later cue changes it;
- models ignore the first clue even in unchanged episodes;
- changed-condition success comes from final-view leakage;
- prediction improves local CE but not update behavior;
- performance is matched by a simple recency baseline, so no belief-update
  mechanism is needed.

Alternative explanations to check:

- the task becomes a recency heuristic instead of belief updating;
- the public phase cue tells the model which clue is valid;
- the later cue is easier to parse than the initial cue, hiding memory demands;
- unsupported queries or cued-unknown states are poorly calibrated, making
  unknown behavior hard to interpret.

## Non-ceiling difficulty adjustments

The original task-only GRU hit 1.0 observed-clue success in all three main
seeds. Follow-ups need room for improvement without becoming broken.

Candidate adjustments:

- increase delay or distractor diversity gradually;
- remove or coarsen the public phase cue in a controlled ablation;
- increase layout variation after the target-relevance question is stable;
- reduce training set size only as a sensitivity analysis, not as the main
  contribution;
- report a task-only target range before final evaluation, for example high
  but imperfect validation performance.

Do not tune on final test to get a positive result. If task-only remains at
ceiling, report that and choose a harder validation-only setting before freezing
the next held-out evaluation.

## Minimum next package

A useful next private package would contain:

- a dated protocol naming one primary follow-up question;
- train/validation development runs for difficulty calibration;
- frozen final seeds and held-out routes;
- all failed runs and exclusions;
- raw episode-level results;
- one mechanism trace per important success/failure class;
- an explicit comparison to the original pilot.

For outreach, the strongest near-term plan is Priority 1: target relevance. It
most directly tests the competing explanation raised by the original result:
local prediction may be learnable without storing the clue.
