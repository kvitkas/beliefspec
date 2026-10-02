# Related work notes for BeliefSpec

Access date: 2026-10-01. Sources are primary or upstream sources: arXiv records,
arXiv paper HTML, the official AgentSpec repository, and MiniGrid
documentation. These notes support scientific positioning; they do not claim
novelty for predictive memory, world models, recurrent belief states, or
auxiliary prediction losses.

## Narrow positioning

BeliefSpec asks when predictive supervision makes recurrent memory more useful
for later decisions. The completed pilot tests one narrow case: a supervised
scripted-route MiniGrid Memory adaptation with matched GRU models, one trained
only on the final clue label and one trained with an additional
action-conditioned next-observation objective.

The pilot does not evaluate autonomous navigation, reinforcement learning, LLM
agents, or AgentSpec integration.

## Verified source matrix

| Source | Verified bibliographic facts | What it learns or stores | Information access and supervision | Overlap with BeliefSpec | Narrow relevance |
| --- | --- | --- | --- | --- | --- |
| AgentSpec | arXiv:2606.14674v1, submitted 2026-06-12. Title: "AgentSpec: Understanding Embodied Agent Scaffolds Through Controlled Composition." Authors: Jixuan Chen, Jianzhi Shen, Haoqiang Kang, Zhi Hong, Qingyi Jiang, Soham Bose, Yiming Zhang, Leon Leng, Amit Vyas, Lingjun Mao, Siru Ouyang, Kun Zhou, Lianhui Qin. Official repo: `chenjix/AgentSpec`. | Typed embodied-agent scaffold with perception, memory, reasoning, reflection, action, and optional learning modules. | Standardized module interfaces across DeliveryBench, ALFRED, MiniGrid, and RoboTHOR; repo documents swappable memory/reasoning/reflection implementations. | Shared interest in controlled component composition and memory/reasoning interactions. | BeliefSpec is a standalone diagnostic of one memory-training mechanism. It does not reproduce or extend AgentSpec. |
| Shaping Belief States with Generative Environment Models for RL | arXiv:1906.09237v2, revised 2019-06-24. Authors: Karol Gregor, Danilo Jimenez Rezende, Frederic Besse, Yan Wu, Hamza Merzic, Aaron van den Oord. | Recurrent belief state shared by policy/value heads and predictive/generative auxiliary models. | First-person observations and actions; auxiliary objectives include action-conditional CPC, deterministic prediction, expressive generative prediction, and overshooting. | Closest conceptual prior for using predictive supervision to shape belief states. | Supports the caution that short-horizon prediction can be too local and that target horizon/content matters. |
| PlaNet | arXiv:1811.04551v5, revised 2019-06-04. Authors: Danijar Hafner, Timothy Lillicrap, Ian Fischer, Ruben Villegas, David Ha, Honglak Lee, James Davidson. | Recurrent state-space model with deterministic and stochastic latent components for planning. | Pixel observations, actions, and rewards; variational latent dynamics and overshooting. | Shared idea of compact latent state under partial observability. | Background only. BeliefSpec does not perform latent planning or reward optimization. |
| Dreamer | arXiv:1912.01603v3, revised 2020-03-17. Authors: Danijar Hafner, Timothy Lillicrap, Jimmy Ba, Mohammad Norouzi. | Latent dynamics model plus action and value models trained with imagined rollouts. | Image observations, actions, rewards, and experience datasets. | Reinforces the distinction between predictive models and decision-making performance. | Background only. BeliefSpec reports prediction error separately from decision success. |
| WorldEvolver | arXiv:2606.30639v2, revised 2026-09-01. Authors: Xuan Zhang, Wenxuan Zhang, See-Kiong Ng, Yang Deng. | Deployment-time episodic and semantic memory context for a frozen LLM world model. | Text observations/actions in ALFWorld and ScienceWorld; prediction mismatches update retrieved context. | Related to action-conditioned foresight and memory updates. | Different setting: LLM planning with frozen models, not trained GRU memory. |
| 3D-Belief | arXiv:2605.11367v2, revised 2026-05-29. Authors: Yifan Yin, Zehao Wen, Suyu Ye, Jieneng Chen, Zehan Zheng, Nanru Dai, Haojun Shi, Aydan Huang, Zheyuan Zhang, Alan Yuille, Jianwen Xie, Ayush Tewari, Tianmin Shu. | Explicit generative 3D belief representations with sequential updates. | Egocentric RGB streams, camera poses, and 3D evaluation targets. | Shares the broad theme of belief under partial observability. | Not a methodological precedent for this categorical MiniGrid pilot. |
| MiniGrid Memory | Farama MiniGrid documentation, MemoryEnv page accessed 2026-10-01. | Task in which an agent observes an initial object, traverses a hallway, and chooses the matching object. | Partial 7x7 observation, direction, mission text, and discrete actions in the official environment. | Provides the small memory task family. | BeliefSpec uses a controlled scripted-route adaptation, not unchanged benchmark performance. |

## Synthesis

Prior work supports the broad idea that predictive objectives can shape latent
belief states, but it also shows why the target matters. The BeliefSpec pilot is
best interpreted as a small diagnostic: in this setup, lower local next-view
prediction error did not imply more useful delayed clue memory. The post-hoc
target audit strengthens that interpretation by showing that the prediction
target did not depend on the clue after the clue disappeared, while leaving the
cause of the failed predictive seed unresolved.

## Sources

- AgentSpec arXiv: https://arxiv.org/abs/2606.14674 and HTML: https://arxiv.org/html/2606.14674v1
- AgentSpec repository: https://github.com/chenjix/AgentSpec
- Shaping Belief States arXiv: https://arxiv.org/abs/1906.09237 and HTML: https://arxiv.org/html/1906.09237
- PlaNet arXiv: https://arxiv.org/abs/1811.04551 and HTML: https://arxiv.org/html/1811.04551
- Dreamer arXiv: https://arxiv.org/abs/1912.01603 and HTML: https://arxiv.org/html/1912.01603
- WorldEvolver arXiv: https://arxiv.org/abs/2606.30639 and HTML: https://arxiv.org/html/2606.30639
- 3D-Belief arXiv: https://arxiv.org/abs/2605.11367 and HTML: https://arxiv.org/html/2605.11367
- MiniGrid Memory docs: https://minigrid.farama.org/environments/minigrid/MemoryEnv/
