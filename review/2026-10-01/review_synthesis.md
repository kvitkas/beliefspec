# Two-lane code and architecture review

The code-review workflow used separate code/spec/security and architectural
devil's-advocate lanes. The leader synthesized them here; this is an internal
AI-assisted review, not peer review or an independent human endorsement.

Code lane: **COMMENT**. No critical/high experiment implementation defect was found.
The material medium issue was that the private archive includes personal-path logs.
See `code_review.md` for source anchors.

Architecture lane: initially **BLOCK** for public packaging, then **WATCH** after
the Git index was inspected and private application files/logs were confirmed absent.
The original `src/beliefspec/package.py` is explicitly a private export and is not
used to publish. Durable exclusions are in `.gitignore`; the replacement README
links only to public review materials. `public_preflight.py` checks the staged
file set before publication without printing any matched secret values.

Scientific watch items remain:

- `src/beliefspec/task.py`: fixed geometry, scripted route, public phase cue,
  and compatibility-only data seed parameters. Do not claim layout generalization.
- `src/beliefspec/model.py` and `experiment.py`: one matched shared architecture,
  but the allocated control prediction head is untrained. Extra predictive compute
  is real; prediction-head performance is not a fair trained-predictor comparison.
- `tests/test_model.py`: tiny-fit output is CWD-relative. New tests ran from review
  scratch directories, avoiding replacement of the original verification artifact.
- `analyze_results.py` and `verify_package.py`: original commands write old outputs.
  The public README uses separate review output paths instead.
- The task-only arm is at ceiling, three training seeds give little precision,
  and the target-dependence audit does not identify a cause for seed-11 failure.

Final synthesis: **COMMENT / scientific WATCH**, not a claim of a publication-ready
result. The packaging privacy blocker is addressed by selective tracking and checked
again before push. No frozen experiment files were changed to address these concerns.
