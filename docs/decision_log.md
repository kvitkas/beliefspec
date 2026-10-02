# Decision log

## 2026-10-01 — before implementation and main experiments

- Empty workspace; create standalone `beliefspec/`. No completed work existed to preserve.
- Local macOS 15.7.7, arm64, 16 GiB RAM, 8 physical/logical CPU cores. Python 3.14.5 is system default; use existing Python 3.12 in a project environment for compatibility.
- CPU first, two Torch threads, small categorical encoder and GRU. No paid compute, API calls, large datasets, or LLM evaluation.
- User's October 1 target is personal, not a lab deadline. Record actual execution dates.
- Independent work lanes: primary-source verification, time-boxed AgentSpec smoke, and controlled MiniGrid data construction. Main owner integrates and validates.
- Pilot is supervised memory/decision learning on scripted, clue-independent trajectories, not autonomous navigation or reinforcement learning. AgentSpec inspection does not imply framework integration or paper reproduction.

## 2026-10-01 — implementation checks and development, before main runs

- AgentSpec revision `f558379e4ef1b39d39bff46e34cd3923e468c550`: 11 offline tests passed; documented API-backed quickstart failed at missing credentials with provider keys unset. Standalone pilot selected; no integration or published-result reproduction claimed.
- Fixed a visibility bug before generating experiment data: clue remains visible after the first turn, so masking only frame 0 would leak it. Both clue-visible frames are now masked in the never-observed condition. Delay uses the original clue cell's actual visibility, not generic key/ball detection that could mistake choice objects for clues.
- Route partitions use one fixed ordering and disjoint offsets, avoiding overlap from independently shuffled split lists. The public seed argument is a compatibility placeholder; actual route RNG is `10000+wait`, environment reset seed 0, crossed object identities. Fixed geometry repeats; no layout generalization is claimed.
- Train/validation: 1,536/384 episodes, 1,152/288 distinct visible histories, zero cross-split overlap. Never-observed clue twins intentionally duplicate visible histories with opposite hidden answers.
- Measured clue delays are 17, 29, 53 steps, corresponding to extra waits 8, 20, 44. Structured observed memory solves the task.
- Tiny-set checks fit three real episodes (key/ball/unknown); this is a debugging gate, not evidence of generalization.
- Development seed 101, 10 epochs: task-only reached validation readout accuracy 1.0; predictive 0.5442708333. Exact losses/times in `runs/development/*/history.jsonl` and `result.json`. Predictive loss and task optimization can compete; do not assume benefit. No test model outcomes inspected.
- Freeze main budget at 30 epochs (720 updates per run), seeds 11/22/33, prediction weight 0.1, unchanged architecture/objectives. CPU dev timing supports this laptop budget; no acceleration benchmark needed because CPU is already fast. Both arms retain identical data, shuffle, initialization and checkpoint selection. Do not use the development convergence contrast as a final test finding.
- Prespecified supporting diagnostic: plot all main validation learning curves and report first epoch reaching 99% validation readout, without selecting new budgets or targets from test data.

## 2026-10-01 — review before held-out model scoring

- Independent code review found no critical leakage or fairness issue. Fixed explicit freeze/audit/replay guards so Python optimization cannot disable them; expanded freeze hashes to include selection histories, metadata, environment and package records; prevented accidental rerun from writing failures into completed runs; distinguished unavailable unknown readout from unsupported hallucinated readout. These are guard/reporting changes, not model/objective changes.
- Six main runs completed, all retained. Predictive seed 11 reached only the prior solution on training/validation; checkpoint selection nevertheless follows the prespecified minimum validation task CE rule. This run is an observed optimization failure, not an excluded crash.

## 2026-10-01 — frozen held-out evaluation and handoff

- `artifacts/freeze.json` hashed 50 code/config/data/checkpoint/selection/evidence files before any final learned-model test scoring. No architecture, objective, model selection, evaluation episode set or metric changed after final outcomes were read.
- All three control seeds scored 100% on observed clues; predictive seeds 11/22/33 scored 50%/100%/100%. The paired mean difference is -16.667 percentage points, descriptive 95% t interval [-88.38,+55.04] points, with only three training replications. Every method scored 50% when the clue was unavailable. No run or episode was excluded.
- Prediction improved but did not reliably improve decisions. One predictive run has a readout/optimization failure, while the control is at ceiling. This pilot cannot identify a general causal effect of predictive supervision or distinguish all optimization explanations. No follow-up prediction target, loss-weight search, second task, or LLM experiment was executed.
- Fresh `.venv-repro` from locked dependencies regenerated all three datasets exactly and retrained control seed 11 with identical tensors and all 768 recorded decisions. `runs/reproduction/verification.json` is the evidence.
- Final record audit: 7,680 scored rows, 10 method/seed groups sharing episodes, 1,920 unavailable hidden-clue swap checks, 768 structured simulator replays, and 30,720 decoded-memory intervention rows. All 50 frozen files still match. Three selected illustrative neural-model traces were additionally replayed to actual terminal simulator rewards; these are illustration/verification, not exploratory aggregate results.
- Regenerated figures from saved records, rendered a five-page pilot report and one-page summary, and reviewed document claims against data. Added a beginner tutorial with actual state/readout/prediction records, comprehension checklist, unsent 175-word email and manuscript outline. Public preprint not warranted; exploratory outreach is reasonable after the user understands the package and replaces personal placeholders.
- Rechecked Q-Lab official application instructions. Actual form fields remain behind Google sign-in. No email, form, public repository or preprint was sent/submitted/published/uploaded.

### Post-hoc target-dependence diagnostic (specified before this check)

After primary evaluation, compare observed-clue key/ball episode twins with the same route and choice placement. Count whether prediction targets differ after the clue vanishes. This audits the information required by the chosen target and helps interpret a limitation; it is a post-hoc deterministic data-property check, not another trained experiment or a prespecified primary result. No change to models or primary evaluation is permitted.

Outcome: 192 observed episode pairs; clue-dependent next-view targets only at t=0; zero differences in 6,336 post-clue target comparisons. The target therefore does not require long-delay clue retention in this controlled route. It does not establish the cause of the predictive seed-11 optimization failure. Raw pair records are saved in `results/target_dependence_diagnostic.json`.
