# Public-package review decisions

Started 2026-10-01, after the original held-out results were already available.
This is retrospective verification and packaging, not a new preregistration or a
change to the frozen experiment.

- Work from the existing `beliefspec` project. Preserve the original source, data,
  configurations, checkpoints, results, unsuccessful predictive run, and experiment log.
  New checks and regenerated figures live under `review/`; manuscript sources live
  under `manuscript/`. Follow-up experiments are proposals, not executed work.
- No prior Git repository was present. Create a truthful initial import of the public
  subset, followed by commits for actual packaging changes. Do not recreate historical
  commits. The original README remains in the initial commit.
- GitHub authentication identifies one active account, `kvitkas`. The API confirmed that
  `kvitkas/beliefspec` was absent before repository creation. Use the account's GitHub
  noreply commit address rather than publishing its configured personal email.
- Preserve evidence bytes using `.gitattributes` (`* -text`). Git's initial default
  normalized two CSVs in the initial import; the packaging commit stores their original
  CRLF bytes. No local evidence contents were changed.
- Exclude private application drafts, environments, caches, the local vendor checkout,
  redundant preview/archive files, and three original AgentSpec files with personal
  absolute paths. They remain intact locally. Include a public smoke-test summary instead.
  Do not use the original private-archive script as a public export tool.
- Run tests with their working directory under the new review directory: the original
  tiny-fit test writes a diagnostic relative to CWD. Use a new reproduction destination.
- Compile actual LaTeX using project-local Tectonic 0.17.0, obtained from the official
  release, not the existing ReportLab renderer. Archive SHA-256:
  `a3f1cac7c5678f01661a92212f58480ae3b0634115d880dbc59e2953ded45667`.
  The downloaded compiler and archive stay outside Git. TeX support files may be fetched
  by Tectonic; these are document-build dependencies, not experimental data.
- Keep AI-assisted provenance explicit. Do not invent an author name, affiliation,
  personal contribution, or a project-wide reuse license.
