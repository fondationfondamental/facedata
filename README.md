# facedata

Load, harmonise and quality-check data from the FACE psychiatric cohorts
(bipolar disorder, schizophrenia, resistant depression, Asperger).

One module per cohort. Everything specific to an instrument is written in a
small YAML schema; the Python code is generic and stays small.

**Status:** every column of the four extractions (BP, SZ, DR, ASP) is read or
deliberately ignored. The schemas are reviewed tab by tab (BP 125 of 135, SZ 54 of 125,
DR 47 of 137, ASP 43 of 139; the others are drafts): each cohort's progress file
lists the decisions taken and the questions still open
([BP](docs/bp/PROGRESS.md), [SZ](docs/sz/PROGRESS.md), [DR](docs/dr/PROGRESS.md),
[ASP](docs/asp/PROGRESS.md)).

## Read first

| Document | What it tells you |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | What the package returns, the pipeline steps, the flag codes, the QC report |
| [docs/SCHEMA_SPEC.md](docs/SCHEMA_SPEC.md) | Every field a schema may contain, and how to add an instrument |
| [docs/bp/PROGRESS.md](docs/bp/PROGRESS.md) | FACE BP checklist, decisions taken, decisions still open |
| [docs/bp/QUESTIONS.md](docs/bp/QUESTIONS.md) | The open questions of FACE BP as a list to close, sorted by who can close them (the application, the data, a choice of method, the data managers) and by priority, and the state of the norms |
| [docs/sz/PROGRESS.md](docs/sz/PROGRESS.md) | FACE SZ checklist, decisions taken, decisions still open, and what was corrected, separated or flagged |
| [docs/sz/QUESTIONS.md](docs/sz/QUESTIONS.md) | The same questions for FACE SZ |
| [docs/dr/PROGRESS.md](docs/dr/PROGRESS.md) | FACE DR (resistant depression) checklist, decisions taken, decisions still open, and what was corrected, separated or flagged |
| [docs/dr/QUESTIONS.md](docs/dr/QUESTIONS.md) | The same questions for FACE DR |
| [docs/asp/PROGRESS.md](docs/asp/PROGRESS.md) | FACE ASP (autism spectrum, children and adults) checklist, decisions taken, decisions still open. The dictionary arrived after the module was written: every instrument was identified from the data, then checked against it |
| [docs/asp/QUESTIONS.md](docs/asp/QUESTIONS.md) | The same questions for FACE ASP |
| [bipolar-tutorial.ipynb](bipolar-tutorial.ipynb) | A first tour of the FACE BP data for people who do not code much: load, find a variable, plot, follow patients, avoid the traps |
| [schizophrenia-tutorial.ipynb](schizophrenia-tutorial.ipynb) | The same tour for FACE SZ, with a last section that puts the two cohorts in one table |
| [depression-tutorial.ipynb](depression-tutorial.ipynb) | The same tour for FACE DR, with four use cases (response and remission, resistance and treatments, MINI diagnoses, life events) and a last section that puts the three cohorts in one table |
| [autism-tutorial.ipynb](autism-tutorial.ipynb) | The same tour for FACE ASP: children and adults, a dictionary that arrived after the work, four use cases (diagnostic profile, children and adults, comorbidities and treatments, self-reported traits) and a last section that puts the four cohorts in one table |
| [common-instruments.ipynb](common-instruments.ipynb) | The four cohorts together, for transdiagnostic work: the catalogue of the instruments they share, the screening and the inclusion visits in one row per patient, the stacked table, what to check before comparing |

## Use

```bash
uv sync
```

```python
from facedata import bp

result = bp.load("data/bp/BPALL_20261113_2.tsv")

result.data       # one row per patient visit, harmonised
result.patients   # one row per patient
result.flags      # one row per flagged cell, with the raw value
result.qc         # one row per variable
result.treatments # one row per patient and medication, with its dates
result.relatives  # one row per patient and relative: the family history

bp.report(result, "reports/bp")          # open reports/bp/index.html
bp.coverage("data/bp/BPALL_20261113_2.tsv", "thesauri/FACEBP_thesaurus_V4.34.xlsx")
```

Loading everything takes about a minute and a half (a few seconds when you
name the instruments you need), the report about ten minutes.

