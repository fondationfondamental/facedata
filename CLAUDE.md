# facedata — project conventions

Python package that loads, harmonises and quality-checks FACE cohort
extractions. One module per cohort; FACE BP first, tab by tab, instrument by
instrument. Specs live in `docs/` and are the source of truth:
`docs/ARCHITECTURE.md`, `docs/SCHEMA_SPEC.md`, `docs/bp/PROGRESS.md`,
`docs/sz/PROGRESS.md`, `docs/dr/PROGRESS.md`, `docs/asp/PROGRESS.md`.

## Code style

- Written for undergraduates. Plain functions that take and return DataFrames,
  Series and dicts. The only class is the `Result` named tuple.
- No inheritance, registries, decorators, metaprogramming or clever one-liners.
  A function does one step and fits on a screen.
- Special cases belong in a YAML schema, never in code. If code needs
  `if instrument == ...`, the schema spec is missing a field: change the spec.
- The generic code (`facedata/*.py`, plots and report included) has a budget of
  about 3,700 lines (raised from 3,600 on 2026-11-19 for the expected-value and
  distance scores); it was 3,637 on 2026-11-21. Adding an instrument adds a
  YAML file and, rarely, one small function in `facedata/custom.py`.
- Change `docs/SCHEMA_SPEC.md` before changing what a schema field means.

## Data rules

- `norms/` holds copyrighted norm tables of the test manuals and is
  git-ignored. Never copy a value of a norm table into code, tests, docs or
  commits; tests use made-up tables.
- `data/` and `thesauri/` hold pseudonymised patient records and are
  git-ignored. Never copy patient rows or identifiers into code, tests, docs,
  commits or chat. Report aggregates only. Do not name individual sites in
  committed files.
- Tests use small hand-written tables. No real data in the repository.
- A notebook is saved without its results: what appears under a cell is
  patient data. `tests/test_notebook.py` checks it.
- Read an extraction as text, never let pandas guess types:
  `pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-8-sig")`.
  The `.tsv` is the source; the `.xlsx` has Excel-coerced types.
- Read schemas with `yaml.BaseLoader` (every value a string). The default
  loader turns `No` into False and crashes on `0000-00-00`.

## Working method

- One instrument at a time. An instrument is done when it meets the
  definition of done in `docs/ARCHITECTURE.md`.
- One schema per edition or form of an instrument (BIS-10 and BIS-12, WAIS-III
  and WAIS-IV). Never deliver two editions in one output column, even when
  the extraction stores them in the same raw columns.
- The thesaurus only seeds a schema. Its labels and formulas can be wrong;
  check every scoring formula and column meaning against the data.
- Log each decision and each open question in the progress file of the
  cohort (`docs/bp/PROGRESS.md`, `docs/sz/PROGRESS.md`, `docs/dr/PROGRESS.md`,
  `docs/asp/PROGRESS.md`).
