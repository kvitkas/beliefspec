# Execution Log

Public paths are normalized for review portability. Use:

```bash
PROJECT_ROOT=/path/to/beliefspec
cd "$PROJECT_ROOT"
```

Exact local logs with machine-specific absolute paths were preserved under
`.review-runs/private-review-logs/2026-10-01-verification/`, which is ignored by
the project. Public path normalization changed only paths, not checked results.

## 1. Preserve Exact Local Logs Privately

Command:

```bash
rtk mkdir -p .review-runs/private-review-logs/2026-10-01-verification
rtk cp review/2026-10-01/verification/audit_before.json .review-runs/private-review-logs/2026-10-01-verification/audit_before.absolute.json
rtk cp review/2026-10-01/verification/audit_after.json .review-runs/private-review-logs/2026-10-01-verification/audit_after.absolute.json
rtk cp review/2026-10-01/verification/execution_log.md .review-runs/private-review-logs/2026-10-01-verification/execution_log.absolute.md
rtk cp review/2026-10-01/verification/report.md .review-runs/private-review-logs/2026-10-01-verification/report.absolute.md
```

Output: no stdout/stderr.

## 2. Focused Verification Tests From Review CWD

Command:

```bash
cd "$PROJECT_ROOT/review/2026-10-01/verification"
rtk env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PROJECT_ROOT/src" "$PROJECT_ROOT/.venv/bin/python" -m pytest "$PROJECT_ROOT/tests/test_model.py" "$PROJECT_ROOT/tests/test_leakage.py" -q
```

Output:

```text
............                                                             [100%]
12 passed in 3.38s
```

## 3. Full Test Suite From Review CWD

Command:

```bash
cd "$PROJECT_ROOT/review/2026-10-01/verification"
rtk env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PROJECT_ROOT/src" "$PROJECT_ROOT/.venv/bin/python" -m pytest "$PROJECT_ROOT/tests" -q
```

Output:

```text
......................                                                   [100%]
22 passed in 4.06s
```

## 4. Representative Reproduction

Command:

```bash
cd "$PROJECT_ROOT"
rtk env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PROJECT_ROOT/src" "$PROJECT_ROOT/.venv/bin/python" -m beliefspec.reproduce --output review/2026-10-01/verification/reproduction
```

Key output:

```text
[
  {
    "seed": 11,
    "variant": "control",
    "exact_checkpoint_tensors": true,
    "max_probability_or_prediction_ce_difference": 0.0,
    "all_episode_successes_identical": true,
    "observed_success": 1.0,
    "never_success": 0.5
  }
]
```

The reproduction output is saved at `review/2026-10-01/verification/reproduction/verification.json`.

## 5. Expanded Public Audit

Command:

```bash
cd "$PROJECT_ROOT"
rtk env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python review/2026-10-01/verification/audit_review.py --root "$PROJECT_ROOT" --stage after --reproduction "$PROJECT_ROOT/review/2026-10-01/verification/reproduction" --output "$PROJECT_ROOT/review/2026-10-01/verification/publicaudit_final.json"
```

Output:

```text
{
  "output": "review/2026-10-01/verification/publicaudit_final.json",
  "passed": true,
  "failures": [],
  "audit_runtime_seconds": 2.5632239169208333
}
```

The same expanded audit was also written to
`review/2026-10-01/verification/public_audit_final.json` for readability.

## 6. Path-Leakage Check

Command:

```bash
PRIVATE_PATH_PATTERN='<local absolute path or account name>'
rtk rg -n "$PRIVATE_PATH_PATTERN" review/2026-10-01/verification
```

Final result after public log normalization: no matches.
