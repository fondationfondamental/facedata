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
- One exception, generated and checked by a test: the data dictionary
  (`facedata/dictionary/`, `dictionary/stats/`) holds figures computed from
  the extractions. Aggregates only, a count from 1 to 4 written -1, no value
  of a text column, no centre, no label of the Excel dictionaries. Never
  commit a build made with `excel_labels: true`.
- A notebook is saved without its results: what appears under a cell is
  patient data. `tests/test_notebook.py` checks it.
- Read an extraction as text, never let pandas guess types:
  `pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-8-sig")`.
  The `.tsv` is the source; the `.xlsx` has Excel-coerced types.
- Read schemas with `yaml.BaseLoader` (every value a string). The default
  loader turns `No` into False and crashes on `0000-00-00`.

## Data dictionary

`facedata/dictionary/face_dictionary.json` describes every delivered variable
of the four cohorts: meaning, construct, direction, derivation, raw column,
range and codes, cohorts and visits, missing values, distribution, what
differs between cohorts. Use it to choose variables and before using one in
an analysis. The page for people is
`facedata/dictionary/FACE-data-dictionary.html`. How to use both: `README.md`.
Fields and rebuild: `dictionary/README.md`.

- A variable id is the column name that `load()` delivers. The file has one
  line per variable: read one record with
  `grep -m1 '^"madrs_total":' facedata/dictionary/face_dictionary.json`, or
  load the file with `json` and filter. Do not print the whole file (18 MB).
- Check `direction` before putting variables on one scale, `harmonisation`
  before stacking cohorts, `missing` and `timepoints` before a longitudinal
  model, and `incomplete` for what no source documents.
- An empty field means "not documented". Never fill it from memory: add it to
  `dictionary/annotations/` with its source, then rebuild.
- The JSON, the page, `dictionary/incomplete.csv` and `dictionary/stats/` are
  generated and committed. Never edit them by hand. Rebuild them when a
  schema, an annotation or an extraction changes, and commit them with that
  change: a test fails when the dictionary and the schemas do not list the
  same variables.

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
