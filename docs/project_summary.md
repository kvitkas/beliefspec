# BeliefSpec one-page project summary

BeliefSpec is a small exploratory pilot for Project Alice, a longer-term research direction on adaptive self/world modeling under uncertainty. The narrow pilot question was: under what controlled conditions does predictive supervision make an agent's memory more useful for decisions?

With AI-assisted engineering support, I implemented a standalone controlled adaptation of MiniGrid Memory. The agent saw an early key/ball clue, moved through a shared scripted route where the clue disappeared, and then made one final top/bottom choice between two visible objects. The scripted controller handled movement; the tested memory systems controlled only the final choice. This means the pilot is about memory and decision readout, not autonomous navigation, reinforcement learning, or LLM agency.

The comparison used six methods with a common decision interface:

- Current observation only.
- Recent observation/action history.
- Structured memory of previously observed facts.
- Simple episodic retrieval.
- A compact GRU trained only on the common final clue-readout objective.
- The same GRU trained with the same task objective plus action-conditioned next-view prediction.

The learned variants shared inputs, data, architecture, optimizer, budget, checkpoint rule, controller, and paired evaluation episodes. The auxiliary prediction target was categorical next observation, not regression over arbitrary object IDs. The control model allocated the same prediction head for accounting, but only the predictive arm trained it.

Main held-out result: the task-only GRU reached 100% observed-clue decision success for seeds 11, 22, and 33. The predictive GRU reached 50%, 100%, and 100%. The paired mean predictive-control difference was -16.667 percentage points, with seed SD 28.87 pp and a descriptive 95% t interval of [-88.38, +55.04] pp. Every method scored 50% in never-observed conditions, as expected in the balanced forced-choice setting. No runs were excluded.

The informative limitation is that prediction got better without reliably making decision memory better. Predictive next-view CE/accuracy improved relative to the untrained control head, but predictive seed 11 decoded observed clues incorrectly or as unknown and failed at chance. This does not prove predictive supervision is harmful. It shows that this short-horizon local prediction target and easy fixed-layout task are not enough evidence for a positive mechanism claim.

The strongest lab connection is to AgentSpec, which studies embodied agents through controlled composition of modules such as memory and reasoning. This pilot is not integrated with AgentSpec and does not reproduce its paper. It is a small, reproducible diagnostic package that could support exploratory outreach to Q-Lab because it has a dated protocol, verified related-work notes, leakage checks, saved raw results, figures, interventions, fresh-environment reproduction evidence, and honest limits.

Outreach-ready claim: I completed a local, reproducible predictive-memory pilot showing that improved local prediction did not reliably improve decision-relevant memory in a small controlled MiniGrid-style task. The result motivates better-designed follow-up experiments rather than a publication or novelty claim.

Primary evidence files: `docs/protocol.md`, `docs/related_work.md`, `results/summary.json`, `results/final/episodes.csv`, `results/figures/`, `artifacts/main_execution.json`, `runs/reproduction/verification.json`, and `artifacts/verification/package_checks.json`.
