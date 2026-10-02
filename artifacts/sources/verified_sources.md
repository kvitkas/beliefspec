# Verified source notes

Access date: 2026-10-01. These notes summarize primary/upstream evidence gathered for the BeliefSpec pilot package. The source summaries are intentionally short and paraphrased.

## AgentSpec

- arXiv: https://arxiv.org/abs/2606.14674
- Paper HTML: https://arxiv.org/html/2606.14674v1
- Official repository: https://github.com/chenjix/AgentSpec
- Version/date: arXiv v1 submitted 2026-06-12.
- Verified title: "AgentSpec: Understanding Embodied Agent Scaffolds Through Controlled Composition."
- Verified authors: Jixuan Chen; Jianzhi Shen; Haoqiang Kang; Zhi Hong; Qingyi Jiang; Soham Bose; Yiming Zhang; Leon Leng; Amit Vyas; Lingjun Mao; Siru Ouyang; Kun Zhou; Lianhui Qin.
- Evidence note: The paper and repo define AgentSpec as a modular embodied-agent scaffold with standardized typed interfaces across perception, memory, reasoning, reflection, action, and optional learning. The repository documents install/setup commands, a studio, and CLI examples, including MiniGrid/BabyAI-related runs. This supports positioning BeliefSpec as a small controlled memory/prediction diagnostic related to scaffold-component analysis, not as an AgentSpec reproduction.

## Shaping Belief States with Generative Environment Models for RL

- arXiv: https://arxiv.org/abs/1906.09237
- Paper HTML: https://arxiv.org/html/1906.09237
- Version/date: arXiv v2 revised 2019-06-24.
- Verified title: "Shaping Belief States with Generative Environment Models for RL."
- Verified authors: Karol Gregor; Danilo Jimenez Rezende; Frederic Besse; Yan Wu; Hamza Merzic; Aaron van den Oord.
- Evidence note: The paper trains recurrent belief states shared with policy/value heads and auxiliary predictive models. It compares predictive losses and memory architectures, and argues that multi-step prediction/overshooting can produce more stable belief representations than short local prediction. This is the closest direct prior for the BeliefSpec mechanism.

## PlaNet

- arXiv: https://arxiv.org/abs/1811.04551
- Paper HTML: https://arxiv.org/html/1811.04551
- Version/date: arXiv v5 revised 2019-06-04.
- Verified title: "Learning Latent Dynamics for Planning from Pixels."
- Verified authors: Danijar Hafner; Timothy Lillicrap; Ian Fischer; Ruben Villegas; David Ha; Honglak Lee; James Davidson.
- Evidence note: PlaNet learns a recurrent state-space dynamics model from pixel observations, actions, and rewards, then plans online in latent space. The paper emphasizes stochastic plus deterministic latent components and latent overshooting for multi-step predictions. It is relevant background for latent belief dynamics, but BeliefSpec is not doing model-predictive control.

## Dreamer

- arXiv: https://arxiv.org/abs/1912.01603
- Paper HTML: https://arxiv.org/html/1912.01603
- Version/date: arXiv v3 revised 2020-03-17.
- Verified title: "Dream to Control: Learning Behaviors by Latent Imagination."
- Verified authors: Danijar Hafner; Timothy Lillicrap; Jimmy Ba; Mohammad Norouzi.
- Evidence note: Dreamer learns a compact latent world model from experience, then learns action and value models from imagined latent rollouts. It supports the broader claim that latent predictions can support behavior, while highlighting why BeliefSpec should report decision metrics separately from prediction metrics.

## WorldEvolver

- arXiv: https://arxiv.org/abs/2606.30639
- Paper HTML: https://arxiv.org/html/2606.30639
- Version/date: arXiv v2 revised 2026-09-01; arXiv page states EMNLP 2026 Findings acceptance.
- Verified title: "Self-Evolving World Models for LLM Agent Planning."
- Verified authors: Xuan Zhang; Wenxuan Zhang; See-Kiong Ng; Yang Deng.
- Evidence note: WorldEvolver keeps the downstream agent and world-model parameters frozen, while evolving retrieved memory context from prior transitions and prediction-observation mismatches. It also filters predictions by confidence before exposing them to the agent. It is relevant for action-conditioned foresight and the risk that inaccurate prediction can harm decisions, but it is not a trained recurrent memory experiment.

## 3D-Belief

- arXiv: https://arxiv.org/abs/2605.11367
- Paper HTML: https://arxiv.org/html/2605.11367
- Version/date: arXiv v2 revised 2026-05-29.
- Verified title: "3D-Belief: Embodied Belief Inference via Generative 3D World Modeling."
- Verified authors: Yifan Yin; Zehao Wen; Suyu Ye; Jieneng Chen; Zehan Zheng; Nanru Dai; Haojun Shi; Aydan Huang; Zheyuan Zhang; Alan Yuille; Jianwen Xie; Ayush Tewari; Tianmin Shu.
- Evidence note: 3D-Belief models belief as sequentially updated explicit 3D representations with observed and imagined content, using 3D Gaussian splatting and generative modeling. It is conceptually relevant to belief under partial observability, but much higher-dimensional and more heavily supervised/evaluated than the BeliefSpec pilot.

## MiniGrid Memory

- Documentation: https://minigrid.farama.org/environments/minigrid/MemoryEnv/
- Version/date context: page accessed 2026-10-01; no pinned local package version inferred from the page.
- Evidence note: The documented task has the agent see an object in a start room, move through a narrow hallway, and choose the matching object at a split. The documented action space is `Discrete(7)`, the observation is a dictionary with partial image, direction, and mission, and the documented creation example is `gymnasium.make("MiniGrid-MemoryS7-v0")`.

## Q-Lab application page

- Public page: https://lianhui.ucsd.edu/getinvolved.html
- UCSD undergrad/master form link discovered on page: https://forms.gle/ZE7WjwyEXfg7uShJ7
- Resolved form URL: https://docs.google.com/forms/d/e/1FAIpQLSdwrmDyIKgKO_g4tuAgzClG__sqFZBjJ5ueoUJnqGOY2Kz7dg/viewform?usp=send_form
- Evidence note: The page instructs UCSD undergraduate and master's students to fill out the linked form, then email `l6qin@ucsd.edu`, and mentions an expected commitment of about 16 hours per week. The form body was not accessible without Google sign-in from this environment, so field labels could not be verified.

## Retrieval limitations and ambiguity flags

- Google Forms field labels for the UCSD undergrad/master application were not accessible read-only without sign-in. The package should not list form fields until the user opens the form in an authenticated browser and records them.
- AgentSpec integration status belongs to the implementation lane. These source notes only verify that an official repo and documented commands exist.
- arXiv HTML was sufficient for method-section inspection for all listed papers. No claim here depends on reproducing paper experiments.
