# BeliefSpec code/spec/security review

Date: 2026-10-01

Role: code-reviewer lane for public research packaging.

Verdict: COMMENT

## Files reviewed

Reviewed 31 source/config/test/core-doc files plus saved evidence artifacts:

- `src/beliefspec/task.py`
- `src/beliefspec/model.py`
- `src/beliefspec/dataio.py`
- `src/beliefspec/experiment.py`
- `src/beliefspec/audit.py`
- `src/beliefspec/analyze_results.py`
- `src/beliefspec/freeze.py`
- `src/beliefspec/package.py`
- `src/beliefspec/render_report.py`
- `src/beliefspec/replay_traces.py`
- `src/beliefspec/reproduce.py`
- `src/beliefspec/run_main.py`
- `src/beliefspec/target_diagnostic.py`
- `src/beliefspec/verify_package.py`
- `tests/test_task.py`
- `tests/test_model.py`
- `tests/test_leakage.py`
- `tests/test_interface.py`
- `configs/frozen.json`
- `configs/development.json`
- `pyproject.toml`
- `README.md`
- `.gitignore`
- `docs/protocol.md`
- `docs/task_contract.md`
- `docs/decision_log.md`
- `docs/pilot_report.md`
- `docs/project_summary.md`
- `docs/preprint_readiness.md`
- `docs/related_work.md`
- `docs/application_procedure.md`

Evidence artifacts inspected included `results/summary.json`, `results/final/episodes.csv`, `results/final/interventions.csv`, `artifacts/freeze.json`, `artifacts/verification/package_checks.json`, `runs/reproduction/verification.json`, and review packaging files under `review/2026-10-01/`.

## Severity summary

- CRITICAL: 0
- HIGH: 0
- MEDIUM: 0
- LOW: 0

No code/spec/security finding currently requires changes before private exploratory outreach. The appropriate verdict is COMMENT rather than APPROVE because this is a research package with known scientific limitations, not production software or a merge gate.

## Review findings

No open CRITICAL/HIGH/MEDIUM/LOW findings.

The previously identified public privacy risk from local absolute paths appears addressed for the public packaging surface:

- `.gitignore:15-20` excludes the private outreach/application docs and AgentSpec raw logs that contain personal machine paths.
- `README.md:96-106` states the freeze is preserved, older reports are historical, author identity/personal contribution must be supplied honestly, no license has been selected, private application drafts and personal-path logs remain local, and no email/application/preprint was submitted.
- `README.md:72-75` tells public users not to run the old private `package` entry point because it writes original/private artifacts.

Residual note: private local files such as `docs/agentspec_smoke.md` and `artifacts/agentspec/*.log` still exist in the working tree and contain local paths. That is acceptable only because they are explicitly private/local and ignored for public packaging. Do not add or publish them without sanitizing.

## Spec compliance and scientific validity

### Leakage and label provenance

Status: pass.

Evidence:

- `src/beliefspec/task.py:164-169` derives `observed_clue` from permitted visible history and checks it against the intended observed/unknown condition during generation.
- `src/beliefspec/model.py:42` uses `episode.observed_clue` as the learned task label, not hidden simulator truth.
- `src/beliefspec/dataio.py:40-53` loads evaluator metadata only when `with_evaluator=True`.
- `src/beliefspec/experiment.py:263-265` trains on `data/train` and `data/validation` through `load_dataset(...)` without evaluator metadata.
- `tests/test_leakage.py:11-74` covers evaluator metadata mutation, mission/info/filename leakage, hidden/evaluator separation, and identical visible histories under hidden-truth swaps.
- `artifacts/verification/package_checks.json` records 1,920 hidden-swap output checks.

Intentional limitation, not a bug: the completed package includes `data/*/evaluator_only.json` and final raw outcome rows with hidden truth for evaluation and reproducibility. The docs present those as evaluator-only records, not model inputs or a sealed benchmark.

### Matched arms, checkpointing, and freeze

Status: pass.

Evidence:

