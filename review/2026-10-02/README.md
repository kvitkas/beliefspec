# Publication revision verification — 2026-10-02 UTC

This revision edits the presentation of the completed 2026-10-01 pilot. It does
not change the experiment or execute any proposed follow-up. Original evidence
is distinguished from publication copies in
[evidence preservation](../../docs/evidence_preservation.md).

## Checks executed for this revision

- Before editing: 22 original tests passed in 4.16 s; the raw-record audit passed
  with all 50 frozen live files unchanged. See [tests_before.log](tests_before.log)
  and [audit_before.json](audit_before.json).
- After removing obsolete report/export helpers: the same 22 tests passed in
  4.52 s; source and test lint passed.
- Eight new provenance tests exercise a valid copy, changed current protocol,
  changed frozen code, changed freeze manifest, wrong history, missing history,
  staged-versus-working-tree checks, and an unauthorized second exception.
  All 30 tests passed in 5.03 s. [tests_after.log](tests_after.log) and
  [lint.log](lint.log) record the final suite.
- [audit_after.json](audit_after.json) recomputes all 7,680 episode rows, checks
  split separation and checkpoint selection, re-evaluates all six checkpoints,
  and independently counts the saved target-dependence pairs. It checks the
  original freeze plus the explicitly documented protocol publication copy.
- [reproduction.json](reproduction.json) and [reproduction.log](reproduction.log):
  all three datasets regenerated exactly. A new control-seed-11 training run
  produced identical checkpoint tensors, probabilities, prediction CE, and all
  768 test successes. The command took 42.31 s real, 37.24 s user CPU, and 5.21 s
  system CPU; training took 17.18 s. This is one reproduction, not a fourth
  independent training seed. The existing Python 3.12 project environment and
  CPU-only stack were used.
- The four regenerated figure PNGs and `figure_inputs.json` match the existing
  manuscript figures byte-for-byte. Figure PDFs were regenerated to scratch;
  original figure files were not overwritten. See [figures.log](figures.log).
- Tectonic 0.17.0 built the paper with no warnings, unresolved references, or
  missing figures. Text was extracted from every retained PDF (the seven-page
  paper and seven one-page figure PDFs). Every paper page was visually inspected.
  The first build left a nearly empty eighth page; shortening repetitive prose
  fixed it without changing results. Pages 1–5 rendered identically after the
  final edit; revised pages 6–7 were inspected again. See
  [latex_build.log](latex_build.log) and [pdf_inspection.json](pdf_inspection.json).
- [presentation_checks.json](presentation_checks.json) records the whole-tree
  text and PDF-text scan, local Markdown link check, citation-key check, and
  byte checks for 71 data/configuration/result/checkpoint/dependency records.
  All 71 are unchanged. AgentSpec and its complete author list remain cited.
- [public_preflight.json](public_preflight.json) records the staged-file
  credential/path scan and staged evidence-byte checks. It reports no findings.

## Commands

Executed from the repository root; tests use a scratch CWD because an original
tiny-fit test writes a diagnostic there. Output paths were new. The executable
payloads below omit the local shell logging wrapper.

```bash
PROJECT_ROOT="$PWD"
mkdir -p .review-runs/cleanup-2026-10-02/final-tests
(cd .review-runs/cleanup-2026-10-02/final-tests && "$PROJECT_ROOT/.venv/bin/python" -m pytest "$PROJECT_ROOT/tests" -q)
.venv/bin/python -m ruff check src tests review
.venv/bin/python review/2026-10-01/make_figures.py --output .review-runs/cleanup-2026-10-02/figures
/usr/bin/time -p .venv/bin/python -m beliefspec.reproduce --output .review-runs/cleanup-2026-10-02/reproduction
.venv/bin/python review/2026-10-01/verification/audit_review.py --root . --stage after --reproduction .review-runs/cleanup-2026-10-02/reproduction --output review/2026-10-02/audit_after.json
(cd manuscript && ../.tools/tectonic/tectonic --keep-logs main.tex)
swift review/2026-10-01/inspect_pdf.swift manuscript/main.pdf .review-runs/cleanup-2026-10-02/paper-final
```

The compiler is local-only; a clone can use `tectonic` on PATH as described in
the [manuscript build instructions](../../manuscript/README.md). The Swift helper
requires macOS; it is not an experimental dependency.

## Interpretation and remaining limits

Reported success remains task-only **100%, 100%, 100%** and predictive **50%,
100%, 100%** for seeds 11, 22, and 33 on observed clues. The paired difference
is −16.67 percentage points, with descriptive seed-level 95% t interval
[−88.38, +55.04] points. All never-observed results remain 50%. The post-hoc
audit still finds 0 differing targets among 6,336 post-clue comparisons; it
does not explain the failed predictive run causally.

No new scientific effect, external peer review, cross-platform reproduction,
or all-six-model retraining is claimed. No dedicated type-checker is configured;
the code checks here are pytest, Ruff, and the executable audits. The original
six-run compute figures are historical records, not new measurements.

The author name, individual contribution statement, and project reuse license
remain unresolved. Scientific assistance and dependency attribution are in
[THIRD_PARTY.md](../../THIRD_PARTY.md).
