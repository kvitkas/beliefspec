# Release verification

Review session: 2026-10-01 America/New_York (final checks also fall on 2026-10-02 UTC).
This is packaging/reproduction of the existing pilot, not a new experiment.

## Newly executed from a clean checkout

The local Git checkout of commit `6017950` was cloned with `git clone --no-hardlinks`
into ignored `.review-runs/clean-checkout`. A new `.venv` was created there; it did not
reuse the installed project or environment from the original working directory.
Dependencies were installed from the local package cache where available.

Commands below were executed through the workspace's `rtk proxy sh -c` wrapper.
Paths are relative to the clean checkout; `PROJECT_ROOT` was its actual absolute path.

```bash
uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python requirements.lock.txt
uv pip install --python .venv/bin/python --no-deps -e .
PROJECT_ROOT="$PWD"
mkdir -p .review-runs/tests
(cd .review-runs/tests && "$PROJECT_ROOT/.venv/bin/python" -m pytest "$PROJECT_ROOT/tests" -q)
.venv/bin/python -m ruff check src tests review/2026-10-01
.venv/bin/python review/2026-10-01/verification/audit_review.py --root . --stage after --output .review-runs/audit.json
.venv/bin/python review/2026-10-01/make_figures.py --output .review-runs/figures
/usr/bin/time -p .venv/bin/python -m beliefspec.reproduce --output .review-runs/reproduction
.venv/bin/python review/2026-10-01/verification/audit_review.py --root . --stage after --reproduction .review-runs/reproduction --output .review-runs/audit_post.json
```

Results:

- Fresh Python 3.12.13 environment; all 33 pinned dependencies installed successfully.
- **22 tests passed in 23.17 s**; lint passed. Earlier warm review-CWD test run: 4.06 s.
  These individual timings are not a benchmark.
- All-six-checkpoint re-inference and full record audit passed with no mismatches.
- All three datasets regenerated exactly; control seed 11 retrained with identical
  tensors, probabilities, prediction CE, and all 768 success outcomes.
- Full reproduction command: 44.41 s real, 37.69 s user CPU, 5.89 s system CPU;
  includes dataset regeneration, training, and comparison. CPU only.
- Four regenerated PNGs and `figure_inputs.json` are byte-identical to the review figures.
- Original experiment freeze still matches all 50 files in the clone and original project.

Raw command outputs and final audit are in `clean_checkout/`. The original main-run
109.224 s training time and peak memory are supplied historical measurements, not
remeasured six-run training in this review. Only control seed 11 was retrained;
all six saved checkpoints were re-evaluated, not retrained.

## Manuscript

Tectonic 0.17.0 compiled `manuscript/main.tex` with BibTeX/reference passes, with no
warnings in the final build. The clean checkout also compiled successfully, using
the same local compiler with `--keep-logs --outdir ../.review-runs/latex main.tex`
from `manuscript/`. The compiler binary is not included in Git.

The macOS PDFKit helper `inspect_pdf.swift` rendered the PDF to page images and
extracted text. The final PDF has **7 pages**, four data-derived figures, all six
learned runs in the table, and resolved references. Page images were visually checked
for clipping and readability. Machine-readable page counts are in `pdf_inspection.json`;
large redundant page previews stay local.

## Preservation and publication checks

- Compared the private original package manifest's 127 files: **125 unchanged**.
  Only `README.md` and `.gitignore` changed, intentionally. Their original versions
  remain in the truthful initial Git import. All frozen experiment files are unchanged.
- Git initially normalized CSV newlines in its index. `.gitattributes` now preserves
  original bytes and recognizes CRLF CSV lines; the final Git blobs match the original
  raw CSVs exactly. No result value was changed.
- Checked all 18 local links in the replacement README; none were missing.
- Staged-file heuristic scan found no credential patterns, personal machine paths,
  personal email addresses, private application documents, environments, or archives.
  This bounded scan is not a guarantee against every possible secret representation.
- Both the current tree and initial import exclude the private application files.
  The private-archive script was not used for publication.
- Follow-up questions were documented only. No new target, loss-weight sweep,
  information-gathering task, adaptation task, email, form, or arXiv submission was run.

Minor integration fixes during packaging: corrected a privacy scanner's self-match on
its regex source; preserved CSV CRLF rather than satisfying a default whitespace rule
by changing evidence; corrected figure captions and proposal wording; recompiled after
removing a redundant paragraph that left a nearly empty eighth page. None changed
experimental outputs.
