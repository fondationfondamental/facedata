# facedata

Load, harmonise and quality-check data from the FACE psychiatric cohorts
(bipolar disorder, schizophrenia, resistant depression, Asperger).

One module per cohort. Everything specific to an instrument is written in a
small YAML schema; the Python code is generic and stays small.

**Status:** the pipeline works on FACE BP for the first 130 instrument schemas.
The other BP instruments are added one by one; see
[docs/bp/PROGRESS.md](docs/bp/PROGRESS.md).

## Read first

| Document | What it tells you |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | What the package returns, the pipeline steps, the flag codes, the QC report |
| [docs/SCHEMA_SPEC.md](docs/SCHEMA_SPEC.md) | Every field a schema may contain, and how to add an instrument |
| [docs/bp/PROGRESS.md](docs/bp/PROGRESS.md) | FACE BP checklist, decisions taken, decisions still open |

## Use

```bash
uv sync
```

```python
from facedata import bp

result = bp.load("data/bp/BPALL_20261030.tsv")

result.data       # one row per patient visit, harmonised
result.patients   # one row per patient
result.flags      # one row per flagged cell, with the raw value
result.qc         # one row per variable
result.treatments # one row per patient and medication, with its dates
result.relatives  # one row per patient and relative: the family history

bp.report(result, "reports/bp")          # open reports/bp/index.html
bp.coverage("data/bp/BPALL_20261030.tsv", "thesauri/FACEBP_thesaurus_V4.34.xlsx")
```

Loading takes about 15 seconds, the report about one minute.

## Tests

```bash
uv run pytest
```

The tests use small hand-written tables. One test file also checks the real
extraction when it is on the computer, and is skipped otherwise.

## Data

The extractions (`data/`) and the data dictionaries (`thesauri/`) are not part
of the repository. Put them next to the code:

```
data/bp/BPALL_20261030.tsv
thesauri/FACEBP_thesaurus_V4.34.xlsx
norms/wais3_vocabulary.csv
```

`norms/` holds the norm tables of the tests (age band and raw score to
scaled score or percentile band). They are copyrighted, so they stay out of the repository
too. Without them the package still loads; the checks that need a table say
so in `result.flags`.

They hold pseudonymised patient records. Never copy rows or identifiers into
code, tests, documents or commits.
