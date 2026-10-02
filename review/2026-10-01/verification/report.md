# BeliefSpec Verification Report

Date: 2026-10-01

Scope: independent verification/reproduction for scientific review and public
GitHub packaging. This pass wrote public artifacts only under
`review/2026-10-01/verification/`, plus private exact local logs under ignored
`.review-runs/private-review-logs/2026-10-01-verification/`.

## Result

Pass. No mismatches were found in the expanded public audit:
`review/2026-10-01/verification/publicaudit_final.json`.

Public files use `PROJECT_ROOT` / root-relative paths. Exact local absolute-path
versions were preserved privately before redaction; path normalization changed
only paths, not results.

## Newly Verified Here

- Frozen package integrity: all 50 files listed in `artifacts/freeze.json`
  matched before and after the review/reproduction run.
- Split validity: train/validation/test visible-history hash overlap was zero
  for all split pairs.
- Labels and metadata: structured-memory labels recomputed from permitted
  observed histories matched `observed_clue`; test row metadata matched the
  saved NPZ/evaluator records.
- Raw final rows: `results/final/episodes.csv` contains 7,680 rows across the
  expected 10 method/seed groups; each group has 768 unique episode IDs and the
  same paired visible-history set.
- Row integrity: choices, readouts, readout correctness, and success were
  recomputed from saved probabilities plus evaluator truth; mismatch count `0`.
- Primary contrast from raw episode rows:
  seed 11 difference = `-0.5`, seed 22 = `0.0`, seed 33 = `0.0`;
  mean = `-0.16666666666666666`; seed SD = `0.2886751345948129`;
  descriptive 95% t interval = `[-0.8837754549852125, 0.5504421216518792]`.
- Six main runs: each config matched frozen settings plus seed/variant, each
  selected checkpoint epoch matched the validation-task-CE minimum rule, and
  checkpoint epochs matched `result.json`.
- Architecture pairing: all six saved checkpoints had matched state-dict shapes
  under `MemoryModel(encoder_size=48, hidden_size=32)`.
- All-six checkpoint re-inference: all six saved checkpoints were re-inferred on
  the 768 held-out episodes; max probability difference `0.0`, max prediction
  metric difference `0.0`, readout mismatches `0`, success mismatches `0`.
- Saved test NPZ target-dependence audit: 192 observed-clue twin pairs differed
  only at observation steps `[0, 1]`; clue-dependent prediction-input times were
  `[0]`; post-clue target comparisons were `6336`; post-clue target differences
  were `0`.
- Representative reproduction: `beliefspec.reproduce` regenerated datasets,
  retrained control seed 11, exactly matched the original checkpoint tensors,
  and reproduced episode successes with max probability / prediction-CE
  difference `0.0`.
- Tests from review CWD: focused model/leakage tests passed (`12 passed`), full
  project tests passed (`22 passed`).

## Readout And Prediction Means

Observed-clue readout accuracy:

- control seeds 11/22/33: `1.0`, `1.0`, `1.0`
- predictive seeds 11/22/33: `0.0`, `1.0`, `1.0`

Observed-clue next-view prediction CE:

- control seeds 11/22/33: `2.4886266185591617`, `2.5179939524581036`,
  `2.4858010994891324`
- predictive seeds 11/22/33: `0.5272918842577686`, `0.4258355345421781`,
  `0.43057170587902266`

## Review-Owned Outputs

- `audit_review.py`: independent audit implementation.
- `publicaudit_final.json`: expanded public final audit and main
  machine-readable evidence.
- `public_audit_final.json`: readability alias of the same audit command.
- `audit_before.json` and `audit_after.json`: path-normalized audit snapshots.
- `execution_log.md`: portable commands and observed outputs.
- `reproduction/verification.json`: representative reproduction result.
- `artifacts/verification/model_checks.json`: tiny-fit debug artifact generated
  from running tests with the review directory as CWD.

## Supplied, Not Fully Reverified Here

- Source-paper claims and related-work accuracy.
- PDF rendering fidelity.
- Public GitHub upload state.
- All-six-run retraining reproduction. Only the requested representative
  reproduction retrained a model; all six saved checkpoints were re-inferred.

## Mismatches

None found in this verification pass.
