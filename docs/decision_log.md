# Decision log

This is the publication-facing decision log. It preserves scientific and
engineering decisions from the completed pilot. On 2026-10-02, non-scientific
completion logistics were removed from this copy; the original 2026-10-01 text
remains recoverable through Git history and the private pre-cleanup archive.

## 2026-10-01 - setup and scope

- The workspace did not contain a completed BeliefSpec project, so a standalone
  `beliefspec/` package was created.
- Execution was local on macOS 15.7.7, arm64, 16 GiB RAM, 8 CPU cores. Python
  3.12 was used in a project environment for package compatibility.
- The initial budget used CPU, two Torch threads, a small categorical encoder,
  and a GRU. No paid compute, paid APIs, large datasets, or LLM evaluation were
  used.
- The pilot was scoped as supervised memory/decision learning on scripted,
  clue-independent MiniGrid trajectories. It is not autonomous navigation,
  reinforcement learning, an LLM-agent evaluation, or an AgentSpec reproduction.

## 2026-10-01 - source and framework checks

- AgentSpec revision `f558379e4ef1b39d39bff46e34cd3923e468c550` was inspected.
  Eleven offline tests passed. API-backed quickstart commands were blocked by
  missing provider credentials, so the final pilot remained standalone.
- Primary sources were verified before citation. The source notes distinguish
  broad related work from claims supported by this pilot.

## 2026-10-01 - task construction and development checks

- A visibility bug was fixed before final data generation: the clue remains
  visible after the first turn, so never-observed episodes must mask every frame
  where the clue cell is visible, not only frame 0.
- Delay measurement was tied to actual visibility of the original clue cell.
  This avoids confusing final choice objects with the initial clue.
- Route partitions use fixed ordering and disjoint offsets. This prevents
  accidental train/validation/test overlap from independently shuffled split
  lists. Fixed geometry repeats, so no layout-generalization claim is made.
- Train/validation contained 1,536/384 episodes and 1,152/288 distinct visible
  histories, with zero cross-split overlap. Never-observed clue twins
  intentionally duplicate visible histories with opposite hidden answers.
- Measured observed-clue delays were 17, 29, and 53 steps, corresponding to
  extra waits 8, 20, and 44.
- Tiny-set fitting was used as a debugging gate for key, ball, and unknown
  labels. It was not treated as evidence of generalization.
- Development seed 101 showed task-only validation readout accuracy 1.0 after
  10 epochs and predictive validation readout accuracy 0.5442708333. This
  warned that the auxiliary objective could compete with the task objective.
  Test outcomes were not inspected during this development step.

## 2026-10-01 - frozen main run

- The main budget was frozen at 30 epochs, 720 updates per run, seeds 11/22/33,
  prediction weight 0.1, and unchanged architecture/objectives.
- Before main scoring, validation learning curves and first epoch reaching 99%
  readout accuracy were specified as supporting diagnostics, not budget-selection
  criteria based on test results.
- Task-only and predictive arms used matched data, shuffling, initialization,
  optimizer, recurrent capacity, downstream controller, and validation-based
  checkpoint selection.
- Independent code review found no critical leakage or fairness issue. Guard
  changes used explicit errors rather than optimization-removable assertions,
  expanded freeze coverage to selection histories and execution metadata, and
  prevented reruns from altering completed runs. These did not change the model
  objective or evaluation episode set.
- Six main runs completed and were all retained. Predictive seed 11 reached a
  prior-like solution on train/validation and was kept under the frozen
  selection rule; it was not excluded as a crash.

## 2026-10-01 - held-out evaluation and audits

- `artifacts/freeze.json` hashed 50 code/config/data/checkpoint/selection/evidence
  files before final learned-model test scoring.
- Final observed-clue success was 1.0/1.0/1.0 for task-only seeds 11/22/33 and
  0.5/1.0/1.0 for predictive seeds 11/22/33. The paired mean difference was
  -0.1667 with descriptive 95% t interval [-0.8838, 0.5504].
- Every method scored 0.5 forced-choice success when the clue was unavailable.
  No run or episode was excluded.
- Prediction improved substantially, but decision success did not improve
  reliably. The control was at ceiling, and the failed predictive seed does not
  identify a general causal effect.
- A fresh `.venv-repro` from locked dependencies regenerated all three datasets
  and retrained control seed 11 with identical tensors and all 768 recorded
  decisions.
- Final audits covered 7,680 scored rows, 10 method/seed groups sharing
  episodes, 1,920 unavailable hidden-clue swap checks, 768 structured simulator
  replays, and 30,720 decoded-memory intervention rows.
- Figures were regenerated from saved records. The report and summary were
  checked against the saved data.

## Post-hoc target-dependence diagnostic

After primary evaluation, a deterministic audit compared observed-clue key/ball
episode twins with the same route and choice placement. This was a post-hoc
data-property check, not a new trained experiment or a prespecified primary
result.

Outcome: 192 observed episode pairs were compared. Clue-dependent next-view
targets appeared only for input `t=0` predicting observation `t=1`; there were
zero differences in 6,336 post-clue
target comparisons. The chosen target therefore did not require long-delay clue
retention after the clue disappeared. This does not establish the cause of the
predictive seed-11 optimization failure.
