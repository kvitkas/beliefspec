# BeliefSpec manuscript source

`main.tex` is a restrained exploratory working draft generated from the saved BeliefSpec package on 2026-10-01.

References are in `references.bib` and are cited with `natbib` plus `plainnat`.

Expected build context is this directory:

```bash
tectonic --keep-logs main.tex
```

The figure paths assume the manuscript remains at `beliefspec/manuscript/main.tex` and the public-review figures remain at `beliefspec/review/2026-10-01/figures/*.pdf`.

Before scholarly submission, replace `[Author name to be supplied]` and finalize the personal contribution statement. The public-review package excludes private raw docs/logs that contained local absolute paths.

Install Tectonic using its [official instructions](https://tectonic-typesetting.github.io/book/latest/installation/).
The review used version 0.17.0. On the original machine the compiler was downloaded
to `.tools/tectonic/tectonic` (ignored by Git); that local path is not included in a clone.
Tectonic automatically runs bibliography/reference passes and may download TeX support
files on the first build. Alternatively, a standard LaTeX installation can use
`pdflatex main.tex`, `bibtex main`, and `pdflatex main.tex` twice; this alternative
was not executed in this review.
