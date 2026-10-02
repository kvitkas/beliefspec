# BeliefSpec: a controlled predictive-memory pilot

**When does predictive supervision make recurrent memory more useful for later decisions?**

This exploratory pilot compares matched GRUs on scripted, partially observed MiniGrid
trajectories. The model controls the final choice, not navigation. Training is supervised;
this is not reinforcement learning, an LLM-agent evaluation, or an AgentSpec reproduction.

[Exploratory working paper (PDF)](manuscript/main.pdf) · [LaTeX source](manuscript/main.tex) ·
[Walkthrough](docs/beginner_walkthrough.md) · [Verification](review/2026-10-02/README.md)

![Actual saved partial observations: early clue, hallway, final choices](review/2026-10-01/figures/task_illustration.png)

The clue is last visible at step 1; this saved episode's final decision is at step 18.
The delay is 17 simulator steps. `K` means key and `B` ball. These are actual agent-visible
categorical observations, not a full-map debugging render.

## Main result

| Training seed | Task-only GRU | GRU + next-view prediction |
| --- | ---: | ---: |
| 11 | 100% | 50% |
| 22 | 100% | 100% |
| 33 | 100% | 100% |

Observed-clue success, averaged equally over delays 17, 29, and 53; each seed has
384 observed-clue test episodes. All methods scored 50% on 384 never-observed episodes.
All six main runs are retained, including predictive seed 11.

The paired mean difference is −16.67 percentage points; the descriptive 95% seed-level
t interval is [−88.38, +55.04] points (three replications, df=2). It is unstable and
conditional on these routes—not thousands of independent training replications.

The predictive objective did not improve decision success in this pilot. The control
is at ceiling. A **post-hoc** saved-observation audit found 0 differences
in 6,336 post-clue next-view targets between matched opposite-clue episodes. Predicting
these targets does not require delayed clue retention. That property does not establish
why one predictive run failed. The control prediction head is untrained; its error is
not a trained-predictor baseline. Fixed geometry, short budgets, and three seeds limit
interpretation. These results do not establish that predictive supervision is generally
harmful or beneficial.

## Reproduce without overwriting the evidence

Use a full Git clone (not a source ZIP) for historical hash verification:
`git clone https://github.com/kvitkas/beliefspec.git`, then `cd beliefspec`.
Python 3.12 and [uv](https://docs.astral.sh/uv/) are required
for these setup commands. The original and review runs used a local Apple Silicon Mac,
macOS 15.7.7, 16 GiB RAM, CPU only, two Torch threads. Other platforms are not verified.
No GPU, API key, paid compute, or external dataset is needed.

```bash
uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python requirements.lock.txt
uv pip install --python .venv/bin/python --no-deps -e .

# Run tests in a scratch CWD: one original test writes a diagnostic there.
PROJECT_ROOT="$PWD"
mkdir -p .review-runs/tests
(cd .review-runs/tests && "$PROJECT_ROOT/.venv/bin/python" -m pytest "$PROJECT_ROOT/tests" -q)
.venv/bin/python -m ruff check src tests

# Independent record/configuration/checkpoint audit; writes only a new review file.
.venv/bin/python review/2026-10-01/verification/audit_review.py \
  --root . --stage after --output .review-runs/audit.json

# Regenerate figures from saved episode records and learning histories.
.venv/bin/python review/2026-10-01/make_figures.py --output .review-runs/figures

# Regenerate all datasets and retrain control seed 11; compare with original evidence.
.venv/bin/python -m beliefspec.reproduce --output .review-runs/reproduction
# Optional: add --all to reproduce all six original runs, not new experiments.
```

Figure and training output directories must be unused; choose new names on a repeat run.
Exact tensors reproduced on the recorded stack; bitwise equality across platforms is not
promised. The historical `analyze_results` and `verify_package` entry points write
original artifacts; use the commands above for read-only evidence checks and new outputs.
The review audit distinguishes the edited protocol publication copy from its frozen
original; see [evidence preservation](docs/evidence_preservation.md).

To compile the editable manuscript, install [Tectonic](https://tectonic-typesetting.github.io/book/latest/installation/)
(review build: 0.17.0), then run `cd manuscript && tectonic main.tex`. See
[build details](manuscript/README.md). Tectonic may download TeX support files.

## Inspect the evidence

- [Protocol](docs/protocol.md), [task contract](docs/task_contract.md), and
  [scientific decisions](docs/decision_log.md).
- `src/beliefspec/`, `tests/`, `configs/frozen.json`, and `requirements.lock.txt`.
- `data/`: separate visible arrays and evaluator-only records; no cross-split visible-history overlap.
- `runs/main/`: all six checkpoints, configurations, training curves, and selection records.
  `runs/development/` retains both development runs.
- [Raw episode outcomes](results/final/episodes.csv), [original summary](results/summary.json),
  and [verification records](review/2026-10-02/).
- [Related work](docs/related_work.md), [fresh primary-source checks](review/2026-10-01/sources.md),
  and [limited AgentSpec smoke](review/2026-10-01/agentspec_public_note.md).
- [Three proposed follow-ups](docs/followup_plan.md): target relevance, information gathering,
  and stale-clue adaptation. **None was executed.** Each needs a fresh protocol and test set.

The original freeze manifest is unchanged: 49 files remain byte-identical in the current
tree; the original protocol is verified from the preserved Git revision. The current
protocol is a labeled publication copy. All data, raw results and checkpoints are unchanged.

[Attribution and dependencies](THIRD_PARTY.md) document substantial AI assistance.
Author identity and individual contributions remain unresolved. No project-wide reuse
license has been selected. This is an exploratory working paper, not peer-reviewed work.
