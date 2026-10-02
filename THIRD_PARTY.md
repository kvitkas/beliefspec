# Attribution, dependencies, and provenance

This package was developed with substantial OpenAI Codex assistance: implementation,
experiment execution, checking, analysis, and drafting. The user supplied the research
direction, constraints, and request for the pilot. The records do not establish which
technical work the user can independently perform. Personal contribution and experience
must be described by the user, not inferred from this repository. No Q-Lab affiliation,
endorsement, or supervision is claimed.

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
  (BSD-style distribution license). The new manuscript uses
  [Tectonic](https://tectonic-typesetting.github.io/book/latest/installation/), downloaded
  separately and not redistributed here. A license inventory is in the review directory.
- [AgentSpec](https://github.com/chenjix/AgentSpec) was inspected in a separate environment.
  Its source is **not included** and is **not a dependency of the pilot**. The preserved
  offline test log is evidence of a smoke test, not replication of a published result.

Exact pilot versions are in `requirements.lock.txt`. Generated data consist of symbolic
MiniGrid observations, not a downloaded third-party dataset. Figures were produced from
the saved records. No external figure or paper text is reproduced. Primary research
attributions are recorded in `manuscript/references.bib` and the dated source review.

## Distribution status

Public hosting was authorized by the project owner. No project-wide reuse license has
been selected in this task, and this package is not described as open-source. Third-party
software retains its own licensing terms. A project reuse license can be chosen separately;
public visibility alone should not be interpreted as an additional license grant.
