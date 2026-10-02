# Source verification for working manuscript

Date checked: 2026-10-01. Publication edit: 2026-10-02. Scope: primary sources
for the LaTeX working manuscript and related-work framing. The publication edit
removed non-scientific logistics and did not add new source checks.

## Scope captured for manuscript framing

The source review supports describing BeliefSpec as a standalone, supervised,
scripted-route MiniGrid-style memory pilot. The verified sources do not support
claims that the pilot integrates AgentSpec, reproduces AgentSpec, reproduces
PlaNet/Dreamer/Shaping Belief States, or establishes a general world-model
result. The supported claim is narrower: the pilot tests whether adding an
auxiliary action-conditioned prediction loss to a matched recurrent memory model
improves a delayed forced-choice memory decision under controlled histories.

## Core sources

### Gregor et al. 2019 - Shaping Belief States with Generative Environment Models for RL

- Primary URLs: https://arxiv.org/abs/1906.09237 and https://arxiv.org/html/1906.09237
- arXiv metadata: submitted 2019-06-21; last revised 2019-06-24, v2; arXiv:1906.09237 [cs.LG].
- Verified title: "Shaping Belief States with Generative Environment Models for RL."
- Verified authors: Karol Gregor; Danilo Jimenez Rezende; Frederic Besse; Yan Wu; Hamza Merzic; Aaron van den Oord.
- Relevant contents checked beyond abstract: shared belief state, SimCore/generative prediction, overshooting, belief-state decoding, and experiments varying predictive loss, overshoot length, and memory architecture.
- What it supports: predictive or generative auxiliary models can shape recurrent belief states, and longer-horizon prediction can encourage representations containing more global environment information.
- What it does not support: the BeliefSpec task, MiniGrid Memory, categorical object recall, supervised forced-choice control, or the exact GRU-plus-next-observation setup.

### Hafner et al. 2019 - PlaNet

- Primary URLs: https://arxiv.org/abs/1811.04551 and https://arxiv.org/html/1811.04551
- arXiv metadata: submitted 2018-11-12; last revised 2019-06-04, v5; arXiv:1811.04551 [cs.LG].
- Verified title: "Learning Latent Dynamics for Planning from Pixels."
- Verified authors: Danijar Hafner; Timothy Lillicrap; Ian Fischer; Ruben Villegas; David Ha; Honglak Lee; James Davidson.
- Relevant contents checked beyond abstract: recurrent state-space model and latent dynamics objective sections.
- What it supports: learned recurrent state-space models can summarize image observations and actions into deterministic and stochastic latent state for planning.
- What it does not support: BeliefSpec does not learn from pixels, optimize rewards, or plan online in latent space.

### Hafner et al. 2020 - Dreamer

- Primary URLs: https://arxiv.org/abs/1912.01603 and https://arxiv.org/html/1912.01603
- arXiv metadata: submitted 2019-12-03; last revised 2020-03-17, v3; arXiv:1912.01603 [cs.LG].
- Verified title: "Dream to Control: Learning Behaviors by Latent Imagination."
- Verified authors: Danijar Hafner; Timothy Lillicrap; Jimmy Ba; Mohammad Norouzi.
- Relevant contents checked beyond abstract: control with world models, latent imagination, and learning latent dynamics.
- What it supports: learned latent world models can support behavior learning through imagined trajectories and value/action learning.
- What it does not support: BeliefSpec does not use imagined rollouts, actor/value learning, or RL control.

### Chen et al. 2026 - AgentSpec

- Primary URLs: https://arxiv.org/abs/2606.14674, https://arxiv.org/html/2606.14674v1, and https://github.com/chenjix/AgentSpec
- arXiv metadata: submitted 2026-06-12, v1; arXiv:2606.14674 [cs.CL].
- Verified title: "AgentSpec: Understanding Embodied Agent Scaffolds Through Controlled Composition."
- Verified authors: Jixuan Chen; Jianzhi Shen; Haoqiang Kang; Zhi Hong; Qingyi Jiang; Soham Bose; Yiming Zhang; Leon Leng; Amit Vyas; Lingjun Mao; Siru Ouyang; Kun Zhou; Lianhui Qin.
- Relevant contents checked beyond abstract: introduction and repository README describing typed modular interfaces across perception, memory, reasoning, reflection, action, and optional learning, plus documented MiniGrid-related launcher support.
- What it supports: controlled scaffold/component analysis, including memory and reasoning modules in embodied-agent settings.
- What it does not support: the current BeliefSpec pilot did not extend AgentSpec, run within AgentSpec, or reproduce AgentSpec paper results.

## Task/environment source

### MiniGrid Memory documentation

- Primary URL: https://minigrid.farama.org/environments/minigrid/MemoryEnv/
- Checked contents: documented Memory task description, action space, observation space, creation command, reward/termination, and registered configurations.
- What it supports: the task family tests memory by showing an object early, requiring hallway traversal, and later requiring the matching choice.
- What it does not support: unchanged MiniGrid benchmark performance for
  BeliefSpec's scripted, balanced, same-history diagnostic.

## Optional context

- WorldEvolver: https://arxiv.org/abs/2606.30639 verified as "Self-Evolving World Models for LLM Agent Planning" by Xuan Zhang, Wenxuan Zhang, See-Kiong Ng, and Yang Deng; arXiv v2 revised 2026-09-01. Relevance is limited to the warning that foresight/prediction can be unreliable or harmful if misused in downstream planning.
- 3D-Belief: https://arxiv.org/abs/2605.11367 verified as "3D-Belief: Embodied Belief Inference via Generative 3D World Modeling" by Yifan Yin, Zehao Wen, Suyu Ye, Jieneng Chen, Zehan Zheng, Nanru Dai, Haojun Shi, Aydan Huang, Zheyuan Zhang, Alan Yuille, Jianwen Xie, Ayush Tewari, and Tianmin Shu; arXiv v2 revised 2026-05-29. Relevance is limited to belief under partial observability, not the methods or evidence in this pilot.

## Citation context

- Gregor et al. is the closest prior for predictive supervision shaping belief
  states and for the caution that short-horizon prediction can fail to force
  decision-relevant memory.
- PlaNet and Dreamer provide broader latent dynamics and world-model context.
- AgentSpec provides controlled component-composition context.
- MiniGrid documentation supports the memory-task family; the pilot itself is a
  controlled supervised/scripted-route setup.
- WorldEvolver and 3D-Belief are different problem settings and serve only as
  optional broader context.