FACE SZ is read the same way (`from facedata import sz`): every column of its
extraction is read by a schema or ignored with a reason, in 127 instruments.
Its schemas are reviewed tab by tab (54 of 125, the others are drafts) and
the questions of `docs/sz/QUESTIONS.md` stay open until answered;
`docs/sz/PROGRESS.md` logs each decision. The tables of the two
cohorts have the same key columns and the same names for the instruments
they share, so they can be stacked:

```python
import pandas as pd
from facedata import bp, sz

one = bp.load("data/bp/BPALL_20261113_2.tsv", instruments=["identite", "ymrs"])
two = sz.load("data/sz/SZALL_20261117.tsv", instruments=["identite", "ymrs"])
patients = pd.concat([one.patients, two.patients], ignore_index=True)
visits = pd.concat([one.data, two.data], ignore_index=True)
```

FACE DR, the cohort of resistant depression, is read the same way too
(`from facedata import dr`): every one of the 2,375 columns of its extraction
is read by one of 137 schemas or ignored with a reason, and
`docs/dr/PROGRESS.md` logs each decision. Its screening visit is a visit of
its own (`visit == "screening"`), where the MINI is given. Its table
`treatments` holds three lists, named in the column `list`.

FACE ASP, the cohort of autism spectrum disorders, has children and adults
(`from facedata import asp`). Its extraction came without a dictionary: each
of its 4,364 columns is read by one of 138 schemas or ignored with a reason,
and every instrument was identified from its column names, its items and its
stored scores. The thesaurus arrived afterwards: it confirmed the instruments,
corrected eight readings and gave the wording of the lists and the labels; a
code that it does not document is delivered as a numbered code. Its table `treatments` holds eleven lists (the treatments of each
visit, the diseases of each body system, the relatives, the
hospitalisations). `docs/asp/PROGRESS.md` logs each decision.

The first column of every table is `cohort`. A `usubjid` is unique inside a
cohort only (the same number can be another patient in the other cohort), so
the key is `cohort` with `usubjid`. `patients` also holds `fondacode`, the
patient code that is unique across cohorts and does not change from one
extraction to the next.

`facedata.common` is for work across cohorts. Its catalogue lists the
instruments that two cohorts or more share, says which can be stacked as they
are, and names the variables to use; `baseline()` puts the screening visit and
the inclusion visit of a patient in one row:

```python
from facedata import bp, sz, common

table = common.catalogue()                                  # instrument, cohorts, stack (yes / with care / no), use, note
wanted = table[table["stack"] != "no"]

bipolar = bp.load("data/bp/BPALL_20261113_2.tsv", instruments=common.instruments_of("bp", wanted), winsorise=False)
first, source = common.baseline(bipolar)                    # one row per patient, and the visit each instrument comes from
```

## Tutorial

```bash
uv run jupyter lab bipolar-tutorial.ipynb
```

```bash
uv run jupyter lab schizophrenia-tutorial.ipynb
```

```bash
uv run jupyter lab depression-tutorial.ipynb
```

```bash
uv run jupyter lab autism-tutorial.ipynb
```

```bash
uv run jupyter lab common-instruments.ipynb
```

One notebook per cohort. The second one ends with a section that loads the
instruments shared by FACE BP and FACE SZ and stacks the two cohorts; the
third one stacks the three, and the fourth one the four. The fifth notebook
is about the four cohorts together: the catalogue of the common instruments,
one baseline row per patient, and the stacked table.

A notebook opens in the web browser. Run its cells from top to bottom with
`Shift` + `Enter`. What appears under a cell is patient data: clear it
(*Edit*, *Clear Outputs of All Cells*) before you save a notebook that will
be shared or sent to GitHub.

## Tests

```bash
uv run pytest
```

The tests use small hand-written tables. One test file per cohort also checks
the real extraction when it is on the computer, and is skipped otherwise.

## Data

The extractions (`data/`) and the data dictionaries (`thesauri/`) are not part
of the repository. Put them next to the code:

```
data/bp/BPALL_20261113_2.tsv
thesauri/FACEBP_thesaurus_V4.34.xlsx
norms/wais3_vocabulary.csv
```

`norms/` holds the norm tables of the tests (age band and raw score to
scaled score or percentile band). They are copyrighted, so they stay out of the repository
too. Without them the package still loads; the checks that need a table say
so in `result.flags`.

They hold pseudonymised patient records. Never copy rows or identifiers into
code, tests, documents or commits.
