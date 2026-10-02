# Verified source notes

Access date: 2026-10-01. Publication edit: 2026-10-02. These notes summarize
primary or upstream sources used for the BeliefSpec pilot package. The
publication edit removed non-scientific logistics and did not add new source
checks. The notes are short paraphrases, not reproductions of the cited papers.

## AgentSpec

- arXiv: https://arxiv.org/abs/2606.14674
- Paper HTML: https://arxiv.org/html/2606.14674v1
- Official repository: https://github.com/chenjix/AgentSpec
- Version/date: arXiv v1 submitted 2026-06-12.
- Verified title: "AgentSpec: Understanding Embodied Agent Scaffolds Through Controlled Composition."
- Verified authors: Jixuan Chen; Jianzhi Shen; Haoqiang Kang; Zhi Hong; Qingyi Jiang; Soham Bose; Yiming Zhang; Leon Leng; Amit Vyas; Lingjun Mao; Siru Ouyang; Kun Zhou; Lianhui Qin.
- Evidence note: The paper and repository define AgentSpec as a modular
  embodied-agent scaffold with typed interfaces across perception, memory,
  reasoning, reflection, action, and optional learning. This supports a related
  scientific theme of controlled component analysis, but the BeliefSpec pilot
  does not integrate AgentSpec or reproduce its reported results.

## Shaping Belief States with Generative Environment Models for RL

- arXiv: https://arxiv.org/abs/1906.09237
- Paper HTML: https://arxiv.org/html/1906.09237
- Version/date: arXiv v2 revised 2019-06-24.
- Verified title: "Shaping Belief States with Generative Environment Models for RL."
- Verified authors: Karol Gregor; Danilo Jimenez Rezende; Frederic Besse; Yan Wu; Hamza Merzic; Aaron van den Oord.
- Evidence note: The paper trains recurrent belief states shared with
  policy/value heads and auxiliary predictive models. It compares predictive
  losses and memory architectures, and argues that multi-step prediction can
  shape more useful belief representations than short local prediction.

## PlaNet

- arXiv: https://arxiv.org/abs/1811.04551
- Paper HTML: https://arxiv.org/html/1811.04551
- Version/date: arXiv v5 revised 2019-06-04.
- Verified title: "Learning Latent Dynamics for Planning from Pixels."
- Verified authors: Danijar Hafner; Timothy Lillicrap; Ian Fischer; Ruben Villegas; David Ha; Honglak Lee; James Davidson.
- Evidence note: PlaNet learns a recurrent state-space dynamics model from
  pixel observations, actions, and rewards, then plans online in latent space.
  It is relevant background for latent belief dynamics, but BeliefSpec is not a
  model-predictive control experiment.

## Dreamer

- arXiv: https://arxiv.org/abs/1912.01603
- Paper HTML: https://arxiv.org/html/1912.01603
- Version/date: arXiv v3 revised 2020-03-17.
- Verified title: "Dream to Control: Learning Behaviors by Latent Imagination."
- Verified authors: Danijar Hafner; Timothy Lillicrap; Jimmy Ba; Mohammad Norouzi.
- Evidence note: Dreamer learns a compact latent world model from experience,
  then learns action and value models from imagined latent rollouts. It supports
  the broader distinction between prediction quality and downstream behavior.

## WorldEvolver

- arXiv: https://arxiv.org/abs/2606.30639
- Paper HTML: https://arxiv.org/html/2606.30639
- Version/date: arXiv v2 revised 2026-09-01; arXiv page states EMNLP 2026 Findings acceptance.
- Verified title: "Self-Evolving World Models for LLM Agent Planning."
- Verified authors: Xuan Zhang; Wenxuan Zhang; See-Kiong Ng; Yang Deng.
- Evidence note: WorldEvolver keeps model parameters frozen while updating
  retrieved memory context from prior transitions and prediction-observation
  mismatches. It is relevant to action-conditioned foresight, but not a trained
  recurrent-memory experiment.

## 3D-Belief

- arXiv: https://arxiv.org/abs/2605.11367
- Paper HTML: https://arxiv.org/html/2605.11367
- Version/date: arXiv v2 revised 2026-05-29.
- Verified title: "3D-Belief: Embodied Belief Inference via Generative 3D World Modeling."
- Verified authors: Yifan Yin; Zehao Wen; Suyu Ye; Jieneng Chen; Zehan Zheng; Nanru Dai; Haojun Shi; Aydan Huang; Zheyuan Zhang; Alan Yuille; Jianwen Xie; Ayush Tewari; Tianmin Shu.
- Evidence note: 3D-Belief models belief as sequentially updated explicit 3D
  representations with observed and imagined content. It is conceptually
  relevant to partial observability, but much higher-dimensional than the
  BeliefSpec pilot.

## MiniGrid Memory

- Documentation: https://minigrid.farama.org/environments/minigrid/MemoryEnv/
- Version/date context: page accessed 2026-10-01; no package version is inferred from the page.
- Evidence note: The documented task has the agent see an object in a start
  room, move through a narrow hallway, and choose the matching object at a
  split. The documented observation is a dictionary with partial image,
  direction, and mission. BeliefSpec uses a controlled scripted-route
  adaptation rather than unchanged benchmark evaluation.

## Retrieval limitations

- AgentSpec integration status belongs to the implementation record. These
  source notes verify that an official repository and documented commands exist.
- arXiv HTML was sufficient for the inspected source summaries. No claim here
  depends on reproducing paper experiments.
