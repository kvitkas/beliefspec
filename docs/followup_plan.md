# Follow-up plan

This document proposes future experiments only. None were executed as part of
the original pilot or the 2026-10-02 cleanup. Each requires a fresh protocol,
validation-only tuning, frozen held-out evaluation, and seed-level reporting.

Shared rules: preserve model-visible versus evaluator-only separation, include
unavailable-information controls, match learned variants, and keep final test
data untouched after the protocol is frozen.

## 1. Target relevance

Question: Does prediction help when the prediction target genuinely requires
retaining the earlier clue?

Hypothesis: A clue-dependent future observation will make predictive supervision
more relevant to delayed memory than the original local next-view target.

Smallest useful modification: add a training-only future panel near the decision
point. Its object identity depends on the earlier observed clue. The auxiliary
head predicts that panel from a state before the panel is visible, and the
decision readout does not see the revealed panel before choosing.

Baselines and controls: task-only GRU, original local-prediction GRU,
clue-relevant prediction GRU, structured/episodic sanity checks, a matched extra
clue-readout loss, a shuffled-panel-target placebo, and neutral or
unknown-compatible never-observed targets
unless privileged hidden-label supervision is isolated separately.

Primary metric: seed-level predictive-minus-control observed-clue success, with
readout accuracy and auxiliary prediction loss as supporting metrics.

Counts against the hypothesis: clue-relevant prediction improves only its
auxiliary metric; decision/readout gains disappear on fresh held-out routes; or
local and clue-relevant targets behave the same.

Alternative explanations: label leakage, ceiling control, extra gradient
signal, duplicated clue supervision, or route timing rather than memory.

## 2. Information gathering

Question: When clue information is absent or unreliable, can the agent choose a
useful observation action instead of making an unsupported choice?

Hypothesis: Predictive or uncertainty-aware memory should matter more when the
agent can choose whether to gather information before committing.

Smallest useful modification: add one query point before the final choice. The
model chooses `inspect` or `commit`. `inspect` has a known cost and reveals a
small observation that can resolve uncertainty; `commit` skips the query.

Baselines and controls: always-inspect, never-inspect, validation-tuned
uncertainty threshold, matched task-only and predictive GRUs, and balanced clue
identity, top option, clue reliability, and query result.

Primary metric: cost-adjusted decision utility. Query rate split by available,
unreliable, and unavailable clue conditions is a supporting metric.

Counts against the hypothesis: no utility gain over simple policies,
indiscriminate inspection, low inspection when evidence is unavailable, or
better prediction loss without better query targeting.

Alternative explanations: inspect cost makes a trivial policy optimal,
calibration alone explains querying, query observations leak choice position, or
the task is no longer comparable to the scripted-route pilot.

## 3. Adaptation to stale clues

Question: When an earlier clue becomes stale because the environment changes,
can the agent update its memory and uncertainty appropriately?

Hypothesis: A useful belief state should revise remembered information when
later visible evidence supersedes it.

Smallest useful modification: add a later visible event that confirms the
initial clue, changes it, or makes it unsupported. The final label is the latest
clue state supported by visible history: key, ball, or unknown.

Baselines and controls: initial-only memory, latest-visible-fact structured
memory, simple recency, matched task-only and predictive GRUs, balanced
changed/unchanged/unsupported conditions, and masking that prevents final
choices or route phase from revealing the change condition.

Primary metric: forced-choice success split by unchanged, changed, and
unsupported conditions. Three-class readout accuracy and calibration are
supporting metrics.

Counts against the hypothesis: models keep using the first clue after a visible
change, ignore the first clue in unchanged episodes, or match a simple recency
baseline.

Alternative explanations: the task reduces to recency, public phase identifies
the valid cue, the later cue is easier to parse, or unknown states are poorly
calibrated.

## Difficulty rule

The original task-only GRU reached ceiling on observed clues in all three seeds.
Follow-ups should calibrate difficulty on train/validation data so the control
is strong but imperfect. Possible validation-only adjustments include longer
delays, controlled distractors, reduced phase cues, or modest layout variation.