- `src/beliefspec/model.py:47-83` defines one matched `MemoryModel` shape with shared encoder, GRU, readout, and prediction head.
- `src/beliefspec/experiment.py:59-64` seeds each run and sets the prediction-loss weight by variant.
- `src/beliefspec/experiment.py:68-83` uses the same epoch/batch/update loop shape for both learned variants.
- `src/beliefspec/experiment.py:89-93` selects checkpoints by validation task cross-entropy, not by test success or prediction error.
- `configs/frozen.json:1-19` freezes the model size, optimizer, seeds, waits, measured delays, update budget, split sizes, and CPU device.
- `src/beliefspec/freeze.py:15-33` hashes frozen config, source, train/validation/test data, selected checkpoints, run configs/results/histories, environment, requirements, and train/validation/test audit evidence before final scoring.
- `src/beliefspec/run_main.py:16-17` prevents overwriting the original main execution.
- `src/beliefspec/reproduce.py:26-33` checks deterministic dataset regeneration before representative reproduction.

Intentional limitation, not a bug: the task-only control allocates a prediction head but does not train it. The report and README correctly describe its prediction metrics as an untrained contrast.

### Uncertainty and reporting

Status: pass.

Evidence:

- `docs/protocol.md:41` prespecifies seed-level paired differences and warns against treating episode rows as independent training replications.
- `src/beliefspec/analyze_results.py:44-62` computes the primary contrast across three training seeds and writes a descriptive df=2 interval.
- `results/summary.json` records seed differences `[-0.5, 0.0, 0.0]`, mean `-0.16666666666666666`, and a warning that the interval is unstable and not an episode-binomial confidence interval.
- `docs/pilot_report.md`, `docs/preprint_readiness.md`, `docs/project_summary.md`, and `README.md` consistently present the result as exploratory outreach evidence, not a public-preprint-ready contribution.

Intentional limitation, not a bug: the t critical value in the original analysis is specialized to the frozen three-seed pilot. It should be generalized before any larger follow-up, but it matches the current protocol.

### Publication, credential, and privacy safety

Status: pass with residual private-file caution.

Evidence:

- `README.md:103-106` says substantial AI assistance must be disclosed, no license has been selected, private application drafts and personal-path logs remain local, and no email/application/preprint was submitted.
- `docs/application_procedure.md:3` and `docs/outreach_email.md:3` state no email was sent and no form was submitted.
- `.gitignore:10-14` excludes common secret material such as `.env`, `.pem`, `.key`, and zip archives.
- `.gitignore:15-20` excludes the private personal-path logs and outreach/application drafts.
- Secret scan found credential variable names and missing-credential messages, but no stored credential values.

Intentional limitation, not a bug: `src/beliefspec/package.py:1` is explicitly a private local handoff archive builder. Public packaging should follow the README/review instructions rather than this old private helper.

### Maintainability

Status: acceptable for a small pilot.

Evidence:

- Core modules have narrow responsibilities: task generation, model/losses, IO, training/evaluation, analysis, freeze, reproduction, and verification.
- Validation paths use explicit exceptions in current critical scripts, e.g. `src/beliefspec/freeze.py:12-13` and `src/beliefspec/freeze.py:27-28`, `src/beliefspec/reproduce.py:31-32`, `src/beliefspec/verify_package.py:13-15`.
- Existing tests cover the main scientific contracts: route invariance, split disjointness, structured replay, recent-window boundary, prediction alignment, padding masks, no future leakage, reset behavior, gradient path, predictive gradients, save/load consistency, tiny-subset fit, interface validation, and metadata leakage.

## Verification note

I did not rerun the isolated test suite in this review pass because the model-verification agent owns that lane. This review used source inspection, saved-evidence inspection, and static pattern scans through `rtk rg` for local paths, credentials, hidden/evaluator access, uncertainty claims, and publication-risk terms.

## Recommendation

COMMENT.

The current package is acceptable for private exploratory lab outreach and technical discussion, provided the user preserves the distinction between original frozen evidence and later review/package materials. Before any broader public release, keep ignored private docs/logs out of the archive, run the public preflight, and explicitly choose a license/provenance policy.
