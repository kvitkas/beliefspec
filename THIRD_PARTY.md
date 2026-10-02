# Attribution, dependencies, and provenance

OpenAI Codex provided substantial assistance with implementation, experiment execution,
checking, analysis, and drafting. The project owner supplied the research direction and
constraints. Author identity and individual contributions have not yet been finalized;
the repository does not establish unaided implementation or independent human review.

## Upstream work

- The task uses Farama Foundation's [MiniGrid](https://github.com/Farama-Foundation/Minigrid)
  `MemoryEnv` through its Python API and [Gymnasium](https://github.com/Farama-Foundation/Gymnasium).
  Both installed distributions identify an MIT license. This repository supplies its own
  controlled trajectory collection and task adaptation; it does not distribute those libraries.
- Training uses [PyTorch](https://github.com/pytorch/pytorch), array processing uses
  [NumPy](https://github.com/numpy/numpy), and figures use
  [Matplotlib](https://github.com/matplotlib/matplotlib). Their installed distributions
  include multiple component licenses; consult their distribution notices rather than
  assuming a single license covers every bundled component.
- Tests/lint use pytest and Ruff (MIT). The original report was rendered with ReportLab
  (BSD-style distribution license); its superseded rendering helper has been removed.
  The working paper uses
  [Tectonic](https://tectonic-typesetting.github.io/book/latest/installation/), downloaded
  separately and not redistributed here. See the
  [installed-distribution inventory](review/2026-10-01/dependencies.json).
- [AgentSpec](https://github.com/chenjix/AgentSpec) was inspected in a separate environment.
  Its source is **not included** and is **not a dependency of the pilot**. The preserved
  offline test log is evidence of a smoke test, not replication of a published result.

Exact pilot versions are in `requirements.lock.txt`. Generated data consist of symbolic
MiniGrid observations, not a downloaded third-party dataset. Figures were produced from
the saved records. No external figure or paper text is reproduced. Primary research
attributions are recorded in `manuscript/references.bib` and the dated source review.

## Distribution status

No project-wide reuse license has been selected. Third-party
software retains its own licensing terms. A project reuse license can be chosen separately;
public visibility alone should not be interpreted as an additional license grant.
