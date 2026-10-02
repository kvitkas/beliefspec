# BeliefSpec: a small predictive-memory pilot

Executed locally on 2026-10-01. A standalone, controlled adaptation of MiniGrid Memory tests whether action-conditioned next-view prediction improves a matched GRU's decision-relevant memory. Models choose only the final top/bottom branch; movement is scripted. This is supervised learning, not autonomous navigation, RL, or an LLM experiment.

Start with [the pilot report](docs/pilot_report.md), [the PDF](docs/pilot_report.pdf), and [the beginner walkthrough](docs/beginner_walkthrough.md). Results, including unfavorable seeds, are in `results/summary.json` and `results/final/episodes.csv`.

## Setup (Python 3.12)

Run from this project directory. `uv` was already installed on the execution machine.

```bash
uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python requirements.lock.txt
uv pip install --python .venv/bin/python --no-deps -e .
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests
```

The lock records exact versions, including Torch 2.14.1, MiniGrid 3.1.0, NumPy 2.5.3 and Gymnasium 1.3.0. No GPU, API key, downloaded dataset or paid service is required. The original machine was macOS 15.7.7, Apple Silicon, 16 GiB RAM; CPU training used two Torch threads. Other operating systems/hardware were not verified.

## Reproduce from the saved package

```bash
# Regenerate all plots/tables and real-episode traces from saved records:
.venv/bin/python -m beliefspec.analyze_results

# Replay the three illustrated model choices to actual simulator termination:
.venv/bin/python -m beliefspec.replay_traces

# Reproduce the separately labeled post-hoc target-dependence audit:
.venv/bin/python -m beliefspec.target_diagnostic

# Retrain control seed 11, regenerate all datasets, and compare exact decisions:
.venv/bin/python -m beliefspec.reproduce --output runs/my_reproduction

# Optional: retrain every original seed and variant without overwriting originals:
.venv/bin/python -m beliefspec.reproduce --all --output runs/my_full_reproduction

# Rebuild the editable report's PDF:
.venv/bin/python -m beliefspec.render_report

# Audit frozen files, paired scoring, hidden swaps and saved reproduction:
.venv/bin/python -m beliefspec.verify_package
```

Reproduction outputs must use an unused directory. Existing checkpoints and datasets are protected from accidental replacement. Determinism is checked on the recorded Mac/Python/Torch stack; exact floating-point equivalence is not promised across hardware or package versions.

The same setup was executed in a fresh `.venv-repro` environment, followed by a representative training reproduction. Evidence is in `runs/reproduction/verification.json` and `artifacts/reproduction.log`.

## Run the original pipeline from a source-only copy

These commands require a copy without `data/`, `runs/`, `results/`, or `artifacts/freeze.json`. Keep the supplied completed package intact; use the reproduction commands above for ordinary verification.

```bash
.venv/bin/python -m beliefspec.experiment environment
.venv/bin/python -m beliefspec.experiment generate --split train
.venv/bin/python -m beliefspec.experiment generate --split validation
.venv/bin/python -m beliefspec.audit --splits train validation
.venv/bin/python -m beliefspec.run_main
.venv/bin/python -m beliefspec.experiment generate --split test
.venv/bin/python -m beliefspec.audit
.venv/bin/python -m beliefspec.freeze
.venv/bin/python -m beliefspec.experiment evaluate
.venv/bin/python -m beliefspec.analyze_results
```

`configs/frozen.json` specifies the six runs, 30 epochs/720 updates each, three measured delays, 1,536 train / 384 validation / 768 test episodes. The compatibility `data_seeds` values do not select routes: actual routes use RNG seed `10000 + wait`, fixed disjoint split offsets, simulator seed 0 and fully crossed object assignments. Never-observed hidden-clue twins intentionally have identical visible histories with opposite hidden answers. No exact visible history crosses train/validation/test, but all splits share one geometry: **no layout-generalization claim**.

## Files and evidence

| Location | Purpose |
| --- | --- |
| `docs/protocol.md`, `configs/frozen.json` | Internal protocol and frozen main settings |
| `docs/decision_log.md` | Development choices, fixes, scope and interpretations |
| `docs/task_contract.md` | Scripted controller, masking and information access |
| `src/beliefspec/task.py` | Real MiniGrid collection and terminal-choice replay |
| `src/beliefspec/model.py` | Six baselines, GRU, categorical prediction loss and decision interface |
| `src/beliefspec/experiment.py` | Training, checkpoint selection, inference, interventions |
| `src/beliefspec/dataio.py` | Visible arrays separated from evaluator-only truth |
| `src/beliefspec/audit.py`, `tests/` | Data and implementation validity checks |
| `data/*/visible.npz`, `visible_index.json` | Permitted histories and observed-history labels |
| `data/*/evaluator_only.json` | Hidden truth used only for task generation/evaluation |
| `runs/main/*` | All six checkpoints, configs, losses, durations and selected epochs |
| `runs/development/*` | Both seed-101 development runs; not final evidence |
| `results/final/episodes.csv` | Every evaluated method/seed/episode |
| `results/final/interventions.csv` | Decoded-memory controller interventions |
| `results/final/simulator_replay.json` | Real final-action simulator checks |
| `results/figures/`, `results/traces/` | Generated figures and actual saved episode traces |
| `artifacts/freeze.json` | Pre-evaluation SHA-256 hashes of sources/data/checkpoints |
| `artifacts/environment.json`, `main_execution.json` | Hardware, actual compute and all run statuses |
| `docs/related_work.md`, `artifacts/sources/` | Verified primary-source notes |
| `docs/agentspec_smoke.md`, `artifacts/agentspec/` | Successful offline checks and credential-blocked quickstart |
| `docs/project_summary.md` | One-page project summary |
| `docs/application_procedure.md`, `docs/outreach_email.md` | Official procedure, reusable paragraphs and unsent email |
| `docs/preprint_readiness.md` | Candid readiness decision and manuscript outline |

## Interpretation boundaries

Task loss is cross-entropy over the clue classes key/ball/unknown, derived from permitted history. Auxiliary loss is 0.1 times categorical next-view cross-entropy. Both arms have the same 34,611 shared parameters plus a 21,560-parameter prediction head; only the predictive arm trains that head. Handwritten structured/retrieval baselines have privileged *design knowledge*, not privileged observations. The public controller phase is also a hand-designed cue shared by all methods.

Prediction accuracy mostly measures local visible geometry; it need not imply useful clue memory. Three training seeds give limited uncertainty information. The descriptive t interval uses paired seed differences, not thousands of episode rows as independent training runs. Interventions change decoded clue probabilities at a deterministic controller, not internal neural dimensions or an LLM's reasoning.

AgentSpec's offline contract tests passed; its documented API quickstart required credentials and did not complete. This project is not integrated with AgentSpec and does not reproduce its paper. No email/form/repository/preprint was sent, submitted, published or uploaded.
