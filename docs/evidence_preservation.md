# Original evidence and publication copies

The experiment was completed on 2026-10-01. The 2026-10-02 revision changes its
presentation, not its models, evaluation conditions, data, checkpoints, or results.
No follow-up experiment was run and the held-out set was not used for tuning.

## Original freeze

`artifacts/freeze.json` remains byte-for-byte unchanged. Its SHA-256 is
`32f29ded1b7cd547509addd000fbf6375d9d86f660e3a74c56e9a48076a7b98b`.
It lists 50 files captured before held-out model scoring. Forty-nine still match
their original hashes at their current paths.

The one publication-copy exception is `docs/protocol.md`. Its revised header
identifies the edit; only non-scientific completion logistics in the final
paragraph were removed or restated. The hypotheses, task, objectives, splits,
budgets, checkpoint rule, metrics, uncertainty method and validation gates are
unchanged. This is a presentation edit after the results, not a new preregistration.

| Document | SHA-256 |
| --- | --- |
| Original protocol | `8e41a14956bbfd7a4789e3da88db5da7b2b1ba2e2bc557de3fb11758e1bf4bb6` |
| Publication copy | `a674b33339fcf8bd85fd99ce3f3a3259a552bf29882f1cc65cd63e9f35e2c2d6` |

The original bytes remain in Git revision
`0b0298ee75accc2306caeca205c5225ce5a2ceae`, at the same path. They were also saved
in a private local archive before editing. Git history has not been rewritten.
The original freeze was not regenerated to match the revised document.

## Verification contract

The review audit verifies **49 live frozen files, one historical protocol, and
one separately hashed publication copy**. It does not claim that all 50 current
files match the old freeze. The exception is fixed to this document and revision;
other mismatches remain failures. Missing historical Git objects are failures,
not silently skipped checks.

Use a full clone for this check. A source ZIP lacks the history needed to verify
the original document. For a shallow checkout, run `git fetch --unshallow origin`.
The historical `beliefspec.verify_package` command still applies the old strict
live-file rule and is not the publication-copy verifier. The README uses the
current review audit instead. Training and reproduction do not read the protocol
document, so this distinction does not alter their behavior.

## Other presentation changes

The manuscript is now the single report. Superseded report PDFs, their renderer,
an unused archive exporter, repeated tutorials, duplicate audit aliases and
review narratives were removed from the current tree. Exact pre-edit tracked
files were archived locally and remain available in the preserved Git revision.
The scientific decision log and source notes are labeled edited publication
copies where appropriate; their original dates describe the recorded work, not
the date of the edit. Historical machine-readable execution records retain their
original contents and are interpreted as dated evidence.

Original figures remain under `results/figures/`; manuscript figures regenerated
from records remain under `review/2026-10-01/figures/`. These are distinct versions,
not replacements for original results. `.gitattributes` preserves the original
CSV bytes, including CRLF line endings.

New verification outputs live under [review/2026-10-02](../review/2026-10-02/README.md).
