# Source verification for working manuscript

Date checked: 2026-10-01. Scope: primary sources for the LaTeX working manuscript and outreach context. Existing notes in `docs/related_work.md` and `artifacts/sources/verified_sources.md` were read for continuity and left unchanged.

## Manuscript framing guardrail

The manuscript should describe BeliefSpec as a standalone, supervised, scripted-route MiniGrid-style memory pilot. It should not say that it integrates AgentSpec, reproduces AgentSpec, reproduces PlaNet/Dreamer/Shaping Belief States, or establishes a general world-model result. The defensible claim is narrower: this pilot tests whether adding an auxiliary action-conditioned prediction loss to a matched recurrent memory model improves a delayed forced-choice memory decision under controlled histories.

## Core sources

### Gregor et al. 2019 - Shaping Belief States with Generative Environment Models for RL

- Primary URLs: https://arxiv.org/abs/1906.09237 and https://arxiv.org/html/1906.09237
- arXiv metadata: submitted 2019-06-21; last revised 2019-06-24, v2; arXiv:1906.09237 [cs.LG].
- Verified title: "Shaping Belief States with Generative Environment Models for RL."
- Verified authors: Karol Gregor; Danilo Jimenez Rezende; Frederic Besse; Yan Wu; Hamza Merzic; Aaron van den Oord.
- Relevant contents checked beyond abstract: Sections describing shared belief state, SimCore/generative prediction, overshooting, belief-state decoding, and experiments varying predictive loss, overshoot length, and memory architecture.
- What it supports: A predictive/generative auxiliary model can shape a recurrent belief state shared with an RL agent, and longer-horizon prediction can encourage representations containing more global environment information.
- What it does not support: It does not evaluate the BeliefSpec task, MiniGrid Memory, categorical object recall, a supervised forced-choice controller, or the exact GRU-plus-next-observation setup. It should be cited as closest conceptual prior and a caution about prediction target/horizon, not as direct precedent for the observed pilot result.

### Hafner et al. 2019 - PlaNet

- Primary URLs: https://arxiv.org/abs/1811.04551 and https://arxiv.org/html/1811.04551
- arXiv metadata: submitted 2018-11-12; last revised 2019-06-04, v5; arXiv:1811.04551 [cs.LG].
- Verified title: "Learning Latent Dynamics for Planning from Pixels."
- Verified authors: Danijar Hafner; Timothy Lillicrap; Ian Fischer; Ruben Villegas; David Ha; Honglak Lee; James Davidson.
- Relevant contents checked beyond abstract: Recurrent State Space Model section and latent dynamics objective sections.
- What it supports: A learned recurrent state-space model can summarize image observations/actions into deterministic and stochastic latent state for model-based planning, with multi-step latent prediction/overshooting.
- What it does not support: BeliefSpec does not learn from pixels, optimize rewards, or plan online in latent space. PlaNet should frame broader latent dynamics history, not the central experimental claim.

### Hafner et al. 2020 - Dreamer

- Primary URLs: https://arxiv.org/abs/1912.01603 and https://arxiv.org/html/1912.01603
- arXiv metadata: submitted 2019-12-03; last revised 2020-03-17, v3; arXiv:1912.01603 [cs.LG].
- Verified title: "Dream to Control: Learning Behaviors by Latent Imagination."
- Verified authors: Danijar Hafner; Timothy Lillicrap; Jimmy Ba; Mohammad Norouzi.
- Relevant contents checked beyond abstract: Control with world models, learning behaviors by latent imagination, and learning latent dynamics sections.
- What it supports: Learned latent world models can support behavior learning through imagined trajectories and value/action learning.
- What it does not support: BeliefSpec does not use imagined rollouts, actor/value learning, or RL control. Cite only as broader world-model context and to separate prediction quality from decision quality.

### Chen et al. 2026 - AgentSpec

- Primary URLs: https://arxiv.org/abs/2606.14674, https://arxiv.org/html/2606.14674v1, and https://github.com/chenjix/AgentSpec
- arXiv metadata: submitted 2026-06-12, v1; arXiv:2606.14674 [cs.CL].
- Verified title: "AgentSpec: Understanding Embodied Agent Scaffolds Through Controlled Composition."
- Verified authors: Jixuan Chen; Jianzhi Shen; Haoqiang Kang; Zhi Hong; Qingyi Jiang; Soham Bose; Yiming Zhang; Leon Leng; Amit Vyas; Lingjun Mao; Siru Ouyang; Kun Zhou; Lianhui Qin.
- Relevant contents checked beyond abstract: Introduction and repository README describing typed modular interfaces across perception, memory, reasoning, reflection, action, and optional learning, plus documented MiniGrid-related launcher support.
- What it supports: A lab-specific connection to controlled scaffold/component analysis, especially memory/reasoning interactions in embodied agents.
- What it does not support: The current BeliefSpec pilot did not extend AgentSpec, run within the AgentSpec framework, or reproduce any AgentSpec paper results.

## Task/environment source

### MiniGrid Memory documentation

- Primary URL: https://minigrid.farama.org/environments/minigrid/MemoryEnv/
- Checked contents: documented Memory task description, action space, observation space, creation command, reward/termination, and registered configurations.
- What it supports: The task family is a memory test in which an agent observes an object, traverses a hallway, and must choose the matching object later.
- What it does not support: BeliefSpec's scripted, balanced, same-history diagnostic is a controlled adaptation/pilot. It should not be reported as unchanged MiniGrid benchmark performance if custom data generation or scripted control is used.

## Optional context, one-line relevance only

- WorldEvolver: https://arxiv.org/abs/2606.30639 verified as "Self-Evolving World Models for LLM Agent Planning" by Xuan Zhang, Wenxuan Zhang, See-Kiong Ng, and Yang Deng; arXiv v2 revised 2026-09-01. Relevance is limited to the warning that foresight/prediction can be unreliable or harmful if misused in downstream planning.
- 3D-Belief: https://arxiv.org/abs/2605.11367 verified as "3D-Belief: Embodied Belief Inference via Generative 3D World Modeling" by Yifan Yin, Zehao Wen, Suyu Ye, Jieneng Chen, Zehan Zheng, Nanru Dai, Haojun Shi, Aydan Huang, Zheyuan Zhang, Alan Yuille, Jianwen Xie, Ayush Tewari, and Tianmin Shu; arXiv v2 revised 2026-05-29. Relevance is limited to belief under partial observability, not the methods or evidence in this pilot.

## Q-Lab procedure check

- Public page: https://lianhui.ucsd.edu/getinvolved.html
- Checked on 2026-10-01.
- Current public instruction for UCSD undergraduates and master's students: complete the linked form, then email `l6qin@ucsd.edu`; the page asks for about 16 hours/week and says some NLP/ML background is helpful but beginners are not excluded.
- Form link observed from page: https://forms.gle/ZE7WjwyEXfg7uShJ7
- No form was submitted. Form field labels were not accessible without Google sign-in from this environment, so no application fields should be invented.

## Citation-use recommendations

- Use Gregor et al. as the closest prior for predictive supervision shaping belief states and as the main caution that short-horizon prediction can fail to force decision-relevant memory.
- Use PlaNet and Dreamer sparingly as broader latent dynamics/world-model background.
- Use AgentSpec for Q-Lab relevance and controlled component-composition motivation only.
- Use MiniGrid docs to justify the memory-task choice, while being explicit that the pilot uses a controlled supervised/scripted-route setup.
- Avoid padding with WorldEvolver or 3D-Belief unless the manuscript has a short future-work/context paragraph that clearly marks them as different problem settings.
