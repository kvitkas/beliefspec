# BeliefSpec internal experiment protocol

Written 2026-10-01, before main training or held-out evaluation. This is an internal protocol, not an external preregistration. Budget values will be frozen after CPU timing and development-only checks in `configs/frozen.json`.

## Question and hypotheses

Under what conditions does predictive supervision make an agent's memory more useful for decisions? This pilot tests the narrow case of a small GRU on controlled MiniGrid Memory histories. H1: adding action-conditioned next-view prediction changes held-out forced-choice decision success relative to the same recurrent model trained on the common task objective alone. No directional improvement is promised. H2: any benefit may depend on the measured delay. H3: when the clue is never observed, balanced forced-choice success is chance regardless of memory; successful structured memory when the clue is available validates the task.

Next-view prediction often concerns local walls, not the remote clue. A null effect, harm, or ceiling can therefore be an informative limitation of this setup, but cannot establish that predictive memory in general is ineffective.

## Environment and information boundary

Use MiniGrid Memory, fixed size 13, partial 7x7 egocentric observations. Scripted, clue-independent movement delivers histories to a final top/bottom decision. Explicitly document deterministic start, balancing, clue masking, and wait-route modifications. This is a controlled adaptation, not the standard autonomous-navigation benchmark. Models control only the final binary choice. A shared controller executes it in the simulator.

Permitted input: categorical object IDs in partial observations, direction, previous action, and shared controller phase (clue/transit/decision, if needed). Colors/states are constant task-irrelevant values and omitted. No mission text, info, reward, simulator map, hidden clue, episode/seed ID, filenames, or evaluator metadata enters the learned model. Current action enters only the prediction head. Evaluator-only truth stays separate from visible records.

Balance key/ball clue and top/bottom placement in a full factorial design, also crossed with observed/never-observed clue and three delays. Change delay using clue-independent waiting/turning histories. Measure elapsed simulator steps since last actual clue observation; never-observed delay is undefined. Report wait condition separately. Structured memory stores only an observed clue; options must not overwrite it.

## Common interface and baselines

Memory output is a probability vector over [key, ball, unknown]. An explicitly unknown output is [0,0,1]. Binary key probability is p(key)+0.5*p(unknown); choose the observed matching option, resolving an exact tie toward top. This deterministic forced choice is balanced across hidden truths. Three-class readout accuracy is reported separately from binary decision success. Unknown does not count as binary success by itself.

The controller receives a record with `clue_probabilities` and optional nuisance notes. It reads only the probabilities. The irrelevant-information intervention changes a nuisance note; invariance is therefore a by-construction interface check, not a discovered model capability.

Baselines: current observation; last 32 observation/action records; structured last observed clue; episodic retrieval of a previously observed clue-bearing frame; GRU common task loss; matched GRU common task loss plus prediction. Every baseline uses the same choice map observed at the final view and same controller. Handwritten baselines receive the same categorical inputs; their hand-designed parsing is explicitly a source of inductive bias. Retrieval is exact symbolic retrieval, not a pretrained embedding model. No full-state oracle needed.

Common task supervision: final three-class decision-relevant clue label, derived exclusively from permitted history, with unknown when no clue was ever observed. Cross-entropy on this sufficient-statistic readout is the shared supervised task objective. This is not RL and is not hidden-label training on never-observed cases. All learned models share encoder, GRU, readout, initialization within seed, minibatch order, optimizer, update budget and validation selection. The prediction head exists in both models, but only the predictive variant trains it; report allocated and active parameters.

## Prediction and alignment

Categorical cross-entropy for each cell's next object category from [current recurrent state, executed current action]. No arbitrary-ID regression. The recurrent input at t is [view_t, direction_t, previous_action_t, phase_t]; target is view_(t+1). Normalize prediction loss across valid transitions and cells; padding and final steps without a successor are excluded. Total loss is task CE + 0.1*prediction CE for the predictive arm, task CE for control. Baseline prediction-head error is explicitly an untrained reference, not an independent predictor. Also report copy-current-view prediction accuracy.

## Splits and budgets

Development seeds are distinct from three main training seeds [11,22,33]. Candidate route-template counts: 64 train / 16 validation / 32 held-out test per delay; each template crosses the 2x2x2 factors. Disjoint split seeds and exact visible-history hash checks; fixed geometry repeats, so no layout-generalization claim. All variants use paired episodes. Keep final test outcomes unopened until configuration/checkpoint freeze. If test evidence causes a model change, retire that test set as development and generate a fresh test set.

Start with CPU, two Torch threads, one small GRU (32 hidden), encoder width 48, batch size 64, Adam at 0.003, gradient norm clip 1.0. Benchmark a short development run before freezing training epochs (maximum initial budget 200 epochs per main seed/arm). Select lowest validation task cross-entropy checkpoint, not best test success or prediction error; ties retain earliest checkpoint. No best-seed selection. Every run's status, duration, epoch, losses and selected checkpoint are saved.

## Outcomes and uncertainty

Primary contrast: predictive minus control forced-choice success, averaged equally across the three observed-clue delay conditions, calculated within each training seed. Report all three paired seed differences, mean, sample SD, and a descriptive 95% t interval using df=2. This interval is unstable with three training replicates and assumes independent approximately normal seed effects; do not claim significance. Per-delay plots show seed means and seed range. Episode counts are not independent training replications. Report never-observed success separately, three-class readout accuracy, prediction CE/cell accuracy, counts, parameter counts, runtime, evaluation cost, actual delay distributions. Deterministic baselines are descriptive for this finite balanced test set. No broad population or layout confidence claim.

## Validation gates and mechanism checks

Before main runs: assert trajectory/target alignment; prefix invariance to future frames; padding loss masking; episode-state reset; final-task gradient back to clue input; tiny-subset fitting; prediction gradients entering encoder/GRU; save/load equality. Verify structured memory solves all available-clue cases and chance on never-observed cases using real executed final choices. Verify hidden-clue swaps cannot affect outputs for identical visible histories. Test recent-window boundary and clue-independent actions. Check exact visible-history split overlap, and log repeated layouts without a generalization claim.

At final decision compare decoded memory unchanged, replaced by unknown, key/ball swapped, and irrelevant metadata altered. These interventions test the shared deterministic controller's use of the supplied clue probabilities, not causal neural dimensions or an LLM. Classify failures as unavailable, incorrect/forgotten readout, supplied-but-misused, or navigation/interface failure. Trace actual saved episodes.

## Follow-up and stopping rule

Finish a tested, executed pilot and honest report even if negative. Do not alter prediction targets to obtain a win. Any follow-up gets a dated protocol amendment before execution and is labeled exploratory. LLMs, second task families and layout generalization are optional and outside this initial pilot. No paid compute, external publishing, email sending or form submission. Stop when records, code, figures, report/PDF, beginner explanation, outreach drafts and an independent reproduction check are complete, or record a concrete unrecoverable blocker.
