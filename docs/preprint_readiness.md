# Preprint-readiness assessment

Verdict: ready for exploratory lab outreach; reasonable as a private manuscript outline; not ready for a public preprint.

## What the evidence supports

This package supports a narrow, honest statement:

In a controlled MiniGrid-style memory task, a matched GRU with auxiliary action-conditioned next-view prediction learned better local prediction but did not reliably outperform the task-only GRU on decision-relevant memory. The task-only control reached 100% observed-clue success for seeds 11, 22, and 33. The predictive model reached 50%, 100%, and 100%. All never-observed controls were 50%. The paired mean predictive-control difference was -16.667 percentage points, with seed SD 28.87 pp and a descriptive 95% t interval of [-88.38, +55.04] pp.

That is enough for a credible outreach package because it shows implementation discipline, traceability, leakage checks, negative-result honesty, and an understanding that prediction quality and decision usefulness are different measurements.

## What it does not support

The package does not support a novelty claim about predictive memory, recurrent belief states, or world models. Those ideas are well represented in prior work, especially Gregor et al. (2019), "Shaping Belief States with Generative Environment Models for RL." AgentSpec is the strongest Q-Lab connection, but this pilot is standalone and does not reproduce or extend AgentSpec.

The package also does not support a broad claim that predictive supervision hurts memory. Predictive seed 11 is an observed optimization/readout failure, not a general mechanism result. Seeds 22 and 33 matched the control ceiling. The control model was already at 100%, the layout was fixed, the prediction target was local next-view prediction, and there were only three training seeds. The descriptive t interval is too wide for a directional conclusion.

## Why a public preprint is not warranted yet

A public preprint should contribute evidence beyond a clean implementation exercise. This pilot is useful but too small and too ceiling-limited. The current result mainly says that one short-horizon predictive objective did not reliably help in one fixed-layout controlled task. That is a good pilot conclusion, not a mature paper conclusion.

Main missing evidence:

- More independent training seeds under a frozen protocol.
- A task where the task-only GRU is not already at ceiling.
- Loss-weight, shuffled-target placebo, and longer-budget checks to separate optimization failure from the predictive objective itself.
- A prediction target that is plausibly decision-relevant, specified before evaluation.
- Held-out layout or task-family tests before claiming generalization.
- A trained prediction-head baseline or ablation if prediction metrics are used as substantive evidence.
- A clearer population claim: fixed route templates, fixed geometry, new layouts, or new task families.

## Private manuscript outline

1. Motivation: predictive objectives may shape memory, but better prediction need not mean better decisions.
2. Related work: AgentSpec for controlled embodied-agent scaffolds; Gregor et al. (2019) as closest direct prior; PlaNet and Dreamer for latent world-model context; WorldEvolver and 3D-Belief as modern belief/world-model references.
3. Task: controlled MiniGrid Memory adaptation with scripted clue-independent routes, observed and never-observed clues, delays 17/29/53, and forced final choice.
4. Methods: current-only, recent-history, structured memory, episodic retrieval, GRU task-only, matched GRU plus next-view prediction.
5. Validity checks: leakage boundaries, split overlap, structured-memory solvability, tiny-subset fit, gradient/prediction alignment, simulator replay.
6. Results: ceiling control, predictive seed-11 failure, never-observed chance controls, prediction error improvement, readout quality, interventions.
7. Interpretation: local prediction improved but did not reliably produce useful clue memory; ceiling and optimization limits prevent strong conclusions.
8. Next experiments: specify stronger tests before any public claim.

This outline is appropriate for a private draft or mentorship discussion. It should not be styled as a completed contribution until the missing evidence above is addressed.

## Smallest useful next experiments

1. Repeat the exact frozen setting with more seeds and at least one loss-weight or budget check, registered as an optimization-sensitivity follow-up. This tests whether seed 11 was a rare failure or a systematic tradeoff.
2. Add a harder non-ceiling condition where the task-only GRU has room to improve but structured memory still solves observed clues. This makes a positive or negative effect more interpretable.
3. Define a more informative predictive target before running it, such as a longer-horizon or decision-relevant observation target. Keep the original next-view objective as the baseline; do not quietly replace it because it failed to win.
4. Add new layouts or qualitatively different route policies after the within-layout mechanism is stable. The current test already reserves distinct wait-action templates within one fixed geometry.

No positive result is required. A stronger negative result would also be valuable if it isolates the reason: irrelevant prediction target, optimization competition, insufficient capacity, or no decision benefit under a clearly sensitive task.
